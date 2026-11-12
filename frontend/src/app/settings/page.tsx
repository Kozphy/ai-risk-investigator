"use client";

import { useEffect, useState } from "react";
import { AppShell } from "@/components/AppShell";
import { api } from "@/lib/api";

export default function SettingsPage() {
  const [me, setMe] = useState<any>(null);
  const [knowledge, setKnowledge] = useState<any[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([api.me(), api.listKnowledge()])
      .then(([user, kb]) => {
        setMe(user);
        setKnowledge(kb);
      })
      .catch((e) => setError(e.message));
  }, []);

  return (
    <AppShell>
      <h1 className="font-display text-3xl">Settings</h1>
      <p className="mb-6 text-slate-500">Account, RBAC role, and RAG knowledge base sources.</p>
      {error && <p className="mb-4 text-sm text-danger">{error}</p>}
      <div className="grid gap-6 md:grid-cols-2">
        <div className="card">
          <h2 className="font-medium">Account</h2>
          {me ? (
            <dl className="mt-3 space-y-2 text-sm">
              <div>
                <dt className="text-slate-500">Name</dt>
                <dd>{me.full_name}</dd>
              </div>
              <div>
                <dt className="text-slate-500">Email</dt>
                <dd>{me.email}</dd>
              </div>
              <div>
                <dt className="text-slate-500">Role</dt>
                <dd className="uppercase tracking-wide">{me.role}</dd>
              </div>
              <div>
                <dt className="text-slate-500">Organization</dt>
                <dd>{me.organization || "—"}</dd>
              </div>
            </dl>
          ) : (
            <p className="mt-2 text-sm text-slate-500">Loading…</p>
          )}
        </div>
        <div className="card">
          <h2 className="font-medium">Knowledge Base</h2>
          <ul className="mt-3 space-y-2 text-sm">
            {knowledge.length === 0 && <li className="text-slate-500">No knowledge documents yet.</li>}
            {knowledge.map((k) => (
              <li key={k.id} className="rounded border border-slate-100 px-3 py-2">
                <p className="font-medium">{k.title}</p>
                <p className="text-xs text-slate-500">
                  {k.framework || k.source_type} · {k.filename}
                </p>
              </li>
            ))}
          </ul>
          <p className="mt-4 text-xs text-slate-500">
            Upload regulations via <code>POST /api/v1/knowledge</code> (compliance+ roles).
          </p>
        </div>
      </div>
    </AppShell>
  );
}
