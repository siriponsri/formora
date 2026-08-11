import Image from "next/image";
import Link from "next/link";
import type { ReactNode } from "react";

interface AppShellProps {
  children: ReactNode;
  eyebrow?: string;
  title?: string;
  description?: string;
  action?: ReactNode;
}

export function AppShell({ children, eyebrow, title, description, action }: AppShellProps) {
  return (
    <div className="app-frame">
      <header className="topbar">
        <Link href="/" className="brand" aria-label="Formora home">
          <Image src="/formora-mark.svg" width={38} height={38} alt="" priority />
          <span>formora</span>
        </Link>
        <nav aria-label="Primary navigation">
          <Link href="/">Templates</Link>
          <Link href="/templates/new" className="nav-primary">
            New template
          </Link>
        </nav>
      </header>
      <main className="page-shell">
        {(title || description) && (
          <section className="page-heading">
            <div>
              {eyebrow && <p className="eyebrow">{eyebrow}</p>}
              {title && <h1>{title}</h1>}
              {description && <p className="page-description">{description}</p>}
            </div>
            {action && <div className="heading-action">{action}</div>}
          </section>
        )}
        {children}
      </main>
      <footer className="footer">
        <span>Local-first · Your templates stay on this computer</span>
        <span>POC v0.1 · Human review required</span>
      </footer>
    </div>
  );
}

export function StatusPill({ status }: { status: string }) {
  const label: Record<string, string> = {
    uploaded: "Uploaded",
    analyzed: "Analyzed",
    needs_review: "Needs review",
    ready: "Ready",
    rendered: "Rendered",
  };
  return <span className={`status status-${status}`}>{label[status] ?? status}</span>;
}

export function Notice({ children, tone = "info" }: { children: ReactNode; tone?: "info" | "error" | "success" }) {
  return <div className={`notice notice-${tone}`}>{children}</div>;
}

export function LoadingState({ label = "Loading…" }: { label?: string }) {
  return (
    <div className="loading-state" role="status">
      <span className="spinner" />
      {label}
    </div>
  );
}

