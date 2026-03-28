import { useState, useEffect, useRef } from "react";
import {
  Box,
  TextField,
  Button,
  Typography,
  Paper,
  LinearProgress,
  Chip,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Stack,
  Alert,
  IconButton,
  Tooltip,
  Divider,
} from "@mui/material";
import {
  ExpandMore as ExpandMoreIcon,
  CheckCircle as CheckIcon,
  Cancel as FailIcon,
  PlayArrow as RunIcon,
  Timeline as TimelineIcon,
  BarChart as BarChartIcon,
  Functions as FunctionsIcon,
  Article as ArticleIcon,
  Close as CloseIcon,
} from "@mui/icons-material";
import Drawer from "@mui/material/Drawer";
import { pipelineAPI } from "../api";
import { PipelineJob, ValidationResult } from "../types";
import { StepTrackerPanel } from "../components/validate/StepTrackerPanel";
import { PlotHelperPanel } from "../components/validate/PlotHelperPanel";
import { MathAssistantPanel } from "../components/validate/MathAssistantPanel";
import { CitationsReviewPanel } from "../components/validate/CitationsReviewPanel";
import { RightToolbarPortal } from "./MainPage";

type PanelTab = "steps" | "plot" | "math" | "citations";

const PANEL_CONFIG: Array<{
  tab: PanelTab;
  label: string;
  icon: React.ReactNode;
  unlockStep: number | null;
  tooltip: string;
}> = [
  {
    tab: "steps",
    label: "Steps",
    icon: <TimelineIcon fontSize="small" />,
    unlockStep: null,
    tooltip: "Pipeline step tracker",
  },
  {
    tab: "plot",
    label: "Plot",
    icon: <BarChartIcon fontSize="small" />,
    unlockStep: 6,
    tooltip: "Figure evaluation results",
  },
  {
    tab: "math",
    label: "Math",
    icon: <FunctionsIcon fontSize="small" />,
    unlockStep: 7,
    tooltip: "Math validation & equation chat",
  },
  {
    tab: "citations",
    label: "Citations",
    icon: <ArticleIcon fontSize="small" />,
    unlockStep: 8,
    tooltip: "Related papers & citation scores",
  },
];

const PANEL_TITLES: Record<PanelTab, string> = {
  steps: "Pipeline Steps",
  plot: "Plot Helper",
  math: "Math Assistant",
  citations: "Citation Review",
};

const PANEL_WIDTH = 380;

const STEP_LABELS = [
  "Reading paper",
  "Gathering papers",
  "Mapping logic",
  "Finding evidence",
  "Evaluating figures",
  "Validating math",
  "Scoring citations",
  "Compiling results",
];

