"use client";

import { useEffect, useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { AppShell } from "@/components/AppShell";
import { api } from "@/lib/api";

export default function DashboardPage() {
  const [stats, setStats] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .dashboard()
      .then(setStats)
      .catch((e) => setError(e.message));
  }, []);

  const byCategory = Object.entries(stats?.risks_by_category || {}).map(([name, value]) => ({
    name,
    value,
  }));
  const bySeverity = Object.entries(stats?.risks_by_severity || {}).map(([name, value]) => ({
    name,
    value,
  }));

  return (
    <AppShell>
      <div className="mb-6">
        <h1 className="font-display text-3xl">Risk Dashboard</h1>
        <p className="text-slate-500">Portfolio view of analyzed documents and findings.</p>
      </div>
      {error && <p className="mb-4 text-sm text-danger">{error}</p>}
      <div className="mb-6 grid gap-4 sm:grid-cols-3">
        <div className="card">
          <p className="text-xs uppercase tracking-wide text-slate-500">Documents</p>
          <p className="mt-2 text-3xl font-semibold">{stats?.document_volume ?? "—"}</p>
        </div>
        <div className="card">
          <p className="text-xs uppercase tracking-wide text-slate-500">Analyses</p>
          <p className="mt-2 text-3xl font-semibold">{stats?.analysis_count ?? "—"}</p>
        </div>
        <div className="card">
          <p className="text-xs uppercase tracking-wide text-slate-500">Findings</p>
          <p className="mt-2 text-3xl font-semibold">{stats?.finding_count ?? "—"}</p>
        </div>
      </div>
      <div className="grid gap-6 lg:grid-cols-2">
        <div className="card h-80">
          <h2 className="mb-4 font-medium">Risks by Category</h2>
          <ResponsiveContainer width="100%" height="85%">
            <BarChart data={byCategory}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" hide={byCategory.length > 6} />
              <YAxis allowDecimals={false} />
              <Tooltip />
              <Bar dataKey="value" fill="#0d9488" name="Findings" />
            </BarChart>
          </ResponsiveContainer>
        </div>
        <div className="card h-80">
          <h2 className="mb-4 font-medium">Risks by Severity</h2>
          <ResponsiveContainer width="100%" height="85%">
            <BarChart data={bySeverity}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis allowDecimals={false} />
              <Tooltip />
              <Bar dataKey="value" fill="#1e293b" name="Findings" />
            </BarChart>
          </ResponsiveContainer>
        </div>
        <div className="card h-80 lg:col-span-2">
          <h2 className="mb-4 font-medium">Finding Trend Over Time</h2>
          <ResponsiveContainer width="100%" height="85%">
            <LineChart data={stats?.trend_over_time || []}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" />
              <YAxis allowDecimals={false} />
              <Tooltip />
              <Legend />
              <Line type="monotone" dataKey="findings" stroke="#0d9488" strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>
    </AppShell>
  );
}
