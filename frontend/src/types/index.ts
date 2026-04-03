export * from "./contentJson";

export interface User {
  id: number;
  email: string;
  username: string;
  created_at: string;
  updated_at: string;
}

export interface Document {
  id: number;
  title: string;
  content: string;
  owner_id: number;
  workspace_id: number | null;
  created_at: string;
  updated_at: string;
}

export interface Attachment {
  id: number;
  filename: string;
  object_key: string;
  content_type: string;
  size: number;
  created_at: string;
  url?: string;
}

export interface Workspace {
  id: number;
  name: string;
  created_by: number;
  created_at: string;
  updated_at: string;
}

export interface WorkspaceMember {
  id: number;
  workspace_id: number;
  user_id: number;
  role: "owner" | "editor" | "viewer";
  joined_at: string;
}

export interface DocumentShare {
  id: number;
  document_id: number;
  shared_with_user_id: number;
  permission: "view" | "edit";
  shared_at: string;
}

export interface AuthTokens {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

// Pipeline types
export interface PipelineJob {
  job_id: string;
  paper_id: string;
  title: string;
  status: "pending" | "running" | "completed" | "failed";
  current_step: number;
  total_steps: number;
  step_name: string;
  error?: string;
}

export interface ValidateRequest {
  paper_text: string;
  title: string;
  paper_id?: string;
  authors?: string[];
  abstract?: string;
  document_id?: number;
  figures?: Record<
    string,
    | {
        object_key?: string;
        media_type?: string;
        filename?: string;
        url?: string;
        data?: string;
      }
    | {
        submitted?: {
          object_key?: string;
          media_type?: string;
          filename?: string;
          url?: string;
          data?: string;
        };
        predicted?: {
          object_key?: string;
          media_type?: string;
          filename?: string;
          url?: string;
          data?: string;
        };
      }
  >;
}

export interface StepValidation {
  evidence_count: number;
  figure_validations: Array<{
    figure_name: string;
    supports_step: number;
    validity: { confirmations: string[]; contradictions: string[] };
  }>;
  math_validations: Array<{
    equation_reference: string;
    calculation_valid: boolean;
    details: string;
  }>;
}

export interface RelatedPaper {
  paper_id: string;
  title: string;
  authors: string;
  abstract: string;
  source: string;
  relevancy_score: number;
  relevancy_reasoning: string;
  convergence_score: number;
  convergence_reasoning: string;
  /** Legacy demo fields */
  venue?: string;
  year?: number;
  context?: string;
  comparison?: string;
}

export interface ValidationResult {
  paper_id: string;
  confidence_score: number;
  overall_assessment: { review: string };
  paper_structure: {
    title: string;
    main_claim: string;
    logical_steps: Array<{
      step_number: number;
      description: string;
      section: string;
    }>;
  };
  step_validations: Record<string, StepValidation>;
  related_papers?: RelatedPaper[];
}

// Paper graph types (from NetworkX node_link_data format)
export type GraphNodeType =
  | "paper"
  | "step"
  | "evidence"
  | "figure"
  | "math"
  | "related_paper";

export type GraphEdgeType =
  | "HAS_STEP"
  | "DEPENDS_ON"
  | "SUPPORTS"
  | "ASSESSES"
  | "RELATED_TO";

export interface GraphNode {
  id: string;
  node_type: GraphNodeType;
  [key: string]: unknown;
}

export interface GraphLink {
  source: string;
  target: string;
  edge_type: GraphEdgeType;
  [key: string]: unknown;
}

/** Raw shape from NetworkX — may use "links" or "edges" depending on version. */
export interface NodeLinkGraphRaw {
  directed: boolean;
  multigraph: boolean;
  graph: Record<string, unknown>;
  nodes: GraphNode[];
  links?: GraphLink[];
  edges?: GraphLink[];
}

/** Normalized graph with `links` always populated. */
export interface NodeLinkGraph {
  directed: boolean;
  multigraph: boolean;
  graph: Record<string, unknown>;
  nodes: GraphNode[];
  links: GraphLink[];
}

/** Normalize a raw NetworkX node-link payload so `links` is always present. */
export function normalizeGraph(raw: NodeLinkGraphRaw): NodeLinkGraph {
  return {
    directed: raw.directed,
    multigraph: raw.multigraph,
    graph: raw.graph,
    nodes: raw.nodes,
    links: raw.links ?? raw.edges ?? [],
  };
}
