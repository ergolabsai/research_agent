import { useState } from "react";
import { Box, TextField, IconButton, Tooltip, useTheme } from "@mui/material";
import { ContentCopy as CopyIcon, Check as CheckIcon } from "@mui/icons-material";
import type { ContentJson } from "../../types/contentJson";
import { contentJsonToLatex } from "../../utils/contentJsonUtils";

interface LatexViewProps {
  contentJson: ContentJson;
}

export const LatexView = ({ contentJson }: LatexViewProps) => {
  const theme = useTheme();
  const latex = contentJsonToLatex(contentJson);
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    await navigator.clipboard.writeText(latex);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <Box sx={{ height: "100%", display: "flex", flexDirection: "column", position: "relative" }}>
      <Tooltip title={copied ? "Copied!" : "Copy LaTeX"}>
        <IconButton
          size="small"
          onClick={handleCopy}
          sx={{
            position: "absolute",
            top: 4,
            right: 4,
            zIndex: 1,
            bgcolor: theme.palette.background.paper,
            "&:hover": { bgcolor: theme.palette.action.hover },
          }}
        >
          {copied ? <CheckIcon fontSize="small" color="success" /> : <CopyIcon fontSize="small" />}
        </IconButton>
      </Tooltip>

      <TextField
        multiline
        fullWidth
        value={latex}
        variant="standard"
        InputProps={{
          readOnly: true,
          disableUnderline: true,
          sx: {
            fontFamily: '"Fira Code", "Consolas", "Monaco", monospace',
            fontSize: "0.82rem",
            lineHeight: 1.5,
            color: theme.palette.text.primary,
            "& textarea": { resize: "none" },
          },
        }}
        sx={{ flex: 1 }}
      />
    </Box>
  );
};
