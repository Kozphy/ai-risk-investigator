"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import { AppShell } from "@/components/AppShell";
import { api } from "@/lib/api";

const TYPES = [
  "contract",
  "financial_report",
  "policy",
  "audit_evidence",
  "compliance_manual",
  "other",
];

export default function UploadPage() {
  const router = useRouter();
  const [file, setFile] = useState<File | null>(null);
  const [documentType, setDocumentType] = useState("contract");
  const [status, setStatus] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    if (!file) return;
    setError(null);
    setStatus("Uploading…");
    try {
      const doc: any = await api.uploadDocument(file, documentType);
      setStatus("Starting analysis…");
      const analysis: any = await api.createAnalysis(doc.id);
      setStatus(`Analysis queued: ${analysis.id}`);
      router.push(`/findings?analysis=${analysis.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed");
      setStatus(null);
    }
  }

  return (
    <AppShell>
      <h1 className="font-display text-3xl">Document Upload</h1>
      <p className="mb-6 text-slate-500">
        Upload PDF, DOCX, or TXT. Analysis runs against your RAG knowledge base.
      </p>
      <form onSubmit={onSubmit} className="card max-w-xl space-y-4">
        <label className="block text-sm">
          Document type
          <select
            className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2"
            value={documentType}
            onChange={(e) => setDocumentType(e.target.value)}
          >
            {TYPES.map((t) => (
              <option key={t} value={t}>
                {t}
              </option>
            ))}
          </select>
        </label>
        <label className="block text-sm">
          File
          <input
            type="file"
            accept=".pdf,.docx,.txt"
            className="mt-1 block w-full text-sm"
            onChange={(e) => setFile(e.target.files?.[0] || null)}
            required
          />
        </label>
        {error && <p className="text-sm text-danger">{error}</p>}
        {status && <p className="text-sm text-accent">{status}</p>}
        <button
          type="submit"
          className="rounded-md bg-slatepanel px-4 py-2 text-white hover:bg-slate-800"
        >
          Upload & Analyze
        </button>
      </form>
    </AppShell>
  );
}
