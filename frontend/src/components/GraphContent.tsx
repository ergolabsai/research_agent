import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  Box,
  Checkbox,
  Chip,
  Collapse,
  Divider,
  FormControlLabel,
  IconButton,
  Paper,
  Stack,
  ToggleButton,
  ToggleButtonGroup,
  Tooltip,
  Typography,
  useTheme,
} from "@mui/material";
import {
  List as ListIcon,
  Hub as GraphIcon,
  Close as CloseIcon,
  ArrowForward as ArrowForwardIcon,
  ArrowBack as ArrowBackIcon,
  ExpandMore as ExpandMoreIcon,
  ChevronRight as ChevronRightIcon,
} from "@mui/icons-material";
import ForceGraph2D from "react-force-graph-2d";
import type { LinkObject, NodeObject } from "react-force-graph-2d";
import {
  GraphNodeType,
  GraphEdgeType,
  NodeLinkGraph,
  PipelineJob,
} from "../types";
import { useTheme as useAppTheme } from "../theme";

// --- Constants ---

const NODE_TYPE_LABELS: Record<GraphNodeType, string> = {
  paper: "Paper",
  step: "Step",
  evidence: "Evidence",
  figure: "Figure",
  math: "Math",
  related_paper: "Reference",
};

const NODE_TYPES = Object.keys(NODE_TYPE_LABELS) as GraphNodeType[];

const NODE_TYPE_PALETTE_INDEX: Record<GraphNodeType, number> = {
  paper: 0,
  step: 2,
  evidence: 1,
  figure: 4,
  math: 3,
  related_paper: 7,
};

function useNodeColors(): Record<GraphNodeType, string> {
  const theme = useTheme();
  return useMemo(() => {
    const p = theme.palette.discrete;
    const out = {} as Record<GraphNodeType, string>;
    for (const [type, idx] of Object.entries(NODE_TYPE_PALETTE_INDEX)) {
      out[type as GraphNodeType] = p[idx % p.length];
    }
    return out;
  }, [theme.palette.discrete]);
}

const EDGE_TYPE_LABELS: Record<GraphEdgeType, string> = {
  HAS_STEP: "Has Step",
  DEPENDS_ON: "Depends On",
  SUPPORTS: "Supports",
  ASSESSES: "Assesses",
  RELATED_TO: "Related To",
};

const EDGE_TYPES = Object.keys(EDGE_TYPE_LABELS) as GraphEdgeType[];

const EDGE_TYPE_PALETTE_INDEX: Record<GraphEdgeType, number> = {
  HAS_STEP: 5,
  DEPENDS_ON: 6,
  SUPPORTS: 8,
  ASSESSES: 9,
  RELATED_TO: 10,
};

function useEdgeColors(): Record<GraphEdgeType, string> {
  const theme = useTheme();
  return useMemo(() => {
    const p = theme.palette.discrete;
    const out = {} as Record<GraphEdgeType, string>;
    for (const [type, idx] of Object.entries(EDGE_TYPE_PALETTE_INDEX)) {
      out[type as GraphEdgeType] = p[idx % p.length];
    }
    return out;
  }, [theme.palette.discrete]);
}

// --- Helpers ---

function getNodeLabel(node: Record<string, unknown>): string {
  const t = node.node_type as GraphNodeType;
  switch (t) {
    case "paper":
      return (node.title as string) ?? "Paper";
    case "step":
      return `Step ${node.step_number}: ${truncate(node.description as string, 60)}`;
    case "evidence":
      return `[${getEvidenceCategory(node)}] ${truncate(node.description as string, 60)}`;
    case "figure":
      return formatFigureShortLabel(node.figure_name as string | undefined);
    case "math":
      return node.equation_reference as string;
    case "related_paper":
      return truncate(node.title as string, 60);
    default:
      return String(node.id);
  }
}

function getEvidenceCategory(node: Record<string, unknown>): string {
  const raw = String(node.evidence_type ?? "").toLowerCase();
  if (raw.includes("figure")) return "figure";
  if (raw.includes("math") || raw.includes("equation")) return "math";
  if (raw.includes("citation") || raw.includes("reference")) return "citation";
  const compact = raw.replace(/[^a-z0-9]+/g, "").trim();
  return compact || "other";
}

function formatFigureShortLabel(figureName: string | undefined): string {
  const raw = String(figureName ?? "").trim();
  if (!raw) return "Fig.";

  const figureNumberMatch =
    /\bfig(?:ure)?\.?\s*\(?\s*([0-9]+[a-z]?)\s*\)?/i.exec(raw);
  if (figureNumberMatch?.[1]) return `Fig. (${figureNumberMatch[1]})`;

  if (/^[0-9]+[a-z]?$/i.test(raw)) return `Fig. (${raw})`;

  return "Fig.";
}

