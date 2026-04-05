import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Typography, Link, Divider, Box } from "@mui/material";
import type { Components } from "react-markdown";

const components: Components = {
  h1: ({ children }) => (
    <Typography variant="subtitle1" fontWeight={700} sx={{ mt: 2.5, mb: 1 }}>
      {children}
    </Typography>
  ),
  h2: ({ children }) => (
    <Typography variant="subtitle1" fontWeight={700} sx={{ mt: 2, mb: 1 }}>
      {children}
    </Typography>
  ),
  h3: ({ children }) => (
    <Typography variant="subtitle2" fontWeight={700} sx={{ mt: 1.5, mb: 0.5 }}>
      {children}
    </Typography>
  ),
  p: ({ children }) => (
    <Typography variant="body2" color="text.secondary" sx={{ mb: 1, lineHeight: 1.6 }}>
      {children}
    </Typography>
  ),
  strong: ({ children }) => <strong>{children}</strong>,
  hr: () => <Divider sx={{ my: 1.5 }} />,
  ul: ({ children }) => (
    <Box component="ul" sx={{ pl: 2, mb: 1, mt: 0 }}>
      {children}
    </Box>
  ),
  ol: ({ children }) => (
    <Box component="ol" sx={{ pl: 2, mb: 1, mt: 0 }}>
      {children}
    </Box>
  ),
  li: ({ children }) => (
    <Typography component="li" variant="body2" color="text.secondary" sx={{ mb: 0.5, lineHeight: 1.6 }}>
      {children}
    </Typography>
  ),
  a: ({ href, children }) => (
    <Link href={href} target="_blank" rel="noopener">
      {children}
    </Link>
  ),
};

export function MarkdownRenderer({ children }: { children: string }) {
  return (
    <ReactMarkdown remarkPlugins={[remarkGfm]} components={components}>
      {children}
    </ReactMarkdown>
  );
}
