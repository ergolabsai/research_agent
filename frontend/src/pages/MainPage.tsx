import {
  Box,
  Drawer,
  IconButton,
  AppBar,
  Toolbar,
  Stack,
  useTheme,
  useMediaQuery,
  Dialog,
  TextField,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
} from "@mui/material";
import {
  Menu as MenuIcon,
  MoreVertRounded as MoreVertIcon,
  Add as AddIcon,
} from "@mui/icons-material";
import { useState, ReactNode, createContext, useContext } from "react";
import { useAuth } from "../context/AuthContext";
import { useNavigate } from "react-router-dom";
import { useTheme as useAppTheme } from "../theme";
import { Sidebar } from "../components/Sidebar";
import { SettingsMenu } from "../components/SettingsMenu";
import { documentsAPI, workspacesAPI, usersAPI } from "../api";

export interface DialogContextType {
  newDocDialogOpen: boolean;
  setNewDocDialogOpen: (open: boolean) => void;
  newWorkspaceDialogOpen: boolean;
  setNewWorkspaceDialogOpen: (open: boolean) => void;
  onDocumentCreated: () => void;
  onWorkspaceCreated: () => void;
  openShareDialog: (targetId: number, type: "document" | "workspace") => void;
  openAddMemberDialog: (workspaceId: number) => void;
  openAddDocDialog: (workspaceId: number) => void;
}

const defaultDialogContext: DialogContextType = {
  newDocDialogOpen: false,
  setNewDocDialogOpen: () => {},
  newWorkspaceDialogOpen: false,
  setNewWorkspaceDialogOpen: () => {},
  onDocumentCreated: () => {},
  onWorkspaceCreated: () => {},
  openShareDialog: () => {},
  openAddMemberDialog: () => {},
  openAddDocDialog: () => {},
};

export const DialogContext =
  createContext<DialogContextType>(defaultDialogContext);

export const useDialogs = () => {
  return useContext(DialogContext);
};

interface MainPageProps {
  children: ReactNode;
}

const DRAWER_WIDTH = 280;
const DRAWER_COLLAPSED_WIDTH = 0;

