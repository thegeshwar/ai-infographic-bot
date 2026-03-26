"""Y Vault — FastAPI application."""

import json
import os
import time
import uuid
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

import httpx
from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from web.auth import authenticate, create_session, validate_session, delete_session
from web.db import init_db, get_posts, get_post, update_post, mark_posted, insert_post, get_counts

# Rate limiter: track login attempts per IP
_login_attempts: dict[str, list[float]] = defaultdict(list)
LOGIN_RATE_LIMIT = 5  # max attempts
LOGIN_RATE_WINDOW = 60  # per 60 seconds

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
API_KEY = os.getenv("Y_API_KEY", "change-me-in-production")
MAC_WEBHOOK_URL = os.getenv("Y_MAC_WEBHOOK", "http://localhost:9876")
SCHEDULE_HOUR = int(os.getenv("SCHEDULE_HOUR", "8"))

# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------
app = FastAPI(docs_url=None, redoc_url=None)

BASE_DIR = Path(__file__).parent
STATIC_DIR = BASE_DIR / "static"
STATIC_DIR.mkdir(exist_ok=True)
(STATIC_DIR / "images").mkdir(exist_ok=True)

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

# ---------------------------------------------------------------------------
# Template filters
# ---------------------------------------------------------------------------

def filter_format_time(value: str | None) -> str:
    """Parse ISO datetime string, return 'Mar 25, 8:04 PM' format."""
    if not value:
        return ""
    try:
        dt = datetime.fromisoformat(value)
        hour = dt.hour % 12 or 12
        ampm = "AM" if dt.hour < 12 else "PM"
        minute = f"{dt.minute:02d}"
        return f"{dt.strftime('%b')} {dt.day}, {hour}:{minute} {ampm}"
    except (ValueError, AttributeError):
        return str(value)


def filter_domain(value: str | None) -> str:
    """Extract domain from URL."""
    if not value:
        return ""
    try:
        return urlparse(value).netloc or value
    except Exception:
        return str(value)


def filter_join(value, sep: str = " ") -> str:
    """Convert hashtags (JSON string or list) to space-separated string."""
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except (json.JSONDecodeError, TypeError):
            return value
    if isinstance(value, list):
        return sep.join(str(v) for v in value)
    return str(value) if value else ""


templates.env.filters["format_time"] = filter_format_time
templates.env.filters["domain"] = filter_domain
templates.env.filters["join"] = filter_join

# ---------------------------------------------------------------------------
# Auth helper
# ---------------------------------------------------------------------------

async def get_user(request: Request) -> int | None:
    """Read session cookie and validate. Returns user_id or None."""
    session_id = request.cookies.get("session")
    if not session_id:
        return None
    return await validate_session(session_id)


def parse_hashtags(post: dict) -> dict:
    """Parse hashtags JSON string into a list if needed."""
    ht = post.get("hashtags")
    if isinstance(ht, str):
        try:
            post["hashtags"] = json.loads(ht)
        except (json.JSONDecodeError, TypeError):
            post["hashtags"] = []
    elif ht is None:
        post["hashtags"] = []
    return post

# ---------------------------------------------------------------------------
# Startup
# ---------------------------------------------------------------------------

@app.on_event("startup")
async def startup():
    await init_db()

# ---------------------------------------------------------------------------
# Auth routes
# ---------------------------------------------------------------------------

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    user = await get_user(request)
    if user:
        return RedirectResponse("/", status_code=302)
    csrf = str(uuid.uuid4())
    response = templates.TemplateResponse("login.html", {
        "request": request,
        "csrf_token": csrf,
        "error": None,
    })
    response.set_cookie("csrf", csrf, httponly=True, samesite="strict", secure=True)
    return response


@app.post("/login")
async def login_submit(request: Request, email: str = Form(...), password: str = Form(...), csrf_token: str = Form("")):
    # CSRF validation
    csrf_cookie = request.cookies.get("csrf", "")
    if not csrf_token or csrf_token != csrf_cookie:
        csrf = str(uuid.uuid4())
        response = templates.TemplateResponse("login.html", {
            "request": request, "csrf_token": csrf, "error": "Invalid request. Please try again.",
        })
        response.set_cookie("csrf", csrf, httponly=True, samesite="strict", secure=True)
        return response

    # Rate limiting
    client_ip = request.client.host if request.client else "unknown"
    now = time.time()
    _login_attempts[client_ip] = [t for t in _login_attempts[client_ip] if now - t < LOGIN_RATE_WINDOW]
    if len(_login_attempts[client_ip]) >= LOGIN_RATE_LIMIT:
        csrf = str(uuid.uuid4())
        response = templates.TemplateResponse("login.html", {
            "request": request, "csrf_token": csrf, "error": "Too many attempts. Try again later.",
        })
        response.set_cookie("csrf", csrf, httponly=True, samesite="strict", secure=True)
        return response
    _login_attempts[client_ip].append(now)

    user_id = await authenticate(email, password)
    if not user_id:
        csrf = str(uuid.uuid4())
        response = templates.TemplateResponse("login.html", {
            "request": request,
            "csrf_token": csrf,
            "error": "Invalid email or password.",
        })
        response.set_cookie("csrf", csrf, httponly=True, samesite="strict", secure=True)
        return response
    session_id = await create_session(user_id)
    response = RedirectResponse("/", status_code=302)
    response.set_cookie(
        "session", session_id,
        httponly=True, secure=True, samesite="strict",
        max_age=30 * 24 * 60 * 60,
    )
    return response


