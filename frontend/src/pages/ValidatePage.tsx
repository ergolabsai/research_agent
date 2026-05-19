// SPDX-FileCopyrightText: 2026 Chelsea Liekhus-Schmaltz and Johnathon Barhydt
//
// SPDX-License-Identifier: AGPL-3.0-only

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
  useTheme,
} from "@mui/material";
import {
  ExpandMore as ExpandMoreIcon,
  CheckCircle as CheckIcon,
  Cancel as FailIcon,
  HelpOutline as UnknownIcon,
  PlayArrow as RunIcon,
} from "@mui/icons-material";
import { pipelineAPI } from "../api";
import { PipelineJob, ValidationResult } from "../types";

const STEP_LABELS = [
  "Reading paper",
  "Finding evidence",
  "Evaluating figures",
  "Validating math",
  "Checking citations",
  "Compiling results",
];

export const ValidatePage = () => {
  const theme = useTheme();
  const [title, setTitle] = useState("");
  const [paperText, setPaperText] = useState("");
  const [job, setJob] = useState<PipelineJob | null>(null);
  const [result, setResult] = useState<ValidationResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // Poll for job status
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
        // keep polling
      }
    }, 2000);

    return () => {
      if (pollRef.current) clearInterval(pollRef.current);
    };
  }, [job?.job_id, job?.status]);

  const handleSubmit = async () => {
    if (!paperText.trim()) return;
    setSubmitting(true);
    setError(null);
    setResult(null);

    try {
      const { data } = await pipelineAPI.validate({
        paper_text: paperText,
        title: title || "Untitled Paper",
      });
      setJob(data);
    } catch (err: any) {
      setError(err?.response?.data?.detail || "Failed to submit");
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

      {/* Input Section */}
      {!result && (
        <Paper sx={{ p: 3, display: "flex", flexDirection: "column", gap: 2 }}>
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

      {/* Progress Section */}
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
                  color={isDone ? "success" : isCurrent ? "primary" : "default"}
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

      {/* Results Section */}
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

          {/* Overall Review */}
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Overall Assessment
            </Typography>
            <Typography variant="body1" sx={{ whiteSpace: "pre-wrap" }}>
              {result.overall_assessment.review}
            </Typography>
          </Paper>

          {/* Step-by-step breakdown */}
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
                    <Typography sx={{ flex: 1 }}>{step.description}</Typography>
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

          {/* Run Again */}
          <Button
            variant="outlined"
            onClick={() => {
              setResult(null);
              setJob(null);
            }}
          >
            Validate Another Paper
          </Button>
        </Box>
      )}
    </Box>
  );
};
