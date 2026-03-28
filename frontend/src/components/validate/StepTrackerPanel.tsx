import {
  Box,
  Typography,
  LinearProgress,
  Stack,
  Chip,
} from "@mui/material";
import {
  CheckCircle as CheckCircleIcon,
  RadioButtonChecked as ActiveIcon,
  RadioButtonUnchecked as PendingIcon,
} from "@mui/icons-material";
import { PipelineJob } from "../../types";

const PIPELINE_STEPS = [
  {
    id: "make_context",
    label: "Context",
    description: "Extracting domain context and manuscript metadata.",
    metric: "12 manuscript signals",
  },
  {
    id: "gather_papers",
    label: "Gather Papers",
    description: "Collecting related literature and abstracts.",
    metric: "18 papers retrieved",
  },
  {
    id: "map_logic",
    label: "Map Logic",
    description: "Building claim dependency map from arguments.",
    metric: "7 linked claims",
  },
  {
    id: "find_evidence",
    label: "Evidence",
    description: "Linking logical steps to textual evidence.",
    metric: "24 evidence spans",
  },
  {
    id: "evaluate_figures",
    label: "Figures",
    description: "Comparing visual trajectories and figures.",
    metric: "3 figures audited",
  },
  {
    id: "evaluate_math",
    label: "Math",
    description: "Validating equations and symbolic assumptions.",
    metric: "4 equations traced",
  },
  {
    id: "score_papers",
    label: "Citations",
    description: "Scoring related papers for relevancy and convergence.",
    metric: "4 papers surfaced",
  },
  {
    id: "compile_results",
    label: "Compile",
    description: "Synthesizing confidence score and final assessment.",
    metric: "Final recommendation",
  },
];

interface StepTrackerPanelProps {
  job: PipelineJob | null;
}

export function StepTrackerPanel({ job }: StepTrackerPanelProps) {
  if (!job) {
    return (
      <Box sx={{ p: 2 }}>
        <Typography variant="body2" color="text.secondary">
          Submit a paper to track pipeline progress here.
        </Typography>
      </Box>
    );
  }

  const isComplete = job.status === "completed";
  const isFailed = job.status === "failed";
  const progressPercent = isComplete
    ? 100
    : (job.current_step / job.total_steps) * 100;

  return (
    <Box sx={{ p: 2, display: "flex", flexDirection: "column", gap: 2 }}>
      <Stack direction="row" justifyContent="space-between" alignItems="center">
        <Typography variant="subtitle2" fontWeight={600}>
          Pipeline Progress
        </Typography>
        <Chip
          label={
            isComplete
              ? "Done"
              : isFailed
                ? "Failed"
                : `${Math.round(progressPercent)}%`
          }
          size="small"
          color={isComplete ? "success" : isFailed ? "error" : "primary"}
        />
      </Stack>

      <LinearProgress
        variant="determinate"
        value={progressPercent}
        sx={{ height: 6, borderRadius: 3 }}
        color={isComplete ? "success" : isFailed ? "error" : "primary"}
      />

      <Box>
        {PIPELINE_STEPS.map((step, index) => {
          const stepNum = index + 1;
          const isDone = isComplete || job.current_step > stepNum;
          const isCurrent =
            !isComplete && !isFailed && job.current_step === stepNum;

          return (
            <Box
              key={step.id}
              sx={{
                display: "flex",
                alignItems: "flex-start",
                gap: 1.5,
                py: 0.75,
                px: 1,
                borderRadius: 1,
                bgcolor: isCurrent ? "action.selected" : "transparent",
                transition: "background-color 0.3s",
              }}
            >
              {isDone ? (
                <CheckCircleIcon
                  color="success"
                  sx={{ mt: 0.25, fontSize: 18, flexShrink: 0 }}
                />
              ) : isCurrent ? (
                <ActiveIcon
                  color="primary"
                  sx={{ mt: 0.25, fontSize: 18, flexShrink: 0 }}
                />
              ) : (
                <PendingIcon
                  color="disabled"
                  sx={{ mt: 0.25, fontSize: 18, flexShrink: 0 }}
                />
              )}
              <Box sx={{ flex: 1, minWidth: 0 }}>
                <Stack
                  direction="row"
                  justifyContent="space-between"
                  alignItems="center"
                >
                  <Typography
                    variant="body2"
                    fontWeight={isCurrent ? 700 : 500}
                    color={
                      isDone
                        ? "text.secondary"
                        : isCurrent
                          ? "text.primary"
                          : "text.disabled"
                    }
                  >
                    {step.label}
                  </Typography>
                  {isDone && (
                    <Typography
                      variant="caption"
                      color="text.disabled"
                      sx={{ fontSize: "0.68rem" }}
                    >
                      {step.metric}
                    </Typography>
                  )}
                </Stack>
                {isCurrent && (
                  <Typography
                    variant="caption"
                    color="text.secondary"
                    display="block"
                    sx={{ mt: 0.25 }}
                  >
                    {step.description}
                  </Typography>
                )}
              </Box>
            </Box>
          );
        })}
      </Box>

      {isComplete && (
        <Box
          sx={{
            p: 1.5,
            borderRadius: 1,
            bgcolor: "success.main",
            color: "success.contrastText",
            opacity: 0.9,
          }}
        >
          <Typography variant="body2" fontWeight={600}>
            All stages complete
          </Typography>
          <Typography variant="caption">
            Results are ready for review.
          </Typography>
        </Box>
      )}
    </Box>
  );
}
