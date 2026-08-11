# POC scope and safety boundary

## Goal

Prove one concrete statement locally:

> A user can upload a styled DOCX template, describe a new Thai document, and receive an editable DOCX
> where intended content changed while native formatting remained acceptably intact.

XLSX value insertion is the secondary proof.

## Included

- Windows + VS Code local workflow.
- Next.js, FastAPI, SQLite, local filesystem.
- Macro-free DOCX and XLSX upload.
- Real native structure inspection.
- Explicit DOCX placeholder and XLSX cell bindings.
- Human manifest review.
- Deterministic offline mock drafting.
- Optional Typhoon text adapter.
- Optional LibreOffice PDF preview.
- Synthetic fixtures and preservation tests.

## Explicitly excluded

- Deployment and hosted databases/storage.
- Accounts, authentication, collaboration, RBAC, and payments.
- Fine-tuning, vector databases, agent frameworks, and queues.
- Automated procurement or legal approval.
- Arbitrary reconstruction from scanned PDFs.
- LaTeX as a canonical document format.
- Guaranteed support for all Microsoft Office features.

## Owner gates

1. **DOCX value proof:** Does the generated Word file retain acceptable native formatting?
2. **XLSX value proof:** Does workbook population preserve formulas and layout?
3. **Product proof:** Does the combined flow save enough work to justify cloud engineering?

No deployment work should begin before these gates are answered.

