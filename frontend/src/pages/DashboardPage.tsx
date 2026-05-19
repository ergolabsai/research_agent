// SPDX-FileCopyrightText: 2026 Chelsea Liekhus-Schmaltz and Johnathon Barhydt
//
// SPDX-License-Identifier: AGPL-3.0-only

import {
  Box,
  Typography,
  Grid,
  Button,
  Stack,
  List,
  CircularProgress,
  Alert,
  useTheme,
} from "@mui/material";
import { Add as AddIcon } from "@mui/icons-material";
import { useNavigate } from "react-router-dom";
import { useEffect, useState } from "react";
import { documentsAPI, workspacesAPI } from "../api";
import { useDialogs } from "./MainPage";
import { DocumentItem } from "../components/DocumentItem";
import { WorkspaceItem } from "../components/WorkspaceItem";
import { useDragPreview } from "../hooks/useDragPreview";

interface Document {
  id: number;
  title: string;
  created_at: string;
  updated_at: string;
  workspace_id?: number | null;
}

interface Workspace {
  id: number;
  name: string;
  created_at: string;
  created_by: number;
  documents?: Document[];
}

export const DashboardPage = () => {
  const theme = useTheme();
  const navigate = useNavigate();
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
  const [error, setError] = useState<string | null>(null);
  const [docMenuAnchor, setDocMenuAnchor] = useState<{
    [key: number]: HTMLElement | null;
  }>({});
  const [wsMenuAnchor, setWsMenuAnchor] = useState<{
    [key: number]: HTMLElement | null;
  }>({});
  const [draggedDocId, setDraggedDocId] = useState<number | null>(null);
  const [refreshKey, setRefreshKey] = useState(0);
  const { showDragPreview, hideDragPreview, setDragImage, DragPreviewPortal } =
    useDragPreview();

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        const [docsRes, wsRes] = await Promise.all([
          documentsAPI.list(),
          workspacesAPI.list(),
        ]);

        const allDocs = docsRes.data || [];
        const allWorkspaces = wsRes.data || [];

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

        const privateDocs = allDocs.filter(
          (doc: Document) => !doc.workspace_id,
        );

        setDocuments(privateDocs);
        setWorkspaces(workspacesWithDocs);
        setError(null);
      } catch (err) {
        setError("Failed to load data");
        setDocuments([]);
        setWorkspaces([]);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [refreshKey]);

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

  const handleDeleteWorkspace = (wsId: number) => {
    workspacesAPI.delete(wsId);
    setWorkspaces(workspaces.filter((w) => w.id !== wsId));
    handleWsMenuClose(wsId);
  };

  const handleDocumentDragStart = (docId: number, e: React.DragEvent) => {
    setDraggedDocId(docId);

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
    const element = e.currentTarget as HTMLElement;
    element.style.backgroundColor = "rgba(33, 150, 243, 0.08)";
    element.style.borderRadius = "12px";
  };

  const handleDocumentsDragLeave = (e: React.DragEvent) => {
    (e.currentTarget as HTMLElement).style.backgroundColor = "transparent";
  };

  const handleDocumentsDrop = async (e: React.DragEvent) => {
    e.preventDefault();
    (e.currentTarget as HTMLElement).style.backgroundColor = "transparent";

    if (!draggedDocId) return;

    try {
      await documentsAPI.moveToWorkspace(draggedDocId, null);
      setDraggedDocId(null);
      setRefreshKey((prev) => prev + 1);
    } catch (err) {
      console.error("Failed to move document to Documents area:", err);
      setDraggedDocId(null);
    }
  };

  const handleWorkspaceDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    (e.currentTarget as HTMLElement).style.backgroundColor =
      "rgba(100, 200, 255, 0.1)";
  };

  const handleWorkspaceDragLeave = (e: React.DragEvent) => {
    (e.currentTarget as HTMLElement).style.backgroundColor = "transparent";
  };

  const handleWorkspaceDrop = async (wsId: number, e: React.DragEvent) => {
    e.preventDefault();
    (e.currentTarget as HTMLElement).style.backgroundColor = "transparent";

    if (!draggedDocId) return;

    try {
      await documentsAPI.moveToWorkspace(draggedDocId, wsId);
      setDraggedDocId(null);
      setRefreshKey((prev) => prev + 1);
    } catch (err) {
      console.error("Failed to add document to workspace via drag-drop");
      setDraggedDocId(null);
    }
  };

  if (loading) {
    return (
      <Box
        sx={{
          display: "flex",
          justifyContent: "center",
          alignItems: "center",
          minHeight: "400px",
        }}
      >
        <CircularProgress />
      </Box>
    );
  }

  return (
    <>
      <Box
        sx={{
          border: `1px solid ${theme.palette.divider}`,
          borderRadius: "20px",
          bgcolor: theme.palette.background.paper,
          height: "100%",
          p: 4,
        }}
      >
        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}

        <Box sx={{ mb: 4 }}>
          <Stack
            direction="row"
            alignItems="center"
            justifyContent="space-between"
            sx={{ mb: 1 }}
          >
            <Typography
              variant="h2"
              sx={{
                fontWeight: 700,
              }}
            >
              Documents
            </Typography>
            <Button
              variant="contained"
              color="primary"
              startIcon={<AddIcon />}
              onClick={() => setNewDocDialogOpen(true)}
            >
              New Document
            </Button>
          </Stack>
          <Typography
            variant="body1"
            sx={{
              color: "text.secondary",
            }}
          >
            Access and manage your documents
          </Typography>
        </Box>

        <Box
          onDragOver={handleDocumentsDragOver}
          onDragLeave={handleDocumentsDragLeave}
          onDrop={handleDocumentsDrop}
          sx={{ borderRadius: "12px" }}
        >
          <Grid container spacing={2} sx={{ mb: 4 }}>
            {documents.length === 0 ? (
              <Grid item xs={12}>
                <Typography variant="body2" color="text.secondary">
                  No documents yet. Create one to get started!
                </Typography>
              </Grid>
            ) : (
              documents.map((doc) => (
                <Grid item xs={12} sm={6} md={4} key={doc.id}>
                  <DocumentItem
                    doc={doc}
                    variant="dashboard"
                    draggable
                    onDragStart={(e) => handleDocumentDragStart(doc.id, e)}
                    onDragEnd={handleDocumentDragEnd}
                    onClick={() => navigate(`/app/editor/${doc.id}`)}
                    menuAnchorEl={docMenuAnchor[doc.id]}
                    onMenuOpen={(e) => handleDocMenuOpen(doc.id, e)}
                    onMenuClose={() => handleDocMenuClose(doc.id)}
                    onShare={() => openShareDialog(doc.id, "document")}
                    onDelete={() => handleDeleteDocument(doc.id)}
                  />
                </Grid>
              ))
            )}
          </Grid>
        </Box>

        <Box sx={{ mt: 6, mb: 4 }}>
          <Stack
            direction="row"
            alignItems="center"
            justifyContent="space-between"
            sx={{ mb: 2 }}
          >
            <Typography
              variant="h3"
              sx={{
                fontWeight: 700,
              }}
            >
              Your Workspaces
            </Typography>
            <Button
              variant="outlined"
              color="primary"
              startIcon={<AddIcon />}
              onClick={() => setNewWorkspaceDialogOpen(true)}
            >
              New Workspace
            </Button>
          </Stack>

          <Grid container spacing={2}>
            {workspaces.length === 0 ? (
              <Grid item xs={12}>
                <Typography variant="body2" color="text.secondary">
                  No workspaces yet. Create one to organize your documents!
                </Typography>
              </Grid>
            ) : (
              workspaces.map((ws) => (
                <Grid item xs={12} sm={6} md={4} key={ws.id}>
                  <WorkspaceItem
                    workspace={ws}
                    variant="dashboard"
                    draggedDocId={draggedDocId}
                    onDragOver={handleWorkspaceDragOver}
                    onDragLeave={handleWorkspaceDragLeave}
                    onDrop={(e) => handleWorkspaceDrop(ws.id, e)}
                    menuAnchorEl={wsMenuAnchor[ws.id]}
                    onMenuOpen={(e) => handleWsMenuOpen(ws.id, e)}
                    onMenuClose={() => handleWsMenuClose(ws.id)}
                    onAddMember={() => openAddMemberDialog(ws.id)}
                    onAddDocument={() => openAddDocDialog(ws.id)}
                    onShare={() => openShareDialog(ws.id, "workspace")}
                    onDelete={() => handleDeleteWorkspace(ws.id)}
                    documents={
                      ws.documents?.length ? (
                        <List sx={{ p: 0 }}>
                          {ws.documents.map((doc) => (
                            <DocumentItem
                              key={doc.id}
                              doc={doc}
                              variant="workspace"
                              draggable
                              onDragStart={(e) =>
                                handleDocumentDragStart(doc.id, e)
                              }
                              onDragEnd={handleDocumentDragEnd}
                              onClick={() => navigate(`/app/editor/${doc.id}`)}
                              menuAnchorEl={docMenuAnchor[doc.id]}
                              onMenuOpen={(e) => handleDocMenuOpen(doc.id, e)}
                              onMenuClose={() => handleDocMenuClose(doc.id)}
                              onShare={() =>
                                openShareDialog(doc.id, "document")
                              }
                              onDelete={() => handleDeleteDocument(doc.id)}
                            />
                          ))}
                        </List>
                      ) : undefined
                    }
                    emptyStateText="No documents yet. Drag or add one."
                  />
                </Grid>
              ))
            )}
          </Grid>
        </Box>
      </Box>
      {DragPreviewPortal}
    </>
  );
};
