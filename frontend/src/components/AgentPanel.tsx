import {
  Box,
  Stack,
  Typography,
  Divider,
  IconButton,
  useTheme,
  Tab,
  Tabs,
  Button,
  LinearProgress,
  Chip,
  Tooltip,
} from "@mui/material";
import {
  ChevronRight as ChevronRightIcon,
  Functions as MathIcon,
  LocalLibrary as LibrarianIcon,
  Insights as PlotsIcon,
  PlayArrow as RunIcon,
  CheckCircleOutline as CheckIcon,
  ErrorOutline as ErrorIcon,
  Science as ValidateIcon,
} from "@mui/icons-material";
import { useState, useEffect, useRef } from "react";
import { pipelineAPI } from "../api";
import { PipelineJob, ValidationResult } from "../types";

export type AgentTab = "validate" | "math" | "citations" | "figures";

const PIPELINE_STEPS = [
  { id: "make_context", label: "Context" },
  { id: "gather_papers", label: "Gather Papers" },
  { id: "map_logic", label: "Map Logic" },
  { id: "find_evidence", label: "Evidence" },
  { id: "evaluate_figures", label: "Figures" },
  { id: "evaluate_math", label: "Math" },
  { id: "score_papers", label: "Citations" },
  { id: "compile_results", label: "Compile" },
];

// ── Validate Tab Content ─────────────────────────────────────────────────────

