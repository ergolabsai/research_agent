import axios, { AxiosInstance, AxiosError } from "axios";
import {
  AuthTokens,
  User,
  PipelineJob,
  ValidateRequest,
  ValidationResult,
  GraphAnalysis,
  NodeLinkGraphRaw,
  Attachment,
} from "../types";

let currentAccessToken: string | null = null;
let isRefreshing = false;
let refreshSubscribers: Array<(token: string) => void> = [];

// Simple axios instance with token interceptor
const api: AxiosInstance = axios.create({
  baseURL: "/api",
  withCredentials: true,
});

// Add request interceptor to include access token
api.interceptors.request.use((config) => {
  if (currentAccessToken) {
    config.headers.Authorization = `Bearer ${currentAccessToken}`;
  }
  return config;
});

// Add response interceptor to handle token expiration
api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as any;

    // Check if error is 401 and we haven't already tried to refresh
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      if (!isRefreshing) {
        isRefreshing = true;

        try {
          // Call refresh endpoint
          const response = await axios.post<AuthTokens>(
            "/api/auth/refresh",
            {},
            {
              withCredentials: true,
            },
          );

          const newAccessToken = response.data.access_token;
          setCurrentAccessToken(newAccessToken);
          isRefreshing = false;

          // Retry all queued requests with new token
          refreshSubscribers.forEach((callback) => callback(newAccessToken));
          refreshSubscribers = [];

          // Retry original request
          originalRequest.headers.Authorization = `Bearer ${newAccessToken}`;
          return api(originalRequest);
        } catch (refreshError) {
          // Refresh failed - user is logged out
          isRefreshing = false;
          refreshSubscribers = [];
          setCurrentAccessToken(null);
          // Optionally redirect to login here
          return Promise.reject(refreshError);
        }
      } else {
        // Refresh is already in progress, queue this request
        return new Promise((resolve) => {
          refreshSubscribers.push((token: string) => {
            originalRequest.headers.Authorization = `Bearer ${token}`;
            resolve(api(originalRequest));
          });
        });
      }
    }

    return Promise.reject(error);
  },
);

export const setCurrentAccessToken = (token: string | null) => {
  currentAccessToken = token;
};

// Simple auth API - caller handles tokens manually
export const authAPI = {
  async register(email: string, username: string, password: string) {
    const { data } = await api.post<AuthTokens>("/auth/register", {
      email,
      username,
      password,
    });
    return data;
  },

  async login(identifier: string, password: string) {
    const { data } = await api.post<AuthTokens>("/auth/login", {
      identifier,
      password,
    });
    return data;
  },

  async me(accessToken: string) {
    const { data } = await api.get<User>("/auth/me", {
      headers: {
        Authorization: `Bearer ${accessToken}`,
      },
    });
    return data;
  },

  async refresh() {
    const { data } = await api.post<AuthTokens>("/auth/refresh", {});
    return data;
  },

  async tryItNow() {
    const { data } = await api.post<AuthTokens>("/auth/try", {});
    return data;
  },

  async logout() {
    await api.post("/auth/logout");
  },
};

// Documents endpoints
export const documentsAPI = {
  list: () => api.get("/documents"),

  get: (id: number) => api.get(`/documents/${id}`),

  create: (title: string, workspaceId?: number) =>
    api.post("/documents", { title, workspace_id: workspaceId }),

  update: (id: number, title: string, content: string) =>
    api.put(`/documents/${id}`, { title, content }),

  moveToWorkspace: (id: number, workspaceId: number | null) =>
    api.put(`/documents/${id}`, { workspace_id: workspaceId }),

  delete: (id: number) => api.delete(`/documents/${id}`),

  share: (id: number, userId: number, permission: "view" | "edit") =>
    api.post(`/documents/${id}/share`, { user_id: userId, permission }),

  unshare: (id: number, userId: number) =>
    api.delete(`/documents/${id}/share/${userId}`),

  listAttachments: (id: number) =>
    api.get<Attachment[]>(`/documents/${id}/attachments`),

  uploadAttachment: (id: number, file: File) => {
    const formData = new FormData();
    formData.append("file", file);
    return api.post<Attachment>(`/documents/${id}/attachments`, formData, {
      headers: { "Content-Type": "multipart/form-data" },
    });
  },

  deleteAttachment: (documentId: number, attachmentId: number) =>
    api.delete(`/documents/${documentId}/attachments/${attachmentId}`),
};

// Workspaces endpoints
export const workspacesAPI = {
  list: () => api.get("/workspaces"),

  get: (id: number) => api.get(`/workspaces/${id}`),

  create: (name: string) => api.post("/workspaces", { name }),

  update: (id: number, name: string) => api.put(`/workspaces/${id}`, { name }),

  delete: (id: number) => api.delete(`/workspaces/${id}`),

  addMember: (id: number, userId: number, role: string) =>
    api.post(`/workspaces/${id}/members`, { user_id: userId, role }),

  removeMember: (id: number, userId: number) =>
    api.delete(`/workspaces/${id}/members/${userId}`),

  documents: (id: number) => api.get(`/workspaces/${id}/documents`),
};

// Users endpoints
export const usersAPI = {
  search: (query: string) => api.get("/users/search", { params: { q: query } }),
};

// Pipeline endpoints
export const pipelineAPI = {
  validate: (request: ValidateRequest) =>
    api.post<PipelineJob>("/pipeline/validate", request),

  status: (jobId: string) => api.get<PipelineJob>(`/pipeline/status/${jobId}`),

  results: (jobId: string) =>
    api.get<ValidationResult>(`/pipeline/results/${jobId}`),

  figures: (jobId: string) =>
    api.get<{
      job_id: string;
      figures: Array<{
        figure_name: string;
        submitted?: {
          filename?: string;
          media_type?: string;
          url?: string | null;
        };
        predicted?: {
          filename?: string;
          media_type?: string;
          url?: string | null;
        };
      }>;
    }>(`/pipeline/figures/${jobId}`),

  history: (paperId: string) =>
    api.get<ValidationResult[]>(`/pipeline/history/${paperId}`),

  jobs: () => api.get<PipelineJob[]>("/pipeline/jobs"),

  graph: (jobId: string) => api.get<NodeLinkGraphRaw>(`/pipeline/graph/${jobId}`),

  analysis: (jobId: string) => api.get<GraphAnalysis>(`/pipeline/analysis/${jobId}`),
};

export default api;
