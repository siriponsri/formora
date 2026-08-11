"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { AppShell, LoadingState, Notice } from "@/components/app-shell";
import { CheckIcon, FileIcon } from "@/components/icons";
import { api, fileUrl } from "@/lib/api";
import type { GenerationRecord, RenderResult } from "@/lib/types";

export default function GenerationResultPage() {
  const params = useParams<{ id: string }>();
  const [generation, setGeneration] = useState<GenerationRecord | null>(null);
  const [render, setRender] = useState<RenderResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const cached = sessionStorage.getItem(`formora-render-${params.id}`);
    api<GenerationRecord>(`/api/generations/${params.id}`)
      .then((record) => {
        setGeneration(record);
        if (cached) setRender(JSON.parse(cached) as RenderResult);
      })
      .catch((reason: unknown) => setError(reason instanceof Error ? reason.message : "Could not load generation."))
      .finally(() => setLoading(false));
  }, [params.id]);

  if (loading) return <AppShell><LoadingState label="Verifying generated output…" /></AppShell>;
  if (!generation) return <AppShell title="Generation unavailable"><Notice tone="error">{error}</Notice></AppShell>;

  const downloadPath = render?.download_url ?? `/api/files/${generation.id}`;
  const previewPath = render?.preview_url ?? (generation.preview_path ? `/api/files/${generation.id}?kind=preview` : null);
  const warnings = render?.warnings ?? [];

  return (
    <AppShell eyebrow="Generation result" title="Your editable native file is ready" description="Open it in Microsoft Office and complete the required human review before official use.">
      <section className="card result-card">
        <div className="result-icon"><CheckIcon /></div>
        <h2>Rendered from a copy of the original</h2>
        <p>
          Formora changed only reviewed binding targets. The registered source template was not modified.
          Property-level tests cover page setup, headers and footers, merges, dimensions, formulas, and print settings.
        </p>
        {warnings.map((warning) => <Notice key={warning}>{warning}</Notice>)}
        {generation.preview_status && <Notice>{generation.preview_status}</Notice>}
        <div className="inline-actions" style={{ justifyContent: "center", marginTop: 24 }}>
          <a className="button" href={fileUrl(downloadPath)} download>
            <FileIcon /> Download editable file
          </a>
          {previewPath && (
            <a className="button button-secondary" href={fileUrl(previewPath)} target="_blank" rel="noreferrer">
              Open PDF preview
            </a>
          )}
          <Link className="button button-secondary" href={`/generate/${generation.template_id}`}>
            Create another
          </Link>
        </div>
      </section>
    </AppShell>
  );
}
