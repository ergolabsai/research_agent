import {
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
  TextField,
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
  Send as SendIcon,
  CheckCircle as ValidIcon,
  Cancel as InvalidIcon,
  Close as CloseIcon,
  ZoomInMap as ZoomIcon,
} from "@mui/icons-material";
import {
  FormEvent,
  ReactNode,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import { pipelineAPI } from "../api";
import { PipelineJob, ValidationResult, NodeLinkGraph } from "../types";
import { GraphContent } from "./GraphContent";
import { AccountTree as GraphTabIcon } from "@mui/icons-material";

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

interface ChatMessage {
  role: "agent" | "user";
  text: string;
}

interface EquationValidation {
  equation_reference: string;
  calculation_valid: boolean;
  details: string;
  equation_text?: string;
  formula_used?: string;
}

interface FigureValidation {
  figure_name: string;
  supports_step?: number;
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
  const exact = assets.find((a) => a.figure_name === figure.figure_name);
  if (exact) {
    return exact;
  }

  const figureNum = extractFigureNumber(figure.figure_name);
  if (!figureNum) {
    return null;
  }

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

const FALLBACK_EQUATIONS: EquationValidation[] = [
  {
    equation_reference: "Eq. (1)",
    equation_text: "C = w_1 r_1 + w_2 r_2 + w_3 r_3",
    calculation_valid: true,
    details:
      "Confidence aggregation is numerically stable under current weights.",
  },
  {
    equation_reference: "Eq. (2)",
    equation_text: "S = C - lambda sigma_r",
    calculation_valid: false,
    details:
      "Citation convergence term drifts when residual variance exceeds threshold.",
  },
  {
    equation_reference: "Eq. (3)",
    equation_text: "P = max(0, 1 - alpha |y - y_hat|)",
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
  subtitle: string;
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
        <Button
          variant="outlined"
          size="small"
          fullWidth
          sx={{ mt: 1 }}
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

function MathContent({ result }: { result: ValidationResult | null }) {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      role: "agent",
      text: "I've traced the equations in this paper. Select one to inspect details and add context.",
    },
  ]);
  const [draft, setDraft] = useState("");
  const [selectedEq, setSelectedEq] = useState<string | null>(null);
  const [equationNotes, setEquationNotes] = useState<Record<string, string>>(
    {},
  );
  const chatListRef = useRef<HTMLDivElement>(null);

  const allMath = result
    ? Object.values(result.step_validations).flatMap(
        (v) => v.math_validations ?? [],
      )
    : [];
  const displayedMath: EquationValidation[] =
    allMath.length > 0 ? allMath : FALLBACK_EQUATIONS;

  const selectedEquation = selectedEq
    ? (displayedMath.find((m) => m.equation_reference === selectedEq) ?? null)
    : null;

  useEffect(() => {
    if (!displayedMath.length) {
      setSelectedEq(null);
      return;
    }
    if (
      !selectedEq ||
      !displayedMath.some((m) => m.equation_reference === selectedEq)
    ) {
      setSelectedEq(displayedMath[0].equation_reference);
    }
  }, [displayedMath, selectedEq]);

  useEffect(() => {
    const container = chatListRef.current;
    if (!container) {
      return;
    }
    container.scrollTo({ top: container.scrollHeight, behavior: "smooth" });
  }, [messages]);

  const handleSelectEquation = (ref: string) => {
    setSelectedEq(ref);
    const eq = displayedMath.find((m) => m.equation_reference === ref);
    if (!eq) {
      return;
    }
    setMessages((prev) => [
      ...prev,
      {
        role: "agent",
        text: `Selected ${ref}: ${eq.calculation_valid ? "validation passed" : "validation failed"}. ${eq.details}`,
      },
    ]);
  };

  const handleSend = (e: FormEvent) => {
    e.preventDefault();
    if (!draft.trim()) {
      return;
    }
    const userMessage = draft.trim();
    const currentNote = selectedEq ? equationNotes[selectedEq]?.trim() : "";
    setMessages((prev) => [
      ...prev,
      { role: "user", text: userMessage },
      {
        role: "agent",
        text: `Noted. For ${selectedEq ?? "the selected equation"}, the context has been recorded${currentNote ? ` (${currentNote})` : ""}. Re-run the pipeline with updated assumptions to recompute confidence.`,
      },
    ]);
    setDraft("");
  };

  return (
    <Box
      sx={{ display: "flex", flexDirection: "column", gap: 2, height: "100%" }}
    >
      {!!selectedEquation && (
        <Box
          sx={{
            px: 2,
            py: 1.5,
            borderRadius: 1.5,
            border: 1,
            borderColor: "divider",
            background:
              "linear-gradient(180deg, rgba(33,150,243,0.08), rgba(76,175,80,0.08))",
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
        </Box>
      )}

      {allMath.length === 0 && (
        <Typography variant="body2" color="text.secondary">
          No math validation data available yet. Showing demo equation
          placeholders.
        </Typography>
      )}

      <Stack spacing={1}>
        {displayedMath.map((eq, idx) => (
          <Box
            key={`${eq.equation_reference}-${idx}`}
            onClick={() => handleSelectEquation(eq.equation_reference)}
            sx={{
              p: 1.25,
              borderRadius: 1,
              border: 1,
              borderColor:
                selectedEq === eq.equation_reference
                  ? "primary.main"
                  : "divider",
              cursor: "pointer",
              bgcolor:
                selectedEq === eq.equation_reference
                  ? "action.selected"
                  : "transparent",
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
            <Typography variant="caption" color="text.secondary">
              {eq.details}
            </Typography>
            {eq.formula_used && (
              <Typography
                variant="caption"
                color="text.secondary"
                display="block"
              >
                Formula: {eq.formula_used}
              </Typography>
            )}
          </Box>
        ))}
      </Stack>

      {!!selectedEquation && (
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
          <Typography variant="caption" color="text.secondary" display="block">
            {selectedEquation.details}
          </Typography>
          <TextField
            sx={{ mt: 1 }}
            size="small"
            fullWidth
            multiline
            minRows={3}
            value={selectedEq ? (equationNotes[selectedEq] ?? "") : ""}
            onChange={(e) => {
              if (!selectedEq) {
                return;
              }
              setEquationNotes((prev) => ({
                ...prev,
                [selectedEq]: e.target.value,
              }));
            }}
            placeholder="Add context to guide the math agent..."
          />
        </Box>
      )}

      <Box sx={{ mt: "auto" }}>
        <Divider sx={{ mb: 1.5 }} />

        <Typography variant="subtitle2" fontWeight={700} sx={{ mb: 1 }}>
          Agent Chat
        </Typography>
        <Box
          ref={chatListRef}
          sx={{
            display: "flex",
            flexDirection: "column",
            gap: 0.75,
            maxHeight: 190,
            overflow: "auto",
            pr: 0.5,
          }}
        >
          {messages.map((m, i) => (
            <Box
              key={`${m.role}-${i}`}
              sx={{
                alignSelf: m.role === "user" ? "flex-end" : "flex-start",
                maxWidth: "88%",
                p: 1,
                borderRadius: 2,
                bgcolor: m.role === "user" ? "primary.main" : "action.selected",
                color:
                  m.role === "user" ? "primary.contrastText" : "text.primary",
              }}
            >
              <Typography variant="caption" fontWeight={700} display="block">
                {m.role === "agent" ? "Agent" : "You"}
              </Typography>
              <Typography variant="body2">{m.text}</Typography>
            </Box>
          ))}
        </Box>
        <Box
          component="form"
          onSubmit={handleSend}
          sx={{ display: "flex", gap: 1, mt: 1 }}
        >
          <TextField
            size="small"
            fullWidth
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
            placeholder="Ask the agent about an equation..."
          />
          <IconButton
            type="submit"
            size="small"
            color="primary"
            disabled={!draft.trim()}
          >
            <SendIcon />
          </IconButton>
        </Box>
      </Box>
    </Box>
  );
}

function CitationsContent({ result }: { result: ValidationResult | null }) {
  const [selectedPaperId, setSelectedPaperId] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      role: "agent",
      text: "Citation scoring is ready. Select a paper and ask for convergence interpretation.",
    },
  ]);
  const [draft, setDraft] = useState("");
  const chatListRef = useRef<HTMLDivElement>(null);

  const papers: CitationPaperItem[] = result?.related_papers ?? [];
  const displayedPapers = papers.length > 0 ? papers : FALLBACK_PAPERS;

  useEffect(() => {
    if (!displayedPapers.length) {
      setSelectedPaperId(null);
      return;
    }
    if (
      !selectedPaperId ||
      !displayedPapers.some((p) => p.paper_id === selectedPaperId)
    ) {
      setSelectedPaperId(displayedPapers[0].paper_id);
    }
  }, [displayedPapers, selectedPaperId]);

  useEffect(() => {
    const container = chatListRef.current;
    if (!container) {
      return;
    }
    container.scrollTo({ top: container.scrollHeight, behavior: "smooth" });
  }, [messages]);

  const selectedPaper = useMemo(
    () =>
      selectedPaperId
        ? (displayedPapers.find((p) => p.paper_id === selectedPaperId) ?? null)
        : null,
    [displayedPapers, selectedPaperId],
  );

  const handleSend = (e: FormEvent) => {
    e.preventDefault();
    if (!draft.trim()) {
      return;
    }

    const userMessage = draft.trim();
    const relevancy =
      selectedPaper?.relevancy_score ?? selectedPaper?.relevancy ?? 0;
    const convergence =
      selectedPaper?.convergence_score ?? selectedPaper?.convergence ?? 0;

    setMessages((prev) => [
      ...prev,
      { role: "user", text: userMessage },
      {
        role: "agent",
        text: `For ${selectedPaper?.title ?? "the selected paper"}, relevancy is ${relevancy.toFixed(2)} and convergence is ${convergence.toFixed(2)}. ${convergence >= 0 ? "This supports your manuscript direction." : "This introduces tension with your manuscript direction."}`,
      },
    ]);
    setDraft("");
  };

  return (
    <Box
      sx={{ display: "flex", flexDirection: "column", gap: 2, height: "100%" }}
    >
      {papers.length === 0 && (
        <Typography variant="body2" color="text.secondary">
          No related papers data available yet. Showing demo citation
          placeholders.
        </Typography>
      )}

      <Stack spacing={1.25}>
        {displayedPapers.map((paper) => {
          const relevancy = paper.relevancy_score ?? paper.relevancy ?? 0;
          const convergence = paper.convergence_score ?? paper.convergence ?? 0;
          return (
            <Box
              key={paper.paper_id}
              onClick={() => setSelectedPaperId(paper.paper_id)}
              sx={{
                p: 1.25,
                borderRadius: 1,
                border: 1,
                borderColor:
                  selectedPaperId === paper.paper_id
                    ? "primary.main"
                    : "divider",
                cursor: "pointer",
                bgcolor:
                  selectedPaperId === paper.paper_id
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
                {[paper.venue, paper.year].filter(Boolean).join(" | ")}
              </Typography>
              <Stack direction="row" spacing={0.5} sx={{ mt: 0.75 }}>
                <Chip
                  label={`Rel ${relevancy.toFixed(2)}`}
                  size="small"
                  color="primary"
                />
                <Chip
                  label={`Conv ${convergence >= 0 ? "+" : ""}${convergence.toFixed(2)}`}
                  size="small"
                  color={convergence >= 0 ? "success" : "error"}
                />
              </Stack>
            </Box>
          );
        })}
      </Stack>

      {!!selectedPaper && (
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
            Selected Paper Details
          </Typography>
          <Typography variant="body2" fontWeight={700} sx={{ mb: 0.25 }}>
            {selectedPaper.title}
          </Typography>
          <Typography variant="caption" color="text.secondary" display="block">
            {[
              selectedPaper.authors,
              selectedPaper.source || selectedPaper.venue,
              selectedPaper.year,
            ]
              .filter(Boolean)
              .join(" | ")}
          </Typography>
          {(selectedPaper.abstract || selectedPaper.relevancy_reasoning) && (
            <Typography
              variant="caption"
              color="text.secondary"
              display="block"
              sx={{ mt: 0.75 }}
            >
              {selectedPaper.abstract || selectedPaper.relevancy_reasoning}
            </Typography>
          )}
          {(selectedPaper.convergence_reasoning ||
            selectedPaper.comparison) && (
            <Typography
              variant="caption"
              color="text.secondary"
              display="block"
              sx={{ mt: 0.5 }}
            >
              {selectedPaper.convergence_reasoning || selectedPaper.comparison}
            </Typography>
          )}
        </Box>
      )}

      <Box sx={{ mt: "auto" }}>
        <Divider sx={{ mb: 1.5 }} />

        <Typography variant="subtitle2" fontWeight={700} sx={{ mb: 1 }}>
          Agent Chat
        </Typography>
        <Box
          ref={chatListRef}
          sx={{
            display: "flex",
            flexDirection: "column",
            gap: 0.75,
            maxHeight: 190,
            overflow: "auto",
            pr: 0.5,
          }}
        >
          {messages.map((m, i) => (
            <Box
              key={`${m.role}-${i}`}
              sx={{
                alignSelf: m.role === "user" ? "flex-end" : "flex-start",
                maxWidth: "88%",
                p: 1,
                borderRadius: 2,
                bgcolor: m.role === "user" ? "primary.main" : "action.selected",
                color:
                  m.role === "user" ? "primary.contrastText" : "text.primary",
              }}
            >
              <Typography variant="caption" fontWeight={700} display="block">
                {m.role === "agent" ? "Agent" : "You"}
              </Typography>
              <Typography variant="body2">{m.text}</Typography>
            </Box>
          ))}
        </Box>
        <Box
          component="form"
          onSubmit={handleSend}
          sx={{ display: "flex", gap: 1, mt: 1 }}
        >
          <TextField
            size="small"
            fullWidth
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
            placeholder="Ask the agent about citation convergence..."
          />
          <IconButton
            type="submit"
            size="small"
            color="primary"
            disabled={!draft.trim()}
          >
            <SendIcon />
          </IconButton>
        </Box>
      </Box>
    </Box>
  );
}

function FiguresContent({
  result,
  jobId,
}: {
  result: ValidationResult | null;
  jobId: string | null;
}) {
  const theme = useTheme();
  const [selectedFigure, setSelectedFigure] = useState<string | null>(null);
  const [figureAssets, setFigureAssets] = useState<FigureAsset[]>([]);
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      role: "agent",
      text: "Figure checks are loaded. Select a figure and ask for discrepancy analysis.",
    },
  ]);
  const [draft, setDraft] = useState("");
  const chatListRef = useRef<HTMLDivElement>(null);

  const allFigures = result
    ? Object.values(result.step_validations).flatMap(
        (v) => v.figure_validations ?? [],
      )
    : [];
  const displayedFigures: FigureValidation[] =
    allFigures.length > 0 ? allFigures : FALLBACK_FIGURES;

  useEffect(() => {
    if (!displayedFigures.length) {
      setSelectedFigure(null);
      return;
    }
    if (
      !selectedFigure ||
      !displayedFigures.some((f) => f.figure_name === selectedFigure)
    ) {
      setSelectedFigure(displayedFigures[0].figure_name);
    }
  }, [displayedFigures, selectedFigure]);

  useEffect(() => {
    const container = chatListRef.current;
    if (!container) {
      return;
    }
    container.scrollTo({ top: container.scrollHeight, behavior: "smooth" });
  }, [messages]);

  const selectedFigureData = useMemo(
    () =>
      selectedFigure
        ? (displayedFigures.find((f) => f.figure_name === selectedFigure) ??
          null)
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

  const handleSend = (e: FormEvent) => {
    e.preventDefault();
    if (!draft.trim()) {
      return;
    }

    const userMessage = draft.trim();
    const confirmations =
      selectedFigureData?.validity?.confirmations?.length ?? 0;
    const contradictions =
      selectedFigureData?.validity?.contradictions?.length ?? 0;

    setMessages((prev) => [
      ...prev,
      { role: "user", text: userMessage },
      {
        role: "agent",
        text: `For ${selectedFigure ?? "the current figure"}, I see ${confirmations} confirmations and ${contradictions} contradictions. If this discrepancy matters for your claim, prioritize evidence around the inflection region.`,
      },
    ]);
    setDraft("");
  };

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
    <Box
      sx={{ display: "flex", flexDirection: "column", gap: 2, height: "100%" }}
    >
      {allFigures.length === 0 && (
        <Typography variant="body2" color="text.secondary">
          No figure validation data available yet. Showing demo placeholder
          figures.
        </Typography>
      )}

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
                title="Observed / Submitted"
                subtitle={
                  selectedFigureAsset?.submitted?.filename ??
                  "Placeholder figure"
                }
                imageUrl={selectedFigureAsset?.submitted?.url}
                alt={`${selectedFigureData.figure_name} submitted`}
                placeholder={submittedPlaceholder}
              />
              <ZoomableFigureCard
                title="Predicted / Expected"
                subtitle={
                  selectedFigureAsset?.predicted?.filename ??
                  "Placeholder figure"
                }
                imageUrl={selectedFigureAsset?.predicted?.url}
                alt={`${selectedFigureData.figure_name} predicted`}
                placeholder={predictedPlaceholder}
              />
            </Stack>
          </Box>
        </Box>
      )}

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
              key={`${fig.figure_name}-${i}`}
              onClick={() => setSelectedFigure(fig.figure_name)}
              sx={{
                p: 1.25,
                borderRadius: 1,
                border: 1,
                borderColor:
                  selectedFigure === fig.figure_name
                    ? "primary.main"
                    : "divider",
                cursor: "pointer",
                bgcolor:
                  selectedFigure === fig.figure_name
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
                Confirmations: {fig.validity?.confirmations?.length ?? 0} |
                Contradictions: {fig.validity?.contradictions?.length ?? 0}
              </Typography>
            </Box>
          ))}
        </Stack>
      </Box>

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
          {(selectedFigureData.validity?.confirmations ?? []).map((c, i) => (
            <Typography
              key={`c-${i}`}
              variant="caption"
              color="text.secondary"
              display="block"
            >
              + {c}
            </Typography>
          ))}
          {(selectedFigureData.validity?.contradictions ?? []).map((c, i) => (
            <Typography
              key={`x-${i}`}
              variant="caption"
              color="text.secondary"
              display="block"
            >
              - {c}
            </Typography>
          ))}
        </Box>
      )}

      <Box sx={{ mt: "auto" }}>
        <Divider sx={{ mb: 1.5 }} />

        <Typography variant="subtitle2" fontWeight={700} sx={{ mb: 1 }}>
          Agent Chat
        </Typography>
        <Box
          ref={chatListRef}
          sx={{
            display: "flex",
            flexDirection: "column",
            gap: 0.75,
            maxHeight: 190,
            overflow: "auto",
            pr: 0.5,
          }}
        >
          {messages.map((m, i) => (
            <Box
              key={`${m.role}-${i}`}
              sx={{
                alignSelf: m.role === "user" ? "flex-end" : "flex-start",
                maxWidth: "88%",
                p: 1,
                borderRadius: 2,
                bgcolor: m.role === "user" ? "primary.main" : "action.selected",
                color:
                  m.role === "user" ? "primary.contrastText" : "text.primary",
              }}
            >
              <Typography variant="caption" fontWeight={700} display="block">
                {m.role === "agent" ? "Agent" : "You"}
              </Typography>
              <Typography variant="body2">{m.text}</Typography>
            </Box>
          ))}
        </Box>
        <Box
          component="form"
          onSubmit={handleSend}
          sx={{ display: "flex", gap: 1, mt: 1 }}
        >
          <TextField
            size="small"
            fullWidth
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
            placeholder="Ask the agent about figure discrepancies..."
          />
          <IconButton
            type="submit"
            size="small"
            color="primary"
            disabled={!draft.trim()}
          >
            <SendIcon />
          </IconButton>
        </Box>
      </Box>
    </Box>
  );
}

interface AgentPanelProps {
  content: string;
  title: string;
  documentId?: number;
  activeTab: AgentTab;
  onTabChange: (tab: AgentTab) => void;
  onCollapse: () => void;
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
  const [job, setJob] = useState<PipelineJob | null>(null);
  const [result, setResult] = useState<ValidationResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [graphData, setGraphData] = useState<NodeLinkGraph | null>(null);
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
                setGraphData(graphRes.data);
              } catch {
                // Graph data is optional — don't block on failure
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

      <Box sx={{ flex: 1, minHeight: 0, overflow: "auto", p: 1.5 }}>
        {safeTab === "validate" && (
          <ValidateContent
            content={content}
            job={job}
            result={result}
            error={error}
            onRun={handleRun}
          />
        )}
        {safeTab === "math" && <MathContent result={result} />}
        {safeTab === "citations" && <CitationsContent result={result} />}
        {safeTab === "figures" && (
          <FiguresContent result={result} jobId={job?.job_id ?? null} />
        )}
        {safeTab === "graph" && <GraphContent graph={graphData} job={job} />}
      </Box>
    </Stack>
  );
};