function getNodeShortLabel(node: Record<string, unknown>): string {
  const t = node.node_type as GraphNodeType;
  switch (t) {
    case "paper":
      return truncate(node.title as string, 20);
    case "step":
      return `S${node.step_number}`;
    case "evidence":
      return `E[${getEvidenceCategory(node)}]`;
    case "figure":
      return formatFigureShortLabel(node.figure_name as string | undefined);
    case "math":
      return truncate(node.equation_reference as string, 14);
    case "related_paper":
      return truncate(node.title as string, 14);
    default:
      return String(node.id);
  }
}

function truncate(s: string | undefined, len: number): string {
  if (!s) return "";
  return s.length > len ? s.slice(0, len - 1) + "…" : s;
}

/** Splits a node label into a colored prefix and plain suffix for list display. */
function getNodeLabelParts(node: Record<string, unknown>): {
  prefix: string;
  suffix: string;
} {
  const t = node.node_type as GraphNodeType;
  switch (t) {
    case "paper":
      return { prefix: "Paper:", suffix: ` ${(node.title as string) ?? ""}` };
    case "step":
      return {
        prefix: `Step ${node.step_number}:`,
        suffix: ` ${truncate(node.description as string, 60)}`,
      };
    case "evidence":
      return {
        prefix: `[${getEvidenceCategory(node)}]`,
        suffix: ` ${truncate(node.description as string, 60)}`,
      };
    case "figure": {
      const figureName = String(node.figure_name ?? "").trim();
      return {
        prefix: "Figure:",
        suffix: figureName ? ` ${figureName}` : "",
      };
    }
    case "math": {
      const eqRef = (node.equation_reference as string) ?? "";
      const colonIdx = eqRef.indexOf(":");
      if (colonIdx !== -1) {
        return {
          prefix: eqRef.slice(0, colonIdx + 1),
          suffix: eqRef.slice(colonIdx + 1),
        };
      }
      return { prefix: eqRef, suffix: "" };
    }
    case "related_paper":
      return {
        prefix: "Ref:",
        suffix: ` ${truncate(node.title as string, 60)}`,
      };
    default:
      return { prefix: String(node.id), suffix: "" };
  }
}

/** Returns the palette color to use for an evidence node's bracket tag. */
function getEvidenceTagColor(
  node: Record<string, unknown>,
  nodeColors: Record<GraphNodeType, string>,
): string {
  const evidenceCategory = getEvidenceCategory(node);
  if (evidenceCategory === "figure") return nodeColors.figure;
  if (evidenceCategory === "math") return nodeColors.math;
  if (evidenceCategory === "citation") return nodeColors.related_paper;
  return nodeColors.evidence;
}

function NodeLabelText({
  node,
  nodeColors,
}: {
  node: Record<string, unknown>;
  nodeColors: Record<GraphNodeType, string>;
}) {
  const { prefix, suffix } = getNodeLabelParts(node);
  const t = node.node_type as GraphNodeType;
  const prefixColor =
    t === "evidence" ? getEvidenceTagColor(node, nodeColors) : nodeColors[t];

  return (
    <Typography variant="body2" noWrap sx={{ flex: 1 }}>
      <Box component="span" sx={{ color: prefixColor, fontWeight: 700 }}>
        {prefix}
      </Box>
      {suffix}
    </Typography>
  );
}

