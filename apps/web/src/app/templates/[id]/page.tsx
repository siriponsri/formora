"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useMemo, useState } from "react";
import { AppShell, LoadingState, Notice, StatusPill } from "@/components/app-shell";
import { SparkIcon } from "@/components/icons";
import { api } from "@/lib/api";
import type {
  CandidateProposal,
  TemplateField,
  TemplateManifest,
  TemplateRecord,
} from "@/lib/types";

export default function TemplateDetailPage() {
  const params = useParams<{ id: string }>();
  const [template, setTemplate] = useState<TemplateRecord | null>(null);
  const [manifest, setManifest] = useState<TemplateManifest | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [proposalDecisions, setProposalDecisions] = useState<Record<string, "accepted" | "rejected">>({});
  const [proposalMappings, setProposalMappings] = useState<Record<string, string>>({});

  useEffect(() => {
    api<TemplateRecord>(`/api/templates/${params.id}`)
      .then((record) => {
        setTemplate(record);
        setManifest(record.manifest);
      })
      .catch((reason: unknown) => setError(reason instanceof Error ? reason.message : "Could not load template."))
      .finally(() => setLoading(false));
  }, [params.id]);

  const structureSummary = useMemo(() => {
    if (!template?.analysis) return [];
    const analysis = template.analysis as Record<string, unknown>;
    if (template.file_type === "docx") {
      return [
        ["Paragraphs", Array.isArray(analysis.paragraphs) ? analysis.paragraphs.length : 0],
        ["Tables", Array.isArray(analysis.tables) ? analysis.tables.length : 0],
        ["Sections", Array.isArray(analysis.sections) ? analysis.sections.length : 0],
      ];
    }
    return [
      ["Sheets", Array.isArray(analysis.sheets) ? analysis.sheets.length : 0],
      ["Names", Array.isArray(analysis.sheet_names) ? analysis.sheet_names.join(", ") : "—"],
    ];
  }, [template]);

  const proposals = useMemo(() => {
    if (template?.file_type !== "docx" || !template.analysis) return [];
    const candidates = (template.analysis as { candidates?: unknown }).candidates;
    return Array.isArray(candidates) ? candidates as CandidateProposal[] : [];
  }, [template]);

  function updateField(index: number, patch: Partial<TemplateField>) {
    if (!manifest) return;
    setManifest({
      ...manifest,
      fields: manifest.fields.map((field, fieldIndex) => fieldIndex === index ? { ...field, ...patch } : field),
    });
  }

  function updateBinding(index: number, value: string) {
    if (!manifest) return;
    const field = manifest.fields[index];
    updateField(index, {
      binding: field.binding.strategy === "placeholder"
        ? { ...field.binding, placeholder: value }
        : { ...field.binding, cell: value.toUpperCase() },
    });
  }

  function addField() {
    if (!manifest) return;
    const id = `field_${manifest.fields.length + 1}`;
    const field: TemplateField = manifest.file_type === "docx"
      ? {
          id,
          label: "New field",
          required: false,
          content_type: "short_text",
          binding: { strategy: "placeholder", placeholder: `{{${id}}}` },
        }
      : {
          id,
          label: "New field",
          required: false,
          content_type: "short_text",
          binding: { strategy: "cell", cell: "A1", sheet: null },
        };
    setManifest({ ...manifest, fields: [...manifest.fields, field] });
  }

  function proposalKey(proposal: CandidateProposal) {
    return `${proposal.block_id}:${proposal.anchor}`;
  }

  function acceptProposal(proposal: CandidateProposal) {
    if (!manifest) return;
    const key = proposalKey(proposal);
    const fieldId = proposalMappings[key] || proposal.field_id;
    const field: TemplateField = {
      id: fieldId,
      label: proposal.label,
      required: false,
      content_type: "short_text",
      binding: {
        strategy: "docx_block",
        block_id: proposal.block_id,
        anchor: proposal.anchor,
        mode: "after_anchor",
      },
    };
    setManifest({
      ...manifest,
      fields: [
        ...manifest.fields.filter(
          (existing) => existing.id !== fieldId && existing.binding.block_id !== proposal.block_id,
        ),
        field,
      ],
    });
    setProposalDecisions({ ...proposalDecisions, [key]: "accepted" });
  }

  function rejectProposal(proposal: CandidateProposal) {
    setProposalDecisions({ ...proposalDecisions, [proposalKey(proposal)]: "rejected" });
  }

  function remapProposal(proposal: CandidateProposal, fieldId: string) {
    if (!manifest) return;
    const key = proposalKey(proposal);
    setProposalMappings({ ...proposalMappings, [key]: fieldId });
    const reviewed = manifest.fields.some((field) => field.binding.block_id === proposal.block_id);
    if (proposalDecisions[key] !== "accepted" && !reviewed) return;
    setManifest({
      ...manifest,
      fields: manifest.fields.map((field) => (
        field.binding.block_id === proposal.block_id ? { ...field, id: fieldId } : field
      )),
    });
  }

  async function save() {
    if (!manifest) return;
    setSaving(true);
    setError("");
    setMessage("");
    try {
      const updated = await api<TemplateRecord>(`/api/templates/${params.id}/manifest`, {
        method: "PUT",
        body: JSON.stringify(manifest),
      });
      setTemplate(updated);
      setManifest(updated.manifest);
      setMessage("Manifest saved. This template is ready for deterministic rendering.");
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Could not save manifest.");
    } finally {
      setSaving(false);
    }
  }

  if (loading) return <AppShell><LoadingState label="Opening template analysis…" /></AppShell>;
  if (!template || !manifest) {
    return <AppShell title="Template unavailable"><Notice tone="error">{error || "No manifest was found. Analyze the template again."}</Notice></AppShell>;
  }

  return (
    <AppShell
      eyebrow={`${template.file_type.toUpperCase()} template`}
      title={template.name}
      description="Review semantic fields before they are allowed to write into the native template."
      action={
        <Link href={`/generate/${template.id}`} className="button">
          <SparkIcon /> Draft a document
        </Link>
      }
    >
      {error && <Notice tone="error">{error}</Notice>}
      {message && <Notice tone="success">{message}</Notice>}
      <div className="two-column" style={{ marginTop: 18 }}>
        <section className="card stack">
          <div className="section-heading">
            <div>
              <h2>Semantic manifest</h2>
              <p>Only these reviewed fields can be changed by the renderer.</p>
            </div>
            <StatusPill status={template.status} />
          </div>
          <div className="two-column" style={{ gridTemplateColumns: "1fr 1fr" }}>
            <label className="label">
              Template name
              <input className="input" value={manifest.name} onChange={(event) => setManifest({ ...manifest, name: event.target.value })} />
            </label>
            <label className="label">
              Document type
              <input className="input" value={manifest.document_type} onChange={(event) => setManifest({ ...manifest, document_type: event.target.value })} />
            </label>
          </div>

          <div className="field-list">
            {manifest.fields.length === 0 && (
              <Notice>
                No safe binding was inferred. Add explicit {manifest.file_type === "docx" ? "placeholders" : "cell coordinates"} manually.
              </Notice>
            )}
            {manifest.fields.map((field, index) => (
              <div className="field-row" key={`${field.id}-${index}`}>
                <div className="field-row-grid">
                  <label className="label">
                    Field ID
                    <input className="input" value={field.id} onChange={(event) => updateField(index, { id: event.target.value })} />
                  </label>
                  <label className="label">
                    Human label
                    <input className="input" value={field.label} onChange={(event) => updateField(index, { label: event.target.value })} />
                  </label>
                  <label className="label">
                    {field.binding.strategy === "placeholder"
                      ? "Placeholder"
                      : field.binding.strategy === "cell"
                        ? "Cell coordinate"
                        : "DOCX block"}
                    {field.binding.strategy === "docx_block" ? (
                      <span className="input binding-readonly">
                        {field.binding.block_id} · {field.binding.anchor}
                      </span>
                    ) : (
                      <input
                        className="input"
                        value={field.binding.placeholder ?? field.binding.cell ?? ""}
                        onChange={(event) => updateBinding(index, event.target.value)}
                      />
                    )}
                  </label>
                  <button
                    className="button button-quiet"
                    type="button"
                    onClick={() => setManifest({ ...manifest, fields: manifest.fields.filter((_, fieldIndex) => fieldIndex !== index) })}
                  >
                    Remove
                  </button>
                </div>
                {field.binding.strategy === "cell" && (
                  <label className="label" style={{ marginTop: 12, maxWidth: 260 }}>
                    Sheet name <span className="hint">Blank uses the first sheet.</span>
                    <input
                      className="input"
                      value={field.binding.sheet ?? ""}
                      onChange={(event) => updateField(index, { binding: { ...field.binding, sheet: event.target.value || null } })}
                    />
                  </label>
                )}
                <label className="checkbox-label">
                  <input type="checkbox" checked={field.required} onChange={(event) => updateField(index, { required: event.target.checked })} />
                  Required before official review
                </label>
              </div>
            ))}
          </div>
          {template.file_type === "docx" && proposals.length > 0 && (
            <div className="proposal-panel">
              <div className="section-heading">
                <div>
                  <h3>Proposed native bindings</h3>
                  <p>These deterministic suggestions are not saved until you accept them.</p>
                </div>
              </div>
              <div className="field-list">
                {proposals.map((proposal) => {
                  const key = proposalKey(proposal);
                  const decision = proposalDecisions[key];
                  const accepted = decision === "accepted" || manifest.fields.some(
                    (field) => field.binding.block_id === proposal.block_id,
                  );
                  return (
                    <div className={`proposal-row${decision ? ` proposal-${decision}` : ""}`} key={key}>
                      <div className="proposal-source">
                        <strong>{proposal.label}</strong>
                        <span>{proposal.source_text}</span>
                      </div>
                      <div className="proposal-meta">
                        <span>Field</span>
                          <select
                            className="select"
                            value={proposalMappings[key] || proposal.field_id}
                          onChange={(event) => remapProposal(proposal, event.target.value)}
                        >
                          {(["subject", "recipient", "date", "document_number"] as const).map((fieldId) => (
                            <option value={fieldId} key={fieldId}>{fieldId}</option>
                          ))}
                        </select>
                      </div>
                      <div className="proposal-details">
                        <span>Block: {proposal.block_id}</span>
                        <span>Anchor: {proposal.anchor}</span>
                        <span>Confidence: {proposal.confidence.toFixed(2)}</span>
                      </div>
                      <div className="inline-actions">
                        <button className="button" type="button" onClick={() => acceptProposal(proposal)} disabled={accepted}>
                          {accepted ? "Accepted" : "Accept"}
                        </button>
                        <button className="button button-secondary" type="button" onClick={() => rejectProposal(proposal)} disabled={accepted}>
                          {decision === "rejected" ? "Ignored" : "Ignore"}
                        </button>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}
          <div className="form-actions">
            <button className="button button-secondary" type="button" onClick={addField}>Add field</button>
            <button className="button" type="button" disabled={saving} onClick={save}>
              {saving ? "Saving…" : "Save manifest"}
            </button>
          </div>
        </section>

        <aside className="card">
          <p className="eyebrow">Native inspection</p>
          <h2>Structural map</h2>
          <p className="card-subtitle">This map helps semantic analysis. It never replaces the Office layout.</p>
          <div className="summary-list">
            {structureSummary.map(([label, value]) => (
              <div className="summary-row" key={String(label)}><span>{label}</span><strong>{String(value)}</strong></div>
            ))}
          </div>
          <pre className="structure-preview">{JSON.stringify(template.analysis, null, 2)}</pre>
        </aside>
      </div>
    </AppShell>
  );
}

