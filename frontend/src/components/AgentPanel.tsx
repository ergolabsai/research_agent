import {
  Accordion,
  AccordionDetails,
  AccordionSummary,
  Box,
  Stack,
  Typography,
  Divider,
  IconButton,
  Modal,
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
  CheckCircle as ValidIcon,
  Cancel as InvalidIcon,
  Close as CloseIcon,
  ZoomOutMap as ZoomIcon,
  ExpandMore as ExpandMoreIcon,
} from "@mui/icons-material";
import { ReactNode, useEffect, useMemo, useRef, useState } from "react";
import { pipelineAPI } from "../api";
import {
  PipelineJob,
  ValidationResult,
  GraphAnalysis,
  NodeLinkGraph,
  normalizeGraph,
  AgentChatMessage,
} from "../types";
import { GraphContent } from "./GraphContent";
import { TabContentWithChat } from "./AgentChat";
import { AccountTree as GraphTabIcon } from "@mui/icons-material";
import { renderMathToHtml } from "../utils/katexRenderer";
import { useTheme as useAppTheme } from "../theme";
import { MarkdownRenderer } from "./MarkdownRenderer";
import { formatMathDetails } from "../utils/formatMathDetails";

export type AgentTab = "validate" | "math" | "citations" | "figures" | "graph";

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

interface EquationValidation {
  id?: string;
  equation_reference: string;
  calculation_valid: boolean;
  details: string;
  equation_text?: string;
  equation_latex?: string;
  formula_used?: string | null;
}

interface FigureValidation {
  id?: string;
  figure_name: string;
  supports_step?: number;
  actual_description?: string;
  expected_description?: string;
  similarities?: string[];
  differences?: string[];
  validity?: {
    confirmations?: string[];
    contradictions?: string[];
  };
}

interface FigureAsset {
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
}

interface FigureDragState {
  pointerId: number;
  startX: number;
  startY: number;
  originX: number;
  originY: number;
}

function extractFigureNumber(label: string): string | null {
  const match = /figure\s*(\d+)/i.exec(label);
  return match ? match[1] : null;
}

function findFigureAsset(
  figure: FigureValidation,
  assets: FigureAsset[],
): FigureAsset | null {
  // Try exact name match
  const exact = assets.find((a) => a.figure_name === figure.figure_name);
  if (exact) return exact;

  // Try matching by id (graph nodes use "figure:filename.jpg")
  if (figure.id) {
    const idName = figure.id.replace(/^figure:/, "");
    const byId = assets.find((a) => a.figure_name === idName);
    if (byId) return byId;
  }

  // Fall back to "Figure N" numeric extraction
  const figureNum = extractFigureNumber(figure.figure_name);
  if (!figureNum) return null;

  return (
    assets.find((a) => extractFigureNumber(a.figure_name) === figureNum) ?? null
  );
}

interface CitationPaperItem {
  paper_id: string;
  title: string;
  authors?: string;
  abstract?: string;
  source?: string;
  venue?: string;
  year?: number;
  context?: string;
  comparison?: string;
  relevancy?: number;
  relevancy_score?: number;
  convergence?: number;
  convergence_score?: number;
  relevancy_reasoning?: string;
  convergence_reasoning?: string;
}

interface CitationEvidenceItem {
  id: string;
  description: string;
  location?: string;
  supports_step?: number;
  excerpt?: string;
  relevancy_score?: number;
  relevancy_reasoning?: string;
  convergence_score?: number;
  convergence_reasoning?: string;
}

type CitationListItem =
  | { kind: "paper"; data: CitationPaperItem }
  | { kind: "citation"; data: CitationEvidenceItem };

const FALLBACK_EQUATIONS: EquationValidation[] = [
  {
    equation_reference: "Eq. (1)",
    equation_text: "C = w_1 r_1 + w_2 r_2 + w_3 r_3",
    equation_latex: "EQUATION LATEX HERE",
    calculation_valid: true,
    details:
      "Confidence aggregation is numerically stable under current weights.",
  },
  {
    equation_reference: "Eq. (2)",
    equation_text: "S = C - lambda sigma_r",
    equation_latex: "EQUATION LATEX HERE",
    calculation_valid: false,
    details:
      "Citation convergence term drifts when residual variance exceeds threshold.",
  },
  {
    equation_reference: "Eq. (3)",
    equation_text: "P = max(0, 1 - alpha |y - y_hat|)",
    equation_latex: "EQUATION LATEX HERE",
    calculation_valid: true,
    details: "Plot agreement penalty remains bounded with monotonic smoothing.",
  },
];

const FALLBACK_FIGURES: FigureValidation[] = [
  {
    figure_name: "Figure 1: Trend Alignment",
    validity: {
      confirmations: ["Primary growth phase matches manuscript narrative."],
      contradictions: ["Peak onset appears later than reported in text."],
    },
  },
  {
    figure_name: "Figure 2: Residual Error",
    validity: {
      confirmations: ["Error bars remain within claimed confidence range."],
      contradictions: [],
    },
  },
];

const FALLBACK_PAPERS: CitationPaperItem[] = [
  {
    paper_id: "fallback-1",
    title: "Structured Verification Graphs for Scientific Reasoning",
    authors: "R. Park, L. Nunez",
    venue: "NeurIPS",
    year: 2024,
    source: "arXiv",
    relevancy_score: 0.88,
    convergence_score: 0.63,
    relevancy_reasoning:
      "Matches the claim-graph decomposition strategy used in this manuscript.",
    convergence_reasoning:
      "Supports confidence weighting across interdependent claims.",
    abstract:
      "Introduces graph-grounded consistency checks for multi-step scientific arguments.",
  },
  {
    paper_id: "fallback-2",
    title: "When Citation Similarity Misleads Scientific Validation",
    authors: "A. Desai, K. Bloom",
    venue: "arXiv",
    year: 2023,
    source: "arXiv",
    relevancy_score: 0.71,
    convergence_score: -0.42,
    relevancy_reasoning:
      "Discusses citation overlap failure modes that are directly relevant here.",
    convergence_reasoning:
      "Challenges the assumption that lexical overlap implies epistemic agreement.",
    abstract:
      "Shows how citation-based retrieval can overstate support under topic drift.",
  },
];

