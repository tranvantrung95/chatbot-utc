import type { UserRole } from "@/lib/types";

const API_BASE = process.env.NEXT_PUBLIC_BACKEND_URL || "http://127.0.0.1:8001";

type RequestOptions = {
  method?: "GET" | "POST";
  token?: string | null;
  body?: unknown;
};

export type ApiUser = {
  id: string;
  name: string;
  identifier: string;
  email: string;
  faculty: string;
  role: UserRole;
  role_label: string;
  status: string;
  created_at: string;
};

export type StudentGrades = {
  gpa: number;
  courses: Array<{
    code: string;
    name: string;
    credits: number;
    qt: number;
    thi: number;
    total: number;
    grade: string;
    passed: boolean;
    semester: number;
  }>;
};

export type StudentProgress = {
  gpa: number;
  earned: number;
  required: number;
  percent: number;
  warnings: string[];
};

export type StudentRecommendations = {
  available: Array<{
    code: string;
    name: string;
    credits: number;
    semester: number;
  }>;
  locked: Array<{
    code: string;
    name: string;
    credits: number;
    semester: number;
  }>;
};

export type ChatSource = {
  title: string;
  source: string;
  source_url?: string;
  source_name: string;
  heading: string;
  type?: string;
  score: number;
  content: string;
};

export type ChatResponse = {
  thinking: string;
  answer: string;
  sources: ChatSource[];
  topic: string;
  latency_sec: number;
  intent?: string;
  intent_confidence?: number;
  route?: string;
  retrieval_tier?: string;
};

type DashboardResponse = {
  kpis: Array<{ label: string; value: string; delta: string }>;
  access_by_day: Array<{ day: string; value: number }>;
  question_topics: Array<{ label: string; value: number }>;
  success_rate: number;
  avg_latency_sec: number;
  recent_activities: Array<{
    id: string;
    action: string;
    user: string;
    status: string;
    time: string;
  }>;
};

async function apiRequest<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
  };
  if (options.token) headers.Authorization = `Bearer ${options.token}`;

  const response = await fetch(`${API_BASE}${path}`, {
    method: options.method || "GET",
    headers,
    body: options.body ? JSON.stringify(options.body) : undefined,
  });
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    const message =
      typeof payload?.detail === "string" ? payload.detail : "Không thể kết nối backend.";
    throw new Error(message);
  }
  return payload as T;
}

export async function apiLogin(identifier: string, password: string) {
  return apiRequest<{ token: string; user: ApiUser }>("/api/auth/login", {
    method: "POST",
    body: { identifier, password },
  });
}

export async function apiRegister(payload: {
  full_name: string;
  identifier: string;
  email: string;
  password: string;
  role: UserRole;
}) {
  return apiRequest<{ message: string; user: ApiUser }>("/api/auth/register", {
    method: "POST",
    body: payload,
  });
}

export async function apiForgotPassword(email: string) {
  return apiRequest<{ message: string }>("/api/auth/forgot-password", {
    method: "POST",
    body: { email },
  });
}

export async function apiMe(token: string) {
  return apiRequest<{ user: ApiUser }>("/api/auth/me", { token });
}

export async function apiLogout(token: string) {
  return apiRequest<{ message: string }>("/api/auth/logout", {
    method: "POST",
    token,
  });
}

export async function apiChangePassword(token: string, current_password: string, new_password: string) {
  return apiRequest<{ message: string }>("/api/auth/change-password", {
    method: "POST",
    token,
    body: { current_password, new_password },
  });
}

export async function apiChat(token: string, question: string, top_k = 5) {
  return apiRequest<ChatResponse>("/api/chat", {
    method: "POST",
    token,
    body: { question, top_k },
  });
}

export async function apiNews() {
  return apiRequest<{
    items: Array<{ id: string; title: string; summary: string; date: string; category: string; url: string }>;
  }>("/api/news");
}

export async function apiCreateFeedback(token: string, payload: { subject: string; satisfaction: string; content: string; email: string }) {
  return apiRequest<{ message: string; id: string }>("/api/feedback", {
    method: "POST",
    token,
    body: payload,
  });
}

export async function apiFeedbackList(token: string) {
  return apiRequest<{
    items: Array<{ id: string; topic: string; student: string; satisfaction: string; content: string; email: string; status: string; time: string }>;
  }>("/api/feedback", { token });
}

export async function apiCreateBug(token: string, payload: { bug_type: string; severity: string; description: string; screenshot_note: string }) {
  return apiRequest<{ message: string; id: string }>("/api/bugs", {
    method: "POST",
    token,
    body: payload,
  });
}

export async function apiBugs(token: string) {
  return apiRequest<{
    items: Array<{ id: string; title: string; type: string; severity: string; description: string; status: string; assignee: string; reporter: string; time: string }>;
  }>("/api/bugs", { token });
}

export async function apiDashboard(token: string) {
  return apiRequest<DashboardResponse>("/api/dashboard", { token });
}

export async function apiUsers(token: string, params: { q?: string; role?: string; status_filter?: string } = {}) {
  const search = new URLSearchParams();
  if (params.q) search.set("q", params.q);
  if (params.role) search.set("role", params.role);
  if (params.status_filter) search.set("status_filter", params.status_filter);
  const qs = search.toString();
  return apiRequest<{ items: ApiUser[] }>(`/api/users${qs ? `?${qs}` : ""}`, { token });
}

export async function apiToggleLock(token: string, userId: string) {
  return apiRequest<{ message: string; status: string }>(`/api/users/${userId}/toggle-lock`, {
    method: "POST",
    token,
  });
}

export async function apiResetPassword(token: string, userId: string) {
  return apiRequest<{ message: string }>(`/api/users/${userId}/reset-password`, {
    method: "POST",
    token,
  });
}

export async function apiDocuments(token: string) {
  return apiRequest<{
    items: Array<{ id: string; name: string; type: string; source: string; status: string; updated_at: string; owner: string; filename: string; char_count: number; chunk_count: number }>;
  }>("/api/documents", { token });
}

export async function apiImportDocument(token: string, payload: { title: string; source: string; content: string }) {
  return apiRequest<{ message: string; filename: string }>("/api/documents/import", {
    method: "POST",
    token,
    body: payload,
  });
}

export async function apiQuestions(token: string) {
  return apiRequest<{
    items: Array<{ id: string; question: string; topic: string; asker: string; time: string; status: string; rating: string }>;
  }>("/api/questions", { token });
}

export async function apiSuggestions() {
  return apiRequest<{ items: string[] }>("/api/suggestions");
}

export async function apiStudentGrades(token: string) {
  return apiRequest<StudentGrades>("/api/student/grades", { token });
}

export async function apiStudentProgress(token: string) {
  return apiRequest<StudentProgress>("/api/student/progress", { token });
}

export async function apiStudentRecommendations(token: string) {
  return apiRequest<StudentRecommendations>("/api/student/recommendations", { token });
}
