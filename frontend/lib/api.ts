import axios from "axios";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export const api = axios.create({ baseURL: API_BASE_URL });

api.interceptors.request.use((config) => {
  if (typeof window !== "undefined") {
    const token = localStorage.getItem("flowmind_token");
    if (token) config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export type User = {
  id: string;
  full_name: string;
  email: string;
  company?: string;
  created_at: string;
};

export type DocumentItem = {
  id: string;
  filename: string;
  content_type: string | null;
  size_bytes: number;
  chunk_count: number;
  status: string;
  summary: string | null;
  created_at: string;
};

export type WorkflowItem = {
  id: string;
  name: string;
  description: string | null;
  is_active: boolean;
  definition: { nodes: any[]; edges: any[] };
  created_at: string;
  updated_at: string;
};

export type DashboardStats = {
  total_documents: number;
  total_workflows: number;
  active_workflows: number;
  total_workflow_runs: number;
  successful_runs: number;
  failed_runs: number;
  runs_last_7_days: { date: string; count: number }[];
};

export const auth = {
  signup: (data: { full_name: string; email: string; password: string; company?: string }) =>
    api.post("/api/auth/signup", data),
  login: (data: { email: string; password: string }) => api.post("/api/auth/login", data),
  me: () => api.get<User>("/api/auth/me"),
};

export const documents = {
  list: () => api.get<DocumentItem[]>("/api/documents"),
  upload: (file: File) => {
    const form = new FormData();
    form.append("file", file);
    return api.post<DocumentItem>("/api/documents/upload", form, {
      headers: { "Content-Type": "multipart/form-data" },
    });
  },
  remove: (id: string) => api.delete(`/api/documents/${id}`),
  chat: (data: { session_id: string; message: string; document_ids?: string[] }) =>
    api.post("/api/documents/chat", data),
};

export const workflows = {
  list: () => api.get<WorkflowItem[]>("/api/workflows"),
  get: (id: string) => api.get<WorkflowItem>(`/api/workflows/${id}`),
  create: (data: Partial<WorkflowItem>) => api.post<WorkflowItem>("/api/workflows", data),
  update: (id: string, data: Partial<WorkflowItem>) => api.put<WorkflowItem>(`/api/workflows/${id}`, data),
  remove: (id: string) => api.delete(`/api/workflows/${id}`),
  run: (id: string) => api.post(`/api/workflows/${id}/run`),
  runs: (id: string) => api.get(`/api/workflows/${id}/runs`),
};

export const analytics = {
  dashboard: () => api.get<DashboardStats>("/api/analytics/dashboard"),
};
