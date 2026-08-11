# Codex handoff

## Implemented in this starter

- Local Next.js/FastAPI application and five-page golden-path UI.
- SQLite templates and generations metadata with automatic initialization.
- UUID-based local storage and Office ZIP validation.
- DOCX native inspection and split-run placeholder rendering from a copy.
- XLSX native inspection and reviewed cell-binding rendering from a copy.
- Deterministic mock provider and validated OpenTyphoon adapter.
- Optional LibreOffice preview adapter.
- Synthetic fixtures, API flow tests, and DOCX/XLSX preservation tests.
- Windows setup, run, doctor, and full-check scripts.

## Intentionally incomplete

- DOCX content controls and anchor-based binding.
- Rich structured-content editing beyond plain strings/numbers.
- Visual page preview and overflow detection.
- Typhoon retry/repair evaluation against a template corpus.
- XLSX formula recalculation (the renderer preserves formulas but does not calculate them).
- Cloud storage, PostgreSQL, authentication, deployment, and multi-user behavior.

## Validation status at handoff

- `ruff check apps/api scripts` — passed.
- `pytest` — 6 tests passed (DOCX, XLSX, AI parser, health, and API golden flow).
- `npm run lint` — passed with zero warnings.
- `npm run typecheck` — passed.
- `npm run build` — passed on Next.js 16.3.0; all five requested application routes compiled.
- Local smoke test — API health, dashboard, and upload page returned HTTP 200.

## First five recommended Codex tasks

1. Add a DOCX content-control inspector/renderer with synthetic fixtures and preservation tests.
2. Replace the simple manifest field list with an accessible binding picker grounded in the structural map.
3. Add Office-to-PDF page preview plus before/after visual comparison when LibreOffice is installed.
4. Build a Typhoon structured-output repair loop with saved redacted test cases and explicit failure metrics.
5. Add generation validation for unresolved placeholders, unexpected page-count changes, and text overflow risk.

## Invariants Codex must preserve

- Never mutate a registered original.
- Never rebuild the complete Office layout from AI output.
- Never let unvalidated AI JSON reach a renderer.
- Never require network access in mock-mode tests.
- Never commit `.env`, local databases, generated outputs, or real organization templates.
- Keep PDF/image OCR separate from native Office template preservation.

## Current risks

- Office libraries can normalize unsupported extension features during save.
- Placeholder replacement inherits the first overlapping run's formatting; deliberately mixed-format placeholders need a UX rule.
- Cell binding can overwrite a formula if a reviewer explicitly binds to that formula cell; the UI should warn before saving such a manifest.
- Local POC endpoints have no authentication and must not be exposed publicly.

Run `scripts/test.ps1` after every renderer or schema change.
