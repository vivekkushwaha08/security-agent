# Security Agent

A Python security investigation agent for Bitbucket repositories. It inspects an exact Git commit, prepares an investigation task for an AI CLI (Claude, Gemini or Copilot), and validates candidate vulnerabilities against **live online security sources**.

## Design principles

- No mandatory local SAST/SCA/secrets-scanner binaries or offline vulnerability database.
- Live lookups against OSV.dev, NVD, GitHub Security Advisories, CISA KEV, vendor advisories and lifecycle sources.
- AI CLI findings require direct online evidence, URLs and source dates. Model memory alone is not proof.
- A failed or unavailable online lookup produces `UNVERIFIED`, never a false "clean" result.
- The target commit is pinned by SHA. Repository content is untrusted and is never executed.

## Features

- FastAPI configuration console and JSON-backed settings.
- Editable, versioned prompt templates stored as JSON.
- Bitbucket webhook signature validation and commit-SHA extraction.
- Live online intelligence adapters in `app/intelligence_sources.py`.
- Provider-neutral CLI investigation task builder in `app/cli_task.py`.
- JSON/SARIF-ready reporting foundation and Docker deployment.

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

Open http://localhost:8000/config. Settings are stored in `config/security_agent.json`; editable prompts are under `config/prompts/*.json`.

## Online intelligence sources

- OSV.dev API: package, ecosystem and exact-version queries.
- NVD CVE API 2.0: CVE metadata, affected ranges and CWE/CVSS details.
- GitHub Security Advisories API: package advisory lookups.
- CISA KEV: known-exploited vulnerability status.
- Vendor security advisories: authoritative affected/fixed version confirmation.
- endoflife.date and vendor lifecycle pages: product support/EOL checks.

Set `NVD_API_KEY` and `GITHUB_TOKEN` in the worker environment where applicable. Never store credentials in JSON or commit them.

## AI CLI web search

Installing Claude, Gemini or Copilot CLI does not automatically guarantee web search. The selected CLI adapter must verify that live web search/tools are enabled for the actual CLI session. The generated task explicitly requires current web research and citations. If the CLI cannot search, the agent must rely only on separately retrieved online evidence or mark the result UNVERIFIED.

## Security

This repository is public. Never commit credentials. Keep the configuration UI restricted to localhost or a trusted admin network until authentication/RBAC is implemented. Run analysis in isolated workers with network egress allow-lists. Never execute repository scripts, build hooks, package lifecycle scripts or arbitrary commands from webhook/repository content.

See [docs/architecture.md](docs/architecture.md) and [docs/configuration.md](docs/configuration.md).
