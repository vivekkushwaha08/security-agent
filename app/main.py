from __future__ import annotations
import hashlib
import hmac
import json
import os
from pathlib import Path
from typing import Any
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from app import config_store

app = FastAPI(title="Security Agent", version="0.1.0")
BASE = Path(__file__).resolve().parent
app.mount("/static", StaticFiles(directory=BASE / "static"), name="static")


class ConfigPayload(BaseModel):
    config: dict[str, Any]


class PromptPayload(BaseModel):
    prompt: dict[str, Any]


@app.get("/", response_class=HTMLResponse)
async def home():
    return (BASE / "templates" / "config.html").read_text(encoding="utf-8")


@app.get("/health")
async def health():
    return {"status": "ok", "service": "security-agent"}


@app.get("/api/config")
async def read_config():
    try:
        return config_store.load_config()
    except (OSError, json.JSONDecodeError) as exc:
        raise HTTPException(500, f"Unable to read configuration: {exc}") from exc


@app.put("/api/config")
async def write_config(body: ConfigPayload):
    try:
        return {"saved": True, "config": config_store.save_config(body.config)}
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc


@app.get("/api/prompts")
async def prompts():
    return config_store.list_prompts()


@app.get("/api/prompts/{prompt_id}")
async def read_prompt(prompt_id: str):
    try:
        return config_store.get_prompt(prompt_id)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    except FileNotFoundError as exc:
        raise HTTPException(404, "Prompt not found") from exc


@app.put("/api/prompts/{prompt_id}")
async def write_prompt(prompt_id: str, body: PromptPayload):
    try:
        return {"saved": True, "prompt": config_store.save_prompt(prompt_id, body.prompt)}
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc


@app.post("/api/webhooks/bitbucket")
async def bitbucket_webhook(request: Request):
    raw = await request.body()
    config = config_store.load_config()
    settings = config.get("webhook", {})
    if not settings.get("enabled", True):
        raise HTTPException(404, "Webhook disabled")
    if settings.get("require_signature", True):
        secret_name = settings.get("secret_env", "BITBUCKET_WEBHOOK_SECRET")
        secret = os.getenv(secret_name)
        signature = request.headers.get("X-Hub-Signature")
        if not secret or not signature:
            raise HTTPException(401, "Missing webhook signature configuration")
        expected = "sha256=" + hmac.new(secret.encode(), raw, hashlib.sha256).hexdigest()
        if not hmac.compare_digest(expected, signature):
            raise HTTPException(401, "Invalid webhook signature")
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise HTTPException(400, "Invalid JSON payload") from exc
    # Bitbucket Cloud push payload: use the event commit hash; never resolve mutable HEAD.
    changes = payload.get("push", {}).get("changes", [])
    commits = [c.get("new", {}).get("target", {}).get("hash") for c in changes]
    commit_sha = next((value for value in commits if value), None)
    if not commit_sha:
        raise HTTPException(422, "No pushed commit SHA found in payload")
    # Queue integration is deliberately a separate adapter; do not execute repository code here.
    return {"accepted": True, "commit_sha": commit_sha, "status": "queued-adapter-not-configured"}


@app.get("/api/prompts/{prompt_id}/render-preview")
async def prompt_preview(prompt_id: str):
    try:
        prompt = config_store.get_prompt(prompt_id)
        return {"id": prompt_id, "version": prompt.get("version"), "template": prompt.get("template", "")}
    except (ValueError, FileNotFoundError) as exc:
        raise HTTPException(404, "Prompt not found") from exc
