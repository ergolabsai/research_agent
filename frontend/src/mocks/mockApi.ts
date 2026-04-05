/**
 * Mock API setup for frontend mock mode (VITE_MOCK_API=true).
 *
 * Intercepts all /api calls via axios-mock-adapter so the frontend runs
 * fully offline — no backend required. The pipeline mock respects
 * MOCK_AGENTS flags from agentConfig.ts to enable/disable agent outputs.
 *
 * Usage: imported dynamically in main.tsx only when VITE_MOCK_API=true,
 * so axios-mock-adapter is excluded from production bundles entirely.
 */

import AxiosMockAdapter from "axios-mock-adapter";
import axios, { type AxiosRequestConfig } from "axios";
import api from "../api/client";
import { MOCK_AGENTS } from "./agentConfig";
import { validationResult } from "./fixtures";
import { graphAnalysisResult } from "./graphAnalysisFixture";
import paperGraph from "./paper_graph.json";
import { demoPaperContentString, demoPaperTitle } from "./demoPaperContent";

// ---------------------------------------------------------------------------
// Local in-memory "DB"
// ---------------------------------------------------------------------------

interface UserRecord {
  id: number;
  email: string;
  username: string;
  password?: string;
  created_at: string;
  updated_at: string;
}

interface DocumentRecord {
  id: number;
  title: string;
  content: string;
  owner_id: number;
  workspace_id: number | null;
  created_at: string;
  updated_at: string;
}

interface WorkspaceRecord {
  id: number;
  name: string;
  created_by: number;
  created_at: string;
  updated_at: string;
}

interface AttachmentRecord {
  id: number;
  filename: string;
  object_key: string;
  content_type: string;
  size: number;
  created_at: string;
}

interface PipelineJobRecord {
  job_id: string;
  paper_id: string;
  title: string;
  status: "pending" | "running" | "completed" | "failed";
  current_step: number;
  total_steps: number;
  step_name: string;
}

interface PipelineFigureAssetRecord {
  figure_name: string;
  submitted?: {
    filename?: string;
    media_type?: string;
    url?: string;
  };
  predicted?: {
    filename?: string;
    media_type?: string;
    url?: string;
  };
}

const STEP_NAMES = [
  "make_context",
  "gather_papers",
  "map_logic",
  "find_evidence",
  "evaluate_figures",
  "evaluate_math",
  "score_papers",
  "compile_results",
];

const nowIso = () => new Date().toISOString();
const makeToken = (userId: number) => `mock-token-${userId}`;

const tokenUserId = new Map<string, number>();
let currentUserId = 1;
let nextUserId = 3;
let nextDocumentId = 7;
let nextWorkspaceId = 3;
let nextAttachmentId = 2;
let nextJobId = 1;

const users: UserRecord[] = [
  {
    id: 1,
    email: "demo@ergolabs.ai",
    username: "demo-user",
    password: "demo123",
    created_at: nowIso(),
    updated_at: nowIso(),
  },
  {
    id: 2,
    email: "collab@ergolabs.ai",
    username: "collaborator",
    created_at: nowIso(),
    updated_at: nowIso(),
  },
];

const documents: DocumentRecord[] = [
  {
    id: 1,
    title: "Catalyst Stability Benchmark",
    content:
      "We evaluate catalyst degradation at 500 thermal cycles and compare retention curves across alloy classes.",
    owner_id: 1,
    workspace_id: null,
    created_at: nowIso(),
    updated_at: nowIso(),
  },
  {
    id: 2,
    title: "Figure-Math Consistency Draft",
    content:
      "Step 3 claims a monotonic gain where Figure 2 indicates variance spikes after epoch 20.",
    owner_id: 1,
    workspace_id: 1,
    created_at: nowIso(),
    updated_at: nowIso(),
  },
  {
    id: 3,
    title: "Citation Convergence Notes",
    content:
      "Primary claim aligns with two related studies and conflicts with one regional survey paper.",
    owner_id: 1,
    workspace_id: 1,
    created_at: nowIso(),
    updated_at: nowIso(),
  },
  {
    id: 4,
    title: "Reaction Kinetics Supplement",
    content:
      "Equation (7) should include the temperature-normalization term from Appendix B.",
    owner_id: 1,
    workspace_id: 2,
    created_at: nowIso(),
    updated_at: nowIso(),
  },
  {
    id: 5,
    title: "Advisor Walkthrough Script",
    content:
      "Use this script during the demo to explain step-by-step scoring and confidence rollup.",
    owner_id: 1,
    workspace_id: null,
    created_at: nowIso(),
    updated_at: nowIso(),
  },
  {
    id: 6,
    title: demoPaperTitle,
    content: demoPaperContentString,
    owner_id: 1,
    workspace_id: null,
    created_at: nowIso(),
    updated_at: nowIso(),
  },
];

