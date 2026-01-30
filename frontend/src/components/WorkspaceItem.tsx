import {
  Accordion,
  AccordionDetails,
  AccordionSummary,
  Box,
  Card,
  CardContent,
  Divider,
  IconButton,
  List,
  Menu,
  MenuItem,
  Stack,
  Typography,
  useTheme,
} from "@mui/material";
import {
  FolderOpen as FolderOpenIcon,
  MoreHoriz as MoreHorizIcon,
  ExpandMore as ExpandMoreIcon,
  Delete as DeleteIcon,
  Share as ShareIcon,
  PersonAdd as PersonAddIcon,
  Add as PlusIcon,
} from "@mui/icons-material";
import { ReactNode } from "react";

export interface WorkspaceItemData {
  id: number;
  name: string;
  created_at?: string;
}

type WorkspaceItemVariant = "sidebar" | "dashboard";

interface WorkspaceItemProps {
  workspace: WorkspaceItemData;
  variant?: WorkspaceItemVariant;
  documents?: ReactNode;
  draggedDocId?: number | null;
  onDragOver?: (e: React.DragEvent) => void;
  onDragLeave?: (e: React.DragEvent) => void;
  onDrop?: (e: React.DragEvent) => void;
  menuAnchorEl?: HTMLElement | null;
  onMenuOpen?: (e: React.MouseEvent) => void;
  onMenuClose?: () => void;
  onAddMember?: () => void;
  onAddDocument?: () => void;
  onShare?: () => void;
  onDelete?: () => void;
  emptyStateText?: string;
  showEmptyAddButton?: boolean;
}

