import { useParams } from "react-router-dom";
import {
  Box,
  TextField,
  useTheme,
  Stack,
  Button,
  IconButton,
  Typography,
} from "@mui/material";
import { useState, useEffect, useRef, useCallback } from "react";
import { createPortal } from "react-dom";
import { documentsAPI } from "../api";
import { Attachment, ContentJson } from "../types";
import {
  AttachFile as AttachFileIcon,
  Delete as DeleteIcon,
  Psychology as BrainIcon,
} from "@mui/icons-material";
import { AgentPanel, AgentTab } from "../components/AgentPanel";
import { useRightPanel } from "./MainPage";
import { ViewModeToggle, ViewMode } from "../components/editor/ViewModeToggle";
import { RichView } from "../components/editor/RichView";
import { JsonView } from "../components/editor/JsonView";
import { LatexView } from "../components/editor/LatexView";
import {
  parseContentJson,
  contentJsonToPlainText,
} from "../utils/contentJsonUtils";
import { useTheme as useAppTheme } from "../theme";
import { HighlightProvider } from "../contexts/HighlightContext";

export const EditorPage = () => {
  const { id } = useParams();
  const theme = useTheme();
  const [title, setTitle] = useState("");
  const [content, setContent] = useState("");
  const [contentJson, setContentJson] = useState<ContentJson | null>(null);
  const [viewMode, setViewMode] = useState<ViewMode>("rich");
  const [hoveredIcon, setHoveredIcon] = useState<string | null>(null);
  const [isLoaded, setIsLoaded] = useState(false);
  const [attachments, setAttachments] = useState<Attachment[]>([]);
  const [isLoadingAttachments, setIsLoadingAttachments] = useState(false);
  const [isUploadingAttachment, setIsUploadingAttachment] = useState(false);

  // Right agent panel state (layout managed by MainPage)
  const { rightPanelOpen, setRightPanelOpen } = useRightPanel();
  const { layoutMode } = useAppTheme();
  const isVertical = layoutMode === "vertical";
  const [agentTab, setAgentTab] = useState<AgentTab>("validate");

  // Vertical mode: drag-to-resize agent panel height
  const [agentPanelHeight, setAgentPanelHeight] = useState(300);
  const dragRefVertical = useRef(false);
  const startYRef = useRef(0);
  const startHeightRef = useRef(300);
  const agentPanelHeightRef = useRef(300);

  const handleVerticalDragMouseDown = (e: React.MouseEvent) => {
    e.preventDefault();
    dragRefVertical.current = true;
    startYRef.current = e.clientY;
    startHeightRef.current = agentPanelHeightRef.current;
  };

  useEffect(() => {
    if (!isVertical) return;
    const onMouseMove = (e: MouseEvent) => {
      if (!dragRefVertical.current) return;
      const delta = startYRef.current - e.clientY;
      const newHeight = Math.min(
        800,
        Math.max(150, startHeightRef.current + delta),
      );
      setAgentPanelHeight(newHeight);
      agentPanelHeightRef.current = newHeight;
    };
    const onMouseUp = () => {
      dragRefVertical.current = false;
    };
    window.addEventListener("mousemove", onMouseMove);
    window.addEventListener("mouseup", onMouseUp);
    return () => {
      window.removeEventListener("mousemove", onMouseMove);
      window.removeEventListener("mouseup", onMouseUp);
    };
  }, [isVertical]);

  const formatFileSize = (sizeInBytes: number) => {
    if (sizeInBytes < 1024) return `${sizeInBytes} B`;
    if (sizeInBytes < 1024 * 1024)
      return `${(sizeInBytes / 1024).toFixed(1)} KB`;
    return `${(sizeInBytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  const loadAttachments = async (documentId: number) => {
    setIsLoadingAttachments(true);
    try {
      const response = await documentsAPI.listAttachments(documentId);
      setAttachments(response.data || []);
    } catch (err) {
      console.error("Failed to load attachments:", err);
      setAttachments([]);
    } finally {
      setIsLoadingAttachments(false);
    }
  };

  useEffect(() => {
    const loadDocument = async () => {
      if (!id) return;
      try {
        const response = await documentsAPI.get(Number(id));
        const raw = response.data.content || "";
        setTitle(response.data.title || "");

        const parsed = parseContentJson(raw);
        if (parsed) {
          setContentJson(parsed);
          setContent(raw);
          setViewMode("rich");
        } else {
          setContentJson(null);
          setContent(raw);
        }
        setIsLoaded(true);
      } catch (err) {
        console.error("Failed to load document:", err);
        setIsLoaded(true);
      }
    };
    loadDocument();
  }, [id]);

  useEffect(() => {
    if (!id) return;
    loadAttachments(Number(id));
  }, [id]);

  // Sync contentJson changes back to content string
  const handleContentJsonChange = useCallback((updated: ContentJson) => {
    setContentJson(updated);
    setContent(JSON.stringify(updated));
  }, []);

  // Auto-save (debounced for JSON editing)
  const saveTimerRef = useRef<ReturnType<typeof setTimeout>>();
  useEffect(() => {
    if (!isLoaded || !id) return;
    clearTimeout(saveTimerRef.current);
    saveTimerRef.current = setTimeout(
      async () => {
        try {
          await documentsAPI.update(Number(id), title, content);
        } catch (err) {
          console.error("Failed to save document:", err);
        }
      },
      contentJson ? 500 : 0,
    );
    return () => clearTimeout(saveTimerRef.current);
  }, [content, title, isLoaded, id, contentJson]);

  // const openPanel = (tab: AgentTab) => {
  //   setAgentTab(tab);
  //   setRightPanelOpen(true);
  // };

  // const handleMath = () => openPanel("math");
  // const handleLogic = () => openPanel("validate");
  // const handleFormatter = () => {};
  // const handleLibrarian = () => openPanel("citations");
  // const handlePlots = () => openPanel("figures");

  const handleAttachmentUpload = async (
    event: React.ChangeEvent<HTMLInputElement>,
  ) => {
    const file = event.target.files?.[0];
    if (!file || !id) return;
    setIsUploadingAttachment(true);
    try {
      await documentsAPI.uploadAttachment(Number(id), file);
      await loadAttachments(Number(id));
    } catch (err) {
      console.error("Failed to upload attachment:", err);
    } finally {
      setIsUploadingAttachment(false);
      event.target.value = "";
    }
  };

  const handleRemoveAttachment = async (attachmentId: number) => {
    if (!id) return;
    try {
      await documentsAPI.deleteAttachment(Number(id), attachmentId);
      await loadAttachments(Number(id));
    } catch (err) {
      console.error("Failed to delete attachment:", err);
    }
  };

  const buttons: any = [
    // { id: "math", label: "Math", icon: MathIcon, handler: handleMath },
    // { id: "logic", label: "Logic", icon: LogicIcon, handler: handleLogic },
    // {
    //   id: "formatter",
    //   label: "Format",
    //   icon: FormatterIcon,
    //   handler: handleFormatter,
    // },
    // {
    //   id: "librarian",
    //   label: "Library",
    //   icon: LibrarianIcon,
    //   handler: handleLibrarian,
    // },
    // { id: "plots", label: "Plots", icon: PlotsIcon, handler: handlePlots },
  ];

  const buttonSx = {
    height: "56px",
    minWidth: "56px",
    padding: "0px",
    gap: "0px",
    display: "flex",
    flexDirection: "column" as const,
    alignItems: "center",
    justifyContent: "center",
    background: `linear-gradient(135deg, ${theme.palette.primary.main}BB 20%, ${theme.palette.secondary.main}BB 100%)`,
    transition: "transform 0.2s ease, box-shadow 0.2s ease",
    "&:hover": {
      transform: "translateY(-2px)",
      boxShadow: "0 8px 16px rgba(0, 0, 0, 0.15)",
    },
  };

  const rpToolbar = document.getElementById("rp-toolbar");
  const [agentPanelRoot, setAgentPanelRoot] = useState<HTMLElement | null>(
    null,
  );

  useEffect(() => {
    if (rightPanelOpen) {
      // Wait for DOM to render the portal target
      const frame = requestAnimationFrame(() => {
        setAgentPanelRoot(document.getElementById("agent-panel-root"));
      });
      return () => cancelAnimationFrame(frame);
    } else {
      setAgentPanelRoot(null);
    }
  }, [rightPanelOpen]);

  return (
    <HighlightProvider>
    <Box
      sx={{
        height: "100%",
        minWidth: 0,
        display: "flex",
        flexDirection: isVertical ? "column" : "row",
        gap: 0,
        overflow: "hidden",
      }}
    >
      {/* Portal: Agent panel toggle button in the AppBar toolbar */}
      {!isVertical &&
        rpToolbar &&
        !rightPanelOpen &&
        createPortal(
          <IconButton
            size="small"
            onClick={() => setRightPanelOpen(true)}
            title="Open agent panel"
            sx={{
              color: "text.primary",
            }}
          >
            <BrainIcon />
          </IconButton>,
          rpToolbar,
        )}

      {/* Editor column */}
      <Box
        sx={{
          flex: 1,
          display: "flex",
          flexDirection: "column",
          gap: 2,
          minWidth: 0,
          minHeight: 0,
          overflow: "hidden",
          p: 2,
        }}
      >
        {/* Toolbar: title + view toggle + action buttons */}
        <Stack direction="row" sx={{ gap: 2, alignItems: "center" }}>
          <Box
            sx={{
              flex: 1,
              background: `linear-gradient(135deg, ${theme.palette.primary.main}10 0%, ${theme.palette.secondary.main}20 100%)`,
              borderRadius: "12px",
              border: "1px solid " + theme.palette.divider,
            }}
          >
            <TextField
              placeholder="Document Title"
              fullWidth
              size="small"
              sx={{
                height: "50px",
                display: "flex",
                alignItems: "center",
                "& .MuiInputBase-root": {
                  height: "100%",
                  fontSize: "1.5rem",
                  fontWeight: 600,
                },
                "& .MuiOutlinedInput-root": {
                  "& fieldset": { border: "none" },
                },
              }}
              value={title}
              onChange={(e) => setTitle(e.target.value)}
            />
          </Box>
          {contentJson && (
            <ViewModeToggle mode={viewMode} onChange={setViewMode} />
          )}
          <Stack
            direction="row"
            sx={{ gap: 1, display: buttons.length ? "flex" : "none" }}
          >
            {buttons.map((btn: any) => {
              const IconComponent = btn.icon;
              return (
                <Box
                  key={btn.id}
                  onMouseEnter={() => setHoveredIcon(btn.id)}
                  onMouseLeave={() => setHoveredIcon(null)}
                >
                  <Button
                    onClick={btn.handler}
                    variant="contained"
                    sx={{ ...buttonSx, position: "relative" }}
                  >
                    <Box
                      sx={{
                        display: "flex",
                        flexDirection: "column",
                        alignItems: "center",
                        justifyContent: "center",
                        width: "100%",
                        height: "100%",
                      }}
                    >
                      <IconComponent fontSize="small" />
                    </Box>
                    {hoveredIcon === btn.id && (
                      <Typography
                        variant="caption"
                        fontWeight={850}
                        sx={{
                          position: "absolute",
                          top: "5px",
                          fontSize: "0.65rem",
                          color: "background.default",
                          lineHeight: 1,
                          whiteSpace: "nowrap",
                        }}
                      >
                        {btn.label}
                      </Typography>
                    )}
                  </Button>
                </Box>
              );
            })}
          </Stack>
        </Stack>

        {/* Editor body */}
        <Box
          sx={{
            flex: 1,
            minHeight: 0,
            backgroundColor: theme.palette.background.paper,
            borderRadius: "12px",
            p: 2,
            border: "1px solid" + theme.palette.divider,
            overflow: "auto",
          }}
        >
          {contentJson ? (
            // Structured document — render based on view mode
            viewMode === "rich" ? (
              <RichView contentJson={contentJson} attachments={attachments} />
            ) : viewMode === "json" ? (
              <JsonView
                contentJson={contentJson}
                onChange={handleContentJsonChange}
              />
            ) : (
              <LatexView contentJson={contentJson} />
            )
          ) : (
            // Legacy plain text editor
            <TextField
              placeholder="Start writing your document..."
              variant="standard"
              fullWidth
              multiline
              minRows={10}
              value={content}
              onChange={(e) => setContent(e.target.value)}
              sx={{ mt: 0 }}
            />
          )}

          <Box
            sx={{
              mt: 2,
              pt: 2,
              borderTop: "1px solid " + theme.palette.divider,
            }}
          >
            <Stack
              direction="row"
              sx={{
                alignItems: "center",
                justifyContent: "space-between",
                mb: 1,
              }}
            >
              <Typography variant="subtitle2">Attachments</Typography>
              <Button
                variant="outlined"
                size="small"
                component="label"
                startIcon={<AttachFileIcon />}
                disabled={!id || isUploadingAttachment}
              >
                {isUploadingAttachment ? "Uploading..." : "Upload"}
                <input hidden type="file" onChange={handleAttachmentUpload} />
              </Button>
            </Stack>

            {isLoadingAttachments ? (
              <Typography variant="body2" color="text.secondary">
                Loading attachments...
              </Typography>
            ) : attachments.length === 0 ? (
              <Typography variant="body2" color="text.secondary">
                No attachments yet.
              </Typography>
            ) : (
              <Stack spacing={1}>
                {attachments.map((attachment) => (
                  <Box
                    key={attachment.id}
                    sx={{
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "space-between",
                      border: "1px solid " + theme.palette.divider,
                      borderRadius: "8px",
                      px: 1.5,
                      py: 1,
                    }}
                  >
                    <Box sx={{ minWidth: 0 }}>
                      <Typography variant="body2" noWrap>
                        {attachment.filename}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        {formatFileSize(attachment.size)}
                      </Typography>
                    </Box>
                    <Button
                      size="small"
                      color="error"
                      startIcon={<DeleteIcon />}
                      onClick={() => handleRemoveAttachment(attachment.id)}
                    >
                      Remove
                    </Button>
                  </Box>
                ))}
              </Stack>
            )}
          </Box>
        </Box>
      </Box>
      {/* End editor column */}

      {/* Portal: Agent panel into MainPage's right panel slot (horizontal mode) */}
      {!isVertical &&
        rightPanelOpen &&
        agentPanelRoot &&
        createPortal(
          <AgentPanel
            content={
              contentJson ? contentJsonToPlainText(contentJson) : content
            }
            title={title}
            documentId={id ? Number(id) : undefined}
            activeTab={agentTab}
            onTabChange={setAgentTab}
            onCollapse={() => setRightPanelOpen(false)}
          />,
          agentPanelRoot,
        )}

      {/* Vertical drag handle */}
      {isVertical && (
        <Box
          onMouseDown={handleVerticalDragMouseDown}
          sx={{
            height: 8,
            flexShrink: 0,
            cursor: "row-resize",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            userSelect: "none",
            "&:hover > div": { bgcolor: "primary.main", opacity: 1 },
          }}
        >
          <Box
            sx={{
              height: 2,
              width: "100%",
              bgcolor: "divider",
              borderRadius: 999,
              opacity: 0,
              transition: "opacity 0.15s, background-color 0.15s",
            }}
          />
        </Box>
      )}

      {/* Inline agent panel (vertical mode) */}
      {isVertical && (
        <Box
          sx={{
            height: agentPanelHeight,
            minHeight: 150,
            minWidth: 0,
            flexShrink: 0,
            overflow: "hidden",
            px: 2,
            pb: 3,
          }}
        >
          <AgentPanel
            content={
              contentJson ? contentJsonToPlainText(contentJson) : content
            }
            title={title}
            documentId={id ? Number(id) : undefined}
            activeTab={agentTab}
            onTabChange={setAgentTab}
          />
        </Box>
      )}
    </Box>
    </HighlightProvider>
  );
};