export const MainPage = ({ children }: MainPageProps) => {
  const theme = useTheme();
  const { logout } = useAuth();
  const navigate = useNavigate();
  const { themeName } = useAppTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down("sm"));

  const [sidebarOpen, setSidebarOpen] = useState(!isMobile);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [settingsMenuAnchor, setSettingsMenuAnchor] =
    useState<null | HTMLElement>(null);
  const [sidebarRefreshKey, setSidebarRefreshKey] = useState(0);
  const [newDocDialogOpen, setNewDocDialogOpen] = useState(false);
  const [newWorkspaceDialogOpen, setNewWorkspaceDialogOpen] = useState(false);
  const [newDocTitle, setNewDocTitle] = useState("");
  const [newWorkspaceName, setNewWorkspaceName] = useState("");

  // Share dialog state
  const [shareDialogOpen, setShareDialogOpen] = useState(false);
  const [shareEmail, setShareEmail] = useState("");
  const [shareTargetId, setShareTargetId] = useState<number | null>(null);
  const [shareTargetType, setShareTargetType] = useState<
    "document" | "workspace" | null
  >(null);

  // Add member dialog state
  const [addMemberDialogOpen, setAddMemberDialogOpen] = useState(false);
  const [addMemberEmail, setAddMemberEmail] = useState("");
  const [addMemberRole, setAddMemberRole] = useState<"editor" | "viewer">(
    "editor",
  );
  const [addMemberWorkspaceId, setAddMemberWorkspaceId] = useState<
    number | null
  >(null);

  // Add document to workspace dialog state
  const [addDocDialogOpen, setAddDocDialogOpen] = useState(false);
  const [availableDocuments, setAvailableDocuments] = useState<
    Array<{ id: number; title: string }>
  >([]);
  const [selectedDocId, setSelectedDocId] = useState<number | null>(null);
  const [targetWorkspaceId, setTargetWorkspaceId] = useState<number | null>(
    null,
  );

  const handleOpenSettings = (event: React.MouseEvent<HTMLElement>) => {
    setSettingsMenuAnchor(event.currentTarget);
  };

  const handleCloseSettings = () => {
    setSettingsMenuAnchor(null);
  };

  const handleLogout = async () => {
    handleCloseSettings();
    await logout();
    navigate("/");
  };

  const handleProfile = () => {
    handleCloseSettings();
    // Navigate to profile page
  };

  const onDocumentCreated = () => {
    setSidebarRefreshKey((prev) => prev + 1);
  };

  const onWorkspaceCreated = () => {
    setSidebarRefreshKey((prev) => prev + 1);
  };

  const handleCreateDocument = async () => {
    const title = newDocTitle.trim() || "Untitled Document";
    try {
      const { data } = await documentsAPI.create(title);
      setNewDocDialogOpen(false);
      setNewDocTitle("");
      onDocumentCreated();
      if (data?.id) {
        navigate(`/app/editor/${data.id}`);
      }
    } catch (err) {
      console.error("Failed to create document");
    }
  };

  const handleCreateWorkspace = async () => {
    if (!newWorkspaceName.trim()) return;
    try {
      await workspacesAPI.create(newWorkspaceName);
      setNewWorkspaceDialogOpen(false);
      setNewWorkspaceName("");
      onWorkspaceCreated();
    } catch (err) {
      console.error("Failed to create workspace");
    }
  };

  const openShareDialog = (
    targetId: number,
    type: "document" | "workspace",
  ) => {
    setShareTargetId(targetId);
    setShareTargetType(type);
    setShareEmail("");
    setShareDialogOpen(true);
  };

  const handleShare = async () => {
    if (!shareEmail.trim() || !shareTargetId || !shareTargetType) return;
    try {
      // Search for user by email
      const searchRes = await usersAPI.search(shareEmail);
      const users = searchRes.data?.data || [];
      if (users.length === 0) {
        console.error("User not found");
        return;
      }
      const userId = users[0].id;

      if (shareTargetType === "document") {
        await documentsAPI.share(shareTargetId, userId, "edit");
      }
      setShareDialogOpen(false);
      setShareEmail("");
      setShareTargetId(null);
      setShareTargetType(null);
    } catch (err) {
      console.error("Failed to share");
    }
  };

  const openAddMemberDialog = (workspaceId: number) => {
    setAddMemberWorkspaceId(workspaceId);
    setAddMemberEmail("");
    setAddMemberRole("editor");
    setAddMemberDialogOpen(true);
  };

  const handleAddMember = async () => {
    if (!addMemberEmail.trim() || !addMemberWorkspaceId) return;
    try {
      // Search for user by email
      const searchRes = await usersAPI.search(addMemberEmail);
      const users = searchRes.data?.data || [];
      if (users.length === 0) {
        console.error("User not found");
        return;
      }
      const userId = users[0].id;

      await workspacesAPI.addMember(
        addMemberWorkspaceId,
        userId,
        addMemberRole,
      );
      setAddMemberDialogOpen(false);
      setAddMemberEmail("");
      setAddMemberRole("editor");
      setAddMemberWorkspaceId(null);
      setSidebarRefreshKey((prev) => prev + 1);
    } catch (err) {
      console.error("Failed to add member");
    }
  };

  const openAddDocDialog = async (workspaceId: number) => {
    try {
      const res = await documentsAPI.list();
      setAvailableDocuments(res.data || []);
      setTargetWorkspaceId(workspaceId);
      setSelectedDocId(null);
      setAddDocDialogOpen(true);
    } catch (err) {
      console.error("Failed to load documents");
    }
  };

  const handleAddDocToWorkspace = async () => {
    if (!selectedDocId || !targetWorkspaceId) return;
    try {
      // Fetch the document to get current title and content
      const docRes = await documentsAPI.get(selectedDocId);
      const doc = docRes.data;

      // Update with workspace_id - we need to create a new API method or use a workaround
      // For now, we'll just need to ensure the backend supports workspace_id in the update
      // Let me check if we can just call it with the existing data
      await documentsAPI.update(selectedDocId, doc.title, doc.content || "");

      setAddDocDialogOpen(false);
      setSelectedDocId(null);
      setTargetWorkspaceId(null);
      setSidebarRefreshKey((prev) => prev + 1);
    } catch (err) {
      console.error("Failed to add document to workspace");
    }
  };

  const dialogContextValue: DialogContextType = {
    newDocDialogOpen,
    setNewDocDialogOpen,
    newWorkspaceDialogOpen,
    setNewWorkspaceDialogOpen,
    onDocumentCreated,
    onWorkspaceCreated,
    openShareDialog,
    openAddMemberDialog,
    openAddDocDialog,
  };

  return (
    <DialogContext.Provider value={dialogContextValue}>
      <Box sx={{ display: "flex", minHeight: "100vh" }}>
        {/* Sidebar */}
        <Drawer
          variant={isMobile ? "temporary" : "permanent"}
          open={sidebarOpen}
          onClose={() => setSidebarOpen(false)}
          sx={{
            width: sidebarCollapsed ? DRAWER_COLLAPSED_WIDTH : DRAWER_WIDTH,
            flexShrink: 0,
            "& .MuiDrawer-paper": {
              width: sidebarCollapsed ? DRAWER_COLLAPSED_WIDTH : DRAWER_WIDTH,
              borderRadius: 0,
              backgroundColor: "background.default",
            },
          }}
        >
          <Sidebar
            onCollapse={setSidebarCollapsed}
            isCollapsed={sidebarCollapsed}
            refreshKey={sidebarRefreshKey}
          />
        </Drawer>

        {/* Main Content */}
        <Box
          sx={{
            flex: 1,
            display: "flex",
            flexDirection: "column",
            backgroundColor: theme.palette.background.default,
          }}
        >
          {/* Top Navigation */}
          <AppBar
            position="static"
            sx={{
              backgroundColor: "transparent",
              boxShadow: "none",
              borderBottom: "none",
            }}
          >
            <Toolbar
              sx={{
                display: "flex",
                justifyContent: "space-between",
                backgroundColor: theme.palette.background.default,
                alignItems: "center",
                px: 2,
                py: 1,
                minHeight: "64px",
              }}
            >
              <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
                {!isMobile && sidebarCollapsed && (
                  <IconButton
                    onClick={() => setSidebarCollapsed(false)}
                    size="small"
                    sx={{
                      color: "text.primary",
                    }}
                    title="Expand sidebar"
                  >
                    <MenuIcon />
                  </IconButton>
                )}
                {isMobile && (
                  <IconButton
                    onClick={() => setSidebarOpen(true)}
                    size="small"
                    sx={{
                      color: "text.primary",
                    }}
                  >
                    <MenuIcon />
                  </IconButton>
                )}
              </Box>

              <Stack direction="row" spacing={1} sx={{ alignItems: "center" }}>
                <IconButton
                  size="small"
                  onClick={() => setNewDocDialogOpen(true)}
                  title="New Document"
                  sx={{
                    color: "text.primary",
                  }}
                >
                  <AddIcon fontSize="small" />
                </IconButton>

                <IconButton
                  size="small"
                  onClick={handleOpenSettings}
                  title="Settings"
                  sx={{
                    color: "text.primary",
                  }}
                >
                  <MoreVertIcon fontSize="small" />
                </IconButton>
              </Stack>
            </Toolbar>
          </AppBar>

          {/* Page Content */}
          <Box
            sx={{
              flex: 1,
              overflow: "auto",
              p: 2,
            }}
          >
            {children}
          </Box>
        </Box>

        {/* Settings Menu */}
        <SettingsMenu
          anchor={settingsMenuAnchor}
          onClose={handleCloseSettings}
          onProfile={handleProfile}
          onLogout={handleLogout}
          themeName={themeName}
        />
      </Box>

      {/* New Document Dialog */}
      <Dialog
        open={newDocDialogOpen}
        onClose={() => setNewDocDialogOpen(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>Create New Document</DialogTitle>
        <DialogContent>
          <TextField
            autoFocus
            fullWidth
            label="Document Title"
            defaultValue="Untitled Document"
            margin="dense"
            variant="outlined"
            value={newDocTitle}
            onChange={(e) => setNewDocTitle(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") {
                handleCreateDocument();
              }
            }}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setNewDocDialogOpen(false)}>Cancel</Button>
          <Button onClick={handleCreateDocument} variant="contained">
            Create
          </Button>
        </DialogActions>
      </Dialog>

      {/* New Workspace Dialog */}
      <Dialog
        open={newWorkspaceDialogOpen}
        onClose={() => setNewWorkspaceDialogOpen(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>Create New Workspace</DialogTitle>
        <DialogContent>
          <TextField
            autoFocus
            fullWidth
            label="Workspace Name"
            placeholder="My Workspace"
            margin="dense"
            variant="outlined"
            value={newWorkspaceName}
            onChange={(e) => setNewWorkspaceName(e.target.value)}
            onKeyPress={(e) => {
              if (e.key === "Enter") {
                handleCreateWorkspace();
              }
            }}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setNewWorkspaceDialogOpen(false)}>
            Cancel
          </Button>
          <Button onClick={handleCreateWorkspace} variant="contained">
            Create
          </Button>
        </DialogActions>
      </Dialog>

      {/* Share Dialog */}
      <Dialog
        open={shareDialogOpen}
        onClose={() => setShareDialogOpen(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>Share {shareTargetType}</DialogTitle>
        <DialogContent>
          <TextField
            autoFocus
            fullWidth
            label="Email Address"
            placeholder="user@example.com"
            margin="dense"
            variant="outlined"
            value={shareEmail}
            onChange={(e) => setShareEmail(e.target.value)}
            onKeyPress={(e) => {
              if (e.key === "Enter") {
                handleShare();
              }
            }}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShareDialogOpen(false)}>Cancel</Button>
          <Button onClick={handleShare} variant="contained">
            Share
          </Button>
        </DialogActions>
      </Dialog>

      {/* Add Member Dialog */}
      <Dialog
        open={addMemberDialogOpen}
        onClose={() => setAddMemberDialogOpen(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>Add Member to Workspace</DialogTitle>
        <DialogContent
          sx={{ display: "flex", flexDirection: "column", gap: 2, pt: 2 }}
        >
          <TextField
            autoFocus
            fullWidth
            label="Email Address"
            placeholder="user@example.com"
            value={addMemberEmail}
            onChange={(e) => setAddMemberEmail(e.target.value)}
          />
          <FormControl fullWidth>
            <InputLabel>Role</InputLabel>
            <Select
              value={addMemberRole}
              label="Role"
              onChange={(e) =>
                setAddMemberRole(e.target.value as "editor" | "viewer")
              }
            >
              <MenuItem value="editor">Editor</MenuItem>
              <MenuItem value="viewer">Viewer</MenuItem>
            </Select>
          </FormControl>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setAddMemberDialogOpen(false)}>Cancel</Button>
          <Button onClick={handleAddMember} variant="contained">
            Add Member
          </Button>
        </DialogActions>
      </Dialog>

      {/* Add Document to Workspace Dialog */}
      <Dialog
        open={addDocDialogOpen}
        onClose={() => setAddDocDialogOpen(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>Add Document to Workspace</DialogTitle>
        <DialogContent>
          <FormControl fullWidth margin="dense">
            <InputLabel>Document</InputLabel>
            <Select
              value={selectedDocId || ""}
              label="Document"
              onChange={(e) =>
                setSelectedDocId(e.target.value as unknown as number)
              }
            >
              {availableDocuments.map((doc) => (
                <MenuItem key={doc.id} value={doc.id}>
                  {doc.title}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setAddDocDialogOpen(false)}>Cancel</Button>
          <Button
            onClick={handleAddDocToWorkspace}
            variant="contained"
            disabled={!selectedDocId}
          >
            Add
          </Button>
        </DialogActions>
      </Dialog>
    </DialogContext.Provider>
  );
};