function getNodeDetails(
  node: Record<string, unknown>,
): Array<{ label: string; value: string }> {
  const t = node.node_type as GraphNodeType;
  const out: Array<{ label: string; value: string }> = [];
  out.push({ label: "ID", value: String(node.id) });
  out.push({ label: "Type", value: NODE_TYPE_LABELS[t] ?? String(t) });

  switch (t) {
    case "paper":
      if (node.title) out.push({ label: "Title", value: String(node.title) });
      if (node.main_claim)
        out.push({ label: "Main Claim", value: String(node.main_claim) });
      break;
    case "step":
      if (node.step_number != null)
        out.push({ label: "Step #", value: String(node.step_number) });
      if (node.description)
        out.push({ label: "Description", value: String(node.description) });
      if (node.section)
        out.push({ label: "Section", value: String(node.section) });
      break;
    case "evidence":
      if (node.evidence_type)
        out.push({ label: "Evidence Type", value: String(node.evidence_type) });
      if (node.description)
        out.push({ label: "Description", value: String(node.description) });
      if (node.location)
        out.push({ label: "Location", value: String(node.location) });
      if (node.excerpt)
        out.push({ label: "Excerpt", value: String(node.excerpt) });
      break;
    case "figure":
      if (node.figure_name)
        out.push({ label: "Figure", value: String(node.figure_name) });
      if (node.actual_description)
        out.push({
          label: "Observed",
          value: String(node.actual_description),
        });
      if (node.expected_description)
        out.push({
          label: "Expected",
          value: String(node.expected_description),
        });
      if (Array.isArray(node.similarities) && node.similarities.length)
        out.push({
          label: "Similarities",
          value: (node.similarities as string[]).join("; "),
        });
      if (Array.isArray(node.differences) && node.differences.length)
        out.push({
          label: "Differences",
          value: (node.differences as string[]).join("; "),
        });
      break;
    case "math":
      if (node.equation_reference)
        out.push({ label: "Equation", value: String(node.equation_reference) });
      if (node.calculation_valid != null)
        out.push({
          label: "Valid",
          value: node.calculation_valid ? "Yes" : "No",
        });
      if (node.details)
        out.push({ label: "Details", value: String(node.details) });
      if (node.formula_used)
        out.push({ label: "Formula", value: String(node.formula_used) });
      break;
    case "related_paper":
      if (node.title) out.push({ label: "Title", value: String(node.title) });
      if (node.authors)
        out.push({ label: "Authors", value: String(node.authors) });
      if (node.source)
        out.push({ label: "Source", value: String(node.source) });
      if (node.relevancy_score != null)
        out.push({
          label: "Relevancy",
          value: Number(node.relevancy_score).toFixed(2),
        });
      if (node.convergence_score != null)
        out.push({
          label: "Convergence",
          value: Number(node.convergence_score).toFixed(2),
        });
      if (node.abstract)
        out.push({
          label: "Abstract",
          value: truncate(String(node.abstract), 200),
        });
      break;
  }
  return out;
}

interface Neighbor {
  nodeId: string;
  node: Record<string, unknown>;
  edgeType: GraphEdgeType;
  direction: "outgoing" | "incoming";
  edgeAttrs: Record<string, unknown>;
}

function getNeighbors(nodeId: string, graph: NodeLinkGraph): Neighbor[] {
  const nodeMap = new Map(graph.nodes.map((n) => [n.id, n]));
  const results: Neighbor[] = [];

  for (const link of graph.links) {
    if (link.source === nodeId) {
      const target = nodeMap.get(link.target);
      if (target) {
        const { source: _s, target: _t, edge_type, ...attrs } = link;
        results.push({
          nodeId: link.target,
          node: target,
          edgeType: edge_type,
          direction: "outgoing",
          edgeAttrs: attrs,
        });
      }
    } else if (link.target === nodeId) {
      const source = nodeMap.get(link.source);
      if (source) {
        const { source: _s, target: _t, edge_type, ...attrs } = link;
        results.push({
          nodeId: link.source,
          node: source,
          edgeType: edge_type,
          direction: "incoming",
          edgeAttrs: attrs,
        });
      }
    }
  }
  return results;
}

// --- Components ---

function NodeTypeFilters({
  selected,
  onChange,
}: {
  selected: Set<GraphNodeType>;
  onChange: (types: Set<GraphNodeType>) => void;
}) {
  const nodeColors = useNodeColors();
  const toggle = (t: GraphNodeType) => {
    const next = new Set(selected);
    if (next.has(t)) {
      if (next.size > 1) next.delete(t);
    } else {
      next.add(t);
    }
    onChange(next);
  };

  return (
    <Stack direction="row" spacing={0.5} flexWrap="wrap" useFlexGap>
      {NODE_TYPES.map((t) => (
        <Chip
          key={t}
          label={NODE_TYPE_LABELS[t]}
          size="small"
          onClick={() => toggle(t)}
          sx={{
            fontSize: "0.7rem",
            height: 22,
            bgcolor: selected.has(t) ? nodeColors[t] : "transparent",
            color: selected.has(t) ? "#fff" : "text.secondary",
            border: 1,
            borderColor: selected.has(t) ? nodeColors[t] : "divider",
            fontWeight: selected.has(t) ? 700 : 400,
            "&:hover": { opacity: 0.85 },
          }}
        />
      ))}
    </Stack>
  );
}

