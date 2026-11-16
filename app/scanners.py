"""Deterministic scanner execution adapter.

Run this only inside a disposable, resource-limited worker container. Repository
contents are untrusted. No shell is used and subprocesses have a hard timeout.
"""
from __future__ import annotations
import json
import shutil
import subprocess
from pathlib import Path
from typing import Any


def run_enabled_scanners(repository_path: str | Path, config: dict[str, Any]) -> list[dict[str, Any]]:
    repo = Path(repository_path).resolve()
    if not repo.is_dir():
        raise ValueError("Repository workspace does not exist")
    results = []
    timeout = int(config.get("workers", {}).get("job_timeout_seconds", 900))
    for scanner_name, settings in config.get("scanners", {}).items():
        if not settings.get("enabled"):
            continue
        command = str(settings.get("command", scanner_name))
        executable = shutil.which(command)
        if not executable:
            results.append({"scanner": scanner_name, "status": "unavailable", "error": f"Executable not found: {command}"})
            continue
        args = settings.get("args", [])
        if not isinstance(args, list) or not all(isinstance(arg, str) for arg in args):
            results.append({"scanner": scanner_name, "status": "invalid_config", "error": "Scanner args must be a list of strings"})
            continue
        try:
            completed = subprocess.run(
                [executable, *args, str(repo)],
                cwd=repo,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False,
                shell=False,
                env={"PATH": "/usr/local/bin:/usr/bin:/bin", "HOME": "/tmp"},
            )
            raw = completed.stdout[:5_000_000]
            try:
                parsed = json.loads(raw) if raw.strip() else None
            except json.JSONDecodeError:
                parsed = None
            results.append({
                "scanner": scanner_name,
                "status": "completed" if completed.returncode == 0 else "completed_with_errors",
                "exit_code": completed.returncode,
                "findings": parsed,
                "stdout": raw if parsed is None else None,
                "stderr": completed.stderr[-20000:],
            })
        except subprocess.TimeoutExpired:
            results.append({"scanner": scanner_name, "status": "timeout", "error": f"Exceeded {timeout}s"})
    return results
