"use client";

import { Suspense, useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import { AppShell } from "@/components/AppShell";
import { api } from "@/lib/api";

function FindingsInner() {
  const params = useSearchParams();
  const analysisId = params.get("analysis");
  const [analyses, setAnalyses] = useState<any[]>([]);
  const [selected, setSelected] = useState<any | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .listAnalyses()
      .then((items) => {
        setAnalyses(items);
        const target = analysisId
          ? items.find((a: any) => a.id === analysisId)
          : items[0];
        if (target) {
          return api.getAnalysis(target.id).then(setSelected);
        }
      })
      .catch((e) => setError(e.message));
  }, [analysisId]);

  useEffect(() => {
    if (!selected || selected.status === "completed" || selected.status === "failed") return;
    const timer = setInterval(() => {
      api.getAnalysis(selected.id).then(setSelected).catch(() => undefined);
    }, 2000);
    return () => clearInterval(timer);
  }, [selected]);

  return (
    <>
      <h1 className="font-display text-3xl">Findings</h1>
      <p className="mb-6 text-slate-500">Evidence-backed risk findings with confidence scores.</p>
      {error && <p className="mb-4 text-sm text-danger">{error}</p>}
      <div className="mb-4 flex flex-wrap gap-2">
        {analyses.map((a) => (
          <button
            key={a.id}
            className={`rounded-md border px-3 py-1 text-sm ${
              selected?.id === a.id ? "border-accent bg-teal-50" : "border-slate-200 bg-white"
            }`}
            onClick={() => api.getAnalysis(a.id).then(setSelected)}
          >
            {a.id.slice(0, 8)} · {a.status}
          </button>
        ))}
      </div>
      {!selected && <p className="text-slate-500">No analyses yet. Upload a document to begin.</p>}
      {selected && (
        <div className="space-y-4">
          <div className="card">
            <p className="text-sm text-slate-500">Status: {selected.status}</p>
            {selected.executive_summary && (
              <div className="mt-3 grid gap-4 md:grid-cols-3">
                <div>
                  <h3 className="font-medium">Top Risks</h3>
                  <ul className="mt-2 list-disc pl-5 text-sm">
                    {(selected.executive_summary.top_risks || []).map((x: string) => (
                      <li key={x}>{x}</li>
                    ))}
                  </ul>
                </div>
                <div>
                  <h3 className="font-medium">Key Observations</h3>
                  <ul className="mt-2 list-disc pl-5 text-sm">
                    {(selected.executive_summary.key_observations || []).map((x: string) => (
                      <li key={x}>{x}</li>
                    ))}
                  </ul>
                </div>
                <div>
                  <h3 className="font-medium">Recommended Actions</h3>
                  <ul className="mt-2 list-disc pl-5 text-sm">
                    {(selected.executive_summary.recommended_actions || []).map((x: string) => (
                      <li key={x}>{x}</li>
                    ))}
                  </ul>
                </div>
              </div>
            )}
          </div>
          {(selected.findings || []).map((f: any) => (
            <article key={f.id} className="card">
              <div className="flex flex-wrap items-center gap-2">
                <span className="rounded bg-slate-900 px-2 py-0.5 text-xs uppercase text-white">
                  {f.severity}
                </span>
                <span className="rounded bg-slate-100 px-2 py-0.5 text-xs">{f.category}</span>
                <span className="text-xs text-slate-500">
                  P:{f.probability} · I:{f.impact} · conf {(f.confidence_score * 100).toFixed(0)}%
                </span>
              </div>
              <h2 className="mt-2 text-lg font-medium">{f.finding}</h2>
              <p className="mt-1 text-sm text-slate-600">{f.explanation}</p>
              <blockquote className="mt-3 border-l-4 border-accent bg-slate-50 p-3 text-sm">
                <p className="text-xs text-slate-500">Supporting text · page {f.page_number ?? "—"}</p>
                {f.supporting_text}
              </blockquote>
              {f.recommendation && (
                <p className="mt-3 text-sm">
                  <span className="font-medium">Recommendation:</span> {f.recommendation}
                </p>
              )}
            </article>
          ))}
        </div>
      )}
    </>
  );
}

export default function FindingsPage() {
  return (
    <AppShell>
      <Suspense fallback={<p>Loading findings…</p>}>
        <FindingsInner />
      </Suspense>
    </AppShell>
  );
}
