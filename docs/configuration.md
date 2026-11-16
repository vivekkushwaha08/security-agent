# Configuration and prompt editing

Start the service and open `/config` (or `/`):

```bash
uvicorn app.main:app --reload
```

The UI has tabs for general policy, scanners, AI provider, prompt library, and webhook/Git settings.

## Runtime behavior

- The UI reads and writes `config/security_agent.json` through `GET/PUT /api/config`.
- Prompt templates are individual JSON files under `config/prompts`; the UI lists and edits them through `GET/PUT /api/prompts`.
- Every prompt save increments the `version` field.
- The worker-facing `app.prompt_engine.render_prompt(prompt_id, context)` reads the JSON file when called, so a subsequent job sees the latest saved template without a code change.
- `app.scanners.run_enabled_scanners(repository_path, config)` reads scanner settings passed from the loaded config and runs enabled executables without a shell.

For production, mount the config directory as a controlled persistent volume and restrict write access to the service account. Back up the JSON directory and retain prompt revisions in Git or a separate audit store. Protect the UI with authentication/RBAC before network exposure.