function ZoomableFigureCard({
  title,
  subtitle,
  imageUrl,
  alt,
  placeholder,
}: {
  title: string;
  subtitle?: string;
  imageUrl?: string | null;
  alt: string;
  placeholder: ReactNode;
}) {
  const [isOpen, setIsOpen] = useState(false);
  const [scale, setScale] = useState(1);
  const [offset, setOffset] = useState({ x: 0, y: 0 });
  const dragRef = useRef<FigureDragState | null>(null);
  const suppressClickRef = useRef(false);

  const resetViewport = () => {
    setScale(1);
    setOffset({ x: 0, y: 0 });
    dragRef.current = null;
    suppressClickRef.current = false;
  };

  const openViewer = () => {
    resetViewport();
    setIsOpen(true);
  };

  const closeViewer = () => {
    setIsOpen(false);
    resetViewport();
  };

  const toggleZoom = () => {
    setScale((current) => {
      if (current > 1) {
        setOffset({ x: 0, y: 0 });
        return 1;
      }
      return 2.25;
    });
  };

  const handleViewerClick = () => {
    if (suppressClickRef.current) {
      suppressClickRef.current = false;
      return;
    }
    toggleZoom();
  };

  const handlePointerDown = (event: React.PointerEvent<HTMLDivElement>) => {
    if (scale <= 1) {
      return;
    }
    dragRef.current = {
      pointerId: event.pointerId,
      startX: event.clientX,
      startY: event.clientY,
      originX: offset.x,
      originY: offset.y,
    };
    event.currentTarget.setPointerCapture(event.pointerId);
  };

  const handlePointerMove = (event: React.PointerEvent<HTMLDivElement>) => {
    const dragState = dragRef.current;
    if (!dragState || dragState.pointerId !== event.pointerId) {
      return;
    }

    const nextX = dragState.originX + (event.clientX - dragState.startX);
    const nextY = dragState.originY + (event.clientY - dragState.startY);
    if (
      Math.abs(event.clientX - dragState.startX) > 3 ||
      Math.abs(event.clientY - dragState.startY) > 3
    ) {
      suppressClickRef.current = true;
    }
    setOffset({ x: nextX, y: nextY });
  };

  const handlePointerEnd = (event: React.PointerEvent<HTMLDivElement>) => {
    if (
      dragRef.current?.pointerId === event.pointerId &&
      event.currentTarget.hasPointerCapture(event.pointerId)
    ) {
      event.currentTarget.releasePointerCapture(event.pointerId);
    }
    dragRef.current = null;
  };

  const renderMedia = (isViewer: boolean) => {
    const mediaSx = {
      width: "100%",
      height: isViewer ? "100%" : 180,
      maxHeight: isViewer ? "none" : 180,
      objectFit: "contain" as const,
      display: "block",
      userSelect: "none" as const,
      WebkitUserDrag: "none" as const,
      transform: isViewer
        ? `translate(${offset.x}px, ${offset.y}px) scale(${scale})`
        : "none",
      transformOrigin: "center center",
      transition: dragRef.current ? "none" : "transform 160ms ease",
      pointerEvents: "none" as const,
    };

    if (imageUrl) {
      return <Box component="img" src={imageUrl} alt={alt} sx={mediaSx} />;
    }

    return (
      <Box
        sx={{
          width: "100%",
          height: isViewer ? "100%" : 180,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          transform: isViewer
            ? `translate(${offset.x}px, ${offset.y}px) scale(${scale})`
            : "none",
          transformOrigin: "center center",
          transition: dragRef.current ? "none" : "transform 160ms ease",
          pointerEvents: "none",
        }}
      >
        {placeholder}
      </Box>
    );
  };

  return (
    <>
      <Box
        sx={{
          flex: 1,
          p: 1,
          borderRadius: 1,
          border: 1,
          borderColor: "divider",
          bgcolor: "background.paper",
        }}
      >
        <Stack
          direction="row"
          justifyContent="space-between"
          alignItems="center"
          sx={{ mb: 0.5 }}
        >
          <Box>
            <Typography variant="caption" color="text.secondary">
              {title}
            </Typography>
            <Typography
              variant="caption"
              color="text.secondary"
              display="block"
            >
              {subtitle}
            </Typography>
          </Box>
          <Tooltip title="Click to zoom">
            <IconButton size="small" onClick={openViewer}>
              <ZoomIcon fontSize="small" />
            </IconButton>
          </Tooltip>
        </Stack>

        <Box
          onClick={openViewer}
          sx={{
            width: "100%",
            height: 180,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            bgcolor: "background.default",
            overflow: "hidden",
            borderRadius: 1,
            cursor: "zoom-in",
          }}
        >
          {renderMedia(false)}
        </Box>
      </Box>

      <Modal open={isOpen} onClose={closeViewer}>
        <Box
          onClick={closeViewer}
          sx={{
            position: "fixed",
            inset: 0,
            bgcolor: "rgba(11, 18, 32, 0.86)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            p: { xs: 2, sm: 4 },
            zIndex: 1400,
          }}
        >
          <Box
            onClick={(event) => event.stopPropagation()}
            sx={{
              width: "min(96vw, 1200px)",
              height: "min(90vh, 900px)",
              borderRadius: 2,
              overflow: "hidden",
              bgcolor: "background.paper",
              display: "flex",
              flexDirection: "column",
              boxShadow: 24,
            }}
          >
            <Stack
              direction="row"
              justifyContent="space-between"
              alignItems="center"
              sx={{ px: 2, py: 1.25, borderBottom: 1, borderColor: "divider" }}
            >
              <Box>
                <Typography variant="subtitle2" fontWeight={700}>
                  {title}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  Click to {scale > 1 ? "reset" : "zoom"}. Click-drag to pan
                  while zoomed.
                </Typography>
              </Box>
              <IconButton onClick={closeViewer}>
                <CloseIcon fontSize="small" />
              </IconButton>
            </Stack>

            <Box
              onClick={handleViewerClick}
              onPointerDown={handlePointerDown}
              onPointerMove={handlePointerMove}
              onPointerUp={handlePointerEnd}
              onPointerCancel={handlePointerEnd}
              sx={{
                flex: 1,
                minHeight: 0,
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                overflow: "hidden",
                bgcolor: "#0f1720",
                cursor:
                  scale > 1
                    ? dragRef.current
                      ? "grabbing"
                      : "grab"
                    : "zoom-in",
                touchAction: scale > 1 ? "none" : "auto",
              }}
            >
              {renderMedia(true)}
            </Box>
          </Box>
        </Box>
      </Modal>
    </>
  );
}