@app.post("/logout")
async def logout(request: Request):
    session_id = request.cookies.get("session")
    if session_id:
        await delete_session(session_id)
    response = RedirectResponse("/login", status_code=302)
    response.delete_cookie("session")
    return response

# ---------------------------------------------------------------------------
# Queue route
# ---------------------------------------------------------------------------

@app.get("/", response_class=HTMLResponse)
async def queue_page(request: Request, status: str = "all"):
    user = await get_user(request)
    if not user:
        return RedirectResponse("/login", status_code=302)

    if status == "all":
        ready = await get_posts("ready")
        posted = await get_posts("posted")
        posts = sorted(ready + posted, key=lambda p: p["created_at"], reverse=True)
    else:
        posts = await get_posts(status)

    posts = [parse_hashtags(p) for p in posts]
    counts = await get_counts()

    return templates.TemplateResponse("queue.html", {
        "request": request,
        "posts": posts,
        "counts": counts,
        "filter": status,
        "schedule_hour": SCHEDULE_HOUR,
    })

# ---------------------------------------------------------------------------
# Detail route
# ---------------------------------------------------------------------------

@app.get("/post/{post_id}", response_class=HTMLResponse)
async def detail_page(request: Request, post_id: int):
    user = await get_user(request)
    if not user:
        return RedirectResponse("/login", status_code=302)

    post = await get_post(post_id)
    if not post:
        raise HTTPException(404, "Post not found")

    post = parse_hashtags(post)

    return templates.TemplateResponse("detail.html", {
        "request": request,
        "post": post,
    })

# ---------------------------------------------------------------------------
# API routes
# ---------------------------------------------------------------------------

@app.get("/api/posts")
async def api_list_posts(request: Request, status: str = "all"):
    user = await get_user(request)
    if not user:
        raise HTTPException(401, "Not authenticated")
    if status == "all":
        ready = await get_posts("ready")
        posted = await get_posts("posted")
        posts = sorted(ready + posted, key=lambda p: p["created_at"], reverse=True)
    else:
        posts = await get_posts(status)
    return JSONResponse([parse_hashtags(p) for p in posts])


@app.patch("/api/post/{post_id}")
async def api_update_post(request: Request, post_id: int):
    user = await get_user(request)
    if not user:
        raise HTTPException(401, "Not authenticated")

    body = await request.json()
    caption = body.get("caption", "")
    hashtags_str = body.get("hashtags", "")
    hashtags_list = [t.strip() for t in hashtags_str.split() if t.strip()]

    await update_post(post_id, caption, hashtags_list)
    return JSONResponse({"ok": True})


@app.post("/api/post/{post_id}/deploy")
async def api_deploy_post(request: Request, post_id: int):
    user = await get_user(request)
    if not user:
        raise HTTPException(401, "Not authenticated")

    post = await get_post(post_id)
    if not post:
        raise HTTPException(404, "Post not found")
    if post["status"] != "ready":
        raise HTTPException(400, "Post is not ready")

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                f"{MAC_WEBHOOK_URL}/webhook/deploy",
                json=dict(post),
            )
            resp.raise_for_status()
    except Exception as e:
        return JSONResponse(
            {"error": f"Could not reach Mac for posting: {type(e).__name__}. Post NOT deployed."},
            status_code=502,
        )

    await mark_posted(post_id, ["linkedin", "instagram"])
    return JSONResponse({"ok": True, "status": "posted"})


@app.post("/api/post/{post_id}/rework")
async def api_rework_post(request: Request, post_id: int):
    user = await get_user(request)
    if not user:
        raise HTTPException(401, "Not authenticated")

    body = await request.json()
    prompt = body.get("prompt", "")
    if not prompt:
        raise HTTPException(400, "Prompt is required")

    post = await get_post(post_id)
    if not post:
        raise HTTPException(404, "Post not found")

    try:
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                f"{MAC_WEBHOOK_URL}/webhook/rework",
                json={"post_id": post_id, "prompt": prompt, "post": dict(post)},
            )
            resp.raise_for_status()
            result = resp.json()
    except Exception as e:
        return JSONResponse(
            {"error": f"Could not reach Mac for rework: {type(e).__name__}. Try again when Mac is online."},
            status_code=502,
        )

    if result.get("caption"):
        hashtags = result.get("hashtags", post.get("hashtags", []))
        if isinstance(hashtags, str):
            try:
                hashtags = json.loads(hashtags)
            except (json.JSONDecodeError, TypeError):
                hashtags = []
        await update_post(post_id, result["caption"], hashtags)

    return JSONResponse({"ok": True, "result": result})


@app.post("/api/ingest")
async def api_ingest(request: Request):
    auth_header = request.headers.get("authorization", "")
    if auth_header != f"Bearer {API_KEY}":
        raise HTTPException(401, "Invalid API key")

    body = await request.json()
    if not body.get("headline"):
        raise HTTPException(400, "headline is required")

    post_id = await insert_post(body)
    return JSONResponse({"ok": True, "post_id": post_id}, status_code=201)
