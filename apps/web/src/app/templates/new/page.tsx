"use client";

import { useRouter } from "next/navigation";
import { type FormEvent, useState } from "react";
import { AppShell, Notice } from "@/components/app-shell";
import { CheckIcon, UploadIcon } from "@/components/icons";
import { api } from "@/lib/api";
import type { TemplateRecord } from "@/lib/types";

export default function NewTemplatePage() {
  const router = useRouter();
  const [file, setFile] = useState<File | null>(null);
  const [name, setName] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!file) return;
    setBusy(true);
    setError("");
    try {
      const body = new FormData();
      body.append("file", file);
      if (name.trim()) body.append("name", name.trim());
      const uploaded = await api<TemplateRecord>("/api/templates/upload", { method: "POST", body });
      const analyzed = await api<TemplateRecord>(`/api/templates/${uploaded.id}/analyze`, { method: "POST" });
      router.push(`/templates/${analyzed.id}`);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "The template could not be registered.");
      setBusy(false);
    }
  }

  return (
    <AppShell
      eyebrow="Register"
      title="Teach Formora a native template"
      description="The original file is stored unchanged. Analysis creates a separate structural map and editable field manifest."
    >
      <form className="two-column" onSubmit={submit}>
        <div className="card stack">
          {error && <Notice tone="error">{error}</Notice>}
          <label className="upload-zone">
            <input
              type="file"
              accept=".docx,.xlsx,application/vnd.openxmlformats-officedocument.wordprocessingml.document,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
              onChange={(event) => setFile(event.target.files?.[0] ?? null)}
            />
            <span>
              <span className="upload-symbol">
                <UploadIcon />
              </span>
              <h2>Choose a DOCX or XLSX template</h2>
              <p>Macro-free Office files up to 20 MB</p>
              <span className="button button-secondary">Browse this computer</span>
              {file && <span className="file-selection">Selected: {file.name}</span>}
            </span>
          </label>
          <label className="label">
            Template name <span className="hint">Optional—Formora uses the filename by default.</span>
            <input
              className="input"
              value={name}
              onChange={(event) => setName(event.target.value)}
              placeholder="e.g. Procurement approval memo"
            />
          </label>
          <div className="form-actions">
            <button className="button" type="submit" disabled={!file || busy}>
              {busy ? "Uploading and analyzing…" : "Upload and analyze"}
            </button>
          </div>
        </div>

        <aside className="card">
          <p className="eyebrow">Preservation contract</p>
          <h2>Your original remains the source of truth</h2>
          <p className="card-subtitle">
            Formora reads native structure for semantic understanding; it does not convert the full
            layout into AI-generated JSON or LaTeX.
          </p>
          <ul className="safety-list">
            <li><CheckIcon /> The uploaded original is never rendered in place.</li>
            <li><CheckIcon /> Generated files always start from a copy.</li>
            <li><CheckIcon /> AI output must pass schema validation first.</li>
            <li><CheckIcon /> Mock mode works entirely offline.</li>
          </ul>
          <Notice>
            Use synthetic or non-confidential templates during this POC. Macro-enabled files are intentionally rejected.
          </Notice>
        </aside>
      </form>
    </AppShell>
  );
}