function EdgeTypeFilters({
  selected,
  onChange,
}: {
  selected: Set<GraphEdgeType>;
  onChange: (types: Set<GraphEdgeType>) => void;
}) {
  const edgeColors = useEdgeColors();

  const toggle = (t: GraphEdgeType) => {
    const next = new Set(selected);
    if (next.has(t)) {
      if (next.size > 1) next.delete(t);
    } else {
      next.add(t);
    }
    onChange(next);
  };

  return (
    <Stack direction="row" spacing={0.5} flexWrap="wrap" useFlexGap>
      {EDGE_TYPES.map((t) => (
        <Chip
          key={t}
          label={EDGE_TYPE_LABELS[t]}
          size="small"
          variant={selected.has(t) ? "filled" : "outlined"}
          onClick={() => toggle(t)}
          sx={{
            fontSize: "0.65rem",
            height: 20,
            bgcolor: selected.has(t) ? edgeColors[t] : "transparent",
            color: selected.has(t) ? "#fff" : "text.secondary",
            borderColor: selected.has(t) ? edgeColors[t] : "divider",
            "&:hover": { opacity: 0.85 },
          }}
        />
      ))}
    </Stack>
  );
}

function NodeDetailPanel({
  node,
  neighbors,
  onSelectNeighbor,
  onClose,
  showClose = true,
  constrainHeight = true,
}: {
  node: Record<string, unknown>;
  neighbors: Neighbor[];
  onSelectNeighbor: (id: string) => void;
  onClose?: () => void;
  showClose?: boolean;
  constrainHeight?: boolean;
}) {
  const nodeColors = useNodeColors();
  const edgeColors = useEdgeColors();
  const details = getNodeDetails(node);
  const nodeType = node.node_type as GraphNodeType;

  return (
    <Paper
      elevation={4}
      sx={{
        p: 1.5,
        borderRadius: 1.5,
        borderLeft: 3,
        borderColor: nodeColors[nodeType] ?? "primary.main",
        maxHeight: constrainHeight ? 270 : "none",
        display: constrainHeight ? "flex" : "block",
        flexDirection: "column",
        overflow: "hidden",
      }}
    >
      {/* Header — always visible */}
      <Stack
        direction="row"
        justifyContent="space-between"
        alignItems="center"
        sx={{ mb: 0.5, flexShrink: 0 }}
      >
        <Stack direction="row" spacing={0.75} alignItems="center">
          <Chip
            label={NODE_TYPE_LABELS[nodeType]}
            size="small"
            sx={{
              bgcolor: nodeColors[nodeType],
              color: "#fff",
              fontSize: "0.7rem",
              height: 20,
            }}
          />
          <Typography variant="subtitle2" fontWeight={700}>
            {getNodeLabel(node)}
          </Typography>
        </Stack>
        {showClose && onClose ? (
          <IconButton size="small" onClick={onClose}>
            <CloseIcon sx={{ fontSize: 14 }} />
          </IconButton>
        ) : null}
      </Stack>

      {/* Details — scrollable */}
      <Box sx={{ overflow: "auto", flexShrink: 1, minHeight: 0 }}>
        {details.slice(2).map((d, i) => (
          <Box key={i} sx={{ mb: 0.25 }}>
            <Typography
              variant="caption"
              fontWeight={700}
              color="text.secondary"
            >
              {d.label}:{" "}
            </Typography>
            <Typography variant="caption" color="text.primary">
              {d.value}
            </Typography>
          </Box>
        ))}
      </Box>

      {neighbors.length > 0 && (
        <>
          <Divider sx={{ my: 0.75, flexShrink: 0 }} />
          <Typography
            variant="caption"
            fontWeight={700}
            color="text.secondary"
            display="block"
            sx={{ mb: 0.0, flexShrink: 0 }}
          >
            Neighbors ({neighbors.length})
          </Typography>
          {/* Neighbors — scrollable */}
          <Stack
            spacing={0.25}
            sx={{
              overflow: "auto",
              flexShrink: 1,
              minHeight: 28,
              maxHeight: 100,
            }}
          >
            {neighbors.map((n, i) => (
              <Box
                key={i}
                onClick={() => onSelectNeighbor(n.nodeId)}
                sx={{
                  display: "flex",
                  alignItems: "center",
                  gap: 0.5,
                  px: 0.75,
                  py: 0.25,
                  borderRadius: 0.5,
                  cursor: "pointer",
                  flexShrink: 0,
                  "&:hover": { bgcolor: "action.hover" },
                }}
              >
                {n.direction === "outgoing" ? (
                  <ArrowForwardIcon
                    sx={{ fontSize: 12, color: "text.secondary" }}
                  />
                ) : (
                  <ArrowBackIcon
                    sx={{ fontSize: 12, color: "text.secondary" }}
                  />
                )}
                <Chip
                  label={n.edgeType}
                  size="small"
                  sx={{
                    fontSize: "0.6rem",
                    height: 16,
                    bgcolor: edgeColors[n.edgeType],
                    color: "#fff",
                  }}
                />
                <Chip
                  label={NODE_TYPE_LABELS[n.node.node_type as GraphNodeType]}
                  size="small"
                  sx={{
                    fontSize: "0.6rem",
                    height: 16,
                    bgcolor: nodeColors[n.node.node_type as GraphNodeType],
                    color: "#fff",
                  }}
                />
                <Typography variant="caption" noWrap sx={{ flex: 1 }}>
                  {getNodeLabel(n.node)}
                </Typography>
              </Box>
            ))}
          </Stack>
        </>
      )}
    </Paper>
  );
}

