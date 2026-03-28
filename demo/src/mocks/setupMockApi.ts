import axios from "axios";
import AxiosMockAdapter from "axios-mock-adapter";
import api from "../../../frontend/src/api/client";

interface UserRecord {
  id: number;
  email: string;
  username: string;
  created_at: string;
  updated_at: string;
  password?: string;
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
  started_at: number;
}

const nowIso = () => new Date().toISOString();
const makeToken = (userId: number) => `demo-token-${userId}`;

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

let currentUserId = 1;
let nextUserId = 3;
let nextDocumentId = 6;
let nextWorkspaceId = 3;
let nextAttachmentId = 2;
let nextJobId = 2;

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

const tokenUserId = new Map<string, number>();

function parseJson(data: unknown): Record<string, unknown> {
  if (!data || typeof data !== "string") {
    return {};
  }

  try {
    return JSON.parse(data) as Record<string, unknown>;
  } catch {
    return {};
  }
}

function userFromAuthHeader(headerValue?: string): UserRecord | null {
  if (!headerValue) {
    return null;
  }

  const token = headerValue.replace("Bearer ", "").trim();
  const userId = tokenUserId.get(token);
  if (!userId) {
    return null;
  }

  return users.find((u) => u.id === userId) || null;
}

function buildValidationResult(title: string) {
  return {
    paper_id: "demo-paper-001",
    confidence_score: 0.82,
    overall_assessment: {
      review:
        "The paper presents a coherent main claim with strong evidence density. Figure support is mostly consistent, but one plot trend is overstated relative to numeric variance. Mathematical derivations are valid after correcting a normalization constant in Equation (7). Citation convergence is favorable with one dissenting source that reflects a narrower sampling context.",
    },
    paper_structure: {
      title,
      main_claim:
        "Adaptive catalyst tuning improves reaction efficiency while preserving long-term thermal stability.",
      logical_steps: [
        {
          step_number: 1,
          description:
            "Define baseline catalyst behavior and control conditions.",
          section: "Introduction",
        },
        {
          step_number: 2,
          description: "Compare tuned catalyst response under thermal cycling.",
          section: "Results",
        },
        {
          step_number: 3,
          description: "Validate kinetic model against measured outputs.",
          section: "Analysis",
        },
      ],
    },
    step_validations: {
      "1": {
        evidence_count: 3,
        figure_validations: [
          {
            figure_name: "Figure 1",
            supports_step: 1,
            validity: {
              confirmations: [
                "Baseline curve aligns with reported retention for first 100 cycles.",
              ],
              contradictions: [],
            },
          },
        ],
        math_validations: [],
      },
      "2": {
        evidence_count: 4,
        figure_validations: [
          {
            figure_name: "Figure 2",
            supports_step: 2,
            validity: {
              confirmations: [
                "Trendline indicates overall efficiency gain in tuned variant.",
              ],
              contradictions: [
                "Variance spike around epoch 20 weakens claim of strictly monotonic improvement.",
              ],
            },
          },
        ],
        math_validations: [],
      },
      "3": {
        evidence_count: 2,
        figure_validations: [],
        math_validations: [
          {
            equation_reference: "Eq. (7)",
            calculation_valid: true,
            details:
              "Normalization term included and verified against calculator tool output.",
          },
          {
            equation_reference: "Eq. (3)",
            calculation_valid: false,
            details:
              "Inflection point offset not accounted for in the plot agreement formula.",
          },
        ],
      },
    },
    related_papers: [
      {
        paper_id: "cit-1",
        title: "Structured Verification Graphs for Scientific Reasoning",
        authors: "Smith, A., Jones, B., et al.",
        abstract:
          "Reports that typed reasoning graphs reduce unsupported conclusion propagation in review pipelines.",
        source: "semantic_scholar",
        venue: "NeurIPS",
        year: 2024,
        relevancy_score: 0.93,
        relevancy_reasoning:
          "Strongly aligns with our finding that explicit dependency edges improve contradiction detection.",
        convergence_score: 0.78,
        convergence_reasoning:
          "Supports the framework approach to structured claim verification.",
      },
      {
        paper_id: "cit-2",
        title: "Visual Claim Auditing with Latent Trend Models",
        authors: "Patel, N., Chen, M.",
        abstract:
          "Shows trend-based figure auditing succeeds on monotonic dynamics but struggles with abrupt regime shifts.",
        source: "lancedb_vector",
        venue: "ICLR",
        year: 2025,
        relevancy_score: 0.87,
        relevancy_reasoning:
          "Partially agrees. Our discrepancies show similar weakness around inflection-heavy figures.",
        convergence_score: 0.26,
        convergence_reasoning:
          "Partially converges—method agrees on smooth curves, diverges on variance-heavy sections.",
      },
      {
        paper_id: "cit-3",
        title: "Symbolic Consistency Checks in Multi-Agent Review",
        authors: "Ruiz, L., et al.",
        abstract:
          "Demonstrates that equation-context extraction can recover missing assumptions in mathematical claims.",
        source: "lancedb_fts",
        venue: "ACL Findings",
        year: 2025,
        relevancy_score: 0.81,
        relevancy_reasoning:
          "Supports our math assistant workflow where users enrich equation context before re-evaluation.",
        convergence_score: 0.64,
        convergence_reasoning:
          "Strong alignment: both papers advocate for symbolic context enrichment.",
      },
      {
        paper_id: "cit-4",
        title: "When Citation Similarity Misleads Scientific Validation",
        authors: "Garcia, R., Kim, S.",
        abstract:
          "Argues semantic similarity can inflate trust even when methodological assumptions diverge.",
        source: "semantic_scholar",
        venue: "arXiv",
        year: 2023,
        relevancy_score: 0.69,
        relevancy_reasoning:
          "Challenges our current scoring; suggests stronger penalties for methodological mismatch.",
        convergence_score: -0.31,
        convergence_reasoning:
          "Contradicts our approach of weighting semantic relevancy equally with convergence.",
      },
    ],
  };
}

