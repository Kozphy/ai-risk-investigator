const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

function authHeader(): HeadersInit {
  if (typeof window === "undefined") return {};
  const token = localStorage.getItem("access_token");
  return token ? { Authorization: `Bearer ${token}` } : {};
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers);
  if (!(init.body instanceof FormData)) {
    headers.set("Content-Type", "application/json");
  }
  const auth = authHeader();
  Object.entries(auth).forEach(([k, v]) => headers.set(k, String(v)));

  const res = await fetch(`${API_URL}${path}`, { ...init, headers });
  if (!res.ok) {
    const detail = await res.text();
    throw new Error(detail || res.statusText);
  }
  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}

export const api = {
  register: (body: object) =>
    request("/api/v1/auth/register", { method: "POST", body: JSON.stringify(body) }),
  login: (body: object) =>
    request<{ access_token: string; refresh_token: string }>("/api/v1/auth/login", {
      method: "POST",
      body: JSON.stringify(body),
    }),
  me: () => request("/api/v1/auth/me"),
  listDocuments: () => request<Record<string, unknown>[]>("/api/v1/documents"),
  uploadDocument: async (file: File, documentType = "other") => {
    const form = new FormData();
    form.append("file", file);
    form.append("document_type", documentType);
    return request<Record<string, unknown>>("/api/v1/documents", { method: "POST", body: form });
  },
  createAnalysis: (document_id: string, frameworks?: string[]) =>
    request<Record<string, unknown>>("/api/v1/analyses", {
      method: "POST",
      body: JSON.stringify({ document_id, frameworks }),
    }),
  listAnalyses: () => request<Record<string, unknown>[]>("/api/v1/analyses"),
  getAnalysis: (id: string) => request<Record<string, unknown>>(`/api/v1/analyses/${id}`),
  dashboard: () => request<Record<string, unknown>>("/api/v1/analyses/dashboard/stats"),
  createReport: (analysis_id: string, format: "pdf" | "docx" = "pdf") =>
    request<{ id: string; file_size: number }>("/api/v1/reports", {
      method: "POST",
      body: JSON.stringify({ analysis_id, format }),
    }),
  reportDownloadUrl: (reportId: string) => `${API_URL}/api/v1/reports/${reportId}/download`,
  listKnowledge: () => request<Record<string, unknown>[]>("/api/v1/knowledge"),
};
