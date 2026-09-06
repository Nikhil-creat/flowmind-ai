import axios from "axios";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export const api = axios.create({ baseURL: API_BASE_URL });

api.interceptors.request.use((config) => {
  if (typeof window !== "undefined") {
    const token = localStorage.getItem("flowmind_token");
    if (token) config.headers.Authorization = `Bearer ${token}`;
    const workspaceId = localStorage.getItem("flowmind_workspace_id");
    if (workspaceId) config.headers["X-Workspace-ID"] = workspaceId;
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

export type WorkspaceItem = {
  id: string;
  name: string;
  plan: string;
  role: "owner" | "admin" | "member";
  created_at: string;
};

export type MemberItem = {
  user_id: string;
  full_name: string;
  email: string;
  role: string;
  created_at: string;
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

export const workspaces = {
  list: () => api.get<WorkspaceItem[]>("/api/workspaces"),
  create: (data: { name: string }) => api.post<WorkspaceItem>("/api/workspaces", data),
  members: (id: string) => api.get<MemberItem[]>(`/api/workspaces/${id}/members`),
  invite: (id: string, data: { email: string; role: string }) =>
    api.post<MemberItem>(`/api/workspaces/${id}/invite`, data),
  updateRole: (id: string, userId: string, role: string) =>
    api.put(`/api/workspaces/${id}/members/${userId}`, { role }),
  removeMember: (id: string, userId: string) => api.delete(`/api/workspaces/${id}/members/${userId}`),
  checkout: (id: string) => api.post(`/api/workspaces/${id}/billing/checkout`),
};