function updateJobProgress(job: PipelineJobRecord): PipelineJobRecord {
  if (job.status === "completed" || job.status === "failed") {
    return job;
  }

  const completedSteps = STEP_NAMES.length;

  job.current_step = completedSteps;
  job.step_name = STEP_NAMES[completedSteps - 1];

  if (completedSteps >= STEP_NAMES.length) {
    job.status = "completed";
    job.current_step = STEP_NAMES.length;
    job.step_name = STEP_NAMES[STEP_NAMES.length - 1];
  } else {
    job.status = "running";
  }

  return job;
}

const apiMock = new AxiosMockAdapter(api, { delayResponse: 0 });
const axiosMock = new AxiosMockAdapter(axios, { delayResponse: 0 });

apiMock.onPost("/auth/login").reply((config) => {
  const body = parseJson(config.data);
  const identifier = String(body.identifier || "").toLowerCase();
  const password = String(body.password || "");

  const found = users.find(
    (u) =>
      (u.email.toLowerCase() === identifier ||
        u.username.toLowerCase() === identifier) &&
      (u.password ? u.password === password : true),
  );

  if (!found) {
    return [401, { detail: "Invalid credentials" }];
  }

  currentUserId = found.id;
  const token = makeToken(found.id);
  tokenUserId.set(token, found.id);

  return [
    200,
    {
      access_token: token,
      refresh_token: "demo-refresh",
      token_type: "bearer",
    },
  ];
});

apiMock.onPost("/auth/register").reply((config) => {
  const body = parseJson(config.data);
  const email = String(body.email || "")
    .trim()
    .toLowerCase();
  const username = String(body.username || "").trim();
  const password = String(body.password || "");

  if (!email || !username || !password) {
    return [400, { detail: "Missing registration fields" }];
  }

  if (users.some((u) => u.email.toLowerCase() === email)) {
    return [400, { detail: "Email already registered" }];
  }

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
      refresh_token: "demo-refresh",
      token_type: "bearer",
    },
  ];
});

apiMock.onPost("/auth/try").reply(() => {
  const guest: UserRecord = {
    id: nextUserId++,
    email: `guest${Date.now()}@ergolabs.ai`,
    username: `guest-${Date.now().toString().slice(-4)}`,
    created_at: nowIso(),
    updated_at: nowIso(),
  };

  users.push(guest);
  currentUserId = guest.id;

  const token = makeToken(guest.id);
  tokenUserId.set(token, guest.id);

  return [
    200,
    {
      access_token: token,
      refresh_token: "demo-refresh",
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
      refresh_token: "demo-refresh",
      token_type: "bearer",
    },
  ];
});

