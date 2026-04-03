import { Box, Typography, Divider, useTheme } from "@mui/material";
import type { ContentJson, Block } from "../../types/contentJson";
import { renderMathToHtml, renderInlineMath } from "../../utils/katexRenderer";

interface RichViewProps {
  contentJson: ContentJson;
}

export const RichView = ({ contentJson }: RichViewProps) => {
  const theme = useTheme();
  const { metadata, sections } = contentJson;

  return (
    <Box sx={{ width: "100%", py: 2 }}>
      {/* Authors */}
      {metadata.authors.length > 0 && (
        <Typography
          variant="body2"
          color="text.secondary"
          sx={{ mb: 3, fontStyle: "italic", "& .katex": { fontSize: "0.85em" } }}
          dangerouslySetInnerHTML={{
            __html: metadata.authors_raw
              ? renderInlineMath(metadata.authors_raw)
              : metadata.authors.map((a) => a.name).join(", "),
          }}
        />
      )}

      {/* Sections */}
      {sections.map((section) => (
        <Box key={section.id} sx={{ mb: 4 }}>
          <Typography
            variant={section.type === "abstract" ? "h6" : "h5"}
            sx={{
              fontWeight: 700,
              mb: 1.5,
              color: theme.palette.text.primary,
              ...(section.type === "abstract" && {
                fontSize: "1rem",
                textTransform: "uppercase",
                letterSpacing: 1,
              }),
            }}
          >
            {section.heading}
          </Typography>

          {section.type === "abstract" && (
            <Divider sx={{ mb: 1.5 }} />
          )}

          {section.content.map((block, i) => (
            <BlockRenderer key={`${section.id}-${i}`} block={block} />
          ))}
        </Box>
      ))}
    </Box>
  );
};

// ---------------------------------------------------------------------------

const BlockRenderer = ({ block }: { block: Block }) => {
  const theme = useTheme();

  switch (block.type) {
    case "paragraph":
      return (
        <Typography
          variant="body1"
          sx={{
            mb: 1.5,
            lineHeight: 1.8,
            textAlign: "justify",
            "& .katex": { fontSize: "1em" },
          }}
          dangerouslySetInnerHTML={{ __html: renderInlineMath(block.text) }}
        />
      );

    case "equation":
      return (
        <Box
          sx={{
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            my: 2.5,
            px: 2,
            gap: 2,
            "& .katex-display": { margin: 0 },
          }}
        >
          <Box
            sx={{ flex: 1, textAlign: "center", overflow: "auto" }}
            dangerouslySetInnerHTML={{
              __html: renderMathToHtml(block.tex, true),
            }}
          />
          {block.label && (
            <Typography
              variant="body2"
              color="text.secondary"
              sx={{ flexShrink: 0 }}
            >
              ({block.label})
            </Typography>
          )}
        </Box>
      );

    case "figure":
      return (
        <Box
          sx={{
            my: 3,
            textAlign: "center",
            border: "1px solid " + theme.palette.divider,
            borderRadius: 2,
            p: 2,
            backgroundColor: theme.palette.background.default,
          }}
        >
          {block.src && (
            <Box
              sx={{
                mb: 1.5,
                color: "text.secondary",
                fontSize: "0.85rem",
              }}
            >
              [{block.label || "Figure"}: {block.src}]
            </Box>
          )}
          <Typography
            variant="body2"
            color="text.secondary"
            sx={{ textAlign: "left", lineHeight: 1.6 }}
            dangerouslySetInnerHTML={{
              __html: `<strong>${block.label || "Figure"}</strong> | ${renderInlineMath(block.caption)}`,
            }}
          />
        </Box>
      );

    case "list":
      return (
        <Box
          component={block.ordered ? "ol" : "ul"}
          sx={{
            pl: 3,
            mb: 2,
            "& li": {
              mb: 0.5,
              lineHeight: 1.6,
              fontSize: "0.95rem",
            },
          }}
        >
          {block.items.map((item, i) => (
            <li key={i}>
              <span dangerouslySetInnerHTML={{ __html: renderInlineMath(item) }} />
            </li>
          ))}
        </Box>
      );
  }
};
