# Architecture and operational notes

## Request flow

1. Bitbucket sends a push webhook to `POST /api/webhooks/bitbucket`.
2. The API validates the HMAC signature and extracts the pushed commit SHA.
3. A queue adapter should enqueue an immutable job containing repository identity, branch and exact commit SHA.
4. A worker clones only allow-listed HTTPS repositories, checks out the exact SHA, and invokes enabled scanners.
5. Scanner output is normalized into a common finding model; CWE and lifecycle enrichment are applied from authoritative feeds.
6. Optional AI prompt templates add triage/explanation. AI output is labeled advisory and is not treated as a confirmed vulnerability without evidence.
7. Reports are written as JSON/SARIF and optionally posted back to Bitbucket.

## Configuration model

- `config/security_agent.json`: operational settings, scanner commands, provider selection and feature flags.
- `config/prompts/*.json`: editable system instructions and prompt templates. The API increments the prompt version on each save.
- Secrets are referenced by environment-variable name only. Secret values must be injected by the runtime secret manager.

## Production hardening still required

- Replace the in-process placeholder queue with Celery/RQ and Redis or RabbitMQ.
- Run workers in disposable containers/VMs with no privileged mode, read-only base filesystem, CPU/memory/PID limits and restricted egress.
- Enforce repository host/workspace allow-lists and validate redirect targets before cloning.
- Add authentication and RBAC to the configuration UI/API before exposing it beyond localhost or a trusted admin network.
- Add CSRF protection if cookie-based authentication is introduced, audit logs, rate limiting and configuration file permissions.
- Run scanners with fixed argument allow-lists; never accept arbitrary shell strings from a webhook or repository.
- Add lifecycle feed ingestion and integration tests for provider CLI output schemas.
- Use a durable queue and persistent job/report store for multi-instance high availability.

## Running

```bash
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

The initial UI is an administrative bootstrap interface. Do not expose it publicly without authentication, TLS and network restrictions.
