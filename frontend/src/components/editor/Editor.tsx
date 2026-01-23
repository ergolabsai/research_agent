import { useState } from "react";
import { Box, Tabs, Tab, Paper, TextField, useTheme } from "@mui/material";
import ReactMarkdown from "react-markdown";
import remarkMath from "remark-math";
import rehypeKatex from "rehype-katex";
import "katex/dist/katex.min.css"; // Standard LaTeX CSS

const LaTexEditor = ({
  content,
  setContent,
}: {
  content: any;
  setContent: Function;
}) => {
  const theme = useTheme();
  const [tabIndex, setTabIndex] = useState(0);

  return (
    <Paper
      variant="outlined"
      sx={{ borderRadius: 2, overflow: "hidden", bgcolor: "background.paper" }}
    >
      <Tabs
        value={tabIndex}
        onChange={(_, n) => setTabIndex(n)}
        sx={{ borderBottom: 1, borderColor: "divider" }}
      >
        <Tab label="Raw" />
        <Tab label="Preview" />
      </Tabs>

      <Box sx={{ p: 2, minHeight: 400 }}>
        {tabIndex === 0 ? (
          <TextField
            fullWidth
            multiline
            minRows={10}
            variant="standard"
            value={content}
            onChange={(e) => setContent(e.target.value)}
            slotProps={{
              input: {
                disableUnderline: true,
                style: {
                  fontFamily: "monospace",
                  color: theme.palette.text.primary,
                },
              },
            }}
          />
        ) : (
          /* THIS IS THE PREVIEW  */
          <Box
            sx={{
              color: "text.primary",
              bgcolor: "background.default",
              p: 3,
              borderRadius: 1,
              "& .katex": { color: "inherit" },
              "& img": { maxWidth: "100%", borderRadius: 2 },
            }}
          >
            <ReactMarkdown
              remarkPlugins={[remarkMath]}
              rehypePlugins={[rehypeKatex]}
            >
              {content}
            </ReactMarkdown>
          </Box>
        )}
      </Box>
    </Paper>
  );
};

export default LaTexEditor;
