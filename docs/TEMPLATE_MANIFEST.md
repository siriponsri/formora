# Template manifest reference

The manifest is the reviewed permission boundary between semantic content and native Office layout.

## DOCX placeholder example

```json
{
  "template_id": "3f4b5d5d-0000-0000-0000-000000000000",
  "name": "Procurement approval memo",
  "file_type": "docx",
  "original_file": "original.docx",
  "document_type": "internal_memo",
  "fields": [
    {
      "id": "subject",
      "label": "เรื่อง",
      "required": true,
      "content_type": "short_text",
      "binding": {
        "strategy": "placeholder",
        "placeholder": "{{subject}}"
      }
    }
  ]
}
```

## XLSX cell example

```json
{
  "id": "vendor_a_price",
  "label": "ราคาผู้เสนอ A",
  "required": true,
  "content_type": "number",
  "binding": {
    "strategy": "cell",
    "sheet": "Price Comparison",
    "cell": "D10"
  }
}
```

If `sheet` is blank, the renderer uses the first worksheet. Every field ID must start with a letter and
contain only letters, digits, `_`, or `-`.

## Design rules

- A manifest may name only deterministic locations the user can review.
- DOCX placeholder and XLSX cell strategies are the only v0.1 write strategies.
- Content-control and anchor strategies belong in later schema versions.
- Required fields generate warnings when empty.
- `template_id`, `file_type`, and the stored original filename are server-controlled.

