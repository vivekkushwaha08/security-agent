# Security Agent

A configurable Python security-review service for Bitbucket repositories. It combines deterministic security scanners with optional AI-assisted triage. Scanner output remains the source of truth; AI findings are advisory and must be verified.

## Features

- FastAPI configuration console and JSON-backed settings.
- Editable, versioned prompt templates stored as JSON.
- Bitbucket webhook endpoint with HMAC-SHA256 verification and commit-SHA pinning.
- Background job interface (initial local queue; Redis/Celery adapter can be enabled).
- Isolated Git checkout, scanner adapters (Semgrep, OSV-Scanner, Trivy, Gitleaks).
- JSON and SARIF-ready report model.
- Docker deployment.

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

Open http://localhost:8000/config. Configuration is persisted under `config/security_agent.json`; prompt templates are under `config/prompts/*.json`.

## Important security notes

- This repository is public. Do not commit API keys, Bitbucket secrets, access tokens, or private repository URLs.
- Keep secrets in environment variables or a secret manager. The UI stores secret *environment-variable names*, not secret values.
- Run repository analysis in disposable, unprivileged containers with restricted network egress and resource limits.
- Webhook payloads are untrusted. Validate signatures, allow-list workspace/repository URLs, pin the event commit SHA, and never execute repository code.
- AI analysis is not a substitute for SAST/SCA/secrets scanning and cannot guarantee complete CWE coverage.

## Configuration

The configuration UI edits safe operational settings in JSON. Environment variable references are used for secrets (for example, `BITBUCKET_WEBHOOK_SECRET`, `ANTHROPIC_API_KEY`). Prompt JSON can be edited independently and is loaded when a job starts.

## Scanner prerequisites

Install the tools you enable and make their binaries available on PATH:

- Semgrep: `semgrep`
- OSV-Scanner: `osv-scanner`
- Trivy: `trivy`
- Gitleaks: `gitleaks`

## Development

```bash
pytest
```

See [docs/architecture.md](docs/architecture.md) for the processing flow and deployment guidance.
