"use client";

import { useParams, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { AppShell, LoadingState, Notice } from "@/components/app-shell";
import { FileIcon, SparkIcon } from "@/components/icons";
import { api } from "@/lib/api";
import type { DraftResult, RenderResult, TemplateRecord } from "@/lib/types";

const SAMPLE_PROMPT =
  "ขออนุมัติจัดซื้อเครื่องสำรองไฟฟ้า 3 kVA จำนวน 1 เครื่อง เพื่อใช้กับอุปกรณ์ห้องปฏิบัติการ งบประมาณ 45,000 บาท";

export default function GeneratePage() {
  const params = useParams<{ templateId: string }>();
  const router = useRouter();
  const [template, setTemplate] = useState<TemplateRecord | null>(null);
  const [prompt, setPrompt] = useState("");
  const [generationId, setGenerationId] = useState<string | null>(null);
  const [content, setContent] = useState<Record<string, unknown>>({});
  const [warnings, setWarnings] = useState<string[]>([]);
  const [phase, setPhase] = useState<"loading" | "ready" | "drafting" | "review" | "rendering">("loading");
  const [error, setError] = useState("");

  useEffect(() => {
    api<TemplateRecord>(`/api/templates/${params.templateId}`)
      .then((record) => {
        setTemplate(record);
        setPhase("ready");
      })
      .catch((reason: unknown) => {
        setError(reason instanceof Error ? reason.message : "Could not load template.");
        setPhase("ready");
      });
  }, [params.templateId]);

  async function draft() {
    if (!prompt.trim()) return;
    setPhase("drafting");
    setError("");
    try {
      const result = await api<DraftResult>("/api/generations/draft", {
        method: "POST",
        body: JSON.stringify({ template_id: params.templateId, prompt }),
      });
      setGenerationId(result.generation_id);
      setContent(result.content);
      setWarnings(result.warnings);
      setPhase("review");
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Could not create a draft.");
      setPhase("ready");
    }
  }

  async function render() {
    setPhase("rendering");
    setError("");
    try {
      const result = await api<RenderResult>("/api/generations/render", {
        method: "POST",
        body: JSON.stringify({
          template_id: params.templateId,
          generation_id: generationId,
          prompt,
          content,
        }),
      });
      sessionStorage.setItem(`formora-render-${result.generation_id}`, JSON.stringify(result));
      router.push(`/generations/${result.generation_id}`);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Could not render the native file.");
      setPhase("review");
    }
  }

  if (phase === "loading") return <AppShell><LoadingState label="Preparing the compiler…" /></AppShell>;
  if (!template?.manifest) {
    return <AppShell title="Template is not ready"><Notice tone="error">{error || "Review and save a manifest before drafting."}</Notice></AppShell>;
  }

  const isReview = phase === "review" || phase === "rendering";

  return (
    <AppShell
      eyebrow="Generate from native template"
      title={template.name}
      description="AI drafts semantic content. You review it. Deterministic code performs the final Office mutation."
    >
      <div className="two-column">
        <section className="card stack">
          {error && <Notice tone="error">{error}</Notice>}
          {warnings.map((warning) => <Notice key={warning}>{warning}</Notice>)}

          {!isReview ? (
            <>
              <div>
                <p className="eyebrow">Step 1 of 2 · Describe</p>
                <h2>What document do you need?</h2>
                <p className="card-subtitle">Write naturally in Thai. Mock mode returns deterministic sample content without internet.</p>
              </div>
              <label className="label">
                Document request
                <textarea
                  className="textarea"
                  value={prompt}
                  onChange={(event) => setPrompt(event.target.value)}
                  placeholder={SAMPLE_PROMPT}
                />
              </label>
              <div className="form-actions">
                <button className="button button-secondary" type="button" onClick={() => setPrompt(SAMPLE_PROMPT)}>
                  Use demo request
                </button>
                <button className="button" type="button" onClick={draft} disabled={!prompt.trim() || phase === "drafting"}>
                  <SparkIcon /> {phase === "drafting" ? "Drafting…" : "Draft content"}
                </button>
              </div>
            </>
          ) : (
            <>
              <div>
                <p className="eyebrow">Step 2 of 2 · Review</p>
                <h2>Review every generated field</h2>
                <p className="card-subtitle">These values will be inserted only at the reviewed manifest bindings.</p>
              </div>
              <div className="generation-fields">
                {template.manifest.fields.map((field) => (
                  <label className="label" key={field.id}>
                    {field.label} {field.required && <span className="hint">Required</span>}
                    {field.content_type === "rich_text" || String(content[field.id] ?? "").length > 120 ? (
                      <textarea
                        className="textarea"
                        value={String(content[field.id] ?? "")}
                        onChange={(event) => setContent({ ...content, [field.id]: event.target.value })}
                      />
                    ) : (
                      <input
                        className="input"
                        value={String(content[field.id] ?? "")}
                        onChange={(event) => setContent({ ...content, [field.id]: event.target.value })}
                      />
                    )}
                  </label>
                ))}
              </div>
              <Notice>
                This POC does not perform legal, procurement, or compliance approval. The downloaded file remains a draft for human review.
              </Notice>
              <div className="form-actions">
                <button className="button button-secondary" type="button" onClick={() => setPhase("ready")}>
                  Back to request
                </button>
                <button className="button" type="button" onClick={render} disabled={phase === "rendering"}>
                  <FileIcon /> {phase === "rendering" ? "Rendering a native copy…" : `Generate ${template.file_type.toUpperCase()}`}
                </button>
              </div>
            </>
          )}
        </section>

        <aside className="card">
          <p className="eyebrow">Compiler contract</p>
          <h2>{template.manifest.fields.length} reviewed bindings</h2>
          <div className="summary-list">
            <div className="summary-row"><span>Source format</span><strong>{template.file_type.toUpperCase()}</strong></div>
            <div className="summary-row"><span>AI provider</span><strong>Configured locally</strong></div>
            <div className="summary-row"><span>Render target</span><strong>Copy of original</strong></div>
          </div>
          <div className="field-list" style={{ marginTop: 18 }}>
            {template.manifest.fields.map((field) => (
              <div className="field-row" key={field.id}>
                <strong>{field.label}</strong>
                <div className="hint">
                  {field.binding.strategy === "placeholder"
                    ? field.binding.placeholder
                    : `${field.binding.sheet || "First sheet"}!${field.binding.cell}`}
                </div>
              </div>
            ))}
          </div>
        </aside>
      </div>
    </AppShell>
  );
}

