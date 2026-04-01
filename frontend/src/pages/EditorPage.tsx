import { useParams } from "react-router-dom";
import {
  Box,
  TextField,
  useTheme,
  Stack,
  Button,
  Typography,
  Tooltip,
} from "@mui/material";
import { useState, useEffect, useRef } from "react";
import { createPortal } from "react-dom";
import { documentsAPI } from "../api";
import { Attachment } from "../types";
import {
  // Functions as MathIcon,
  // Psychology as LogicIcon,
  // LineStyle as FormatterIcon,
  // LocalLibrary as LibrarianIcon,
  // Insights as PlotsIcon,
  AttachFile as AttachFileIcon,
  Delete as DeleteIcon,
  VerticalSplit as AgentPanelIcon,
} from "@mui/icons-material";
import { AgentPanel, AgentTab } from "../components/AgentPanel";

export const EditorPage = () => {
  const { id } = useParams();
  const theme = useTheme();
  const [title, setTitle] = useState("");
  const [content, setContent] = useState("");
  const [hoveredIcon, setHoveredIcon] = useState<string | null>(null);
  const [isLoaded, setIsLoaded] = useState(false);
  const [attachments, setAttachments] = useState<Attachment[]>([]);
  const [isLoadingAttachments, setIsLoadingAttachments] = useState(false);
  const [isUploadingAttachment, setIsUploadingAttachment] = useState(false);

  // Right agent panel state
  const [rightPanelOpen, setRightPanelOpen] = useState(false);
  const [rightPanelWidth, setRightPanelWidth] = useState(500);
  const [agentTab, setAgentTab] = useState<AgentTab>("validate");
  const dragRef = useRef(false);
  const startXRef = useRef(0);
  const startWidthRef = useRef(0);
  const rightPanelWidthRef = useRef(400);

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
        setContent(response.data.content || "");
        setTitle(response.data.title || "");
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

  useEffect(() => {
    if (!isLoaded) return;
    const saveDocument = async () => {
      if (!id) return;
      try {
        await documentsAPI.update(Number(id), title, content);
      } catch (err) {
        console.error("Failed to save document:", err);
      }
    };
    saveDocument();
  }, [content, title, isLoaded]);

  // Drag-to-resize handler
  const handleDragMouseDown = (e: React.MouseEvent) => {
    e.preventDefault();
    dragRef.current = true;
    startXRef.current = e.clientX;
    startWidthRef.current = rightPanelWidthRef.current;
  };

  useEffect(() => {
    const onMouseMove = (e: MouseEvent) => {
      if (!dragRef.current) return;
      const delta = startXRef.current - e.clientX;
      const newWidth = Math.min(
        1400,
        Math.max(220, startWidthRef.current + delta),
      );
      setRightPanelWidth(newWidth);
      rightPanelWidthRef.current = newWidth;
    };
    const onMouseUp = () => {
      dragRef.current = false;
    };
    window.addEventListener("mousemove", onMouseMove);
    window.addEventListener("mouseup", onMouseUp);
    return () => {
      window.removeEventListener("mousemove", onMouseMove);
      window.removeEventListener("mouseup", onMouseUp);
    };
  }, []);

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

  return (
    <Box
      sx={{
        height: "calc(100vh - 100px)",
        display: "flex",
        flexDirection: "row",
        gap: 0,
        overflow: "hidden",
      }}
    >
      {/* Portal: Agents toggle button in the AppBar toolbar */}
      {rpToolbar &&
        createPortal(
          <Tooltip
            title={rightPanelOpen ? "Close agent panel" : "Open agent panel"}
          >
            <span>
              <Button
                size="small"
                variant={rightPanelOpen ? "contained" : "outlined"}
                startIcon={<AgentPanelIcon fontSize="small" />}
                onClick={() => setRightPanelOpen((v) => !v)}
                sx={{
                  height: 32,
                  fontSize: "0.75rem",
                  fontWeight: 600,
                  textTransform: "none",
                  borderRadius: "8px",
                  px: 1.5,
                }}
              >
                Agents
              </Button>
            </span>
          </Tooltip>,
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
          overflow: "hidden",
        }}
      >
        {/* Toolbar: title + action buttons */}
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
                height: "56px",
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
          <Stack direction="row" sx={{ gap: 1 }}>
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
            backgroundColor: theme.palette.background.paper,
            borderRadius: "12px",
            p: 2,
            border: "1px solid" + theme.palette.divider,
            overflow: "auto",
          }}
        >
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

      {/* Drag handle */}
      {rightPanelOpen && (
        <Box
          onMouseDown={handleDragMouseDown}
          sx={{
            width: 8,
            flexShrink: 0,
            cursor: "col-resize",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            userSelect: "none",
            "&:hover > div": { bgcolor: "primary.main", opacity: 1 },
          }}
        >
          <Box
            sx={{
              width: 2,
              height: "100%",
              bgcolor: "divider",
              borderRadius: 999,
              opacity: 0,
              transition: "opacity 0.15s, background-color 0.15s",
            }}
          />
        </Box>
      )}

      {/* Agent panel */}
      {rightPanelOpen && (
        <Box
          sx={{
            width: rightPanelWidth,
            flexShrink: 0,
            overflow: "hidden",
          }}
        >
          <AgentPanel
            content={content}
            title={title}
            documentId={id ? Number(id) : undefined}
            activeTab={agentTab}
            onTabChange={setAgentTab}
            onCollapse={() => setRightPanelOpen(false)}
          />
        </Box>
      )}
    </Box>
  );
};