export const ValidatePage = () => {
  const [title, setTitle] = useState("");
  const [paperText, setPaperText] = useState("");
  const [job, setJob] = useState<PipelineJob | null>(null);
  const [result, setResult] = useState<ValidationResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [activePanel, setActivePanel] = useState<PanelTab | null>(null);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const isPanelUnlocked = (tab: PanelTab): boolean => {
    if (!job) return false;
    const config = PANEL_CONFIG.find((p) => p.tab === tab)!;
    if (config.unlockStep === null) return true;
    return job.status === "completed" || job.current_step >= config.unlockStep;
  };

  const handlePanelToggle = (tab: PanelTab) => {
    setActivePanel((prev) => (prev === tab ? null : tab));
  };

  useEffect(() => {
    if (!job || job.status === "completed" || job.status === "failed") {
      if (pollRef.current) clearInterval(pollRef.current);
      return;
    }
    pollRef.current = setInterval(async () => {
      try {
        const { data } = await pipelineAPI.status(job.job_id);
        setJob(data);
        if (data.status === "completed") {
          const res = await pipelineAPI.results(job.job_id);
          setResult(res.data);
        } else if (data.status === "failed") {
          setError(data.error || "Pipeline failed");
        }
      } catch {
        /* keep polling */
      }
    }, 100);
    return () => {
      if (pollRef.current) clearInterval(pollRef.current);
    };
  }, [job?.job_id, job?.status]);

  const handleSubmit = async () => {
    if (!paperText.trim()) return;
    setSubmitting(true);
    setError(null);
    setResult(null);
    setActivePanel("steps");
    try {
      const { data } = await pipelineAPI.validate({
        paper_text: paperText,
        title: title || "Untitled Paper",
      });
      setJob(data);
    } catch (err: any) {
      setError(err?.response?.data?.detail || "Failed to submit");
      setActivePanel(null);
    } finally {
      setSubmitting(false);
    }
  };

  const isRunning = job?.status === "running" || job?.status === "pending";
  const confidenceColor =
    result && result.confidence_score >= 0.7
      ? "success"
      : result && result.confidence_score >= 0.4
        ? "warning"
        : "error";

  return (
    <>
      {/* ── Panel icon buttons injected into AppBar via portal ── */}
      {job && (
        <RightToolbarPortal>
          {PANEL_CONFIG.map(({ tab, icon, tooltip, unlockStep }) => {
            const unlocked = isPanelUnlocked(tab);
            const isActive = activePanel === tab;
            const lockedLabel =
              unlockStep === 6
                ? "Unlocks after figure evaluation"
                : unlockStep === 7
                  ? "Unlocks after math validation"
                  : unlockStep === 8
                    ? "Unlocks after citation scoring"
                    : tooltip;
            return (
              <Tooltip key={tab} title={unlocked ? tooltip : lockedLabel}>
                <span>
                  <IconButton
                    size="small"
                    disabled={!unlocked}
                    onClick={() => handlePanelToggle(tab)}
                    sx={{
                      color: isActive ? "primary.main" : "text.primary",
                      bgcolor: isActive ? "action.selected" : "transparent",
                      borderRadius: 1,
                    }}
                  >
                    {icon}
                  </IconButton>
                </span>
              </Tooltip>
            );
          })}
        </RightToolbarPortal>
      )}

      {/* ── Main content ── */}
      <Box
        sx={{
          maxWidth: 900,
          mx: "auto",
          display: "flex",
          flexDirection: "column",
          gap: 3,
        }}
      >
        <Typography variant="h5" fontWeight={700}>
          Validate a Paper
        </Typography>

        {/* Input */}
        {!result && (
          <Paper
            sx={{ p: 3, display: "flex", flexDirection: "column", gap: 2 }}
          >
            <TextField
              label="Paper Title"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              fullWidth
              disabled={isRunning}
            />
            <TextField
              label="Paste paper text"
              value={paperText}
              onChange={(e) => setPaperText(e.target.value)}
              fullWidth
              multiline
              minRows={12}
              maxRows={30}
              disabled={isRunning}
              placeholder="Paste the full text of the paper here..."
            />
            <Button
              variant="contained"
              size="large"
              startIcon={<RunIcon />}
              onClick={handleSubmit}
              disabled={submitting || isRunning || !paperText.trim()}
            >
              {submitting ? "Submitting..." : "Run Validation"}
            </Button>
          </Paper>
        )}

        {/* Progress */}
        {job && !result && !error && (
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Validation in Progress
            </Typography>
            <LinearProgress
              variant="determinate"
              value={(job.current_step / job.total_steps) * 100}
              sx={{ height: 8, borderRadius: 4, mb: 2 }}
            />
            <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap>
              {STEP_LABELS.map((label, i) => {
                const stepNum = i + 1;
                const isDone = job.current_step > stepNum;
                const isCurrent = job.current_step === stepNum;
                return (
                  <Chip
                    key={label}
                    label={label}
                    color={
                      isDone ? "success" : isCurrent ? "primary" : "default"
                    }
                    variant={isCurrent ? "filled" : "outlined"}
                    size="small"
                  />
                );
              })}
            </Stack>
          </Paper>
        )}

        {error && (
          <Alert severity="error" onClose={() => setError(null)}>
            {error}
          </Alert>
        )}

        {/* Results */}
        {result && (
          <Box sx={{ display: "flex", flexDirection: "column", gap: 2 }}>
            <Paper sx={{ p: 3 }}>
              <Stack
                direction="row"
                justifyContent="space-between"
                alignItems="center"
              >
                <Typography variant="h6">
                  {result.paper_structure.title}
                </Typography>
                <Chip
                  label={`${(result.confidence_score * 100).toFixed(0)}% confidence`}
                  color={confidenceColor as any}
                  size="medium"
                  sx={{ fontWeight: 700, fontSize: "1rem" }}
                />
              </Stack>
              <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                Main claim: {result.paper_structure.main_claim}
              </Typography>
            </Paper>

            <Paper sx={{ p: 3 }}>
              <Typography variant="h6" gutterBottom>
                Overall Assessment
              </Typography>
              <Typography variant="body1" sx={{ whiteSpace: "pre-wrap" }}>
                {result.overall_assessment.review}
              </Typography>
            </Paper>

            <Typography variant="h6">Step-by-Step Analysis</Typography>
            {result.paper_structure.logical_steps.map((step) => {
              const validation =
                result.step_validations[String(step.step_number)];
              return (
                <Accordion key={step.step_number}>
                  <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                    <Stack
                      direction="row"
                      spacing={1}
                      alignItems="center"
                      sx={{ width: "100%" }}
                    >
                      <Typography fontWeight={600}>
                        Step {step.step_number}:
                      </Typography>
                      <Typography sx={{ flex: 1 }}>
                        {step.description}
                      </Typography>
                      {validation && (
                        <Chip
                          label={`${validation.evidence_count} evidence`}
                          size="small"
                          variant="outlined"
                        />
                      )}
                    </Stack>
                  </AccordionSummary>
                  <AccordionDetails>
                    {validation ? (
                      <Stack spacing={1}>
                        {validation.math_validations.map((m, i) => (
                          <Stack
                            key={i}
                            direction="row"
                            spacing={1}
                            alignItems="center"
                          >
                            {m.calculation_valid ? (
                              <CheckIcon color="success" fontSize="small" />
                            ) : (
                              <FailIcon color="error" fontSize="small" />
                            )}
                            <Typography variant="body2">
                              {m.equation_reference}: {m.details}
                            </Typography>
                          </Stack>
                        ))}
                        {validation.figure_validations.map((f, i) => (
                          <Stack
                            key={i}
                            direction="row"
                            spacing={1}
                            alignItems="center"
                          >
                            <Typography variant="body2">
                              {f.figure_name}: {f.validity.confirmations.length}{" "}
                              confirmations, {f.validity.contradictions.length}{" "}
                              contradictions
                            </Typography>
                          </Stack>
                        ))}
                        {!validation.math_validations.length &&
                          !validation.figure_validations.length && (
                            <Typography variant="body2" color="text.secondary">
                              No detailed validations for this step.
                            </Typography>
                          )}
                      </Stack>
                    ) : (
                      <Typography variant="body2" color="text.secondary">
                        No validation data for this step.
                      </Typography>
                    )}
                  </AccordionDetails>
                </Accordion>
              );
            })}

            <Button
              variant="outlined"
              onClick={() => {
                setResult(null);
                setJob(null);
                setActivePanel(null);
              }}
            >
              Validate Another Paper
            </Button>
          </Box>
        )}
      </Box>

      {/* ── Right panel Drawer (slides in from right) ── */}
      <Drawer
        anchor="right"
        open={Boolean(activePanel)}
        onClose={() => setActivePanel(null)}
        variant="temporary"
        sx={{
          "& .MuiDrawer-paper": {
            width: PANEL_WIDTH,
            bgcolor: "background.default",
            borderLeft: 1,
            borderColor: "divider",
            display: "flex",
            flexDirection: "column",
          },
        }}
      >
        {/* Header */}
        <Box
          sx={{
            px: 2,
            py: 1.5,
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            borderBottom: 1,
            borderColor: "divider",
            minHeight: 56,
            flexShrink: 0,
          }}
        >
          <Typography variant="subtitle1" fontWeight={700}>
            {activePanel ? PANEL_TITLES[activePanel] : ""}
          </Typography>
          <IconButton
            size="small"
            onClick={() => setActivePanel(null)}
            aria-label="Close panel"
          >
            <CloseIcon fontSize="small" />
          </IconButton>
        </Box>

        <Divider />

        {/* Tab icon strip — switch panels without closing */}
        <Box
          sx={{
            display: "flex",
            px: 1,
            pt: 0.5,
            borderBottom: 1,
            borderColor: "divider",
          }}
        >
          {PANEL_CONFIG.map(({ tab, icon, tooltip }) => {
            const unlocked = isPanelUnlocked(tab);
            return (
              <Tooltip key={tab} title={tooltip}>
                <span>
                  <IconButton
                    size="small"
                    disabled={!unlocked}
                    onClick={() => setActivePanel(tab)}
                    sx={{
                      mb: 0.5,
                      borderRadius: 1,
                      color:
                        activePanel === tab ? "primary.main" : "text.secondary",
                      bgcolor:
                        activePanel === tab ? "action.selected" : "transparent",
                    }}
                  >
                    {icon}
                  </IconButton>
                </span>
              </Tooltip>
            );
          })}
        </Box>

        {/* Scrollable content */}
        <Box sx={{ flex: 1, overflow: "auto" }}>
          {activePanel === "steps" && <StepTrackerPanel job={job} />}
          {activePanel === "plot" && <PlotHelperPanel result={result} />}
          {activePanel === "math" && <MathAssistantPanel result={result} />}
          {activePanel === "citations" && (
            <CitationsReviewPanel result={result} />
          )}
        </Box>
      </Drawer>
    </>
  );
};
