import { useRef, useState } from "react";
import { Box, Typography, useTheme } from "@mui/material";
import { InsertDriveFile as FileTextIcon } from "@mui/icons-material";
import { createPortal, flushSync } from "react-dom";

interface DragPreviewState {
  title: string;
}

export const useDragPreview = () => {
  const theme = useTheme();
  const [dragPreview, setDragPreview] = useState<DragPreviewState | null>(null);
  const dragPreviewRef = useRef<HTMLDivElement | null>(null);

  const showDragPreview = (title: string) => {
    flushSync(() => {
      setDragPreview({ title });
    });
  };

  const hideDragPreview = () => {
    setDragPreview(null);
  };

  const setDragImage = (e: React.DragEvent) => {
    if (dragPreviewRef.current) {
      e.dataTransfer.setDragImage(dragPreviewRef.current, 0, 0);
    }
  };

  const DragPreviewPortal = createPortal(
    <Box
      ref={dragPreviewRef}
      sx={{
        position: "fixed",
        top: -1000,
        left: -1000,
        px: 1.5,
        py: 1,
        borderRadius: "8px",
        backgroundColor: theme.palette.background.paper,
        border: `1px solid ${theme.palette.divider}`,
        color: "text.primary",
        fontSize: "0.875rem",
        fontFamily: theme.typography.fontFamily,
        display: "inline-flex",
        alignItems: "center",
        gap: 1,
        opacity: 0.9,
        pointerEvents: "none",
        visibility: dragPreview ? "visible" : "hidden",
      }}
    >
      <FileTextIcon sx={{ fontSize: "1rem" }} color="primary" />
      <Typography variant="body2" sx={{ fontWeight: 500 }}>
        {dragPreview?.title ?? "Document"}
      </Typography>
    </Box>,
    document.body,
  );

  return {
    showDragPreview,
    hideDragPreview,
    setDragImage,
    DragPreviewPortal,
  };
};
