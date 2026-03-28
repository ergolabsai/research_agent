export type StepStatus = "pending" | "running" | "complete";

export interface AdvisorStep {
  id: string;
  label: string;
  summary: string;
  metric: string;
  deliverable: string;
  status: StepStatus;
  durationMs: number;
}

export interface EquationItem {
  id: string;
  equation: string;
  usage: string;
  context: string;
  editableHint: string;
}

export interface PlotDiscrepancy {
  id: string;
  title: string;
  detail: string;
  severity: "low" | "medium" | "high";
}

export interface CitationPaper {
  id: string;
  title: string;
  venue: string;
  year: number;
  relevancy: number;
  convergence: number;
  context: string;
  comparison: string;
}

export interface PipelineSnapshot {
  steps: AdvisorStep[];
  activeStepId: string | null;
  progressPercent: number;
  isRunning: boolean;
  isComplete: boolean;
  elapsedSeconds: number;
}
