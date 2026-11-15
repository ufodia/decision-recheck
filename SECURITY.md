# Security and private evidence

Decision Recheck processes untrusted pages, model output, local files, and browser traces. Run it with synthetic inputs in a dedicated test environment and review the allowed domains and actions before executing a case.

## Report a vulnerability

Use the repository's private vulnerability-reporting option when available. Otherwise, contact the maintainer through the contact options on <https://github.com/ufodia> and request a private channel. Do not publish credentials, exploit data, personal records, or an active private target in an issue.

Include the affected version, a minimal synthetic reproduction, expected behavior, actual behavior, and potential impact. Do not probe third-party applications without permission.

## Handling data

- Keep API keys in environment variables. Never commit `.env`, browser storage, credentials, or private run bundles.
- Treat raw screenshots, page excerpts, and traces as potentially sensitive. A manifest hash provides integrity information, not anonymization.
- Review exports before sharing. A locally running cloud-model adapter may still transmit the supplied excerpts to its configured provider.
- The static demo has no server-side model key or live audit backend. Loading its fictional case does not authorize access to another application.

This early release has a bounded test scope. Passing the fixture suite is not a security certification or a replacement for an independent assessment.