function ValidateContent({
  content,
  job,
  result,
  error,
  onRun,
  graphAnalysis,
  chatMessages,
}: {
  content: string;
  job: PipelineJob | null;
  result: ValidationResult | null;
  error: string | null;
  onRun: () => void;
  graphAnalysis: GraphAnalysis | null;
  chatMessages: AgentChatMessage[];
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
          color="secondary"
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
              "Starting..."}
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
      <TabContentWithChat
        chatProps={{
          allMessages: chatMessages,
          category: "validation",
          targetId: null,
          placeholder: "Ask the agent about the validation results...",
        }}
      >
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

        {/* Validation Results accordion */}
        <Accordion
          defaultExpanded
          disableGutters
          elevation={0}
          sx={{
            border: 1,
            borderColor: "divider",
            borderRadius: 1,
            "&:before": { display: "none" },
            mb: 1.5,
          }}
        >
          <AccordionSummary
            expandIcon={<ExpandMoreIcon />}
            sx={{
              minHeight: 40,
              "& .MuiAccordionSummary-content": { my: 0.5 },
            }}
          >
            <Typography variant="subtitle2" fontWeight={700}>
              Validation Results
            </Typography>
          </AccordionSummary>
          <AccordionDetails sx={{ pt: 0, px: 2, pb: 1.5 }}>
            {result.overall_assessment?.review ? (
              <MarkdownRenderer>
                {result.overall_assessment.review}
              </MarkdownRenderer>
            ) : (
              <Typography variant="body2" color="text.secondary">
                No review available.
              </Typography>
            )}
          </AccordionDetails>
        </Accordion>

        {/* Graph Analysis accordion */}
        <Accordion
          disableGutters
          elevation={0}
          sx={{
            border: 1,
            borderColor: "divider",
            borderRadius: 1,
            "&:before": { display: "none" },
            mb: 1.5,
          }}
        >
          <AccordionSummary
            expandIcon={<ExpandMoreIcon />}
            sx={{
              minHeight: 40,
              "& .MuiAccordionSummary-content": { my: 0.5 },
            }}
          >
            <Typography variant="subtitle2" fontWeight={700}>
              Graph Analysis
            </Typography>
          </AccordionSummary>
          <AccordionDetails sx={{ pt: 0, px: 2, pb: 1.5 }}>
            {graphAnalysis ? (
              <Box>
                {/* Node counts */}
                <Stack
                  direction="row"
                  flexWrap="wrap"
                  gap={0.75}
                  sx={{ mb: 1.5 }}
                >
                  <Chip
                    label={`${graphAnalysis.node_counts.steps} steps`}
                    size="small"
                    variant="outlined"
                  />
                  <Chip
                    label={`${graphAnalysis.node_counts.evidence} evidence`}
                    size="small"
                    variant="outlined"
                  />
                  <Chip
                    label={`${graphAnalysis.node_counts.figures} figures`}
                    size="small"
                    variant="outlined"
                  />
                  <Chip
                    label={`${graphAnalysis.node_counts.math} math`}
                    size="small"
                    variant="outlined"
                  />
                  <Chip
                    label={`${graphAnalysis.node_counts.related_papers} citations`}
                    size="small"
                    variant="outlined"
                  />
                </Stack>

                {/* Steps with no evaluations */}
                {graphAnalysis.steps_without_evaluation.length > 0 && (
                  <Box sx={{ mb: 1.5 }}>
                    <Typography
                      variant="caption"
                      fontWeight={700}
                      sx={{ mb: 0.5, display: "block" }}
                    >
                      Steps with no evaluations (
                      {graphAnalysis.steps_without_evaluation.length})
                    </Typography>
                    {graphAnalysis.steps_without_evaluation.map((s) => (
                      <Typography
                        key={s.step_number}
                        variant="body2"
                        color="text.secondary"
                        sx={{ mb: 0.25 }}
                      >
                        Step {s.step_number}: {s.description}
                      </Typography>
                    ))}
                  </Box>
                )}

                {/* Contradicted steps */}
                {graphAnalysis.contradicted_steps.length > 0 && (
                  <Box>
                    <Typography
                      variant="caption"
                      fontWeight={700}
                      sx={{ mb: 0.5, display: "block" }}
                    >
                      Contradicted steps (
                      {graphAnalysis.contradicted_steps.length})
                    </Typography>
                    {graphAnalysis.contradicted_steps.map((cs, idx) => (
                      <Accordion
                        key={`${cs.step_number}-${cs.figure}-${idx}`}
                        disableGutters
                        elevation={0}
                        sx={{
                          border: 1,
                          borderColor: "divider",
                          borderRadius: 1,
                          "&:before": { display: "none" },
                          mb: 0.5,
                        }}
                      >
                        <AccordionSummary
                          expandIcon={
                            <ExpandMoreIcon sx={{ fontSize: "1rem" }} />
                          }
                          sx={{
                            minHeight: 32,
                            py: 0,
                            "& .MuiAccordionSummary-content": { my: 0.25 },
                          }}
                        >
                          <Typography variant="caption" color="text.secondary">
                            Step {cs.step_number} ({cs.figure})
                          </Typography>
                        </AccordionSummary>
                        <AccordionDetails sx={{ pt: 0, px: 1.5, pb: 1 }}>
                          <Box component="ul" sx={{ pl: 2, m: 0 }}>
                            {cs.contradictions.map((c, ci) => (
                              <Typography
                                key={ci}
                                component="li"
                                variant="caption"
                                color="text.secondary"
                                sx={{ mb: 0.5, lineHeight: 1.5 }}
                              >
                                {c}
                              </Typography>
                            ))}
                          </Box>
                        </AccordionDetails>
                      </Accordion>
                    ))}
                  </Box>
                )}
              </Box>
            ) : (
              <Typography variant="body2" color="text.secondary">
                No graph analysis available.
              </Typography>
            )}
          </AccordionDetails>
        </Accordion>

        <Button
          variant="outlined"
          size="small"
          fullWidth
          sx={{ mt: 0.5 }}
          onClick={onRun}
          startIcon={<RunIcon />}
        >
          Run Again
        </Button>
      </TabContentWithChat>
    );
  }

  return null;
}

function ScaledKatex({ latex }: { latex: string }) {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;
    const rescale = () => {
      const katexEl = el.querySelector(".katex-display") as HTMLElement;
      if (!katexEl) return;
      katexEl.style.transform = "none";
      const ratio = el.clientWidth / katexEl.scrollWidth;
      if (ratio < 1) {
        katexEl.style.transformOrigin = "center center";
        katexEl.style.transform = `scale(${ratio * 0.9})`;
      }
    };
    rescale();
    const ro = new ResizeObserver(rescale);
    ro.observe(el);
    return () => ro.disconnect();
  }, [latex]);

  return (
    <Box
      ref={containerRef}
      sx={{
        overflow: "hidden",
        "& .katex-display": { margin: 0 },
        "& .katex": { fontSize: "1.35rem" },
      }}
      dangerouslySetInnerHTML={{
        __html: renderMathToHtml(latex, true),
      }}
    />
  );
}

