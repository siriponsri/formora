# Security policy

Formora is an early local-first proof of concept, not a production approval or
records-management system.

## Reporting a vulnerability

Please open a private GitHub security advisory for this repository. Do not put
secrets, confidential templates, or exploitable sample files in a public issue.

## POC security boundaries

- Only `.docx` and `.xlsx` ZIP-based Office files are accepted.
- Uploads are size-limited and stored under UUID-based paths.
- Macro-enabled Office formats are not supported.
- Originals are copied before deterministic rendering.
- API keys are read from environment variables and never returned by status APIs.
- Generated official documents require human review.

Before any public or multi-user deployment, add authentication, authorization,
malware scanning, retention controls, audit logging, rate limiting, and an
independent security review.

