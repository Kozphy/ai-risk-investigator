"use client";

import { useEffect, useState } from "react";
import { AppShell } from "@/components/AppShell";
import { api } from "@/lib/api";

export default function ReportPage() {
  const [analyses, setAnalyses] = useState<any[]>([]);
  const [analysisId, setAnalysisId] = useState("");
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .listAnalyses()
      .then((items) => {
        setAnalyses(items.filter((a: any) => a.status === "completed"));
        if (items[0]) setAnalysisId(items[0].id);
      })
      .catch((e) => setError(e.message));
  }, []);

  async function exportReport(format: "pdf" | "docx") {
    setError(null);
    setMessage(null);
    try {
      const report = await api.createReport(analysisId, format);
      const token = localStorage.getItem("access_token");
      const url = api.reportDownloadUrl(report.id);
      const res = await fetch(url, { headers: { Authorization: `Bearer ${token}` } });
      if (!res.ok) throw new Error("Download failed");
      const blob = await res.blob();
      const objectUrl = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = objectUrl;
      a.download = `audit-report.${format}`;
      a.click();
      URL.revokeObjectURL(objectUrl);
      setMessage(`Exported ${format.toUpperCase()} (${report.file_size} bytes)`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Export failed");
    }
  }

  return (
    <AppShell>
      <h1 className="font-display text-3xl">Audit Report Export</h1>
      <p className="mb-6 text-slate-500">
        Generate PDF or DOCX with executive summary, findings, rankings, and appendix.
      </p>
      <div className="card max-w-xl space-y-4">
        <label className="block text-sm">
          Completed analysis
          <select
            className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2"
            value={analysisId}
            onChange={(e) => setAnalysisId(e.target.value)}
          >
            {analyses.map((a) => (
              <option key={a.id} value={a.id}>
                {a.id} ({a.status})
              </option>
            ))}
          </select>
        </label>
        <div className="flex gap-3">
          <button
            className="rounded-md bg-slatepanel px-4 py-2 text-white"
            onClick={() => exportReport("pdf")}
            disabled={!analysisId}
          >
            Export PDF
          </button>
          <button
            className="rounded-md border border-slate-300 px-4 py-2"
            onClick={() => exportReport("docx")}
            disabled={!analysisId}
          >
            Export DOCX
          </button>
        </div>
        {message && <p className="text-sm text-accent">{message}</p>}
        {error && <p className="text-sm text-danger">{error}</p>}
      </div>
    </AppShell>
  );
}