apiMock.onGet("/auth/me").reply((config) => {
  const user =
    userFromAuthHeader(config.headers?.Authorization as string | undefined) ||
    users.find((u) => u.id === currentUserId);

  if (!user) {
    return [401, { detail: "Not authenticated" }];
  }

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

apiMock.onGet("/documents").reply(() => [200, documents]);

apiMock.onPost("/documents").reply((config) => {
  const body = parseJson(config.data);
  const title =
    String(body.title || "Untitled Document").trim() || "Untitled Document";
  const workspaceId =
    body.workspace_id === null || body.workspace_id === undefined
      ? null
      : Number(body.workspace_id);

  const created: DocumentRecord = {
    id: nextDocumentId++,
    title,
    content: "",
    owner_id: currentUserId,
    workspace_id: Number.isNaN(workspaceId as number) ? null : workspaceId,
    created_at: nowIso(),
    updated_at: nowIso(),
  };

  documents.unshift(created);
  return [200, created];
});

apiMock.onGet(/\/documents\/\d+\/attachments$/).reply((config) => {
  const match = config.url?.match(/\/documents\/(\d+)\/attachments$/);
  const id = Number(match?.[1]);
  return [200, attachmentsByDocument.get(id) || []];
});

apiMock.onPost(/\/documents\/\d+\/attachments$/).reply((config) => {
  const match = config.url?.match(/\/documents\/(\d+)\/attachments$/);
  const id = Number(match?.[1]);

  const attachment: AttachmentRecord = {
    id: nextAttachmentId++,
    filename: `uploaded-file-${nextAttachmentId}.pdf`,
    object_key: `attachments/${id}/uploaded-file-${nextAttachmentId}.pdf`,
    content_type: "application/pdf",
    size: 150000,
    created_at: nowIso(),
  };

  const current = attachmentsByDocument.get(id) || [];
  attachmentsByDocument.set(id, [attachment, ...current]);

  return [200, attachment];
});

apiMock.onDelete(/\/documents\/\d+\/attachments\/\d+$/).reply((config) => {
  const match = config.url?.match(/\/documents\/(\d+)\/attachments\/(\d+)$/);
  const documentId = Number(match?.[1]);
  const attachmentId = Number(match?.[2]);

  const current = attachmentsByDocument.get(documentId) || [];
  attachmentsByDocument.set(
    documentId,
    current.filter((a) => a.id !== attachmentId),
  );

  return [200, { ok: true }];
});

apiMock.onPost(/\/documents\/\d+\/share$/).reply(() => [200, { ok: true }]);
apiMock
  .onDelete(/\/documents\/\d+\/share\/\d+$/)
  .reply(() => [200, { ok: true }]);

apiMock.onGet(/\/documents\/\d+$/).reply((config) => {
  const id = Number(config.url?.split("/").pop());
  const doc = documents.find((d) => d.id === id);
  if (!doc) {
    return [404, { detail: "Document not found" }];
  }
  return [200, doc];
});

apiMock.onPut(/\/documents\/\d+$/).reply((config) => {
  const id = Number(config.url?.split("/").pop());
  const body = parseJson(config.data);
  const doc = documents.find((d) => d.id === id);

  if (!doc) {
    return [404, { detail: "Document not found" }];
  }

  if (typeof body.title === "string") {
    doc.title = body.title;
  }
  if (typeof body.content === "string") {
    doc.content = body.content;
  }
  if (body.workspace_id === null || typeof body.workspace_id === "number") {
    doc.workspace_id = body.workspace_id as number | null;
  }
  doc.updated_at = nowIso();

  return [200, doc];
});

apiMock.onDelete(/\/documents\/\d+$/).reply((config) => {
  const id = Number(config.url?.split("/").pop());
  const index = documents.findIndex((d) => d.id === id);
  if (index >= 0) {
    documents.splice(index, 1);
  }
  return [200, { ok: true }];
});

apiMock.onGet("/workspaces").reply(() => [200, workspaces]);

apiMock.onPost("/workspaces").reply((config) => {
  const body = parseJson(config.data);
  const name =
    String(body.name || "Untitled Workspace").trim() || "Untitled Workspace";

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

apiMock.onGet(/\/workspaces\/\d+$/).reply((config) => {
  const id = Number(config.url?.split("/").pop());
  const ws = workspaces.find((w) => w.id === id);
  if (!ws) {
    return [404, { detail: "Workspace not found" }];
  }
  return [200, ws];
});

apiMock.onPut(/\/workspaces\/\d+$/).reply((config) => {
  const id = Number(config.url?.split("/").pop());
  const body = parseJson(config.data);
  const ws = workspaces.find((w) => w.id === id);
  if (!ws) {
    return [404, { detail: "Workspace not found" }];
  }

  if (typeof body.name === "string") {
    ws.name = body.name;
  }
  ws.updated_at = nowIso();

  return [200, ws];
});

apiMock.onDelete(/\/workspaces\/\d+$/).reply((config) => {
  const id = Number(config.url?.split("/").pop());
  const wsIndex = workspaces.findIndex((w) => w.id === id);

  if (wsIndex >= 0) {
    workspaces.splice(wsIndex, 1);
  }

  documents.forEach((d) => {
    if (d.workspace_id === id) {
      d.workspace_id = null;
      d.updated_at = nowIso();
    }
  });

  workspaceMembers.delete(id);
  return [200, { ok: true }];
});

apiMock.onGet(/\/workspaces\/\d+\/documents$/).reply((config) => {
  const match = config.url?.match(/\/workspaces\/(\d+)\/documents$/);
  const id = Number(match?.[1]);
  return [200, documents.filter((d) => d.workspace_id === id)];
});

apiMock.onPost(/\/workspaces\/\d+\/members$/).reply((config) => {
  const match = config.url?.match(/\/workspaces\/(\d+)\/members$/);
  const id = Number(match?.[1]);
  const body = parseJson(config.data);
  const userId = Number(body.user_id);
  const role = String(body.role || "viewer");

  const members = workspaceMembers.get(id) || [];
  if (!members.some((m) => m.user_id === userId)) {
    members.push({ user_id: userId, role });
    workspaceMembers.set(id, members);
  }

  return [200, { ok: true }];
});

apiMock.onDelete(/\/workspaces\/\d+\/members\/\d+$/).reply((config) => {
  const match = config.url?.match(/\/workspaces\/(\d+)\/members\/(\d+)$/);
  const wsId = Number(match?.[1]);
  const userId = Number(match?.[2]);

  const members = workspaceMembers.get(wsId) || [];
  workspaceMembers.set(
    wsId,
    members.filter((m) => m.user_id !== userId),
  );

  return [200, { ok: true }];
});

apiMock.onGet("/users/search").reply((config) => {
  const rawQuery = (config.params?.q || "").toString().toLowerCase().trim();
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

apiMock.onPost("/pipeline/validate").reply((config) => {
  const body = parseJson(config.data);
  const title = String(body.title || "Untitled Paper");

  const jobId = `demo-job-${nextJobId++}`;
  const paperId = `demo-paper-${nextJobId}`;

  const job: PipelineJobRecord = {
    job_id: jobId,
    paper_id: paperId,
    title,
    status: "running",
    current_step: 1,
    total_steps: STEP_NAMES.length,
    step_name: STEP_NAMES[0],
    started_at: Date.now(),
  };

  pipelineJobs.set(jobId, job);
  pipelineResults.set(jobId, buildValidationResult(title));

  return [200, { ...job }];
});

apiMock.onGet(/\/pipeline\/status\/.+$/).reply((config) => {
  const jobId = config.url?.split("/").pop() || "";
  const job = pipelineJobs.get(jobId);

  if (!job) {
    return [404, { detail: "Job not found" }];
  }

  return [200, { ...updateJobProgress(job) }];
});

apiMock.onGet(/\/pipeline\/results\/.+$/).reply((config) => {
  const jobId = config.url?.split("/").pop() || "";
  const result = pipelineResults.get(jobId);

  if (!result) {
    return [404, { detail: "Result not found" }];
  }

  return [200, result];
});

apiMock.onGet("/pipeline/jobs").reply(() => {
  const jobs = Array.from(pipelineJobs.values()).map((j) => ({
    ...updateJobProgress(j),
  }));
  return [200, jobs];
});

apiMock.onGet(/\/pipeline\/history\/.+$/).reply(() => [200, []]);

axiosMock.onPost("/api/auth/refresh").reply(() => {
  const token = makeToken(currentUserId);
  tokenUserId.set(token, currentUserId);
  return [
    200,
    {
      access_token: token,
      refresh_token: "demo-refresh",
      token_type: "bearer",
    },
  ];
});