const workspaces: WorkspaceRecord[] = [
  {
    id: 1,
    name: "Materials Review",
    created_by: 1,
    created_at: nowIso(),
    updated_at: nowIso(),
  },
  {
    id: 2,
    name: "Math Verification",
    created_by: 1,
    created_at: nowIso(),
    updated_at: nowIso(),
  },
];

const workspaceMembers = new Map<
  number,
  Array<{ user_id: number; role: string }>
>([
  [
    1,
    [
      { user_id: 1, role: "owner" },
      { user_id: 2, role: "editor" },
    ],
  ],
  [2, [{ user_id: 1, role: "owner" }]],
]);

const attachmentsByDocument = new Map<number, AttachmentRecord[]>([
  [
    1,
    [
      {
        id: 1,
        filename: "supplementary-figure.pdf",
        object_key: "attachments/1/supplementary-figure.pdf",
        content_type: "application/pdf",
        size: 284923,
        created_at: nowIso(),
      },
    ],
  ],
]);

const pipelineJobs = new Map<string, PipelineJobRecord>();
const pipelineResults = new Map<string, unknown>();
const pipelineGraphs = new Map<string, unknown>();
const pipelineFigureAssets = new Map<string, PipelineFigureAssetRecord[]>();

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function parseJson(data: unknown): Record<string, unknown> {
  if (!data || typeof data !== "string") return {};
  try {
    return JSON.parse(data) as Record<string, unknown>;
  } catch {
    return {};
  }
}

function userFromAuthHeader(headerValue?: string): UserRecord | null {
  if (!headerValue) return null;
  const token = headerValue.replace("Bearer ", "").trim();
  const userId = tokenUserId.get(token);
  if (!userId) return null;
  return users.find((u) => u.id === userId) ?? null;
}

/**
 * Build the mock pipeline result, applying MOCK_AGENTS flags to strip out
 * agent outputs that are currently disabled. This mirrors what actually
 * happens when a pipeline step is skipped or produces no output.
 */
function buildMockResult(title: string) {
  // Deep-clone so we can mutate without touching the fixture constant.
  const result = JSON.parse(
    JSON.stringify(validationResult),
  ) as typeof validationResult;
  result.paper_structure.title = title;
  result.paper_id = `mock-paper-${nextJobId}`;

  // Strip figure_validations from every step if figures agent is off.
  if (!MOCK_AGENTS.figures) {
    for (const step of Object.values(result.step_validations)) {
      step.figure_validations = [];
    }
  }

  // Strip math_validations from every step if math agent is off.
  if (!MOCK_AGENTS.math) {
    for (const step of Object.values(result.step_validations)) {
      step.math_validations = [];
    }
  }

  // Strip related_papers if citations agent is off.
  if (!MOCK_AGENTS.citations) {
    result.related_papers = [];
  }

  return result;
}

