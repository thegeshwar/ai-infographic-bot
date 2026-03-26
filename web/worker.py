"""
Y Vault Mac Worker — connects to VPS via SSE, picks up jobs, executes them.

Usage:
    python3 -m web.worker --url https://y.thegeshwar.com --key YOUR_API_KEY

The worker:
1. Opens a persistent SSE connection to /api/stream
2. When a job arrives, claims it via POST /api/job/{id}/claim
3. Executes the job (deploy = run posting pipeline, rework = run Claude Code)
4. Reports result via POST /api/job/{id}/complete or /api/job/{id}/fail
5. If disconnected, auto-reconnects and catches up on missed jobs
"""

import argparse
import json
import subprocess
import sys
import time

import httpx

DEFAULT_URL = "https://y.thegeshwar.com"


def api(base_url: str, key: str, method: str, path: str, body: dict = None) -> dict:
    """Make an authenticated API call."""
    headers = {"Authorization": f"Bearer {key}"}
    with httpx.Client(timeout=30) as client:
        if method == "GET":
            r = client.get(f"{base_url}{path}", headers=headers)
        elif method == "POST":
            r = client.post(f"{base_url}{path}", headers=headers, json=body or {})
        r.raise_for_status()
        return r.json()


def execute_deploy(post: dict, job: dict) -> dict:
    """Execute a deploy job — run the posting pipeline."""
    # TODO: Integrate with actual linkedin-poster / infographic bot posting flow
    # For now, this is a placeholder that shows what the worker would do
    print(f"  [DEPLOY] Would post: {post.get('headline', 'unknown')}")
    print(f"  [DEPLOY] Caption: {(post.get('caption', '') or '')[:80]}...")
    print(f"  [DEPLOY] Platforms: {json.loads(job.get('payload', '{}')).get('platforms', [])}")

    # When ready, replace this with actual posting logic:
    # subprocess.run(["python3", "-m", "linkedin_poster.post", ...])
    return {"platforms": ["linkedin", "instagram"], "message": "Posted successfully"}


def execute_rework(post: dict, job: dict) -> dict:
    """Execute a rework job — run Claude to rewrite caption."""
    payload = json.loads(job.get("payload", "{}"))
    prompt = payload.get("prompt", "")
    current_caption = post.get("caption", "")
    headline = post.get("headline", "")

    print(f"  [REWORK] Headline: {headline}")
    print(f"  [REWORK] Prompt: {prompt}")

    # TODO: Integrate with Claude Code CLI or Anthropic API
    # For now, placeholder
    # When ready:
    # result = subprocess.run(
    #     ["claude", "-p", f"Rewrite this LinkedIn caption for CU Circuits. {prompt}\n\nCurrent caption:\n{current_caption}"],
    #     capture_output=True, text=True
    # )
    # new_caption = result.stdout.strip()
    return {"caption": current_caption, "message": "Rework placeholder — integrate Claude CLI"}


def process_job(base_url: str, key: str, job_id: int):
    """Claim, execute, and report on a single job."""
    # Claim
    try:
        api(base_url, key, "POST", f"/api/job/{job_id}/claim")
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 409:
            print(f"  Job {job_id} already claimed, skipping")
            return
        raise

    # Get full job + post data
    data = api(base_url, key, "GET", f"/api/job/{job_id}")
    job = data["job"]
    post = data["post"]
    job_type = job["type"]

    print(f"  Processing job {job_id}: {job_type} for post {job['post_id']}")

    try:
        if job_type == "deploy":
            result = execute_deploy(post, job)
        elif job_type == "rework":
            result = execute_rework(post, job)
        else:
            raise ValueError(f"Unknown job type: {job_type}")

        api(base_url, key, "POST", f"/api/job/{job_id}/complete", {"result": result})
        print(f"  Job {job_id} completed successfully")

    except Exception as e:
        error_msg = f"{type(e).__name__}: {str(e)}"
        print(f"  Job {job_id} failed: {error_msg}")
        try:
            api(base_url, key, "POST", f"/api/job/{job_id}/fail", {"error": error_msg})
        except Exception:
            print(f"  Could not report failure for job {job_id}")


def listen(base_url: str, key: str):
    """Connect to SSE stream and process jobs as they arrive."""
    headers = {"Authorization": f"Bearer {key}"}
    url = f"{base_url}/api/stream"

    while True:
        try:
            print(f"Connecting to {url}...")
            with httpx.Client(timeout=httpx.Timeout(connect=10, read=60, write=10, pool=10)) as client:
                with client.stream("GET", url, headers=headers) as response:
                    response.raise_for_status()
                    print("Connected. Listening for jobs...")
                    buffer = ""
                    for chunk in response.iter_text():
                        buffer += chunk
                        while "\n" in buffer:
                            line, buffer = buffer.split("\n", 1)
                            line = line.strip()
                            if not line or line.startswith(":"):
                                continue
                            if line.startswith("data: "):
                                try:
                                    data = json.loads(line[6:])
                                    job_id = data["job_id"]
                                    print(f"\nJob received: #{job_id} ({data['type']})")
                                    process_job(base_url, key, job_id)
                                except (json.JSONDecodeError, KeyError) as e:
                                    print(f"Bad SSE data: {e}")

        except httpx.ReadTimeout:
            # Normal — keepalive timeout, just reconnect
            print("Stream timeout, reconnecting...")
        except (httpx.ConnectError, httpx.RemoteProtocolError) as e:
            print(f"Disconnected: {type(e).__name__}. Reconnecting in 5s...")
            time.sleep(5)
        except KeyboardInterrupt:
            print("\nWorker stopped.")
            sys.exit(0)
        except Exception as e:
            print(f"Error: {type(e).__name__}: {e}. Reconnecting in 10s...")
            time.sleep(10)


def main():
    parser = argparse.ArgumentParser(description="Y Vault Mac Worker")
    parser.add_argument("--url", default=DEFAULT_URL, help="VPS base URL")
    parser.add_argument("--key", required=True, help="API key")
    args = parser.parse_args()

    print(f"Y Vault Worker")
    print(f"  Server: {args.url}")
    print(f"  Key: {args.key[:8]}...")
    print()

    listen(args.url, args.key)


if __name__ == "__main__":
    main()
