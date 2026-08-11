import type { Metadata } from "next";
import type { ReactNode } from "react";
import "./globals.css";

export const metadata: Metadata = {
  title: {
    default: "Formora — Template-preserving document AI",
    template: "%s · Formora",
  },
  description:
    "A local-first compiler that writes intelligent content into native DOCX and XLSX templates.",
};

export default function RootLayout({ children }: Readonly<{ children: ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}

