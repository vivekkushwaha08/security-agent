# Architecture: live online vulnerability validation

## Processing flow

1. Bitbucket webhook validates its HMAC signature and captures the immutable pushed commit SHA.
2. A worker checks out that exact commit to inspect source code and dependency manifests. Repository code is treated as untrusted and is never executed.
3. The agent inventories packages, versions, runtimes, frameworks, and suspicious code paths.
4. Live online lookups query OSV.dev, NVD CVE API 2.0, GitHub Security Advisories, CISA KEV, endoflife.date and official vendor advisories.
5. A provider-specific AI CLI task is assembled from the editable JSON prompt. The CLI must have live web-search capability enabled or receive the online source results from the agent.
6. Every finding is returned with source URLs, dates, exact affected versions, fixed versions, CWE/CVE mapping, reachability evidence, confidence and validation status.
7. Reports are stored as JSON/SARIF and can later be posted to Bitbucket.

## Online-only security intelligence

No local vulnerability database or mandatory offline scanner is used. The agent requires network access to current sources. Git is used to retrieve the exact target commit; it is not a vulnerability scanner.

The live source adapter is in `app/intelligence_sources.py`. It makes runtime requests to OSV, NVD, GitHub Advisories, CISA KEV and endoflife.date. API failures, timeouts and rate limits are explicit errors and must produce an UNVERIFIED result, never a clean result.

## AI CLI requirements

`app/cli_task.py` creates provider-neutral investigation instructions using the current `vulnerability_analysis` JSON prompt. Provider adapters for Claude, Gemini and Copilot must:
- invoke the configured executable with a fixed, reviewed argument list;
- pass prompt content through supported stdin/prompt input, never shell interpolation;
- verify web-search tools are available and enabled for that CLI session;
- preserve source URLs and source dates from the model response;
- reject claims that have no source evidence;
- mark the result UNVERIFIED if live search is unavailable.

Do not assume a CLI has web search simply because it is installed. The CLI integration must be tested against the actual installed version and account/tool configuration.

## Evidence and status contract

Each candidate finding should include package/product, exact detected version, affected version range, CVE/CWE (when supported), severity, exploit preconditions, reachability evidence, fixed version, known-exploited status, direct source URLs, source publication/modified dates, retrieval timestamp and confidence.

Allowed validation statuses:
- `CONFIRMED`: authoritative current sources support the affected version and the finding is relevant to the inspected application.
- `NOT_AFFECTED`: evidence shows the inspected version/configuration is outside the affected range.
- `UNVERIFIED`: web lookup failed, evidence is incomplete, or sources cannot be validated.
- `CONFLICTING_SOURCES`: credible sources disagree.

A CVE affecting a dependency does not alone prove the application's vulnerable code path is reachable. Do not infer "no vulnerabilities" when sources are unavailable.

## Production hardening

- Add durable Redis/Celery or RabbitMQ job processing.
- Implement provider-specific CLI adapters and end-to-end web-search capability tests.
- Add authenticated configuration UI/API with RBAC, audit logs and TLS before network exposure.
- Restrict repository hosts, redirects, outbound destinations and job resource limits.
- Add rate limiting, bounded concurrency, retry/backoff and source-specific API-key management.
- Keep any cache short-lived and informational; force online refresh for final validation.
- Retain prompt versions and report evidence for auditability.