function ValidateContent({
  content,
  job,
  result,
  error,
  onRun,
}: {
  content: string;
  job: PipelineJob | null;
  result: ValidationResult | null;
  error: string | null;
  onRun: () => void;
}) {
  const theme = useTheme();
  const isRunning = job?.status === "running" || job?.status === "pending";
  const isComplete = job?.status === "completed";
  const isFailed = job?.status === "failed";
  const progress = job
    ? Math.round((job.current_step / job.total_steps) * 100)
    : 0;

  if (!job && !error) {
    return (
      <Box>
        <Typography
          variant="body2"
          color="text.secondary"
          sx={{ mb: 2, lineHeight: 1.6 }}
        >
          Run the full validation pipeline on this document. The Advisor will
          extract context, gather related papers, map logical structure, find
          evidence, evaluate figures and math, and compile a confidence score.
        </Typography>
        <Button
          variant="contained"
          fullWidth
          startIcon={<RunIcon />}
          onClick={onRun}
          disabled={!content.trim()}
          size="small"
        >
          Run Validation
        </Button>
        {!content.trim() && (
          <Typography
            variant="caption"
            color="text.secondary"
            sx={{ mt: 1, display: "block" }}
          >
            Add content to the document first.
          </Typography>
        )}
      </Box>
    );
  }

  if (error) {
    return (
      <Box>
        <Stack direction="row" alignItems="center" gap={1} sx={{ mb: 1.5 }}>
          <ErrorIcon fontSize="small" color="error" />
          <Typography variant="body2" color="error">
            {error}
          </Typography>
        </Stack>
        <Button variant="outlined" size="small" fullWidth onClick={onRun}>
          Retry
        </Button>
      </Box>
    );
  }

  if (isRunning) {
    return (
      <Box>
        <Stack
          direction="row"
          justifyContent="space-between"
          alignItems="center"
          sx={{ mb: 1 }}
        >
          <Typography variant="caption" color="text.secondary" fontWeight={600}>
            {PIPELINE_STEPS.find((s) => s.id === job?.step_name)?.label ??
              "Starting…"}
          </Typography>
          <Chip
            label={`${progress}%`}
            size="small"
            color="primary"
            variant="outlined"
          />
        </Stack>
        <LinearProgress
          variant="determinate"
          value={progress}
          sx={{ borderRadius: 999, mb: 2, height: 6 }}
        />
        <Stack spacing={0.5}>
          {PIPELINE_STEPS.map((step, idx) => {
            const stepNum = idx + 1;
            const isDone = stepNum < (job?.current_step ?? 0);
            const isActive = job?.step_name === step.id;
            return (
              <Box
                key={step.id}
                sx={{
                  display: "flex",
                  alignItems: "center",
                  gap: 1,
                  px: 1,
                  py: 0.75,
                  borderRadius: 1.5,
                  bgcolor: isActive
                    ? `${theme.palette.primary.main}18`
                    : "transparent",
                }}
              >
                {isDone ? (
                  <CheckIcon
                    sx={{
                      fontSize: "0.85rem",
                      color: "success.main",
                      flexShrink: 0,
                    }}
                  />
                ) : isActive ? (
                  <Box
                    component="span"
                    sx={{
                      width: 8,
                      height: 8,
                      borderRadius: "50%",
                      bgcolor: "primary.main",
                      flexShrink: 0,
                      "@keyframes blink": {
                        "0%, 100%": { opacity: 1 },
                        "50%": { opacity: 0.25 },
                      },
                      animation: "blink 1.4s ease-in-out infinite",
                    }}
                  />
                ) : (
                  <Box
                    sx={{
                      width: 8,
                      height: 8,
                      borderRadius: "50%",
                      bgcolor: "action.disabled",
                      flexShrink: 0,
                    }}
                  />
                )}
                <Typography
                  variant="caption"
                  color={
                    isActive
                      ? "primary"
                      : isDone
                        ? "text.primary"
                        : "text.disabled"
                  }
                  fontWeight={isActive ? 700 : 400}
                >
                  {step.label}
                </Typography>
              </Box>
            );
          })}
        </Stack>
      </Box>
    );
  }

  if (isFailed) {
    return (
      <Box>
        <Stack direction="row" alignItems="center" gap={1} sx={{ mb: 1.5 }}>
          <ErrorIcon fontSize="small" color="error" />
          <Typography variant="body2" color="error">
            {job?.error ?? "Validation failed"}
          </Typography>
        </Stack>
        <Button variant="outlined" size="small" fullWidth onClick={onRun}>
          Run Again
        </Button>
      </Box>
    );
  }

  if (isComplete && result) {
    const score = result.confidence_score;
    const scoreColor =
      score >= 0.7 ? "success" : score >= 0.4 ? "warning" : "error";
    return (
      <Box>
        <Stack
          direction="row"
          alignItems="center"
          gap={1}
          sx={{ mb: 1.5, flexWrap: "wrap" }}
        >
          <CheckIcon sx={{ color: "success.main" }} />
          <Typography variant="subtitle2" fontWeight={700}>
            Complete
          </Typography>
          <Chip
            label={`${Math.round(score * 100)}% confidence`}
            size="small"
            color={scoreColor as "success" | "warning" | "error"}
          />
        </Stack>
        <Typography
          variant="body2"
          color="text.secondary"
          sx={{ mb: 2, lineHeight: 1.6 }}
        >
          {result.overall_assessment?.review}
        </Typography>
        {(result.paper_structure?.logical_steps?.length ?? 0) > 0 && (
          <Box>
            <Typography
              variant="caption"
              color="text.secondary"
              fontWeight={700}
              sx={{ textTransform: "uppercase", letterSpacing: "0.08em" }}
            >
              Logical Steps ({result.paper_structure.logical_steps.length})
            </Typography>
            <Stack spacing={0.5} sx={{ mt: 0.75 }}>
              {result.paper_structure.logical_steps.map((step) => (
                <Box
                  key={step.step_number}
                  sx={{
                    display: "flex",
                    gap: 1,
                    alignItems: "flex-start",
                    px: 1,
                    py: 0.5,
                    borderRadius: 1.5,
                    bgcolor: "background.default",
                    border: "1px solid",
                    borderColor: "divider",
                  }}
                >
                  <Typography
                    variant="caption"
                    color="primary"
                    fontWeight={700}
                    sx={{ flexShrink: 0 }}
                  >
                    {step.step_number}.
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    {step.description}
                  </Typography>
                </Box>
              ))}
            </Stack>
          </Box>
        )}
        <Button
          variant="outlined"
          size="small"
          fullWidth
          sx={{ mt: 2 }}
          onClick={onRun}
          startIcon={<RunIcon />}
        >
          Run Again
        </Button>
      </Box>
    );
  }

  return null;
}

// ── Math Tab Content ──────────────────────────────────────────────────────────

function MathContent({ result }: { result: ValidationResult }) {
  const allMath = Object.values(result.step_validations ?? {}).flatMap(
    (sv) => sv.math_validations ?? [],
  );
  if (allMath.length === 0) {
    return (
      <Typography variant="body2" color="text.secondary">
        No equations were validated in this run.
      </Typography>
    );
  }
  return (
    <Stack spacing={1}>
      {allMath.map((eq, i) => (
        <Box
          key={i}
          sx={{
            p: 1.5,
            border: "1px solid",
            borderColor: eq.calculation_valid ? "success.light" : "error.light",
            borderRadius: 2,
            bgcolor: "background.default",
          }}
        >
          <Stack
            direction="row"
            justifyContent="space-between"
            alignItems="flex-start"
            gap={0.5}
            sx={{ mb: 0.5 }}
          >
            <Typography
              variant="caption"
              fontWeight={700}
              sx={{ fontFamily: "monospace", wordBreak: "break-all" }}
            >
              {eq.equation_reference}
            </Typography>
            <Chip
              label={eq.calculation_valid ? "Valid" : "Invalid"}
              size="small"
              color={eq.calculation_valid ? "success" : "error"}
              variant="outlined"
              sx={{ flexShrink: 0 }}
            />
          </Stack>
          <Typography variant="caption" color="text.secondary">
            {eq.details}
          </Typography>
        </Box>
      ))}
    </Stack>
  );
}