function MathContent({
  result,
  graph,
  chatMessages,
}: {
  result: ValidationResult | null;
  graph: NodeLinkGraph | null;
  chatMessages: AgentChatMessage[];
}) {
  const theme = useTheme();
  const [selectedEq, setSelectedEq] = useState<string | null>(null);

  // Prefer graph math nodes; fall back to result step_validations
  const graphMath: EquationValidation[] = useMemo(() => {
    if (!graph) return [];
    return graph.nodes
      .filter((n) => n.node_type === "math")
      .map((n) => ({
        id: String(n.id),
        equation_reference: String(n.equation_reference ?? ""),
        calculation_valid: n.calculation_valid === true,
        details: String(n.details ?? ""),
        equation_latex:
          n.equation_latex != null ? String(n.equation_latex) : undefined,
        formula_used: n.formula_used != null ? String(n.formula_used) : null,
      }));
  }, [graph]);

  const resultMath: EquationValidation[] = useMemo(() => {
    if (!result) return [];
    return Object.values(result.step_validations).flatMap(
      (v) => v.math_validations ?? [],
    );
  }, [result]);

  const allMath = graphMath.length > 0 ? graphMath : resultMath;
  const displayedMath: EquationValidation[] =
    allMath.length > 0 ? allMath : FALLBACK_EQUATIONS;

  const selectedEquation = selectedEq
    ? (displayedMath.find(
        (m) => (m.id ?? m.equation_reference) === selectedEq,
      ) ?? null)
    : null;

  const eqKey = (eq: EquationValidation) => eq.id ?? eq.equation_reference;

  useEffect(() => {
    if (!displayedMath.length) {
      setSelectedEq(null);
      return;
    }
    if (!selectedEq || !displayedMath.some((m) => eqKey(m) === selectedEq)) {
      setSelectedEq(eqKey(displayedMath[0]));
    }
  }, [displayedMath, selectedEq]);

  const handleSelectEquation = (eq: EquationValidation) => {
    setSelectedEq(eqKey(eq));
  };

  return (
    <TabContentWithChat
      chatProps={{
        allMessages: chatMessages,
        category: "equations",
        targetId: selectedEq,
        placeholder: "Ask the agent about an equation...",
      }}
    >
      <Box sx={{ display: "flex", flexDirection: "column", height: "100%", minHeight: 0 }}>
        {/* Pinned: Hero + Details (do not scroll with list) */}
        <Box sx={{ flexShrink: 0 }}>
          <Stack spacing={2}>
            {/* Equation Hero Display */}
            {!!selectedEquation && (
              <Box
                sx={{
                  px: 2,
                  py: 1.5,
                  borderRadius: 1.5,
                  border: 1,
                  borderColor: "divider",
                  background: `linear-gradient(135deg, ${theme.palette.primary.main}10 0%, ${theme.palette.secondary.main}20 100%)`,
                  textAlign: "center",
                }}
              >
                <Typography
                  variant="caption"
                  sx={{
                    display: "block",
                    fontWeight: 700,
                    letterSpacing: "0.08em",
                    mb: 0.75,
                    color: "text.secondary",
                  }}
                >
                  {selectedEquation.equation_reference}
                </Typography>
                {selectedEquation.equation_latex ? (
                  <ScaledKatex latex={selectedEquation.equation_latex} />
                ) : (
                  <Typography
                    sx={{
                      fontFamily: "'IBM Plex Serif', serif",
                      fontSize: { xs: "1.15rem", sm: "1.35rem" },
                      lineHeight: 1.25,
                      color: "text.primary",
                    }}
                  >
                    {selectedEquation.equation_text ??
                      selectedEquation.equation_reference}
                  </Typography>
                )}
              </Box>
            )}

            {/* Detail Panel */}
            {!!selectedEquation && (
              <Box
                sx={{
                  p: 1.25,
                  borderRadius: 1,
                  border: 1,
                  borderColor: "divider",
                  bgcolor: "background.default",
                  maxHeight: 220,
                  overflow: "auto",
                }}
              >
                <Typography variant="subtitle2" fontWeight={700} sx={{ mb: 0.75 }}>
                  Selected Equation Details
                </Typography>
                <Stack
                  direction="row"
                  spacing={1}
                  alignItems="center"
                  sx={{ mb: 0.5 }}
                >
                  <Typography variant="body2" fontWeight={700}>
                    {selectedEquation.equation_reference}
                  </Typography>
                  <Chip
                    label={selectedEquation.calculation_valid ? "Valid" : "Invalid"}
                    size="small"
                    color={selectedEquation.calculation_valid ? "success" : "error"}
                  />
                </Stack>
                <Box sx={{ fontSize: "0.75rem", "& h3": { fontSize: "0.8rem", mt: 1.5, mb: 0.25 }, "& p": { fontSize: "0.75rem", mb: 0.5 }, "& li": { fontSize: "0.75rem" }, "& ul": { pl: 1.5 } }}>
                  <MarkdownRenderer>
                    {formatMathDetails(selectedEquation.details)}
                  </MarkdownRenderer>
                </Box>
                {selectedEquation.formula_used && (
                  <Typography
                    variant="caption"
                    color="text.secondary"
                    display="block"
                    sx={{ mt: 0.5 }}
                  >
                    <strong>Formula:</strong> {selectedEquation.formula_used}
                  </Typography>
                )}
              </Box>
            )}
          </Stack>
        </Box>

        {allMath.length === 0 && (
          <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
            No math validation data available yet. Showing demo equation
            placeholders.
          </Typography>
        )}

        {/* Equation List — scrolls independently */}
        <Box sx={{ flex: 1, minHeight: 0, overflow: "auto", mt: 2 }}>
          <Stack spacing={1}>
            {displayedMath.map((eq, idx) => (
              <Box
                key={`${eqKey(eq)}-${idx}`}
                onClick={() => handleSelectEquation(eq)}
                sx={{
                  p: 1.25,
                  borderRadius: 1,
                  border: 1,
                  borderColor:
                    selectedEq === eqKey(eq) ? "primary.main" : "divider",
                  cursor: "pointer",
                  bgcolor:
                    selectedEq === eqKey(eq) ? "action.selected" : "transparent",
                  "&:hover": { bgcolor: "action.hover" },
                }}
              >
                <Stack
                  direction="row"
                  justifyContent="space-between"
                  sx={{ mb: 0.5 }}
                >
                  <Typography variant="body2" fontWeight={700}>
                    {eq.equation_reference}
                  </Typography>
                  <Chip
                    label={eq.calculation_valid ? "Valid" : "Invalid"}
                    size="small"
                    color={eq.calculation_valid ? "success" : "error"}
                    icon={
                      eq.calculation_valid ? (
                        <ValidIcon fontSize="small" />
                      ) : (
                        <InvalidIcon fontSize="small" />
                      )
                    }
                  />
                </Stack>
                {eq.formula_used && (
                  <Typography
                    variant="caption"
                    color="text.secondary"
                    display="block"
                    noWrap
                  >
                    {eq.formula_used}
                  </Typography>
                )}
              </Box>
            ))}
          </Stack>
        </Box>
      </Box>
    </TabContentWithChat>
  );
}