// --- List Mode ---

function ListMode({
  graph,
  selectedNodeTypes,
}: {
  graph: NodeLinkGraph;
  selectedNodeTypes: Set<GraphNodeType>;
}) {
  const nodeColors = useNodeColors();
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const listRef = useRef<HTMLDivElement>(null);

  const filteredNodes = useMemo(
    () =>
      graph.nodes.filter((n) =>
        selectedNodeTypes.has(n.node_type as GraphNodeType),
      ),
    [graph.nodes, selectedNodeTypes],
  );

  // Reset selection when filter changes
  useEffect(() => {
    if (selectedNodeId && !filteredNodes.some((n) => n.id === selectedNodeId)) {
      setSelectedNodeId(null);
      setExpandedId(null);
    }
  }, [filteredNodes, selectedNodeId]);

  const handleSelect = useCallback(
    (nodeId: string) => {
      if (expandedId === nodeId) {
        setExpandedId(null);
        setSelectedNodeId(null);
        return;
      }

      setSelectedNodeId(nodeId);
      setExpandedId(nodeId);
      // Scroll to node
      requestAnimationFrame(() => {
        const el = document.getElementById(`graph-list-node-${nodeId}`);
        el?.scrollIntoView({ behavior: "smooth", block: "nearest" });
      });
    },
    [expandedId],
  );

  const neighbors = useMemo(
    () => (selectedNodeId ? getNeighbors(selectedNodeId, graph) : []),
    [selectedNodeId, graph],
  );

  // Group by node type
  const grouped = useMemo(() => {
    const groups = new Map<GraphNodeType, typeof filteredNodes>();
    for (const node of filteredNodes) {
      const t = node.node_type as GraphNodeType;
      if (!groups.has(t)) groups.set(t, []);
      groups.get(t)!.push(node);
    }
    return groups;
  }, [filteredNodes]);

  return (
    <Box ref={listRef} sx={{ flex: 1, overflow: "auto", pr: 0.5 }}>
      {NODE_TYPES.filter((t) => grouped.has(t)).map((type) => (
        <Box key={type} sx={{ mb: 1.5 }}>
          <Stack
            direction="row"
            spacing={0.5}
            alignItems="center"
            sx={{ mb: 0.5 }}
          >
            <Box
              sx={{
                width: 10,
                height: 10,
                borderRadius: "50%",
                bgcolor: nodeColors[type],
                flexShrink: 0,
              }}
            />
            <Typography
              variant="caption"
              fontWeight={700}
              color="text.secondary"
              sx={{ textTransform: "uppercase", letterSpacing: "0.05em" }}
            >
              {NODE_TYPE_LABELS[type]} ({grouped.get(type)!.length})
            </Typography>
          </Stack>

          <Stack spacing={0.5}>
            {grouped.get(type)!.map((node) => {
              const isExpanded = expandedId === node.id;
              const isSelected = selectedNodeId === node.id;

              return (
                <Box key={node.id} id={`graph-list-node-${node.id}`}>
                  <Box
                    onClick={() => handleSelect(node.id)}
                    sx={{
                      display: "flex",
                      alignItems: "center",
                      gap: 0.5,
                      px: 1,
                      py: 0.5,
                      borderRadius: 1,
                      border: 1,
                      borderColor: isSelected ? nodeColors[type] : "divider",
                      bgcolor: isSelected ? "action.selected" : "transparent",
                      cursor: "pointer",
                      "&:hover": { bgcolor: "action.hover" },
                    }}
                  >
                    {isExpanded ? (
                      <ExpandMoreIcon
                        sx={{ fontSize: 14, color: "text.secondary" }}
                      />
                    ) : (
                      <ChevronRightIcon
                        sx={{ fontSize: 14, color: "text.secondary" }}
                      />
                    )}
                    <NodeLabelText node={node} nodeColors={nodeColors} />
                  </Box>

                  <Collapse in={isExpanded}>
                    <Box sx={{ pl: 1, pt: 0.5 }}>
                      <NodeDetailPanel
                        node={node}
                        neighbors={neighbors}
                        onSelectNeighbor={handleSelect}
                        showClose={false}
                        constrainHeight={false}
                      />
                    </Box>
                  </Collapse>
                </Box>
              );
            })}
          </Stack>
        </Box>
      ))}

      {filteredNodes.length === 0 && (
        <Typography
          variant="body2"
          color="text.secondary"
          sx={{ mt: 2, textAlign: "center" }}
        >
          No nodes match the selected filters.
        </Typography>
      )}
    </Box>
  );
}

