export type TaskStatus = "backlog" | "todo" | "in_progress" | "review" | "done";
export type Priority = "critical" | "high" | "medium" | "low";
export type ClarifyingQuestion = {
  id: string;
  question: string;
  field_key: string;
  question_type: "text" | "single_choice";
  choices: string[];
  why_it_matters: string;
};
export type AuthUser = { id: string; name: string; email: string };
export type AuthResponse = { token: string; user: AuthUser };
export type Project = {
  id: string; name: string; description: string;
  status: "draft" | "clarifying" | "ready" | "generated" | "stale";
  revision: number;
  context: {
    product_summary: string; business_objectives: string[]; primary_features: string[];
    target_users: string[]; technical_constraints: string[]; organisational_constraints: string[];
    assumptions: string[]; unknown_information: string[]; developer_count: number | null;
    budget: string | null; delivery_deadline: string | null;
  } | null;
};
export type BacklogTask = {
  id: string; title: string; description: string; story_id: string | null; task_type: string;
  priority: Priority; priority_reason: string; estimate_points: number | null;
  dependency_ids: string[]; status: TaskStatus; sprint_number: number | null;
  position: number; revision: number; is_manual: boolean;
};
export type UserStory = {
  id: string; title: string; role: string; goal: string; benefit: string;
  acceptance_criteria: { description: string }[];
};
export type Sprint = {
  id: string; number: number; goal: string; capacity_points: number | null;
  rationale: string; assumptions: string[];
};
export type ProjectDetail = Project & { user_stories: UserStory[]; tasks: BacklogTask[]; sprints: Sprint[] };
export type ClarificationResponse = { project: Project; question: ClarifyingQuestion | null; message: string };

const API_URL = (import.meta.env.VITE_API_URL || "http://127.0.0.1:8000/api/v1").replace(/\/$/, "");
let authToken = localStorage.getItem("planora_token");

export function setAuthToken(token: string | null) {
  authToken = token;
  if (token) localStorage.setItem("planora_token", token);
  else localStorage.removeItem("planora_token");
}

export class ApiError extends Error {
  constructor(message: string, public readonly status: number) {
    super(message);
    this.name = "ApiError";
  }
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  let response: Response;
  const controller = new AbortController();
  const timeout = window.setTimeout(() => controller.abort(), 120_000);
  try {
    const headers = new Headers(options.headers);
    headers.set("Content-Type", "application/json");
    if (authToken) headers.set("Authorization", `Bearer ${authToken}`);
    response = await fetch(`${API_URL}${path}`, { ...options, headers, signal: controller.signal });
  } catch {
    if (controller.signal.aborted) {
      throw new ApiError("Le backend n'a pas répondu après 2 minutes. Vérifiez les logs FastAPI et l'état de l'agent Gemini.", 408);
    }
    throw new ApiError("Impossible de joindre le backend. Vérifiez que FastAPI tourne sur le port 8001.", 0);
  } finally {
    window.clearTimeout(timeout);
  }
  const body = await response.json().catch(() => null) as { detail?: unknown } | null;
  if (!response.ok) throw new ApiError(formatApiError(body?.detail), response.status);
  return body as T;
}

function formatApiError(detail: unknown): string {
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    const messages = detail.map((item) => {
      if (!item || typeof item !== "object") return null;
      const message = "msg" in item && typeof item.msg === "string" ? item.msg : null;
      return message;
    }).filter((message): message is string => Boolean(message));
    if (messages.length) return messages.join(" ");
  }
  if (detail && typeof detail === "object" && "message" in detail && typeof detail.message === "string") {
    return detail.message;
  }
  return "Une erreur est survenue côté serveur.";
}

export function register(name: string, email: string, password: string) {
  return request<AuthResponse>("/auth/register", { method: "POST", body: JSON.stringify({ name, email, password }) });
}
export function login(email: string, password: string) {
  return request<AuthResponse>("/auth/login", { method: "POST", body: JSON.stringify({ email, password }) });
}
export function createProject(name: string, description: string) {
  return request<ProjectDetail>("/projects", { method: "POST", body: JSON.stringify({ name, description }) });
}
export function startClarification(projectId: string) {
  return request<ClarificationResponse>(`/projects/${projectId}/clarifications/start`, { method: "POST" });
}
export function answerClarification(projectId: string, questionId: string, answer: string) {
  return request<ClarificationResponse>(`/projects/${projectId}/clarifications`, {
    method: "POST", body: JSON.stringify({ question_id: questionId, answer }),
  });
}
export function generateProject(projectId: string) {
  return request<{ project: ProjectDetail; warnings: string[] }>(`/projects/${projectId}/generate`, { method: "POST" });
}
export function updateTask(projectId: string, taskId: string, changes: Partial<Pick<BacklogTask, "status" | "priority" | "sprint_number" | "position">>) {
  return request<{ task: BacklogTask }>(`/projects/${projectId}/tasks/${taskId}`, {
    method: "PATCH", body: JSON.stringify(changes),
  });
}