// ── Citations Tab Content ─────────────────────────────────────────────────────

function CitationsContent({ result }: { result: ValidationResult }) {
  const papers = result.related_papers ?? [];
  if (papers.length === 0) {
    return (
      <Typography variant="body2" color="text.secondary">
        No related papers were found.
      </Typography>
    );
  }
  return (
    <Stack spacing={1}>
      {papers.map((paper, i) => (
        <Box
          key={i}
          sx={{
            p: 1.5,
            border: "1px solid",
            borderColor: "divider",
            borderRadius: 2,
            bgcolor: "background.default",
          }}
        >
          <Typography
            variant="caption"
            fontWeight={700}
            sx={{ display: "block", mb: 0.25 }}
          >
            {paper.title}
          </Typography>
          <Typography
            variant="caption"
            color="text.secondary"
            sx={{ display: "block", mb: 0.75 }}
          >
            {paper.authors} · {paper.source}
          </Typography>
          <Stack direction="row" spacing={0.5} flexWrap="wrap" useFlexGap>
            <Chip
              label={`Relevancy ${Math.round(paper.relevancy_score * 100)}%`}
              size="small"
              color="primary"
              variant="outlined"
              sx={{ fontSize: "0.7rem", height: 20 }}
            />
            <Chip
              label={`Convergence ${paper.convergence_score >= 0 ? "+" : ""}${Math.round(paper.convergence_score * 100)}%`}
              size="small"
              color={paper.convergence_score >= 0 ? "success" : "error"}
              variant="outlined"
              sx={{ fontSize: "0.7rem", height: 20 }}
            />
          </Stack>
        </Box>
      ))}
    </Stack>
  );
}

// ── Figures Tab Content ───────────────────────────────────────────────────────

function FiguresContent({ result }: { result: ValidationResult }) {
  const allFigures = Object.values(result.step_validations ?? {}).flatMap(
    (sv) => sv.figure_validations ?? [],
  );
  if (allFigures.length === 0) {
    return (
      <Typography variant="body2" color="text.secondary">
        No figures were evaluated in this run.
      </Typography>
    );
  }
  return (
    <Stack spacing={1}>
      {allFigures.map((fig, i) => {
        const confirmations = fig.validity?.confirmations?.length ?? 0;
        const contradictions = fig.validity?.contradictions?.length ?? 0;
        const supports = fig.supports_step > 0;
        return (
          <Box
            key={i}
            sx={{
              p: 1.5,
              border: "1px solid",
              borderColor: "divider",
              borderRadius: 2,
              bgcolor: "background.default",
            }}
          >
            <Stack
              direction="row"
              justifyContent="space-between"
              alignItems="center"
              sx={{ mb: 0.75 }}
            >
              <Typography variant="caption" fontWeight={700}>
                {fig.figure_name}
              </Typography>
              <Chip
                label={supports ? "Supports" : "Contradicts"}
                size="small"
                color={supports ? "success" : "error"}
                variant="outlined"
                sx={{ fontSize: "0.7rem", height: 20, flexShrink: 0, ml: 0.5 }}
              />
            </Stack>
            <Stack direction="row" spacing={0.5} flexWrap="wrap" useFlexGap>
              {confirmations > 0 && (
                <Chip
                  label={`${confirmations} confirmation${confirmations !== 1 ? "s" : ""}`}
                  size="small"
                  color="success"
                  sx={{ fontSize: "0.7rem", height: 20 }}
                />
              )}
              {contradictions > 0 && (
                <Chip
                  label={`${contradictions} contradiction${contradictions !== 1 ? "s" : ""}`}
                  size="small"
                  color="error"
                  sx={{ fontSize: "0.7rem", height: 20 }}
                />
              )}
            </Stack>
          </Box>
        );
      })}
    </Stack>
  );
}

// ── Main AgentPanel Component ────────────────────────────────────────────────

