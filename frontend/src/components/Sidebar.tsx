import {
  Box,
  Stack,
  Typography,
  List,
  Divider,
  useTheme,
  IconButton,
  Skeleton,
} from "@mui/material";
import {
  Add as PlusIcon,
  ChevronLeft as ChevronLeftIcon,
  Science as ValidateIcon,
} from "@mui/icons-material";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { useEffect, useState } from "react";
import { documentsAPI, workspacesAPI } from "../api";
import { useDialogs } from "../pages/MainPage";
import { DocumentItem } from "./DocumentItem";
import { WorkspaceItem } from "./WorkspaceItem";
import { useDragPreview } from "../hooks/useDragPreview";

interface Document {
  id: number;
  title: string;
  workspace_id?: number | null;
}

interface Workspace {
  id: number;
  name: string;
  documents?: Document[];
}

interface SidebarProps {
  onCollapse?: (collapsed: boolean) => void;
  isCollapsed?: boolean;
  refreshKey?: number;
}

export const Sidebar = ({ onCollapse, isCollapsed = false }: SidebarProps) => {
  const theme = useTheme();
  const navigate = useNavigate();
  const { user } = useAuth();
  const {
    setNewDocDialogOpen,
    setNewWorkspaceDialogOpen,
    openShareDialog,
    openAddMemberDialog,
    openAddDocDialog,
  } = useDialogs();
  const [documents, setDocuments] = useState<Document[]>([]);
  const [workspaces, setWorkspaces] = useState<Workspace[]>([]);
  const [loading, setLoading] = useState(true);
  const [docMenuAnchor, setDocMenuAnchor] = useState<{
    [key: number]: HTMLElement | null;
  }>({});
  const [wsMenuAnchor, setWsMenuAnchor] = useState<{
    [key: number]: HTMLElement | null;
  }>({});
  const [draggedDocId, setDraggedDocId] = useState<number | null>(null);
  const [sidebarRefreshKey, setSidebarRefreshKey] = useState(0);
  const { showDragPreview, hideDragPreview, setDragImage, DragPreviewPortal } =
    useDragPreview();

  useEffect(() => {
    const loadData = async () => {
      try {
        setLoading(true);
        const [docsRes, wsRes] = await Promise.all([
          documentsAPI.list(),
          workspacesAPI.list(),
        ]);

        const allDocs = docsRes.data || [];
        const allWorkspaces = wsRes.data || [];

        // Fetch documents for each workspace
        const workspacesWithDocs = await Promise.all(
          allWorkspaces.map(async (ws: Workspace) => {
            try {
              const wsDocsRes = await workspacesAPI.documents(ws.id);
              return { ...ws, documents: wsDocsRes.data || [] };
            } catch (err) {
              return { ...ws, documents: [] };
            }
          }),
        );

        // Filter documents: only show docs without workspace_id in main list
        const privateDocs = allDocs.filter(
          (doc: Document) => !doc.workspace_id,
        );

        setDocuments(privateDocs);
        setWorkspaces(workspacesWithDocs);
      } catch (err) {
        setDocuments([]);
        setWorkspaces([]);
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, [sidebarRefreshKey]);

  // Poll for updates every 3 seconds
  useEffect(() => {
    const interval = setInterval(async () => {
      try {
        const [docsRes, wsRes] = await Promise.all([
          documentsAPI.list(),
          workspacesAPI.list(),
        ]);

        const allDocs = docsRes.data || [];
        const allWorkspaces = wsRes.data || [];

        // Fetch documents for each workspace
        const workspacesWithDocs = await Promise.all(
          allWorkspaces.map(async (ws: Workspace) => {
            try {
              const wsDocsRes = await workspacesAPI.documents(ws.id);
              return { ...ws, documents: wsDocsRes.data || [] };
            } catch (err) {
              return { ...ws, documents: [] };
            }
          }),
        );

        // Filter documents: only show docs without workspace_id in main list
        const privateDocs = allDocs.filter(
          (doc: Document) => !doc.workspace_id,
        );

        setDocuments(privateDocs);
        setWorkspaces(workspacesWithDocs);
      } catch (err) {
        // Silently fail on polling errors
      }
    }, 10);

    return () => clearInterval(interval);
  }, []);

  const handleDocMenuOpen = (docId: number, e: React.MouseEvent) => {
    e.stopPropagation();
    setDocMenuAnchor({
      ...docMenuAnchor,
      [docId]: e.currentTarget as HTMLElement,
    });
  };

  const handleDocMenuClose = (docId: number) => {
    setDocMenuAnchor({ ...docMenuAnchor, [docId]: null });
  };

  const handleDeleteDocument = (docId: number) => {
    documentsAPI.delete(docId);
    setDocuments(documents.filter((d) => d.id !== docId));
    handleDocMenuClose(docId);
  };

  const handleWsMenuOpen = (wsId: number, e: React.MouseEvent) => {
    e.stopPropagation();
    setWsMenuAnchor({
      ...wsMenuAnchor,
      [wsId]: e.currentTarget as HTMLElement,
    });
  };

  const handleWsMenuClose = (wsId: number) => {
    setWsMenuAnchor({ ...wsMenuAnchor, [wsId]: null });
  };

  const handleDocumentDragStart = (docId: number, e: React.DragEvent) => {
    setDraggedDocId(docId);

    // Find document title (check both documents list and workspace documents)
    let docTitle = "Document";
    const doc = documents.find((d) => d.id === docId);
    if (doc) {
      docTitle = doc.title;
    } else {
      for (const ws of workspaces) {
        const wsDoc = ws.documents?.find((d) => d.id === docId);
        if (wsDoc) {
          docTitle = wsDoc.title;
          break;
        }
      }
    }

    showDragPreview(docTitle);
    setDragImage(e);
  };

  const handleDocumentDragEnd = () => {
    setDraggedDocId(null);
    hideDragPreview();
  };

  const handleDocumentsDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    const element = e.currentTarget as HTMLElement;
    element.style.backgroundColor = "rgba(33, 150, 243, 0.08)";
    element.style.borderRadius = "8px";
  };

  const handleDocumentsDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    (e.currentTarget as HTMLElement).style.backgroundColor = "transparent";
  };

  const handleDocumentsDrop = async (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    (e.currentTarget as HTMLElement).style.backgroundColor = "transparent";

    if (!draggedDocId) return;

    try {
      await documentsAPI.moveToWorkspace(draggedDocId, null);
      setDraggedDocId(null);
      setSidebarRefreshKey((prev) => prev + 1);
    } catch (err) {
      console.error("Failed to move document to Documents area:", err);
      setDraggedDocId(null);
    }
  };

  const handleWorkspaceDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    const element = e.currentTarget as HTMLElement;
    element.style.backgroundColor = "rgba(33, 150, 243, 0.1)";
    element.style.borderRadius = "8px";
  };

  const handleWorkspaceDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    (e.currentTarget as HTMLElement).style.backgroundColor = "transparent";
  };

  const handleWorkspaceDrop = async (wsId: number, e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    (e.currentTarget as HTMLElement).style.backgroundColor = "transparent";

    if (!draggedDocId) return;

    try {
      await documentsAPI.moveToWorkspace(draggedDocId, wsId);
      setDraggedDocId(null);
      setSidebarRefreshKey((prev) => prev + 1);
    } catch (err) {
      console.error("Failed to move document to workspace:", err);
      setDraggedDocId(null);
    }
  };

  const handleDeleteWorkspace = (wsId: number) => {
    workspacesAPI.delete(wsId);
    setWorkspaces(workspaces.filter((w) => w.id !== wsId));
    handleWsMenuClose(wsId);
  };

  return (
    <>
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
        }}
      >
        {/* Header */}
        <Stack
          direction="row"
          sx={{
            justifyContent: "space-between",
            alignItems: "center",
            pl: 1.5,
          }}
        >
          {!isCollapsed && (
            <Typography
              variant="h3"
              color="primary"
              onClick={() => navigate("/app/dashboard")}
              sx={{
                fontSize: "1.3rem",
                fontWeight: 700,
                cursor: "pointer",
                "&:hover": {
                  opacity: 0.8,
                },
                transition: "opacity 0.2s ease",
              }}
            >
              Advisor
            </Typography>
          )}
          <IconButton
            size="small"
            onClick={() => onCollapse?.(!isCollapsed)}
            sx={{ color: "text.primary", mr: 1 }}
            title={isCollapsed ? "Expand" : "Collapse"}
          >
            <ChevronLeftIcon
              sx={{
                transform: isCollapsed ? "rotate(180deg)" : "rotate(0deg)",
                transition: "transform 0.3s ease",
              }}
              color="primary"
            />
          </IconButton>
        </Stack>
        <Divider />
        {/* User Info */}
        {user && (
          <Box
            sx={{
              p: 0.5,
              pl: 1.5,
              background: `linear-gradient(135deg, ${theme.palette.primary.main}10 0%, ${theme.palette.secondary.main}10 100%)`,
            }}
          >
            <Typography
              variant="body2"
              sx={{ fontWeight: 600, color: "text.primary" }}
            >
              {user.username || user.email}
            </Typography>
            <Typography variant="caption" sx={{ color: "text.secondary" }}>
              {user.email}
            </Typography>
          </Box>
        )}
        <Divider />
        {/* Documents Section */}
        <Box
          onDragOver={handleDocumentsDragOver}
          onDragLeave={handleDocumentsDragLeave}
          onDrop={handleDocumentsDrop}
        >
          <Stack
            direction="row"
            sx={{
              alignItems: "center",
              justifyContent: "space-between",
              px: 1.5,
              mt: 0.5,
            }}
          >
            <Typography
              variant="caption"
              sx={{
                fontWeight: 700,
                color: "text.secondary",
                textTransform: "uppercase",
                fontSize: "0.7rem",
              }}
            >
              Documents
            </Typography>
            <IconButton size="small" onClick={() => setNewDocDialogOpen(true)}>
              <PlusIcon color="primary" sx={{ fontSize: "0.9rem" }} />
            </IconButton>
          </Stack>

          <List sx={{ p: 0 }}>
            {loading ? (
              <>
                <Skeleton
                  variant="text"
                  width="100%"
                  height={36}
                  sx={{ mb: 0.5 }}
                />
                <Skeleton variant="text" width="100%" height={36} />
              </>
            ) : documents.length === 0 ? (
              <Typography
                variant="caption"
                sx={{
                  color: "text.secondary",
                  display: "block",
                  pl: 1.5,
                }}
              >
                No documents
              </Typography>
            ) : (
              documents.map((doc) => (
                <DocumentItem
                  key={doc.id}
                  doc={doc}
                  variant="sidebar"
                  draggable
                  isActive={location.pathname === `/app/editor/${doc.id}`}
                  onDragStart={(e) => handleDocumentDragStart(doc.id, e)}
                  onDragEnd={handleDocumentDragEnd}
                  onClick={() => navigate(`/app/editor/${doc.id}`)}
                  menuAnchorEl={docMenuAnchor[doc.id]}
                  onMenuOpen={(e) => handleDocMenuOpen(doc.id, e)}
                  onMenuClose={() => handleDocMenuClose(doc.id)}
                  onShare={() => openShareDialog(doc.id, "document")}
                  onDelete={() => handleDeleteDocument(doc.id)}
                />
              ))
            )}
          </List>
        </Box>

        <Divider />

        {/* Validate Section */}
        {!isCollapsed && (
          <Box
            onClick={() => navigate("/app/validate")}
            sx={{
              display: "flex",
              alignItems: "center",
              gap: 1,
              px: 1.5,
              py: 1,
              cursor: "pointer",
              "&:hover": {
                backgroundColor: theme.palette.action.hover,
              },
              transition: "background-color 0.2s ease",
            }}
          >
            <ValidateIcon color="primary" sx={{ fontSize: "1rem" }} />
            <Typography
              variant="body2"
              sx={{ fontWeight: 600, color: "text.primary" }}
            >
              Validate Paper
            </Typography>
          </Box>
        )}

        <Divider />

        {/* Workspaces Section */}
        <Box sx={{ mt: 1 }}>
          <Stack
            direction="row"
            sx={{
              alignItems: "center",
              justifyContent: "space-between",
              px: 1.5,
            }}
          >
            <Typography
              variant="caption"
              sx={{
                fontWeight: 700,
                color: "text.secondary",
                textTransform: "uppercase",
                fontSize: "0.7rem",
              }}
            >
              Workspaces
            </Typography>
            <IconButton
              size="small"
              onClick={() => setNewWorkspaceDialogOpen(true)}
            >
              <PlusIcon color="primary" sx={{ fontSize: "0.9rem" }} />
            </IconButton>
          </Stack>

          <List sx={{ p: 0 }}>
            {loading ? (
              <>
                <Skeleton
                  variant="text"
                  width="100%"
                  height={36}
                  sx={{ mb: 0.5 }}
                />
                <Skeleton variant="text" width="100%" height={36} />
              </>
            ) : workspaces.length === 0 ? (
              <Typography
                variant="caption"
                sx={{
                  color: "text.secondary",
                  display: "block",
                  pl: 1.5,
                }}
              >
                No workspaces
              </Typography>
            ) : (
              workspaces.map((ws) => (
                <WorkspaceItem
                  key={ws.id}
                  workspace={ws}
                  variant="sidebar"
                  draggedDocId={draggedDocId}
                  onDragOver={handleWorkspaceDragOver}
                  onDragLeave={handleWorkspaceDragLeave}
                  onDrop={(e) => handleWorkspaceDrop(ws.id, e)}
                  menuAnchorEl={wsMenuAnchor[ws.id]}
                  onMenuOpen={(e) => {
                    e.stopPropagation();
                    handleWsMenuOpen(ws.id, e);
                  }}
                  onMenuClose={() => handleWsMenuClose(ws.id)}
                  onAddMember={() => openAddMemberDialog(ws.id)}
                  onAddDocument={() => openAddDocDialog(ws.id)}
                  onShare={() => openShareDialog(ws.id, "workspace")}
                  onDelete={() => handleDeleteWorkspace(ws.id)}
                  showEmptyAddButton
                  documents={
                    ws.documents?.length
                      ? ws.documents.map((doc) => (
                          <DocumentItem
                            key={doc.id}
                            doc={doc}
                            variant="sidebar"
                            draggable
                            isActive={
                              location.pathname === `/app/editor/${doc.id}`
                            }
                            onDragStart={(e) =>
                              handleDocumentDragStart(doc.id, e)
                            }
                            onDragEnd={handleDocumentDragEnd}
                            onClick={() => navigate(`/app/editor/${doc.id}`)}
                            menuAnchorEl={docMenuAnchor[doc.id]}
                            onMenuOpen={(e) => handleDocMenuOpen(doc.id, e)}
                            onMenuClose={() => handleDocMenuClose(doc.id)}
                            onShare={() => openShareDialog(doc.id, "document")}
                            onDelete={() => handleDeleteDocument(doc.id)}
                          />
                        ))
                      : undefined
                  }
                />
              ))
            )}
          </List>
        </Box>
      </Stack>
      {DragPreviewPortal}
    </>
  );
};