// --- Graph Mode ---

function GraphMode({
  graph,
  selectedNodeTypes,
  selectedEdgeTypes,
  showEdgeLabels,
  containerWidth,
  containerHeight,
}: {
  graph: NodeLinkGraph;
  selectedNodeTypes: Set<GraphNodeType>;
  selectedEdgeTypes: Set<GraphEdgeType>;
  showEdgeLabels: boolean;
  containerWidth: number;
  containerHeight: number;
}) {
  const theme = useTheme();
  const { layoutMode } = useAppTheme();
  const isVertical = layoutMode === "vertical";
  const nodeColors = useNodeColors();
  const edgeColors = useEdgeColors();
  const [selectedNode, setSelectedNode] = useState<Record<
    string,
    unknown
  > | null>(null);
  const graphRef = useRef<any>();

  const visibleNodeIds = useMemo(() => {
    const ids = new Set<string>();
    for (const n of graph.nodes) {
      if (selectedNodeTypes.has(n.node_type as GraphNodeType)) {
        ids.add(n.id);
      }
    }
    return ids;
  }, [graph.nodes, selectedNodeTypes]);

  const graphData = useMemo(() => {
    const nodes = graph.nodes
      .filter((n) => visibleNodeIds.has(n.id))
      .map((n) => ({ ...n }));
    const links = graph.links
      .filter(
        (l) =>
          visibleNodeIds.has(l.source) &&
          visibleNodeIds.has(l.target) &&
          selectedEdgeTypes.has(l.edge_type as GraphEdgeType),
      )
      .map((l) => ({ ...l }));
    return { nodes, links };
  }, [graph, visibleNodeIds, selectedEdgeTypes]);

  // Auto-fit after data changes
  useEffect(() => {
    const timer = setTimeout(() => {
      graphRef.current?.zoomToFit(400, 40);
    }, 500);
    return () => clearTimeout(timer);
  }, [graphData]);

  const selectedNeighbors = useMemo(
    () => (selectedNode ? getNeighbors(String(selectedNode.id), graph) : []),
    [selectedNode, graph],
  );

  const handleNodeClick = useCallback((node: NodeObject) => {
    setSelectedNode(node as Record<string, unknown>);
  }, []);

  const handleBgClick = useCallback(() => {
    setSelectedNode(null);
  }, []);

  const nodeLabel = useCallback(
    (node: NodeObject) => getNodeLabel(node as Record<string, unknown>),
    [],
  );

  const nodeCanvasObject = useCallback(
    (node: NodeObject, ctx: CanvasRenderingContext2D, globalScale: number) => {
      const n = node as NodeObject & Record<string, unknown>;
      const label = getNodeShortLabel(n);
      const fontSize = Math.max(10 / globalScale, 2);
      const nodeType = n.node_type as GraphNodeType;
      const color = nodeColors[nodeType] ?? "#999";
      const x = node.x ?? 0;
      const y = node.y ?? 0;
      const r = nodeType === "paper" ? 8 : nodeType === "step" ? 6 : 4;

      // Node circle
      ctx.beginPath();
      ctx.arc(x, y, r, 0, 2 * Math.PI);
      ctx.fillStyle = color;
      ctx.fill();

      // Highlight selected
      if (selectedNode && String(n.id) === String(selectedNode.id)) {
        ctx.strokeStyle = theme.palette.mode === "dark" ? "#fff" : "#000";
        ctx.lineWidth = 2 / globalScale;
        ctx.stroke();
      }

      // Label
      if (globalScale > 0.6) {
        ctx.font = `${fontSize}px Sans-Serif`;
        ctx.textAlign = "center";
        ctx.textBaseline = "top";
        ctx.fillStyle = theme.palette.text.primary;
        ctx.fillText(label, x, y + r + 2);
      }
    },
    [selectedNode, theme, nodeColors],
  );

  const nodePointerAreaPaint = useCallback(
    (node: NodeObject, color: string, ctx: CanvasRenderingContext2D) => {
      const nodeType = (node as Record<string, unknown>)
        .node_type as GraphNodeType;
      const r = nodeType === "paper" ? 8 : nodeType === "step" ? 6 : 4;
      ctx.beginPath();
      ctx.arc(node.x ?? 0, node.y ?? 0, r + 2, 0, 2 * Math.PI);
      ctx.fillStyle = color;
      ctx.fill();
    },
    [],
  );

  const linkColor = useCallback(
    (link: Record<string, unknown>) => {
      const edgeType = link.edge_type as GraphEdgeType;
      return edgeColors[edgeType] ?? theme.palette.text.disabled;
    },
    [edgeColors, theme.palette.text.disabled],
  );

  const linkCanvasObject = useCallback(
    (link: LinkObject, ctx: CanvasRenderingContext2D, globalScale: number) => {
      if (!showEdgeLabels) return;

      const l = link as LinkObject & Record<string, unknown>;
      const source = l.source as { x?: number; y?: number } | undefined;
      const target = l.target as { x?: number; y?: number } | undefined;
      if (
        source?.x == null ||
        source?.y == null ||
        target?.x == null ||
        target?.y == null
      ) {
        return;
      }

      const edgeType = l.edge_type as GraphEdgeType;
      const label = EDGE_TYPE_LABELS[edgeType] ?? String(edgeType);
      const x = (source.x + target.x) / 2;
      const y = (source.y + target.y) / 2;

      const fontSize = Math.max(9 / globalScale, 2.5);
      ctx.font = `${fontSize}px Sans-Serif`;
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";

      const textWidth = ctx.measureText(label).width;
      const padding = 2 / globalScale;
      const boxHeight = fontSize + padding * 2;
      ctx.fillStyle =
        theme.palette.mode === "dark"
          ? "rgba(20,20,20,0.72)"
          : "rgba(255,255,255,0.78)";
      ctx.fillRect(
        x - textWidth / 2 - padding,
        y - boxHeight / 2,
        textWidth + padding * 2,
        boxHeight,
      );

      ctx.fillStyle = edgeColors[edgeType] ?? theme.palette.text.secondary;
      ctx.fillText(label, x, y);
    },
    [
      showEdgeLabels,
      theme.palette.mode,
      theme.palette.text.secondary,
      edgeColors,
    ],
  );

  return (
    <Box sx={{ position: "relative", flex: 1, minHeight: 0 }}>
      <ForceGraph2D
        ref={graphRef}
        graphData={graphData}
        width={containerWidth}
        height={containerHeight}
        nodeId="id"
        linkSource="source"
        linkTarget="target"
        nodeLabel={nodeLabel}
        nodeCanvasObject={nodeCanvasObject}
        nodeCanvasObjectMode={() => "replace"}
        nodePointerAreaPaint={nodePointerAreaPaint}
        linkColor={linkColor}
        linkCanvasObject={linkCanvasObject}
        linkCanvasObjectMode={() => "after"}
        linkDirectionalArrowColor={linkColor}
        linkDirectionalArrowLength={4}
        linkDirectionalArrowRelPos={1}
        linkWidth={1}
        onNodeClick={handleNodeClick}
        onBackgroundClick={handleBgClick}
        enableNodeDrag
        cooldownTicks={80}
        backgroundColor="transparent"
      />

      {selectedNode && (
        <Box
          sx={{
            position: "absolute",
            bottom: 8,
            right: 8,
            left: isVertical ? "auto" : 8,
            width: isVertical ? "40%" : "auto",
            maxHeight: isVertical ? "100%" : "50%",
            overflow: "auto",
            zIndex: 10,
          }}
        >
          <NodeDetailPanel
            node={selectedNode}
            neighbors={selectedNeighbors}
            onSelectNeighbor={(id) => {
              const n = graph.nodes.find((nd) => nd.id === id);
              if (n) setSelectedNode(n);
            }}
            onClose={() => setSelectedNode(null)}
          />
        </Box>
      )}
    </Box>
  );
}

