# Configuration and prompt editing

Start the service and open `/config`:

```bash
uvicorn app.main:app --reload
```

The UI provides general policy, live intelligence sources, AI provider, prompt library, and webhook/Git settings.

## JSON configuration

- `config/security_agent.json`: operational settings, AI CLI selection, online source endpoints and feature flags.
- `config/prompts/*.json`: editable system instructions and investigation templates. The API increments prompt versions on save.
- Credentials are referenced by environment-variable names only. Secret values must be injected by the runtime secret manager.

## Live online intelligence

The application is designed to query current online sources on each analysis run: OSV.dev, NVD, GitHub Security Advisories, CISA KEV and endoflife.date. Vendor security advisories should be consulted for final affected/fixed version confirmation. No local scanner binary or offline vulnerability database is required.

## AI CLI configuration

Select Claude, Gemini or Copilot CLI and configure its executable/model. The CLI adapter must be tested to confirm live web-search capability is available and enabled. The generated task explicitly requires online research and citations. If web search is not available and the agent cannot supply independently retrieved online evidence, the finding must be UNVERIFIED.

## Security

Do not store secret values in JSON. Do not expose the configuration UI publicly until authentication, authorization and audit logging are implemented. Never execute repository scripts or package lifecycle hooks.