interface AgentPanelProps {
  content: string;
  title: string;
  activeTab: AgentTab;
  onTabChange: (tab: AgentTab) => void;
  onCollapse: () => void;
}

export const AgentPanel = ({
  content,
  title,
  activeTab,
  onTabChange,
  onCollapse,
}: AgentPanelProps) => {
  const theme = useTheme();
  const [job, setJob] = useState<PipelineJob | null>(null);
  const [result, setResult] = useState<ValidationResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // If requested tab requires results and none are available, fall back to validate
  useEffect(() => {
    if (activeTab !== "validate" && !result) {
      onTabChange("validate");
    }
  }, [activeTab, result, onTabChange]);

  useEffect(() => {
    return () => {
      if (pollRef.current) clearInterval(pollRef.current);
    };
  }, []);

  const handleRun = async () => {
    if (pollRef.current) clearInterval(pollRef.current);
    setError(null);
    setResult(null);
    try {
      const response = await pipelineAPI.validate({
        paper_text: content,
        title,
      });
      setJob(response.data);
      const newJobId = response.data.job_id;
      pollRef.current = setInterval(async () => {
        try {
          const statusRes = await pipelineAPI.status(newJobId);
          setJob(statusRes.data);
          if (
            statusRes.data.status === "completed" ||
            statusRes.data.status === "failed"
          ) {
            clearInterval(pollRef.current!);
            if (statusRes.data.status === "completed") {
              const resultsRes = await pipelineAPI.results(newJobId);
              setResult(resultsRes.data);
            }
          }
        } catch {
          clearInterval(pollRef.current!);
          setError("Failed to fetch validation status");
        }
      }, 100);
    } catch {
      setError("Failed to start validation");
    }
  };

  // Show validate tab if the targeted tab is still locked
  const safeTab: AgentTab =
    !result && activeTab !== "validate" ? "validate" : activeTab;

  return (
    <Stack
      sx={{
        height: "100%",
        display: "flex",
        flexDirection: "column",
        borderWidth: 1,
        borderColor: "divider",
        borderStyle: "solid",
        borderRadius: "20px",
        mt: 1,
        mb: 2,
        backgroundColor: theme.palette.background.paper,
        overflow: "hidden",
      }}
    >
      {/* Header — mirrors left Sidebar */}
      <Stack
        direction="row"
        sx={{
          justifyContent: "space-between",
          alignItems: "center",
          pl: 1.5,
          flexShrink: 0,
        }}
      >
        <Typography
          variant="h3"
          color="primary"
          sx={{ fontSize: "1.3rem", fontWeight: 700 }}
        >
          Agents
        </Typography>
        <Tooltip title="Close panel">
          <IconButton
            size="small"
            onClick={onCollapse}
            sx={{ color: "text.primary", mr: 1 }}
          >
            <ChevronRightIcon color="primary" />
          </IconButton>
        </Tooltip>
      </Stack>

      <Divider />

      {/* Tabs */}
      <Tabs
        value={safeTab}
        onChange={(_, v) => onTabChange(v as AgentTab)}
        variant="fullWidth"
        sx={{
          flexShrink: 0,
          minHeight: 44,
          "& .MuiTab-root": {
            minHeight: 44,
            py: 0,
            px: 0.5,
            fontSize: "0.72rem",
          },
        }}
      >
        <Tab
          value="validate"
          label="Validate"
          icon={<ValidateIcon sx={{ fontSize: "0.85rem" }} />}
          iconPosition="start"
        />
        <Tab
          value="math"
          label="Math"
          icon={<MathIcon sx={{ fontSize: "0.85rem" }} />}
          iconPosition="start"
          disabled={!result}
        />
        <Tab
          value="citations"
          label="Citations"
          icon={<LibrarianIcon sx={{ fontSize: "0.85rem" }} />}
          iconPosition="start"
          disabled={!result}
        />
        <Tab
          value="figures"
          label="Figures"
          icon={<PlotsIcon sx={{ fontSize: "0.85rem" }} />}
          iconPosition="start"
          disabled={!result}
        />
      </Tabs>

      <Divider />

      {/* Tab Content */}
      <Box sx={{ flex: 1, overflow: "auto", p: 1.5 }}>
        {safeTab === "validate" && (
          <ValidateContent
            content={content}
            job={job}
            result={result}
            error={error}
            onRun={handleRun}
          />
        )}
        {safeTab === "math" && result && <MathContent result={result} />}
        {safeTab === "citations" && result && (
          <CitationsContent result={result} />
        )}
        {safeTab === "figures" && result && <FiguresContent result={result} />}
      </Box>
    </Stack>
  );
};
