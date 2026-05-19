// SPDX-FileCopyrightText: 2026 Chelsea Liekhus-Schmaltz and Johnathon Barhydt
//
// SPDX-License-Identifier: AGPL-3.0-only

import { useState, useEffect } from "react";
import { Box, TextField, Typography, useTheme } from "@mui/material";
import type { ContentJson } from "../../types/contentJson";
import { parseContentJson } from "../../utils/contentJsonUtils";

interface JsonViewProps {
  contentJson: ContentJson;
  onChange: (updated: ContentJson) => void;
}

export const JsonView = ({ contentJson, onChange }: JsonViewProps) => {
  const theme = useTheme();
  const [text, setText] = useState(() => JSON.stringify(contentJson, null, 2));
  const [error, setError] = useState<string | null>(null);

  // Sync from parent when contentJson reference changes (e.g. view switch)
  useEffect(() => {
    setText(JSON.stringify(contentJson, null, 2));
    setError(null);
  }, [contentJson]);

  const handleBlur = () => {
    const parsed = parseContentJson(text);
    if (parsed) {
      setError(null);
      onChange(parsed);
    } else {
      setError("Invalid ContentJson — changes not saved");
    }
  };

  return (
    <Box sx={{ height: "100%", display: "flex", flexDirection: "column" }}>
      {error && (
        <Typography
          variant="caption"
          color="error"
          sx={{ px: 1, py: 0.5 }}
        >
          {error}
        </Typography>
      )}
      <TextField
        multiline
        fullWidth
        value={text}
        onChange={(e) => setText(e.target.value)}
        onBlur={handleBlur}
        variant="standard"
        InputProps={{
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
