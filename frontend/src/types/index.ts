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
  citation_validations: Array<{
    citation: string;
    accessible: boolean;
    supports_claim: boolean | null;
    notes: string;
  }>;
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
}
