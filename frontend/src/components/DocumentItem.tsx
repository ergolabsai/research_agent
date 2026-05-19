// SPDX-FileCopyrightText: 2026 Chelsea Liekhus-Schmaltz and Johnathon Barhydt
//
// SPDX-License-Identifier: AGPL-3.0-only

import {
  Box,
  Card,
  CardActionArea,
  CardContent,
  IconButton,
  ListItemButton,
  Menu,
  MenuItem,
  Stack,
  Typography,
  useTheme,
} from "@mui/material";
import {
  InsertDriveFile as FileTextIcon,
  MoreHoriz as MoreHorizIcon,
  Delete as DeleteIcon,
  Share as ShareIcon,
} from "@mui/icons-material";

export interface DocumentItemData {
  id: number;
  title: string;
  updated_at?: string;
}

type DocumentItemVariant = "sidebar" | "dashboard" | "workspace";

interface DocumentItemProps {
  doc: DocumentItemData;
  variant?: DocumentItemVariant;
  isActive?: boolean;
  draggable?: boolean;
  onDragStart?: (e: React.DragEvent) => void;
  onDragEnd?: () => void;
  onClick?: () => void;
  menuAnchorEl?: HTMLElement | null;
  onMenuOpen?: (e: React.MouseEvent) => void;
  onMenuClose?: () => void;
  onShare?: () => void;
  onDelete?: () => void;
  showMenu?: boolean;
}

export const DocumentItem = ({
  doc,
  variant = "sidebar",
  isActive = false,
  draggable = false,
  onDragStart,
  onDragEnd,
  onClick,
  menuAnchorEl,
  onMenuOpen,
  onMenuClose,
  onShare,
  onDelete,
  showMenu = true,
}: DocumentItemProps) => {
  const theme = useTheme();

  if (variant === "dashboard") {
    return (
      <Card
        draggable={draggable}
        onDragStart={onDragStart}
        onDragEnd={onDragEnd}
        sx={{
          height: "100%",
          display: "flex",
          flexDirection: "column",
          background: `linear-gradient(135deg, ${theme.palette.primary.main}10 0%, ${theme.palette.secondary.main}10 100%)`,
          //   background: `linear-gradient(135deg, ${theme.palette.background.paper}, ${theme.palette.mode === "dark" ? "rgba(255, 255, 255, 0.05)" : "rgba(0, 0, 0, 0.02)"})`,
          transition: "all 0.3s ease",
          cursor: draggable ? "grab" : "default",
          "&:active": {
            cursor: draggable ? "grabbing" : "default",
          },
          "&:hover": {
            transform: "translateY(-4px)",
            boxShadow: "0 12px 24px rgba(0, 0, 0, 0.15)",
          },
          position: "relative",
          border: `1px solid ${theme.palette.divider}`,
        }}
      >
        {showMenu && (
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
        )}
        <CardActionArea
          onClick={onClick}
          sx={{
            flex: 1,
            cursor: draggable ? "grab" : "default",
            "&:active": {
              cursor: draggable ? "grabbing" : "default",
            },
          }}
        >
          <CardContent
            sx={{ display: "flex", flexDirection: "column", gap: 1 }}
          >
            <Stack
              direction="row"
              spacing={1}
              alignItems="center"
              justifyContent="space-between"
            >
              <Stack
                direction="row"
                spacing={1}
                alignItems="center"
                sx={{ flex: 1, minWidth: 0 }}
              >
                <FileTextIcon
                  color="primary"
                  sx={{ fontSize: "1.25rem", flexShrink: 0 }}
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
                  {doc.title}
                </Typography>
              </Stack>
              {doc.updated_at && (
                <Typography
                  variant="body2"
                  sx={{
                    color: "text.secondary",
                    fontSize: "0.85rem",
                    flexShrink: 0,
                    ml: "auto",
                  }}
                >
                  Updated {new Date(doc.updated_at).toLocaleDateString()}
                </Typography>
              )}
            </Stack>
          </CardContent>
        </CardActionArea>
      </Card>
    );
  }

  return (
    <ListItemButton
      draggable={draggable}
      onDragStart={onDragStart}
      onDragEnd={onDragEnd}
      onClick={onClick}
      sx={{
        borderRadius: "8px",
        py: 0,
        mb: variant === "workspace" ? 0.5 : 0,
        display: "flex",
        justifyContent: "space-between",
        alignItems: "center",
        cursor: draggable ? "grab" : "default",
        "&:active": {
          cursor: draggable ? "grabbing" : "default",
        },
        "&:hover .doc-menu": {
          opacity: 1,
        },
      }}
    >
      <Stack direction="row" sx={{ flex: 1, gap: 1, minWidth: 0 }}>
        <FileTextIcon
          color="primary"
          sx={{ fontSize: "1.25rem", flexShrink: 0 }}
        />
        <Typography
          color={isActive ? "text.primary" : "text.secondary"}
          variant="body2"
          sx={{
            overflow: "hidden",
            textOverflow: "ellipsis",
            whiteSpace: "nowrap",
            fontWeight: isActive ? 600 : 400,
          }}
        >
          {doc.title}
        </Typography>
      </Stack>
      {variant === "workspace" && doc.updated_at && (
        <Typography
          variant="body2"
          sx={{
            color: "text.secondary",
            fontSize: "0.85rem",
            flexShrink: 0,
          }}
        >
          Updated {new Date(doc.updated_at).toLocaleDateString()}
        </Typography>
      )}
      {showMenu && (
        <>
          <IconButton
            className="doc-menu"
            size="small"
            onClick={onMenuOpen}
            sx={{
              opacity: 0,
              transition: "opacity 0.2s",
              flexShrink: 0,
            }}
          >
            <MoreHorizIcon color="primary" sx={{ fontSize: "1rem" }} />
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
        </>
      )}
    </ListItemButton>
  );
};
