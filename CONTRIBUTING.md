# Contributing to Formora

Thank you for helping make trustworthy document automation easier to build.

## Development principles

1. Preserve the uploaded Office file as the layout source of truth.
2. Mutate a copy, never the registered original.
3. Validate AI output before it reaches a renderer.
4. Keep mock mode deterministic and offline.
5. Add a property-level preservation test for every renderer change.

## Local contribution flow

1. Fork and clone the repository.
2. Run `./scripts/setup_windows.ps1` in PowerShell on Windows.
3. Create a focused branch.
4. Run `./scripts/test.ps1` before opening a pull request.
5. Describe both the behavior change and its preservation impact.

Please use synthetic files in tests. Never commit confidential templates,
personal data, organization emblems, API keys, or generated local databases.