function makeMockFigureDataUrl(
  label: string,
  index: number,
  variant: "submitted" | "predicted",
): string {
  const hue = (index * 41) % 360;
  const curve =
    variant === "submitted"
      ? "M90 340 C 190 300, 270 240, 360 260 C 450 280, 550 200, 650 180 C 730 164, 790 190, 820 175"
      : "M90 350 C 190 318, 270 255, 360 245 C 450 235, 550 210, 650 198 C 730 188, 790 176, 820 170";
  const labelSuffix = variant === "submitted" ? "Submitted" : "Predicted";
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="900" height="480" viewBox="0 0 900 480"><defs><linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop offset="0%" stop-color="hsl(${hue},72%,94%)"/><stop offset="100%" stop-color="hsl(${(hue + (variant === "submitted" ? 45 : 95)) % 360},78%,88%)"/></linearGradient></defs><rect width="900" height="480" fill="url(#bg)"/><rect x="48" y="56" width="804" height="368" fill="white" stroke="hsl(${hue},25%,70%)" stroke-width="2" rx="12"/><path d="${curve}" fill="none" stroke="hsl(${hue},80%,42%)" stroke-width="6" stroke-linecap="round"/><text x="72" y="108" font-family="Arial, sans-serif" font-size="26" fill="#223">${label.replace(/&/g, "and")}</text><text x="72" y="140" font-family="Arial, sans-serif" font-size="18" fill="#445">${labelSuffix}</text></svg>`;
  return `data:image/svg+xml;utf8,${encodeURIComponent(svg)}`;
}

function buildMockFigureAssets(): PipelineFigureAssetRecord[] {
  // Source figure names from graph nodes (preferred) or fall back to result fixtures
  const graphFigureNames = paperGraph.nodes
    .filter((n: { node_type: string }) => n.node_type === "figure")
    .map((n: { figure_name?: string }) => String(n.figure_name ?? ""));
  const resultFigureNames = Object.values(validationResult.step_validations)
    .flatMap((step) => (step.figure_validations ?? []).map((f) => f.figure_name));
  const names = graphFigureNames.length > 0 ? graphFigureNames : resultFigureNames;

  return names.map((figureName, idx) => {
    // Try to import from mocks/figures/ — the user places real images there
    // matching the graph node's figure_name (e.g. excitation_scheme.jpg)
    let submittedUrl: string | undefined;
    let predictedUrl: string | undefined;
    try {
      // Vite eager glob for mock figure images
      const figureModules = import.meta.glob<{ default: string }>(
        "./figures/*",
        { eager: true },
      );
      const key = `./figures/${figureName}`;
      if (figureModules[key]) {
        submittedUrl = figureModules[key].default;
      }
      // Look for _expected variant (e.g. excitation_scheme_expected.jpg)
      const ext = figureName.lastIndexOf(".") >= 0 ? figureName.slice(figureName.lastIndexOf(".")) : "";
      const base = figureName.lastIndexOf(".") >= 0 ? figureName.slice(0, figureName.lastIndexOf(".")) : figureName;
      const expectedKey = `./figures/${base}_expected${ext}`;
      if (figureModules[expectedKey]) {
        predictedUrl = figureModules[expectedKey].default;
      }
    } catch {
      // Glob not available or file missing — fall through to SVG placeholder
    }

    return {
      figure_name: figureName,
      submitted: {
        filename: figureName,
        media_type: "image/jpeg",
        url: submittedUrl ?? makeMockFigureDataUrl(figureName, idx + 1, "submitted"),
      },
      predicted: {
        filename: `${figureName}-predicted`,
        media_type: "image/png",
        url: predictedUrl ?? makeMockFigureDataUrl(figureName, idx + 1, "predicted"),
      },
    };
  });
}

// ---------------------------------------------------------------------------
// Mock setup — exported and called once from main.tsx
// ---------------------------------------------------------------------------

export function setupMockApi(): void {
  // Intercept the shared Axios instance used by api/client.ts.
  const apiMock = new AxiosMockAdapter(api, { delayResponse: 0 });
  // Also intercept the bare axios instance used by the auth refresh interceptor.
  const axiosMock = new AxiosMockAdapter(axios, { delayResponse: 0 });

  // --- Auth ---

  apiMock.onPost("/auth/login").reply((config: AxiosRequestConfig) => {
    const body = parseJson(config.data);
    const identifier = String(body.identifier ?? "").toLowerCase();
    const password = String(body.password ?? "");

    const found = users.find(
      (u) =>
        (u.email.toLowerCase() === identifier ||
          u.username.toLowerCase() === identifier) &&
        (u.password ? u.password === password : true),
    );
    if (!found) return [401, { detail: "Invalid credentials" }];

    currentUserId = found.id;
    const token = makeToken(found.id);
    tokenUserId.set(token, found.id);
    return [
      200,
      {
        access_token: token,
        refresh_token: "mock-refresh",
        token_type: "bearer",
      },
    ];
  });

  apiMock.onPost("/auth/register").reply((config: AxiosRequestConfig) => {
    const body = parseJson(config.data);
    const email = String(body.email ?? "")
      .trim()
      .toLowerCase();
    const username = String(body.username ?? "").trim();
    const password = String(body.password ?? "");

    if (!email || !username || !password)
      return [400, { detail: "Missing registration fields" }];
    if (users.some((u) => u.email.toLowerCase() === email))
      return [400, { detail: "Email already registered" }];

    const user: UserRecord = {
      id: nextUserId++,
      email,
      username,
      password,
      created_at: nowIso(),
      updated_at: nowIso(),
    };
    users.push(user);
    currentUserId = user.id;
    const token = makeToken(user.id);
    tokenUserId.set(token, user.id);
    return [
      200,
      {
        access_token: token,
        refresh_token: "mock-refresh",
        token_type: "bearer",
      },
    ];
  });

  apiMock.onPost("/auth/try").reply(() => {
    // Log in as the pre-seeded demo user so the demo shows existing documents.
    const demo = users.find((u) => u.email === "demo@ergolabs.ai") ?? users[0];
    currentUserId = demo.id;
    const token = makeToken(demo.id);
    tokenUserId.set(token, demo.id);
    return [
      200,
      {
        access_token: token,
        refresh_token: "mock-refresh",
        token_type: "bearer",
      },
    ];
  });

  apiMock.onPost("/auth/refresh").reply(() => {
    const token = makeToken(currentUserId);
    tokenUserId.set(token, currentUserId);
    return [
      200,
      {
        access_token: token,
        refresh_token: "mock-refresh",
        token_type: "bearer",
      },
    ];
  });

  apiMock.onGet("/auth/me").reply((config: AxiosRequestConfig) => {
    const user =
      userFromAuthHeader(config.headers?.Authorization as string | undefined) ??
      users.find((u) => u.id === currentUserId);
    if (!user) return [401, { detail: "Not authenticated" }];
    return [
      200,
      {
        id: user.id,
        email: user.email,
        username: user.username,
        created_at: user.created_at,
        updated_at: user.updated_at,
      },
    ];
  });

  apiMock.onPost("/auth/logout").reply(() => [200, { ok: true }]);

  // --- Documents ---

  apiMock.onGet("/documents").reply(() => [200, documents]);

  apiMock.onPost("/documents").reply((config: AxiosRequestConfig) => {
    const body = parseJson(config.data);
    const title =
      String(body.title ?? "Untitled Document").trim() || "Untitled Document";
    const workspaceId =
      body.workspace_id == null ? null : Number(body.workspace_id);
    const doc: DocumentRecord = {
      id: nextDocumentId++,
      title,
      content: "",
      owner_id: currentUserId,
      workspace_id: Number.isNaN(workspaceId as number) ? null : workspaceId,
      created_at: nowIso(),
      updated_at: nowIso(),
    };
    documents.unshift(doc);
    return [200, doc];
  });

  apiMock.onGet(/\/documents\/\d+$/).reply((config: AxiosRequestConfig) => {
    const id = Number(config.url?.split("/").pop());
    const doc = documents.find((d) => d.id === id);
    return doc ? [200, doc] : [404, { detail: "Document not found" }];
  });

  apiMock.onPut(/\/documents\/\d+$/).reply((config: AxiosRequestConfig) => {
    const id = Number(config.url?.split("/").pop());
    const body = parseJson(config.data);
    const doc = documents.find((d) => d.id === id);
    if (!doc) return [404, { detail: "Document not found" }];
    if (typeof body.title === "string") doc.title = body.title;
    if (typeof body.content === "string") doc.content = body.content;
    if (body.workspace_id === null || typeof body.workspace_id === "number")
      doc.workspace_id = body.workspace_id as number | null;
    doc.updated_at = nowIso();
    return [200, doc];
  });

  apiMock.onDelete(/\/documents\/\d+$/).reply((config: AxiosRequestConfig) => {
    const id = Number(config.url?.split("/").pop());
    const idx = documents.findIndex((d) => d.id === id);
    if (idx >= 0) documents.splice(idx, 1);
    return [200, { ok: true }];
  });

  apiMock
    .onGet(/\/documents\/\d+\/attachments$/)
    .reply((config: AxiosRequestConfig) => {
      const match = config.url?.match(/\/documents\/(\d+)\/attachments$/);
      return [200, attachmentsByDocument.get(Number(match?.[1])) ?? []];
    });

  apiMock
    .onPost(/\/documents\/\d+\/attachments$/)
    .reply((config: AxiosRequestConfig) => {
      const match = config.url?.match(/\/documents\/(\d+)\/attachments$/);
      const docId = Number(match?.[1]);
      const att: AttachmentRecord = {
        id: nextAttachmentId++,
        filename: `uploaded-file-${nextAttachmentId}.pdf`,
        object_key: `attachments/${docId}/uploaded-file-${nextAttachmentId}.pdf`,
        content_type: "application/pdf",
        size: 150000,
        created_at: nowIso(),
      };
      const current = attachmentsByDocument.get(docId) ?? [];
      attachmentsByDocument.set(docId, [att, ...current]);
      return [200, att];
    });

  apiMock
    .onDelete(/\/documents\/\d+\/attachments\/\d+$/)
    .reply((config: AxiosRequestConfig) => {
      const match = config.url?.match(
        /\/documents\/(\d+)\/attachments\/(\d+)$/,
      );
      const docId = Number(match?.[1]);
      const attId = Number(match?.[2]);
      const current = attachmentsByDocument.get(docId) ?? [];
      attachmentsByDocument.set(
        docId,
        current.filter((a) => a.id !== attId),
      );
      return [200, { ok: true }];
    });

  apiMock.onPost(/\/documents\/\d+\/share$/).reply(() => [200, { ok: true }]);
  apiMock
    .onDelete(/\/documents\/\d+\/share\/\d+$/)
    .reply(() => [200, { ok: true }]);

  // --- Workspaces ---

  apiMock.onGet("/workspaces").reply(() => [200, workspaces]);

  apiMock.onPost("/workspaces").reply((config: AxiosRequestConfig) => {
    const body = parseJson(config.data);
    const name =
      String(body.name ?? "Untitled Workspace").trim() || "Untitled Workspace";
    const ws: WorkspaceRecord = {
      id: nextWorkspaceId++,
      name,
      created_by: currentUserId,
      created_at: nowIso(),
      updated_at: nowIso(),
    };
    workspaces.unshift(ws);
    workspaceMembers.set(ws.id, [{ user_id: currentUserId, role: "owner" }]);
    return [200, ws];
  });

  apiMock.onGet(/\/workspaces\/\d+$/).reply((config: AxiosRequestConfig) => {
    const id = Number(config.url?.split("/").pop());
    const ws = workspaces.find((w) => w.id === id);
    return ws ? [200, ws] : [404, { detail: "Workspace not found" }];
  });

  apiMock.onPut(/\/workspaces\/\d+$/).reply((config: AxiosRequestConfig) => {
    const id = Number(config.url?.split("/").pop());
    const body = parseJson(config.data);
    const ws = workspaces.find((w) => w.id === id);
    if (!ws) return [404, { detail: "Workspace not found" }];
    if (typeof body.name === "string") ws.name = body.name;
    ws.updated_at = nowIso();
    return [200, ws];
  });

  apiMock.onDelete(/\/workspaces\/\d+$/).reply((config: AxiosRequestConfig) => {
    const id = Number(config.url?.split("/").pop());
    const idx = workspaces.findIndex((w) => w.id === id);
    if (idx >= 0) workspaces.splice(idx, 1);
    documents.forEach((d) => {
      if (d.workspace_id === id) {
        d.workspace_id = null;
        d.updated_at = nowIso();
      }
    });
    workspaceMembers.delete(id);
    return [200, { ok: true }];
  });

  apiMock
    .onGet(/\/workspaces\/\d+\/documents$/)
    .reply((config: AxiosRequestConfig) => {
      const match = config.url?.match(/\/workspaces\/(\d+)\/documents$/);
      const id = Number(match?.[1]);
      return [200, documents.filter((d) => d.workspace_id === id)];
    });

  apiMock
    .onGet(/\/workspaces\/\d+\/members$/)
    .reply((config: AxiosRequestConfig) => {
      const match = config.url?.match(/\/workspaces\/(\d+)\/members$/);
      const id = Number(match?.[1]);
      return [200, workspaceMembers.get(id) ?? []];
    });

  apiMock
    .onPost(/\/workspaces\/\d+\/members$/)
    .reply((config: AxiosRequestConfig) => {
      const match = config.url?.match(/\/workspaces\/(\d+)\/members$/);
      const id = Number(match?.[1]);
      const body = parseJson(config.data);
      const userId = Number(body.user_id);
      const role = String(body.role ?? "viewer");
      const members = workspaceMembers.get(id) ?? [];
      if (!members.some((m) => m.user_id === userId)) {
        members.push({ user_id: userId, role });
        workspaceMembers.set(id, members);
      }
      return [200, { ok: true }];
    });

  apiMock
    .onDelete(/\/workspaces\/\d+\/members\/\d+$/)
    .reply((config: AxiosRequestConfig) => {
      const match = config.url?.match(/\/workspaces\/(\d+)\/members\/(\d+)$/);
      const wsId = Number(match?.[1]);
      const userId = Number(match?.[2]);
      const members = workspaceMembers.get(wsId) ?? [];
      workspaceMembers.set(
        wsId,
        members.filter((m) => m.user_id !== userId),
      );
      return [200, { ok: true }];
    });

  // --- Users ---

  apiMock.onGet("/users/search").reply((config: AxiosRequestConfig) => {
    const rawQuery = String(config.params?.q ?? "")
      .toLowerCase()
      .trim();
    const data = users
      .filter(
        (u) =>
          !rawQuery ||
          u.email.toLowerCase().includes(rawQuery) ||
          u.username.toLowerCase().includes(rawQuery),
      )
      .map((u) => ({ id: u.id, email: u.email, username: u.username }));
    return [200, { data }];
  });

  // --- Pipeline ---

  apiMock.onPost("/pipeline/validate").reply((config: AxiosRequestConfig) => {
    const body = parseJson(config.data);
    const title = String(body.title ?? "Untitled Paper");

    const jobId = `mock-job-${nextJobId}`;
    const result = buildMockResult(title);

    const job: PipelineJobRecord = {
      job_id: jobId,
      paper_id: result.paper_id,
      title,
      status: "completed",
      current_step: STEP_NAMES.length,
      total_steps: STEP_NAMES.length,
      step_name: STEP_NAMES[STEP_NAMES.length - 1],
    };

    pipelineJobs.set(jobId, job);
    pipelineResults.set(jobId, result);
    pipelineGraphs.set(jobId, structuredClone(paperGraph));
    pipelineFigureAssets.set(jobId, buildMockFigureAssets());
    nextJobId++;

    return [200, { ...job }];
  });

  apiMock
    .onGet(/\/pipeline\/status\/.+$/)
    .reply((config: AxiosRequestConfig) => {
      const jobId = config.url?.split("/").pop() ?? "";
      const job = pipelineJobs.get(jobId);
      return job ? [200, { ...job }] : [404, { detail: "Job not found" }];
    });

  apiMock
    .onGet(/\/pipeline\/results\/.+$/)
    .reply((config: AxiosRequestConfig) => {
      const jobId = config.url?.split("/").pop() ?? "";
      const result = pipelineResults.get(jobId);
      return result ? [200, result] : [404, { detail: "Result not found" }];
    });

  apiMock
    .onGet(/\/pipeline\/graph\/.+$/)
    .reply((config: AxiosRequestConfig) => {
      const jobId = config.url?.split("/").pop() ?? "";
      const graph = pipelineGraphs.get(jobId);
      return graph ? [200, graph] : [404, { detail: "Graph not found" }];
    });

  apiMock
    .onGet(/\/pipeline\/figures\/.+$/)
    .reply((config: AxiosRequestConfig) => {
      const jobId = config.url?.split("/").pop() ?? "";
      const figures = pipelineFigureAssets.get(jobId) ?? [];
      return [200, { job_id: jobId, figures }];
    });

  apiMock
    .onGet(/\/pipeline\/analysis\/.+$/)
    .reply((config: AxiosRequestConfig) => {
      const jobId = config.url?.split("/").pop() ?? "";
      if (pipelineResults.has(jobId)) {
        return [200, structuredClone(graphAnalysisResult)];
      }
      return [404, { detail: "Analysis not found" }];
    });

  apiMock.onGet("/pipeline/jobs").reply(() => {
    return [200, Array.from(pipelineJobs.values())];
  });

  // Catch-all for any pipeline routes not explicitly handled.
  apiMock.onAny(/\/pipeline\/.+/).reply(404, { detail: "Not found in mock" });

  // The auth refresh interceptor in api/client.ts makes a raw axios call,
  // so we also need to intercept it on the default axios instance.
  axiosMock.onPost("/api/auth/refresh").reply(() => {
    const token = makeToken(currentUserId);
    tokenUserId.set(token, currentUserId);
    return [
      200,
      {
        access_token: token,
        refresh_token: "mock-refresh",
        token_type: "bearer",
      },
    ];
  });

  // Passthrough everything else so any unmocked calls fail loudly in the
  // browser network tab rather than silently returning undefined.
  apiMock.onAny().reply(404, { detail: "Not mocked" });
}