function ScoreChip({
  label,
  value,
  mode,
}: {
  label: string;
  value: number | undefined | null;
  mode: "relevancy" | "convergence";
}) {
  const hasValue = value != null;
  if (!hasValue) {
    return (
      <Tooltip title="This score hasn't been calculated yet. It will appear once the pipeline finishes processing.">
        <Chip label={`${label} --`} size="small" variant="outlined" />
      </Tooltip>
    );
  }
  if (mode === "relevancy") {
    return (
      <Chip
        label={`${label} ${value.toFixed(2)}`}
        size="small"
        color="primary"
      />
    );
  }
  return (
    <Chip
      label={`${label} ${value >= 0 ? "+" : ""}${value.toFixed(2)}`}
      size="small"
      color={value >= 0 ? "success" : "error"}
    />
  );
}

function CitationsContent({
  result,
  graph,
  chatMessages,
}: {
  result: ValidationResult | null;
  graph: NodeLinkGraph | null;
  chatMessages: AgentChatMessage[];
}) {
  const [selectedId, setSelectedId] = useState<string | null>(null);

  // Build related papers from graph nodes (preferred) or fall back to result
  const relatedPapers: CitationPaperItem[] = useMemo(() => {
    if (graph) {
      return graph.nodes
        .filter((n) => n.node_type === "related_paper")
        .map((n) => ({
          paper_id: String(n.paper_id ?? n.id),
          title: String(n.title ?? ""),
          authors: n.authors != null ? String(n.authors) : undefined,
          abstract: n.abstract != null ? String(n.abstract) : undefined,
          source: n.source != null ? String(n.source) : undefined,
          relevancy_score:
            typeof n.relevancy_score === "number"
              ? n.relevancy_score
              : undefined,
          relevancy_reasoning:
            n.relevancy_reasoning != null
              ? String(n.relevancy_reasoning)
              : undefined,
          convergence_score:
            typeof n.convergence_score === "number"
              ? n.convergence_score
              : undefined,
          convergence_reasoning:
            n.convergence_reasoning != null
              ? String(n.convergence_reasoning)
              : undefined,
        }));
    }
    return result?.related_papers ?? [];
  }, [graph, result]);

  // Build citation evidence from graph nodes
  const citations: CitationEvidenceItem[] = useMemo(() => {
    if (!graph) return [];
    return graph.nodes
      .filter(
        (n) => n.node_type === "evidence" && n.evidence_type === "citation",
      )
      .map((n) => ({
        id: String(n.id),
        description: String(n.description ?? ""),
        location: n.location != null ? String(n.location) : undefined,
        supports_step:
          typeof n.supports_step === "number" ? n.supports_step : undefined,
        excerpt: n.excerpt != null ? String(n.excerpt) : undefined,
        relevancy_score:
          typeof n.relevancy_score === "number" ? n.relevancy_score : undefined,
        relevancy_reasoning:
          n.relevancy_reasoning != null
            ? String(n.relevancy_reasoning)
            : undefined,
        convergence_score:
          typeof n.convergence_score === "number"
            ? n.convergence_score
            : undefined,
        convergence_reasoning:
          n.convergence_reasoning != null
            ? String(n.convergence_reasoning)
            : undefined,
      }));
  }, [graph]);

  const hasData = relatedPapers.length > 0 || citations.length > 0;
  const displayedPapers =
    relatedPapers.length > 0 ? relatedPapers : FALLBACK_PAPERS;

  // Build a unified list for selection tracking
  const allItems: CitationListItem[] = useMemo(() => {
    const items: CitationListItem[] = displayedPapers.map((p) => ({
      kind: "paper" as const,
      data: p,
    }));
    for (const c of citations) {
      items.push({ kind: "citation" as const, data: c });
    }
    return items;
  }, [displayedPapers, citations]);

  const getItemId = (item: CitationListItem) =>
    item.kind === "paper" ? item.data.paper_id : item.data.id;

  useEffect(() => {
    if (!allItems.length) {
      setSelectedId(null);
      return;
    }
    if (!selectedId || !allItems.some((it) => getItemId(it) === selectedId)) {
      setSelectedId(getItemId(allItems[0]));
    }
  }, [allItems, selectedId]);

  const selectedItem = useMemo(
    () =>
      selectedId
        ? (allItems.find((it) => getItemId(it) === selectedId) ?? null)
        : null,
    [allItems, selectedId],
  );

  return (
    <TabContentWithChat
      chatProps={{
        allMessages: chatMessages,
        category: "citations",
        targetId: selectedId,
        placeholder: "Ask the agent about citation convergence...",
      }}
    >
      <Stack spacing={2}>
        {!hasData && (
          <Typography variant="body2" color="text.secondary">
            No related papers data available yet. Showing demo citation
            placeholders.
          </Typography>
        )}

        {/* Related Papers section */}
        <Box>
          <Typography
            variant="caption"
            fontWeight={700}
            color="text.secondary"
            sx={{ mb: 0.5, display: "block" }}
          >
            Related Papers ({displayedPapers.length})
          </Typography>
          <Stack spacing={1}>
            {displayedPapers.map((paper) => (
              <Box
                key={paper.paper_id}
                onClick={() => setSelectedId(paper.paper_id)}
                sx={{
                  p: 1.25,
                  borderRadius: 1,
                  border: 1,
                  borderColor:
                    selectedId === paper.paper_id ? "primary.main" : "divider",
                  cursor: "pointer",
                  bgcolor:
                    selectedId === paper.paper_id
                      ? "action.selected"
                      : "transparent",
                  "&:hover": { bgcolor: "action.hover" },
                }}
              >
                <Typography variant="body2" fontWeight={700}>
                  {paper.title}
                </Typography>
                <Typography
                  variant="caption"
                  color="text.secondary"
                  display="block"
                >
                  {[paper.authors, paper.source || paper.venue, paper.year]
                    .filter(Boolean)
                    .join(" | ")}
                </Typography>
                <Stack direction="row" spacing={0.5} sx={{ mt: 0.75 }}>
                  <ScoreChip
                    label="Rel"
                    value={paper.relevancy_score ?? paper.relevancy}
                    mode="relevancy"
                  />
                  <ScoreChip
                    label="Conv"
                    value={paper.convergence_score ?? paper.convergence}
                    mode="convergence"
                  />
                </Stack>
              </Box>
            ))}
          </Stack>
        </Box>

        {/* Citations section */}
        {citations.length > 0 && (
          <Box>
            <Typography
              variant="caption"
              fontWeight={700}
              color="text.secondary"
              sx={{ mb: 0.5, display: "block" }}
            >
              Citations ({citations.length})
            </Typography>
            <Stack spacing={1}>
              {citations.map((cit) => (
                <Box
                  key={cit.id}
                  onClick={() => setSelectedId(cit.id)}
                  sx={{
                    p: 1.25,
                    borderRadius: 1,
                    border: 1,
                    borderColor:
                      selectedId === cit.id ? "primary.main" : "divider",
                    cursor: "pointer",
                    bgcolor:
                      selectedId === cit.id ? "action.selected" : "transparent",
                    "&:hover": { bgcolor: "action.hover" },
                  }}
                >
                  <Typography variant="body2" fontWeight={700} noWrap>
                    {cit.description}
                  </Typography>
                  <Typography
                    variant="caption"
                    color="text.secondary"
                    display="block"
                  >
                    {[
                      cit.location,
                      cit.supports_step != null
                        ? `Step ${cit.supports_step}`
                        : null,
                    ]
                      .filter(Boolean)
                      .join(" | ")}
                  </Typography>
                  <Stack direction="row" spacing={0.5} sx={{ mt: 0.75 }}>
                    <ScoreChip
                      label="Rel"
                      value={cit.relevancy_score}
                      mode="relevancy"
                    />
                    <ScoreChip
                      label="Conv"
                      value={cit.convergence_score}
                      mode="convergence"
                    />
                  </Stack>
                </Box>
              ))}
            </Stack>
          </Box>
        )}

        {/* Detail panel */}
        {selectedItem?.kind === "paper" &&
          (() => {
            const paper = selectedItem.data;
            return (
              <Box
                sx={{
                  p: 1.25,
                  borderRadius: 1,
                  border: 1,
                  borderColor: "divider",
                  bgcolor: "background.default",
                }}
              >
                <Typography
                  variant="subtitle2"
                  fontWeight={700}
                  sx={{ mb: 0.5 }}
                >
                  Selected Paper Details
                </Typography>
                <Typography variant="body1" fontWeight={700} sx={{ mb: 0.25 }}>
                  {paper.title}
                </Typography>
                <Typography
                  variant="caption"
                  color="text.secondary"
                  display="block"
                >
                  {[paper.authors, paper.source || paper.venue, paper.year]
                    .filter(Boolean)
                    .join(" | ")}
                </Typography>
                {paper.abstract && (
                  <Typography
                    variant="body2"
                    color="text.secondary"
                    display="block"
                    sx={{ mt: 0.75 }}
                  >
                    {paper.abstract}
                  </Typography>
                )}
                <Stack direction="row" spacing={0.5} sx={{ mt: 1 }}>
                  <ScoreChip
                    label="Rel"
                    value={paper.relevancy_score ?? paper.relevancy}
                    mode="relevancy"
                  />
                  <ScoreChip
                    label="Conv"
                    value={paper.convergence_score ?? paper.convergence}
                    mode="convergence"
                  />
                </Stack>
                {paper.relevancy_reasoning && (
                  <Typography
                    variant="body2"
                    color="text.secondary"
                    display="block"
                    sx={{ mt: 0.75 }}
                  >
                    <strong>Relevancy:</strong> {paper.relevancy_reasoning}
                  </Typography>
                )}
                {paper.convergence_reasoning && (
                  <Typography
                    variant="body2"
                    color="text.secondary"
                    display="block"
                    sx={{ mt: 0.5 }}
                  >
                    <strong>Convergence:</strong> {paper.convergence_reasoning}
                  </Typography>
                )}
              </Box>
            );
          })()}

        {selectedItem?.kind === "citation" &&
          (() => {
            const cit = selectedItem.data;
            return (
              <Box
                sx={{
                  p: 1.25,
                  borderRadius: 1,
                  border: 1,
                  borderColor: "divider",
                  bgcolor: "background.default",
                }}
              >
                <Typography
                  variant="subtitle2"
                  fontWeight={700}
                  sx={{ mb: 0.5 }}
                >
                  Selected Citation Details
                </Typography>
                <Typography variant="body2" fontWeight={700} sx={{ mb: 0.25 }}>
                  {cit.description}
                </Typography>
                <Typography
                  variant="caption"
                  color="text.secondary"
                  display="block"
                >
                  {[
                    cit.location,
                    cit.supports_step != null
                      ? `Step ${cit.supports_step}`
                      : null,
                  ]
                    .filter(Boolean)
                    .join(" | ")}
                </Typography>
                {cit.excerpt && (
                  <Typography
                    variant="caption"
                    color="text.secondary"
                    display="block"
                    sx={{ mt: 0.75, fontStyle: "italic" }}
                  >
                    "{cit.excerpt}"
                  </Typography>
                )}
                <Stack direction="row" spacing={0.5} sx={{ mt: 1 }}>
                  <ScoreChip
                    label="Rel"
                    value={cit.relevancy_score}
                    mode="relevancy"
                  />
                  <ScoreChip
                    label="Conv"
                    value={cit.convergence_score}
                    mode="convergence"
                  />
                </Stack>
                {cit.relevancy_reasoning && (
                  <Typography
                    variant="caption"
                    color="text.secondary"
                    display="block"
                    sx={{ mt: 0.75 }}
                  >
                    <strong>Relevancy:</strong> {cit.relevancy_reasoning}
                  </Typography>
                )}
                {cit.convergence_reasoning && (
                  <Typography
                    variant="caption"
                    color="text.secondary"
                    display="block"
                    sx={{ mt: 0.5 }}
                  >
                    <strong>Convergence:</strong> {cit.convergence_reasoning}
                  </Typography>
                )}
              </Box>
            );
          })()}
      </Stack>
    </TabContentWithChat>
  );
}

