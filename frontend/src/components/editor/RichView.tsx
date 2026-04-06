import { Box, Typography, Divider, useTheme } from "@mui/material";
import type { ContentJson, Block } from "../../types/contentJson";
import type { Attachment } from "../../types";
import { renderMathToHtml, renderInlineMath } from "../../utils/katexRenderer";

interface RichViewProps {
  contentJson: ContentJson;
  attachments?: Attachment[];
}

/**
 * Build a map from figure `src` (e.g. "excitation_scheme") to the
 * attachment URL whose filename starts with that value.
 */
function buildFigureUrlMap(attachments: Attachment[]): Map<string, string> {
  const map = new Map<string, string>();
  for (const att of attachments) {
    if (!att.url || !att.content_type?.startsWith("image/")) continue;
    // Strip extension to get the base name (e.g. "excitation_scheme.jpg" → "excitation_scheme")
    const base = att.filename.replace(/\.[^.]+$/, "");
    map.set(base, att.url);
    // Also map full filename in case src includes extension
    map.set(att.filename, att.url);
  }
  return map;
}

export const RichView = ({ contentJson, attachments = [] }: RichViewProps) => {
  const theme = useTheme();
  const { metadata, sections } = contentJson;
  const figureUrls = buildFigureUrlMap(attachments);

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
            <BlockRenderer key={`${section.id}-${i}`} block={block} figureUrls={figureUrls} />
          ))}
        </Box>
      ))}
    </Box>
  );
};

// ---------------------------------------------------------------------------

const BlockRenderer = ({ block, figureUrls }: { block: Block; figureUrls: Map<string, string> }) => {
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

    case "figure": {
      const imageUrl = block.src ? figureUrls.get(block.src) : undefined;
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
          {imageUrl ? (
            <Box
              component="img"
              src={imageUrl}
              alt={block.alt || block.label || "Figure"}
              sx={{
                maxWidth: "100%",
                height: "auto",
                mb: 1.5,
                borderRadius: 1,
              }}
            />
          ) : block.src ? (
            <Box
              sx={{
                mb: 1.5,
                color: "text.secondary",
                fontSize: "0.85rem",
              }}
            >
              [{block.label || "Figure"}: {block.src}]
            </Box>
          ) : null}
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
    }

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
