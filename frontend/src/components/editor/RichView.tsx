import { useEffect, useRef } from "react";
import { Box, Typography, Divider, useTheme } from "@mui/material";
import type { ContentJson, Block } from "../../types/contentJson";
import type { Attachment } from "../../types";
import { renderMathToHtml, renderInlineMath } from "../../utils/katexRenderer";
import { darkModeImgSx } from "../../utils/darkModeImageFilter";
import { useHighlight } from "../../contexts/HighlightContext";

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
  const { highlight } = useHighlight();
  const containerRef = useRef<HTMLDivElement>(null);

  // Highlight excerpt text in the rendered DOM
  useEffect(() => {
    const root = containerRef.current;
    console.log("[Highlight] effect fired", { highlight, hasRoot: !!root });
    if (!root) return;

    // Remove previous highlights by unwrapping (preserving child nodes intact)
    root.querySelectorAll("mark[data-evidence-highlight]").forEach((mark) => {
      const parent = mark.parentNode;
      if (parent) {
        while (mark.firstChild) {
          parent.insertBefore(mark.firstChild, mark);
        }
        parent.removeChild(mark);
        parent.normalize();
      }
    });

    if (!highlight?.excerpt) {
      console.log("[Highlight] no excerpt, clearing");
      return;
    }

    // Walk text nodes, skipping those inside KaTeX-rendered math spans
    const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT, {
      acceptNode(node) {
        // Skip text nodes inside .katex elements (rendered inline math)
        let el = node.parentElement;
        while (el && el !== root) {
          if (el.classList.contains("katex")) return NodeFilter.FILTER_REJECT;
          el = el.parentElement;
        }
        return NodeFilter.FILTER_ACCEPT;
      },
    });
    const textNodes: Text[] = [];
    let node: Text | null;
    while ((node = walker.nextNode() as Text | null)) {
      textNodes.push(node);
    }
    console.log("[Highlight] text nodes found (non-katex):", textNodes.length);

    // Build a concatenated text and map each char back to its text node + offset
    let fullText = "";
    const charMap: { node: Text; offset: number }[] = [];
    for (const tn of textNodes) {
      const val = tn.nodeValue ?? "";
      for (let i = 0; i < val.length; i++) {
        charMap.push({ node: tn, offset: i });
        fullText += val[i];
      }
    }

    // Normalize whitespace for matching (the excerpt may not have the exact same spacing)
    const normChars: { char: string; origIndex: number }[] = [];
    let prevSpace = false;
    for (let i = 0; i < fullText.length; i++) {
      const ch = fullText[i];
      const isSpace = /\s/.test(ch);
      if (isSpace) {
        if (!prevSpace) {
          normChars.push({ char: " ", origIndex: i });
        }
        prevSpace = true;
      } else {
        normChars.push({ char: ch, origIndex: i });
        prevSpace = false;
      }
    }
    const normFullStr = normChars.map((c) => c.char).join("");
    const normExcerpt = highlight.excerpt.replace(/\s+/g, " ").trim();

    // Try exact match first; fall back to matching a leading substring
    // (excerpt may differ in trailing punctuation/spacing from rendered text)
    let matchIdx = normFullStr.indexOf(normExcerpt);
    let matchLen = normExcerpt.length;

    if (matchIdx === -1) {
      for (let len = normExcerpt.length - 1; len >= 40; len--) {
        const prefix = normExcerpt.substring(0, len);
        const idx = normFullStr.indexOf(prefix);
        if (idx !== -1) {
          matchIdx = idx;
          matchLen = len;
          break;
        }
      }
    }

    console.log("[Highlight] search result:", {
      excerptLen: normExcerpt.length,
      matchLen,
      matchIdx,
      excerptPreview: normExcerpt.substring(0, 60),
      fullTextPreview: normFullStr.substring(0, 200),
    });
    if (matchIdx === -1) return;

    // Map back to original char positions
    const startOrig = normChars[matchIdx].origIndex;
    const endOrig = normChars[matchIdx + matchLen - 1].origIndex + 1;

    // Find the text node ranges to highlight
    const startEntry = charMap[startOrig];
    const endEntry = charMap[endOrig - 1];
    if (!startEntry || !endEntry) return;

    // Use Range API to wrap the match in a <mark>
    const range = document.createRange();
    range.setStart(startEntry.node, startEntry.offset);
    range.setEnd(endEntry.node, endEntry.offset + 1);

    const mark = document.createElement("mark");
    mark.setAttribute("data-evidence-highlight", "true");
    mark.style.backgroundColor =
      theme.palette.mode === "dark"
        ? `${theme.palette.primary.main}F0`
        : `${theme.palette.primary.main}30`;
    mark.style.borderRadius = "2px";
    mark.style.padding = "1px 0";
    mark.style.transition = "background-color 0.3s ease";

    try {
      range.surroundContents(mark);
    } catch {
      // surroundContents fails if the range crosses element boundaries —
      // fall back to extracting and re-inserting
      const fragment = range.extractContents();
      mark.appendChild(fragment);
      range.insertNode(mark);
    }

    // Scroll the highlight into view
    mark.scrollIntoView({ behavior: "smooth", block: "center" });
  }, [highlight, theme.palette.mode]);

  return (
    <Box ref={containerRef} sx={{ width: "100%", py: 2 }}>
      {/* Authors */}
      {metadata.authors.length > 0 && (
        <Typography
          variant="body2"
          color="text.secondary"
          sx={{
            mb: 3,
            fontStyle: "italic",
            "& .katex": { fontSize: "0.85em" },
          }}
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

          {section.type === "abstract" && <Divider sx={{ mb: 1.5 }} />}

          {section.content.map((block, i) => (
            <BlockRenderer
              key={`${section.id}-${i}`}
              block={block}
              figureUrls={figureUrls}
            />
          ))}
        </Box>
      ))}
    </Box>
  );
};

// ---------------------------------------------------------------------------

const BlockRenderer = ({
  block,
  figureUrls,
}: {
  block: Block;
  figureUrls: Map<string, string>;
}) => {
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
                ...darkModeImgSx(theme.palette.mode),
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
              <span
                dangerouslySetInnerHTML={{ __html: renderInlineMath(item) }}
              />
            </li>
          ))}
        </Box>
      );
  }
};