function FiguresContent({
  result,
  jobId,
  graph,
  chatMessages,
}: {
  result: ValidationResult | null;
  jobId: string | null;
  graph: NodeLinkGraph | null;
  chatMessages: AgentChatMessage[];
}) {
  const theme = useTheme();
  const [selectedFigure, setSelectedFigure] = useState<string | null>(null);
  const [figureAssets, setFigureAssets] = useState<FigureAsset[]>([]);

  // Prefer graph figure nodes; fall back to result step_validations
  const graphFigures: FigureValidation[] = useMemo(() => {
    if (!graph) return [];
    return graph.nodes
      .filter((n) => n.node_type === "figure")
      .map((n) => ({
        id: String(n.id),
        figure_name: String(n.figure_name ?? ""),
        actual_description:
          n.actual_description != null
            ? String(n.actual_description)
            : undefined,
        expected_description:
          n.expected_description != null
            ? String(n.expected_description)
            : undefined,
        similarities: Array.isArray(n.similarities)
          ? (n.similarities as string[])
          : undefined,
        differences: Array.isArray(n.differences)
          ? (n.differences as string[])
          : undefined,
      }));
  }, [graph]);

  const resultFigures: FigureValidation[] = useMemo(() => {
    if (!result) return [];
    return Object.values(result.step_validations).flatMap(
      (v) => v.figure_validations ?? [],
    );
  }, [result]);

  const allFigures = graphFigures.length > 0 ? graphFigures : resultFigures;
  const displayedFigures: FigureValidation[] =
    allFigures.length > 0 ? allFigures : FALLBACK_FIGURES;

  const figKey = (fig: FigureValidation) => fig.id ?? fig.figure_name;

  useEffect(() => {
    if (!displayedFigures.length) {
      setSelectedFigure(null);
      return;
    }
    if (
      !selectedFigure ||
      !displayedFigures.some((f) => figKey(f) === selectedFigure)
    ) {
      setSelectedFigure(figKey(displayedFigures[0]));
    }
  }, [displayedFigures, selectedFigure]);

  const selectedFigureData = useMemo(
    () =>
      selectedFigure
        ? (displayedFigures.find((f) => figKey(f) === selectedFigure) ?? null)
        : null,
    [displayedFigures, selectedFigure],
  );

  useEffect(() => {
    if (!jobId) {
      setFigureAssets([]);
      return;
    }

    let cancelled = false;
    (async () => {
      try {
        const res = await pipelineAPI.figures(jobId);
        if (!cancelled) {
          setFigureAssets(res.data.figures ?? []);
        }
      } catch {
        if (!cancelled) {
          setFigureAssets([]);
        }
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [jobId]);

  const selectedFigureAsset = useMemo(
    () =>
      selectedFigureData
        ? findFigureAsset(selectedFigureData, figureAssets)
        : null,
    [selectedFigureData, figureAssets],
  );

  // Unified accessors: graph uses similarities/differences, result uses confirmations/contradictions
  const getMatches = (fig: FigureValidation) =>
    fig.similarities ?? fig.validity?.confirmations ?? [];
  const getMismatches = (fig: FigureValidation) =>
    fig.differences ?? fig.validity?.contradictions ?? [];

  const submittedPlaceholder = (
    <svg viewBox="0 0 180 72" style={{ width: "100%", height: "100%" }}>
      <polyline
        fill="none"
        stroke={theme.palette.primary.main}
        strokeWidth="2.5"
        strokeLinejoin="round"
        points="8,58 28,51 48,43 72,32 95,24 116,20 138,27 162,38 174,42"
      />
    </svg>
  );

  const predictedPlaceholder = (
    <svg viewBox="0 0 180 72" style={{ width: "100%", height: "100%" }}>
      <polyline
        fill="none"
        stroke={theme.palette.warning.main}
        strokeWidth="2.5"
        strokeLinejoin="round"
        points="8,60 28,55 48,48 72,41 95,35 116,33 138,35 162,39 174,40"
      />
    </svg>
  );

  return (
    <TabContentWithChat
      chatProps={{
        allMessages: chatMessages,
        category: "figures",
        targetId: selectedFigure,
        placeholder: "Ask the agent about figure discrepancies...",
      }}
    >
      <Stack spacing={2}>
        {allFigures.length === 0 && (
          <Typography variant="body2" color="text.secondary">
            No figure validation data available yet. Showing demo placeholder
            figures.
          </Typography>
        )}

        {/* Selected Figure Display */}
        {!!selectedFigureData && (
          <Box
            sx={{
              p: 1.25,
              borderRadius: 1,
              border: 1,
              borderColor: "divider",
              bgcolor: "background.default",
            }}
          >
            <Typography variant="subtitle2" fontWeight={700} sx={{ mb: 0.5 }}>
              Selected Figure
            </Typography>
            <Typography variant="body2" fontWeight={700} sx={{ mb: 1 }}>
              {selectedFigureData.figure_name}
            </Typography>
            <Box sx={{ mb: 1 }}>
              <Stack direction={{ xs: "column", md: "row" }} spacing={1}>
                <ZoomableFigureCard
                  title="Observed"
                  // subtitle={
                  //   selectedFigureAsset?.submitted?.filename ??
                  //   "Placeholder figure"
                  // }
                  imageUrl={selectedFigureAsset?.submitted?.url}
                  alt={`${selectedFigureData.figure_name} submitted`}
                  placeholder={submittedPlaceholder}
                />
                <ZoomableFigureCard
                  title="Predicted"
                  // subtitle={
                  //   selectedFigureAsset?.predicted?.filename ??
                  //   "Placeholder figure"
                  // }
                  imageUrl={selectedFigureAsset?.predicted?.url}
                  alt={`${selectedFigureData.figure_name} predicted`}
                  placeholder={predictedPlaceholder}
                />
              </Stack>
            </Box>
          </Box>
        )}

        {/* Figure Selection */}
        <Box
          sx={{
            p: 1.25,
            borderRadius: 1,
            border: 1,
            borderColor: "divider",
            bgcolor: "background.default",
          }}
        >
          <Typography variant="subtitle2" fontWeight={700} sx={{ mb: 1 }}>
            Figure Selection
          </Typography>
          <Stack
            spacing={1.25}
            sx={{ maxHeight: 220, overflow: "auto", pr: 0.5 }}
          >
            {displayedFigures.map((fig, i) => (
              <Box
                key={`${figKey(fig)}-${i}`}
                onClick={() => setSelectedFigure(figKey(fig))}
                sx={{
                  p: 1.25,
                  borderRadius: 1,
                  border: 1,
                  borderColor:
                    selectedFigure === figKey(fig) ? "primary.main" : "divider",
                  cursor: "pointer",
                  bgcolor:
                    selectedFigure === figKey(fig)
                      ? "action.selected"
                      : "transparent",
                  "&:hover": { bgcolor: "action.hover" },
                }}
              >
                <Typography variant="body2" fontWeight={700} sx={{ mb: 0.5 }}>
                  {fig.figure_name}
                </Typography>
                <Typography
                  variant="caption"
                  color="text.secondary"
                  display="block"
                >
                  Similarities: {getMatches(fig).length} | Differences:{" "}
                  {getMismatches(fig).length}
                </Typography>
              </Box>
            ))}
          </Stack>
        </Box>

        {/* Comparison Notes */}
        {!!selectedFigureData && (
          <Box
            sx={{
              p: 1.25,
              borderRadius: 1,
              border: 1,
              borderColor: "divider",
              bgcolor: "background.default",
            }}
          >
            <Typography variant="subtitle2" fontWeight={700} sx={{ mb: 0.75 }}>
              Comparison Notes
            </Typography>
            {getMatches(selectedFigureData).map((c, i) => (
              <Typography
                key={`s-${i}`}
                variant="caption"
                color="text.secondary"
                display="block"
              >
                + {c}
              </Typography>
            ))}
            {getMismatches(selectedFigureData).map((c, i) => (
              <Typography
                key={`d-${i}`}
                variant="caption"
                color="text.secondary"
                display="block"
              >
                - {c}
              </Typography>
            ))}
          </Box>
        )}
      </Stack>
    </TabContentWithChat>
  );
}

interface AgentPanelProps {
  content: string;
  title: string;
  documentId?: number;
  activeTab: AgentTab;
  onTabChange: (tab: AgentTab) => void;
  onCollapse?: () => void;
}

export const AgentPanel = ({
  content,
  title,
  documentId,
  activeTab,
  onTabChange,
  onCollapse,
}: AgentPanelProps) => {
  const theme = useTheme();
  const { layoutMode } = useAppTheme();
  const isVertical = layoutMode === "vertical";
  const [job, setJob] = useState<PipelineJob | null>(null);
  const [result, setResult] = useState<ValidationResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [graphData, setGraphData] = useState<NodeLinkGraph | null>(null);
  const [graphAnalysis, setGraphAnalysis] = useState<GraphAnalysis | null>(
    null,
  );
  const [chatMessages, setChatMessages] = useState<AgentChatMessage[]>([]);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    return () => {
      if (pollRef.current) {
        clearInterval(pollRef.current);
      }
    };
  }, []);

  const isTabUnlocked = (tab: AgentTab): boolean => {
    if (tab === "validate") {
      return true;
    }

    if (!job) {
      return false;
    }

    if (job.status === "completed") {
      return true;
    }

    if (tab === "figures") {
      return job.current_step >= 6;
    }

    if (tab === "math") {
      return job.current_step >= 7;
    }

    return job.current_step >= 8;
  };

  useEffect(() => {
    if (!isTabUnlocked(activeTab)) {
      onTabChange("validate");
    }
  }, [activeTab, job, result, onTabChange]);

  const handleRun = async () => {
    if (pollRef.current) {
      clearInterval(pollRef.current);
    }

    setError(null);
    setResult(null);
    setGraphData(null);
    setGraphAnalysis(null);
    setChatMessages([]);

    try {
      const response = await pipelineAPI.validate({
        paper_text: content,
        title,
        document_id: documentId,
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
              try {
                const graphRes = await pipelineAPI.graph(newJobId);
                setGraphData(normalizeGraph(graphRes.data));
              } catch {
                // Graph data is optional — don't block on failure
              }
              try {
                const analysisRes = await pipelineAPI.analysis(newJobId);
                setGraphAnalysis(analysisRes.data);
              } catch {
                // Graph analysis is optional
              }
              try {
                const messagesRes = await pipelineAPI.messages(newJobId);
                setChatMessages(messagesRes.data);
              } catch {
                // Chat messages are optional
              }
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

  const safeTab: AgentTab = isTabUnlocked(activeTab) ? activeTab : "validate";

  return (
    <Stack
      sx={{
        height: "100%",
        minWidth: 0,
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
      <Stack
        direction="row"
        sx={{
          justifyContent: isVertical ? "center" : "space-between",
          alignItems: "center",
          pl: isVertical ? 0 : 1.5,
          py: isVertical ? 1 : 0,
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
        {onCollapse && (
          <IconButton
            size="small"
            onClick={onCollapse}
            title="Close panel"
            sx={{ color: "text.primary", mr: 1 }}
          >
            <ChevronRightIcon color="primary" />
          </IconButton>
        )}
      </Stack>

      <Divider />

      <Tabs
        value={safeTab}
        onChange={(_, v) => onTabChange(v as AgentTab)}
        variant="fullWidth"
        sx={{
          flexShrink: 0,
          minHeight: 44,
          background: `linear-gradient(135deg, ${theme.palette.primary.main}10 0%, ${theme.palette.secondary.main}10 100%)`,
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
          label="Validation"
          icon={<ValidateIcon sx={{ fontSize: "0.85rem" }} />}
          iconPosition="start"
        />
        <Tab
          value="math"
          label="Equations"
          icon={<MathIcon sx={{ fontSize: "0.85rem" }} />}
          iconPosition="start"
          disabled={!isTabUnlocked("math")}
        />
        <Tab
          value="citations"
          label="Citations"
          icon={<LibrarianIcon sx={{ fontSize: "0.85rem" }} />}
          iconPosition="start"
          disabled={!isTabUnlocked("citations")}
        />
        <Tab
          value="figures"
          label="Figures"
          icon={<PlotsIcon sx={{ fontSize: "0.85rem" }} />}
          iconPosition="start"
          disabled={!isTabUnlocked("figures")}
        />
        <Tab
          value="graph"
          label="Graph"
          icon={<GraphTabIcon sx={{ fontSize: "0.85rem" }} />}
          iconPosition="start"
          disabled={!isTabUnlocked("graph")}
        />
      </Tabs>

      <Divider />

      <Box
        sx={{ flex: 1, minHeight: 0, minWidth: 0, overflow: "auto", p: 1.5 }}
      >
        {safeTab === "validate" && (
          <ValidateContent
            content={content}
            job={job}
            result={result}
            error={error}
            onRun={handleRun}
            graphAnalysis={graphAnalysis}
            chatMessages={chatMessages}
          />
        )}
        {safeTab === "math" && (
          <MathContent
            result={result}
            graph={graphData}
            chatMessages={chatMessages}
          />
        )}
        {safeTab === "citations" && (
          <CitationsContent
            result={result}
            graph={graphData}
            chatMessages={chatMessages}
          />
        )}
        {safeTab === "figures" && (
          <FiguresContent
            result={result}
            jobId={job?.job_id ?? null}
            graph={graphData}
            chatMessages={chatMessages}
          />
        )}
        {safeTab === "graph" && <GraphContent graph={graphData} job={job} />}
      </Box>
    </Stack>
  );
};