export const WorkspaceItem = ({
  workspace,
  variant = "sidebar",
  documents,
  draggedDocId,
  onDragOver,
  onDragLeave,
  onDrop,
  menuAnchorEl,
  onMenuOpen,
  onMenuClose,
  onAddMember,
  onAddDocument,
  onShare,
  onDelete,
  emptyStateText,
  showEmptyAddButton = false,
}: WorkspaceItemProps) => {
  const theme = useTheme();

  if (variant === "dashboard") {
    return (
      <Card
        onDragOver={onDragOver}
        onDragLeave={onDragLeave}
        onDrop={onDrop}
        sx={{
          height: "100%",
          display: "flex",
          flexDirection: "column",
          background: `linear-gradient(135deg, ${theme.palette.background.paper}, ${theme.palette.mode === "dark" ? "rgba(255, 255, 255, 0.05)" : "rgba(0, 0, 0, 0.02)"})`,
          transition: "all 0.3s ease",
          "&:hover": {
            transform: "translateY(-4px)",
            boxShadow: "0 12px 24px rgba(0, 0, 0, 0.15)",
          },
          position: "relative",
          cursor: draggedDocId ? "copy" : "default",
          border: `1px solid ${theme.palette.divider}`,
        }}
      >
        <Box
          sx={{
            position: "absolute",
            top: 8,
            right: 8,
            zIndex: 10,
            opacity: 0,
            transition: "opacity 0.2s",
            "&:hover": { opacity: 1 },
          }}
          onMouseEnter={(e) => {
            const box = e.currentTarget as HTMLElement;
            box.style.opacity = "1";
          }}
          onMouseLeave={(e) => {
            const box = e.currentTarget as HTMLElement;
            box.style.opacity = "0";
          }}
        >
          <IconButton
            size="small"
            onClick={onMenuOpen}
            sx={{
              backgroundColor: "background.paper",
              "&:hover": {
                backgroundColor: "background.paper",
              },
            }}
          >
            <MoreHorizIcon fontSize="small" />
          </IconButton>
          <Menu
            anchorEl={menuAnchorEl}
            open={Boolean(menuAnchorEl)}
            onClose={onMenuClose}
            slotProps={{
              paper: {
                sx: {
                  backgroundColor: `${theme.palette.background.paper} !important`,
                  border: `1px solid ${theme.palette.divider} !important`,
                  backgroundImage: "none",
                  boxShadow: "none",
                },
              },
            }}
          >
            <MenuItem
              onClick={() => {
                onMenuClose?.();
                onAddMember?.();
              }}
            >
              <PersonAddIcon sx={{ mr: 1, fontSize: "1.2rem" }} />
              Add Member
            </MenuItem>
            <MenuItem
              onClick={() => {
                onMenuClose?.();
                onAddDocument?.();
              }}
            >
              <PlusIcon sx={{ mr: 1, fontSize: "1.2rem" }} />
              Add Document
            </MenuItem>
            <MenuItem
              onClick={() => {
                onMenuClose?.();
                onShare?.();
              }}
            >
              <ShareIcon sx={{ mr: 1, fontSize: "1.2rem" }} />
              Share
            </MenuItem>
            <MenuItem
              onClick={() => {
                onMenuClose?.();
                onDelete?.();
              }}
            >
              <DeleteIcon sx={{ mr: 1, fontSize: "1.2rem" }} />
              Delete
            </MenuItem>
          </Menu>
        </Box>
        <CardContent
          sx={{
            display: "flex",
            flexDirection: "column",
            gap: 1,
            p: 0,
            background: `linear-gradient(135deg, ${theme.palette.primary.main}10 0%, ${theme.palette.secondary.main}10 100%)`,
          }}
        >
          <Stack
            direction="row"
            alignItems="center"
            justifyContent="space-between"
            sx={{ m: 1.5, mb: 0 }}
          >
            <Stack
              direction="row"
              spacing={1}
              alignItems="center"
              sx={{ flex: 1, minWidth: 0 }}
            >
              <FolderOpenIcon
                color="secondary"
                sx={{ fontSize: "1.3rem", flexShrink: 0 }}
              />
              <Typography
                variant="h3"
                sx={{
                  fontSize: "1.1rem",
                  fontWeight: 600,
                  overflow: "hidden",
                  textOverflow: "ellipsis",
                  whiteSpace: "nowrap",
                }}
              >
                {workspace.name}
              </Typography>
            </Stack>
            {workspace.created_at && (
              <Typography
                variant="body2"
                sx={{
                  color: "text.secondary",
                  fontSize: "0.85rem",
                  flexShrink: 0,
                  ml: "auto",
                }}
              >
                Created {new Date(workspace.created_at).toLocaleDateString()}
              </Typography>
            )}
          </Stack>
          <Divider />
          {documents || (
            <Typography variant="body2" color="text.secondary">
              {emptyStateText || "No documents"}
            </Typography>
          )}
        </CardContent>
      </Card>
    );
  }

  return (
    <Accordion
      onDragOver={onDragOver}
      onDragLeave={onDragLeave}
      onDrop={onDrop}
      sx={{
        background: "transparent",
        boxShadow: "none",
        border: "none",
        m: 0,
        borderRadius: "8px",
        transition: "background-color 0.2s",
        "&:before": {
          display: "none",
        },
        "&.Mui-expanded": {
          m: 0,
        },
      }}
    >
      <AccordionSummary
        expandIcon={<ExpandMoreIcon color="secondary" />}
        sx={{
          minHeight: "auto",
          m: 0,
          "&.Mui-expanded": {
            minHeight: "auto",
            m: 0,
          },
          "& .MuiAccordionSummary-content": {
            my: 0,
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            "&.Mui-expanded": {
              my: 0,
            },
          },
          "&:hover .ws-menu": {
            opacity: 1,
          },
        }}
      >
        <Stack direction="row" sx={{ gap: 1, flex: 1, minWidth: 0 }}>
          <FolderOpenIcon
            color="secondary"
            sx={{ fontSize: "1.3rem", flexShrink: 0 }}
          />
          <Typography
            variant="body2"
            color="text.secondary"
            sx={{
              overflow: "hidden",
              textOverflow: "ellipsis",
              whiteSpace: "nowrap",
            }}
          >
            {workspace.name}
          </Typography>
        </Stack>
        <IconButton
          className="ws-menu"
          size="small"
          onClick={onMenuOpen}
          sx={{
            opacity: 0,
            transition: "opacity 0.2s",
            flexShrink: 0,
          }}
        >
          <MoreHorizIcon color="secondary" sx={{ fontSize: "1rem" }} />
        </IconButton>
        <Menu
          anchorEl={menuAnchorEl}
          open={Boolean(menuAnchorEl)}
          onClose={onMenuClose}
          slotProps={{
            paper: {
              sx: {
                backgroundColor: `${theme.palette.background.paper} !important`,
                border: `1px solid ${theme.palette.divider} !important`,
                backgroundImage: "none",
                boxShadow: "none",
              },
            },
          }}
        >
          <MenuItem
            onClick={() => {
              onMenuClose?.();
              onAddMember?.();
            }}
          >
            <PersonAddIcon sx={{ mr: 1, fontSize: "1.2rem" }} />
            Add Member
          </MenuItem>
          <Divider />
          <MenuItem
            onClick={() => {
              onMenuClose?.();
              onAddDocument?.();
            }}
          >
            <PlusIcon sx={{ mr: 1, fontSize: "1.2rem" }} />
            Add Document
          </MenuItem>
          <MenuItem
            onClick={() => {
              onMenuClose?.();
              onShare?.();
            }}
          >
            <ShareIcon sx={{ mr: 1, fontSize: "1.2rem" }} />
            Share
          </MenuItem>
          <MenuItem
            onClick={() => {
              onMenuClose?.();
              onDelete?.();
            }}
          >
            <DeleteIcon sx={{ mr: 1, fontSize: "1.2rem" }} />
            Delete
          </MenuItem>
        </Menu>
      </AccordionSummary>
      <AccordionDetails
        sx={{
          backgroundColor: "background.paper",
          p: 0,
          cursor: draggedDocId ? "copy" : "default",
        }}
      >
        {documents ? (
          <List sx={{ p: 0, width: "100%" }}>{documents}</List>
        ) : (
          <>
            <Box
              sx={{
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                m: 1,
              }}
            >
              <Typography
                variant="caption"
                color={`${theme.palette.text.secondary}AA`}
              >
                {emptyStateText || "Drag documents here or add a new one."}
              </Typography>
              {showEmptyAddButton && (
                <IconButton size="small" onClick={onAddDocument}>
                  <PlusIcon color="primary" sx={{ fontSize: "0.9rem" }} />
                </IconButton>
              )}
            </Box>
            <Divider />
          </>
        )}
      </AccordionDetails>
    </Accordion>
  );
};
