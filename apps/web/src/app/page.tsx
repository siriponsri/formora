"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { AppShell, LoadingState, Notice, StatusPill } from "@/components/app-shell";
import { ArrowIcon, FileIcon, SparkIcon, UploadIcon } from "@/components/icons";
import { api } from "@/lib/api";
import type { TemplateRecord } from "@/lib/types";

export default function DashboardPage() {
  const [templates, setTemplates] = useState<TemplateRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    api<TemplateRecord[]>("/api/templates")
      .then(setTemplates)
      .catch((reason: unknown) => setError(reason instanceof Error ? reason.message : "Could not load templates."))
      .finally(() => setLoading(false));
  }, []);

  return (
    <AppShell>
      <section className="hero-panel">
        <div className="hero-copy">
          <p className="eyebrow">Template-preserving document AI</p>
          <h2>Write new content. Keep the document your organization trusts.</h2>
          <p>
            Formora understands the meaning of your template, then inserts validated content into a
            copy of the original DOCX or XLSX—without rebuilding its native layout.
          </p>
          <div className="hero-actions">
            <Link className="button" href="/templates/new">
              <UploadIcon /> Register a template
            </Link>
            <a className="button button-secondary" href="#templates">
              View local templates
            </a>
          </div>
        </div>
        <div className="document-visual" aria-hidden="true">
          <div className="paper">
            <div className="paper-line title" />
            <div className="paper-line" />
            <div className="paper-line short" />
            <div className="paper-line" />
            <div className="paper-line short" />
            <span className="binding-chip">✓ native format preserved</span>
          </div>
        </div>
      </section>

      <section id="templates" aria-labelledby="templates-heading">
        <div className="section-heading">
          <div>
            <h2 id="templates-heading">Local templates</h2>
            <p>Registered originals and their reviewed semantic bindings.</p>
          </div>
          <Link href="/templates/new" className="button button-secondary">
            <UploadIcon /> Add template
          </Link>
        </div>

        {error && <Notice tone="error">{error} Make sure the local API is running on port 8000.</Notice>}
        {loading ? (
          <LoadingState label="Reading local templates…" />
        ) : templates.length === 0 ? (
          <div className="empty-state">
            <div className="file-tile">
              <SparkIcon />
            </div>
            <h3>Your first template becomes a reusable compiler</h3>
            <p>
              Start with the synthetic memo in <code>fixtures/</code>, or upload a macro-free DOCX/XLSX
              that contains no confidential information.
            </p>
            <Link href="/templates/new" className="button">
              Register first template
            </Link>
          </div>
        ) : (
          <div className="template-grid">
            {templates.map((template) => (
              <Link className="template-card" href={`/templates/${template.id}`} key={template.id}>
                <div className="template-card-top">
                  <span className={`file-tile ${template.file_type}`}>
                    <FileIcon />
                  </span>
                  <StatusPill status={template.status} />
                </div>
                <h3>{template.name}</h3>
                <p className="template-meta">
                  {template.file_type.toUpperCase()} · {template.manifest?.fields.length ?? 0} bound fields
                </p>
                <span className="template-link">
                  Review template <ArrowIcon />
                </span>
              </Link>
            ))}
          </div>
        )}
      </section>
    </AppShell>
  );
}

