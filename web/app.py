"""Y Vault — FastAPI application."""

import asyncio
import json
import os
import time
import uuid
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from web.auth import authenticate, create_session, validate_session, delete_session
from web.db import (
    init_db, get_posts, get_post, update_post, mark_posted, insert_post, get_counts,
    create_job, get_pending_jobs, claim_job, complete_job, fail_job, get_job, get_jobs_for_post,
)

# Rate limiter: track login attempts per IP
_login_attempts: dict[str, list[float]] = defaultdict(list)
LOGIN_RATE_LIMIT = 5  # max attempts
LOGIN_RATE_WINDOW = 60  # per 60 seconds

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
API_KEY = os.getenv("Y_API_KEY", "change-me-in-production")
SCHEDULE_HOUR = int(os.getenv("SCHEDULE_HOUR", "10"))  # 10 AM IST
SCHEDULE_TZ_OFFSET = float(os.getenv("SCHEDULE_TZ_OFFSET", "5.5"))  # IST = UTC+5:30

# SSE: connected worker streams. Each is an asyncio.Queue.
_worker_streams: list[asyncio.Queue] = []

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
        "schedule_tz_offset": SCHEDULE_TZ_OFFSET,
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


async def notify_workers(job_id: int, job_type: str, post_id: int):
    """Push a new job event to all connected worker streams."""
    event = json.dumps({"job_id": job_id, "type": job_type, "post_id": post_id})
    dead = []
    for q in _worker_streams:
        try:
            q.put_nowait(event)
        except asyncio.QueueFull:
            dead.append(q)
    for q in dead:
        _worker_streams.remove(q)


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
    job_id = await create_job(post_id, "deploy", {"platforms": ["linkedin", "instagram"]})
    await notify_workers(job_id, "deploy", post_id)
    return JSONResponse({"ok": True, "job_id": job_id})


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
    job_id = await create_job(post_id, "rework", {"prompt": prompt})
    await notify_workers(job_id, "rework", post_id)
    return JSONResponse({"ok": True, "job_id": job_id})


# ---------------------------------------------------------------------------
# SSE stream for Mac worker
# ---------------------------------------------------------------------------

@app.get("/api/stream")
async def sse_stream(request: Request):
    """SSE endpoint for Mac worker. Authenticated via API key."""
    auth = request.headers.get("authorization", "")
    if auth != f"Bearer {API_KEY}":
        raise HTTPException(401, "Invalid API key")

    q: asyncio.Queue = asyncio.Queue(maxsize=100)
    _worker_streams.append(q)

    async def event_generator():
        try:
            # On connect, send any pending jobs as catchup
            pending = await get_pending_jobs()
            for job in pending:
                data = json.dumps({"job_id": job["id"], "type": job["type"], "post_id": job["post_id"]})
                yield f"data: {data}\n\n"
            # Then wait for new events
            while True:
                if await request.is_disconnected():
                    break
                try:
                    event = await asyncio.wait_for(q.get(), timeout=30)
                    yield f"data: {event}\n\n"
                except asyncio.TimeoutError:
                    yield ": keepalive\n\n"
        finally:
            if q in _worker_streams:
                _worker_streams.remove(q)

    return StreamingResponse(event_generator(), media_type="text/event-stream")


# ---------------------------------------------------------------------------
# Job API (for Mac worker)
# ---------------------------------------------------------------------------

@app.get("/api/job/{job_id}")
async def api_get_job(request: Request, job_id: int):
    """Get job details. Used by Mac worker to get full payload."""
    auth = request.headers.get("authorization", "")
    if auth != f"Bearer {API_KEY}":
        # Also allow session auth for the web UI polling
        user = await get_user(request)
        if not user:
            raise HTTPException(401, "Not authenticated")
    job = await get_job(job_id)
    if not job:
        raise HTTPException(404, "Job not found")
    # Include full post data
    post = await get_post(job["post_id"])
    return JSONResponse({"job": job, "post": post})


@app.post("/api/job/{job_id}/claim")
async def api_claim_job(request: Request, job_id: int):
    """Mac worker claims a job before processing."""
    auth = request.headers.get("authorization", "")
    if auth != f"Bearer {API_KEY}":
        raise HTTPException(401, "Invalid API key")
    claimed = await claim_job(job_id)
    if not claimed:
        raise HTTPException(409, "Job already claimed or not pending")
    return JSONResponse({"ok": True})


@app.post("/api/job/{job_id}/complete")
async def api_complete_job(request: Request, job_id: int):
    """Mac worker reports job completion."""
    auth = request.headers.get("authorization", "")
    if auth != f"Bearer {API_KEY}":
        raise HTTPException(401, "Invalid API key")
    body = await request.json()
    result = body.get("result", {})
    job = await get_job(job_id)
    if not job:
        raise HTTPException(404, "Job not found")

    # Apply results based on job type
    if job["type"] == "deploy":
        await mark_posted(job["post_id"], result.get("platforms", ["linkedin", "instagram"]))
    elif job["type"] == "rework":
        if result.get("caption"):
            hashtags = result.get("hashtags", [])
            if isinstance(hashtags, str):
                try:
                    hashtags = json.loads(hashtags)
                except (json.JSONDecodeError, TypeError):
                    hashtags = []
            await update_post(job["post_id"], result["caption"], hashtags)

    await complete_job(job_id, result)
    return JSONResponse({"ok": True})


@app.post("/api/job/{job_id}/fail")
async def api_fail_job(request: Request, job_id: int):
    """Mac worker reports job failure."""
    auth = request.headers.get("authorization", "")
    if auth != f"Bearer {API_KEY}":
        raise HTTPException(401, "Invalid API key")
    body = await request.json()
    error = body.get("error", "Unknown error")
    await fail_job(job_id, error)
    return JSONResponse({"ok": True})


@app.get("/api/post/{post_id}/jobs")
async def api_post_jobs(request: Request, post_id: int):
    """Get job history for a post. Used by detail page for status polling."""
    user = await get_user(request)
    if not user:
        raise HTTPException(401, "Not authenticated")
    jobs = await get_jobs_for_post(post_id)
    return JSONResponse(jobs)


@app.get("/api/worker/status")
async def api_worker_status(request: Request):
    """Check if any Mac worker is connected."""
    user = await get_user(request)
    if not user:
        raise HTTPException(401, "Not authenticated")
    return JSONResponse({"connected": len(_worker_streams) > 0, "workers": len(_worker_streams)})


# ---------------------------------------------------------------------------
# Ingest API
# ---------------------------------------------------------------------------

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
