"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";

export default function LoginPage() {
  const router = useRouter();
  const [mode, setMode] = useState<"login" | "register">("login");
  const [email, setEmail] = useState("auditor@example.com");
  const [password, setPassword] = useState("ChangeMe123!");
  const [fullName, setFullName] = useState("Lead Auditor");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      if (mode === "register") {
        await api.register({ email, password, full_name: fullName, organization: "Demo Org" });
      }
      const tokens = await api.login({ email, password });
      localStorage.setItem("access_token", tokens.access_token);
      localStorage.setItem("refresh_token", tokens.refresh_token);
      router.push("/dashboard");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Authentication failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-[radial-gradient(circle_at_20%_20%,_#ccfbf1,_transparent_40%),radial-gradient(circle_at_80%_0%,_#e2e8f0,_#f8fafc_60%)] px-4">
      <form onSubmit={onSubmit} className="card w-full max-w-md space-y-4">
        <div>
          <h1 className="font-display text-3xl">AI Risk Investigator</h1>
          <p className="mt-1 text-sm text-slate-500">
            Sign in to analyze contracts, policies, and audit evidence.
          </p>
        </div>
        {mode === "register" && (
          <label className="block text-sm">
            Full name
            <input
              className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2"
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              required
            />
          </label>
        )}
        <label className="block text-sm">
          Email
          <input
            type="email"
            className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
        </label>
        <label className="block text-sm">
          Password
          <input
            type="password"
            className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
        </label>
        {error && <p className="text-sm text-danger">{error}</p>}
        <button
          type="submit"
          disabled={loading}
          className="w-full rounded-md bg-accent px-4 py-2 font-medium text-white hover:bg-teal-700 disabled:opacity-60"
        >
          {loading ? "Working…" : mode === "login" ? "Sign in" : "Create account"}
        </button>
        <button
          type="button"
          className="w-full text-sm text-slate-500 underline"
          onClick={() => setMode(mode === "login" ? "register" : "login")}
        >
          {mode === "login" ? "Need an account? Register" : "Have an account? Sign in"}
        </button>
      </form>
    </div>
  );
}
