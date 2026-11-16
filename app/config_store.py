"""JSON-backed configuration and prompt storage."""
from __future__ import annotations
import json
import os
import re
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CONFIG_FILE = Path(os.getenv("SECURITY_AGENT_CONFIG", ROOT / "config/security_agent.json"))
PROMPTS_DIR = Path(os.getenv("SECURITY_AGENT_PROMPTS", ROOT / "config/prompts"))
PROMPT_ID = re.compile(r"^[a-z0-9_-]{1,64}$")


def _read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _atomic_write(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, ensure_ascii=False)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_name, path)
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)


def load_config() -> dict[str, Any]:
    return _read_json(CONFIG_FILE)


def save_config(payload: dict[str, Any]) -> dict[str, Any]:
    # Keep persisted configuration structured; secrets must be environment references.
    if not isinstance(payload, dict):
        raise ValueError("Configuration must be a JSON object")
    ai = payload.get("ai", {})
    if ai.get("api_key") or ai.get("secret") or ai.get("token"):
        raise ValueError("Do not store secret values in JSON. Use environment-variable references.")
    if not isinstance(payload.get("scanners", {}), dict):
        raise ValueError("scanners must be an object")
    _atomic_write(CONFIG_FILE, payload)
    return payload


def list_prompts() -> list[dict[str, Any]]:
    PROMPTS_DIR.mkdir(parents=True, exist_ok=True)
    prompts = []
    for path in sorted(PROMPTS_DIR.glob("*.json")):
        try:
            item = _read_json(path)
            prompts.append({k: item.get(k) for k in ("id", "name", "version", "enabled")})
        except (OSError, json.JSONDecodeError):
            continue
    return prompts


def get_prompt(prompt_id: str) -> dict[str, Any]:
    if not PROMPT_ID.fullmatch(prompt_id):
        raise ValueError("Invalid prompt id")
    path = PROMPTS_DIR / f"{prompt_id}.json"
    if not path.is_file():
        raise FileNotFoundError(prompt_id)
    return _read_json(path)


def save_prompt(prompt_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    if not PROMPT_ID.fullmatch(prompt_id):
        raise ValueError("Invalid prompt id")
    if payload.get("id") != prompt_id:
        raise ValueError("Prompt id cannot be changed")
    if not isinstance(payload.get("template"), str) or not payload["template"].strip():
        raise ValueError("Prompt template is required")
    path = PROMPTS_DIR / f"{prompt_id}.json"
    old_version = 0
    if path.exists():
        old_version = int(_read_json(path).get("version", 0))
    payload["version"] = max(old_version + 1, int(payload.get("version", 1)))
    _atomic_write(path, payload)
    return payload
