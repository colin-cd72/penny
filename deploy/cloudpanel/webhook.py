#!/usr/bin/env python3
"""
GitHub Webhook Handler for Auto-Deployment
Run as a separate service on a different port (e.g., 9000)
"""

import hashlib
import hmac
import os
import subprocess
from fastapi import FastAPI, Request, HTTPException, Header
from fastapi.responses import PlainTextResponse

app = FastAPI()

# Set this in environment or change here
WEBHOOK_SECRET = os.environ.get("GITHUB_WEBHOOK_SECRET", "change-this-secret")
DEPLOY_SCRIPT = "/home/penny/htdocs/penny.co-l.in/deploy/cloudpanel/auto-deploy.sh"


def verify_signature(payload: bytes, signature: str) -> bool:
    """Verify GitHub webhook signature."""
    if not signature:
        return False

    expected = "sha256=" + hmac.new(
        WEBHOOK_SECRET.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(expected, signature)


@app.post("/webhook/github")
async def github_webhook(
    request: Request,
    x_hub_signature_256: str = Header(None),
    x_github_event: str = Header(None)
):
    """Handle GitHub push webhook."""

    payload = await request.body()

    # Verify signature
    if not verify_signature(payload, x_hub_signature_256):
        raise HTTPException(status_code=401, detail="Invalid signature")

    # Only handle push events to main branch
    if x_github_event == "push":
        data = await request.json()
        ref = data.get("ref", "")

        if ref == "refs/heads/main":
            # Run deployment script in background
            subprocess.Popen(
                ["bash", DEPLOY_SCRIPT],
                stdout=open("/var/log/penny/webhook-deploy.log", "a"),
                stderr=subprocess.STDOUT,
                start_new_session=True
            )
            return PlainTextResponse("Deployment triggered", status_code=200)

        return PlainTextResponse(f"Ignored push to {ref}", status_code=200)

    return PlainTextResponse(f"Ignored event: {x_github_event}", status_code=200)


@app.get("/webhook/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=9000)