// --- Main Export ---

interface GraphContentProps {
  graph: NodeLinkGraph | null;
  job: PipelineJob | null;
}

export function GraphContent({ graph, job }: GraphContentProps) {
  const theme = useTheme();
  const [viewMode, setViewMode] = useState<"list" | "graph">("list");
  const [selectedNodeTypes, setSelectedNodeTypes] = useState<
    Set<GraphNodeType>
  >(() => new Set(NODE_TYPES));
  const [selectedEdgeTypes, setSelectedEdgeTypes] = useState<
    Set<GraphEdgeType>
  >(() => new Set(EDGE_TYPES));
  const [showEdgeLabels, setShowEdgeLabels] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);
  const [containerSize, setContainerSize] = useState({ w: 400, h: 300 });

  // Measure graph container
  useEffect(() => {
    if (viewMode !== "graph") return;
    const el = containerRef.current;
    if (!el) return;

    const measure = () => {
      setContainerSize({ w: el.clientWidth, h: el.clientHeight });
    };
    measure();

    const ro = new ResizeObserver(measure);
    ro.observe(el);
    return () => ro.disconnect();
  }, [viewMode]);

  if (!graph && job?.status !== "completed") {
    return (
      <Box sx={{ textAlign: "center", py: 4 }}>
        <Typography variant="body2" color="text.secondary">
          Paper graph will be available after the pipeline completes.
        </Typography>
      </Box>
    );
  }

  if (!graph) {
    return (
      <Box sx={{ textAlign: "center", py: 4 }}>
        <Typography variant="body2" color="text.secondary">
          Loading graph data…
        </Typography>
      </Box>
    );
  }

  return (
    <Box
      sx={{
        display: "flex",
        flexDirection: "column",
        gap: 1,
        height: "100%",
      }}
    >
      {/* Header: mode toggle */}
      <Stack direction="row" justifyContent="space-between" alignItems="center">
        <Typography variant="caption" fontWeight={700} color="text.secondary">
          {graph.nodes.length} nodes · {graph.links.length} edges
        </Typography>
        <ToggleButtonGroup
          value={viewMode}
          exclusive
          onChange={(_, v) => v && setViewMode(v)}
          size="small"
          sx={{
            height: 32,
            borderRadius: "12px",
            border: "1px solid " + theme.palette.divider,
            background: `linear-gradient(135deg, ${theme.palette.primary.main}10 0%, ${theme.palette.secondary.main}20 100%)`,
            overflow: "hidden",
            "& .MuiToggleButtonGroup-grouped": {
              border: "none",
              borderRadius: "0 !important",
              "&:not(:last-of-type)": {
                borderRight: "1px solid " + theme.palette.divider,
              },
            },
            "& .MuiToggleButton-root": {
              textTransform: "none",
              fontSize: "0.8rem",
              fontWeight: 600,
              gap: 0.75,
              px: 1.5,
              color: theme.palette.text.secondary,
              background: "transparent",
              "&.Mui-selected": {
                color: theme.palette.primary.main,
                background: `${theme.palette.primary.main}18`,
              },
            },
          }}
        >
          <ToggleButton value="list">
            <ListIcon sx={{ fontSize: 14 }} />
            List
          </ToggleButton>
          <ToggleButton value="graph">
            <GraphIcon sx={{ fontSize: 14 }} />
            Graph
          </ToggleButton>
        </ToggleButtonGroup>
      </Stack>

      {/* Node type filters */}
      <Stack direction="row" spacing={1} alignItems="center" flexWrap="wrap">
        <Typography variant="caption" fontWeight={700} color="text.secondary">
          Nodes:
        </Typography>
        <NodeTypeFilters
          selected={selectedNodeTypes}
          onChange={setSelectedNodeTypes}
        />
      </Stack>

      {/* Edge type filters (graph mode only) */}
      {viewMode === "graph" && (
        <Stack direction="row" spacing={1} alignItems="center" flexWrap="wrap">
          <Typography variant="caption" fontWeight={700} color="text.secondary">
            Edges:
          </Typography>
          <EdgeTypeFilters
            selected={selectedEdgeTypes}
            onChange={setSelectedEdgeTypes}
          />
          <FormControlLabel
            sx={{ ml: 0.5, mr: 0, userSelect: "none" }}
            control={
              <Checkbox
                checked={showEdgeLabels}
                onChange={(e) => setShowEdgeLabels(e.target.checked)}
                size="small"
              />
            }
            label={
              <Typography
                variant="caption"
                fontWeight={700}
                color="text.secondary"
              >
                Show
              </Typography>
            }
          />
        </Stack>
      )}

      <Divider />

      {/* Content area */}
      {viewMode === "list" ? (
        <ListMode graph={graph} selectedNodeTypes={selectedNodeTypes} />
      ) : (
        <Box ref={containerRef} sx={{ flex: 1, minHeight: 0 }}>
          <GraphMode
            graph={graph}
            selectedNodeTypes={selectedNodeTypes}
            selectedEdgeTypes={selectedEdgeTypes}
            showEdgeLabels={showEdgeLabels}
            containerWidth={containerSize.w}
            containerHeight={containerSize.h}
          />
        </Box>
      )}
    </Box>
  );
}
