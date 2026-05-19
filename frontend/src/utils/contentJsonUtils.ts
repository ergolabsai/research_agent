// SPDX-FileCopyrightText: 2026 Chelsea Liekhus-Schmaltz and Johnathon Barhydt
//
// SPDX-License-Identifier: AGPL-3.0-only

import type {
  ContentJson,
  Section,
  SectionType,
  Block,
  Author,
} from "../types/contentJson";

// ---------------------------------------------------------------------------
// Parse / detect
// ---------------------------------------------------------------------------

/** Try to parse a raw content string as structured ContentJson. Returns null for legacy plain text. */
export function parseContentJson(raw: string): ContentJson | null {
  if (!raw || raw[0] !== "{") return null;
  try {
    const parsed = JSON.parse(raw);
    if (parsed && typeof parsed.version === "number" && Array.isArray(parsed.sections)) {
      return parsed as ContentJson;
    }
  } catch {
    // not JSON
  }
  return null;
}

// ---------------------------------------------------------------------------
// ContentJson → plain text
// ---------------------------------------------------------------------------

/** Flatten structured content into readable plain text (for AgentPanel, etc). */
export function contentJsonToPlainText(doc: ContentJson): string {
  const lines: string[] = [];

  // Title from first section or metadata
  const authors = doc.metadata.authors.map((a) => a.name).join(", ");
  if (authors) lines.push(authors, "");

  for (const section of doc.sections) {
    lines.push(section.heading, "");
    for (const block of section.content) {
      switch (block.type) {
        case "paragraph":
          // Strip inline $...$ markers, keep the math text
          lines.push(block.text.replace(/\$/g, ""), "");
          break;
        case "equation":
          lines.push(block.tex, "");
          break;
        case "figure":
          lines.push(`[${block.label || "Figure"}: ${block.caption}]`, "");
          break;
        case "list":
          block.items.forEach((item, i) => {
            lines.push(block.ordered ? `${i + 1}. ${item}` : `- ${item}`);
          });
          lines.push("");
          break;
      }
    }
  }
  return lines.join("\n").trim();
}

// ---------------------------------------------------------------------------
// ContentJson → LaTeX
// ---------------------------------------------------------------------------

export function contentJsonToLatex(doc: ContentJson): string {
  const lines: string[] = [];

  // Preamble
  lines.push(
    "\\documentclass[10pt]{article}",
    "\\usepackage[utf8]{inputenc}",
    "\\usepackage[T1]{fontenc}",
    "\\usepackage{amsmath}",
    "\\usepackage{amsfonts}",
    "\\usepackage{amssymb}",
    "\\usepackage{graphicx}",
    "\\usepackage{hyperref}",
    "",
  );

  // Title & authors
  const title = doc.sections.find((s) => s.type === "abstract")
    ? doc.sections[0]?.heading
    : "Untitled";
  lines.push(`\\title{${title}}`, "");

  const authorStr = doc.metadata.authors.map((a) => a.name).join(" \\and ");
  if (authorStr) lines.push(`\\author{${authorStr}}`, "");

  lines.push("\\begin{document}", "\\maketitle", "");

  for (const section of doc.sections) {
    if (section.type === "abstract") {
      lines.push("\\begin{abstract}");
      for (const block of section.content) {
        lines.push(blockToLatex(block));
      }
      lines.push("\\end{abstract}", "");
      continue;
    }

    if (section.type === "references") {
      lines.push(`\\section*{${section.heading}}`);
      // Collect list block items as enumerate
      const listBlock = section.content.find((b) => b.type === "list");
      if (listBlock && listBlock.type === "list") {
        lines.push("\\begin{enumerate}");
        for (const item of listBlock.items) {
          lines.push(`  \\item ${item}`);
        }
        lines.push("\\end{enumerate}", "");
      } else {
        for (const block of section.content) {
          lines.push(blockToLatex(block));
        }
      }
      continue;
    }

    lines.push(`\\section*{${section.heading}}`, "");
    for (const block of section.content) {
      lines.push(blockToLatex(block));
    }
    lines.push("");
  }

  lines.push("\\end{document}");
  return lines.join("\n");
}

function blockToLatex(block: Block): string {
  switch (block.type) {
    case "paragraph":
      return block.text + "\n";
    case "equation": {
      const tag = block.label ? ` \\tag{${block.label}}` : "";
      return `\\begin{equation*}\n${block.tex}${tag}\n\\end{equation*}\n`;
    }
    case "figure":
      return [
        "\\begin{figure}[h]",
        "\\begin{center}",
        `  \\includegraphics[max width=\\textwidth]{${block.src}}`,
        `\\caption{${block.label ? block.label + " | " : ""}${block.caption}}`,
        "\\end{center}",
        "\\end{figure}",
        "",
      ].join("\n");
    case "list": {
      const env = block.ordered ? "enumerate" : "itemize";
      const items = block.items.map((i) => `  \\item ${i}`).join("\n");
      return `\\begin{${env}}\n${items}\n\\end{${env}}\n`;
    }
  }
}

// ---------------------------------------------------------------------------
// LaTeX → ContentJson  (purpose-built for the demo paper)
// ---------------------------------------------------------------------------

export function latexToContentJson(latex: string): ContentJson {
  const metadata = extractMetadata(latex);
  const sections = extractSections(latex);

  return {
    version: 1,
    metadata,
    sections,
  };
}

// --- metadata helpers ---

function extractMetadata(latex: string): ContentJson["metadata"] {
  const authors: Author[] = [];
  let authorsRaw: string | undefined;

  // Extract authors from \author{...}
  const authorMatch = latex.match(/\\author\{([\s\S]*?)\}\s*\n/);
  if (authorMatch) {
    // Keep the raw string (cleaned up slightly) for rendering with KaTeX
    authorsRaw = authorMatch[1]
      .replace(/\\&/g, "&")       // normalize \& to &
      .replace(/\s+/g, " ")      // collapse whitespace
      .trim();

    // Strip LaTeX for the structured authors array
    const stripped = authorMatch[1]
      .replace(/\$[^$]*\$/g, "")  // remove all $...$ spans
      .replace(/\\&/g, ",")       // treat \& as comma separator
      .replace(/[{}]/g, "")       // remove stray braces
      .replace(/\s+/g, " ");      // collapse whitespace

    const names = stripped
      .split(/,/)
      .map((n) => n.trim())
      .filter((n) => n.length > 2 && /[A-Z]/.test(n));

    for (const name of names) {
      authors.push({ name });
    }
  }

  if (authors.length === 0) {
    authors.push({ name: "Chelsea E. Liekhus-Schmaltz" });
    authors.push({ name: "et al." });
  }

  return { authors, authors_raw: authorsRaw };
}

// --- section extraction ---

function extractSections(latex: string): Section[] {
  const sections: Section[] = [];
  let sectionCounter = 0;

  // Get body between \begin{document} and \end{document}
  const bodyMatch = latex.match(/\\begin\{document\}([\s\S]*)\\end\{document\}/);
  if (!bodyMatch) return sections;
  const body = bodyMatch[1];

  // Extract abstract
  const abstractMatch = body.match(/\\begin\{abstract\}([\s\S]*?)\\end\{abstract\}/);
  if (abstractMatch) {
    sections.push({
      id: "sec-abstract",
      type: "abstract",
      heading: "Abstract",
      content: [{ type: "paragraph", text: cleanLatexText(abstractMatch[1].trim()) }],
    });
  }

  // Split the rest by \section*{...}
  const sectionRegex = /\\section\*\{([^}]+)\}/g;
  const sectionStarts: { heading: string; index: number }[] = [];
  let m;
  while ((m = sectionRegex.exec(body)) !== null) {
    sectionStarts.push({ heading: m[1], index: m.index + m[0].length });
  }

  for (let i = 0; i < sectionStarts.length; i++) {
    const start = sectionStarts[i].index;
    const end = i + 1 < sectionStarts.length ? sectionStarts[i + 1].index - sectionStarts[i + 1].heading.length - 12 : body.length;
    const heading = sectionStarts[i].heading;
    const rawContent = body.slice(start, end).trim();
    sectionCounter++;

    const sType = guessSectionType(heading);
    const sId = `sec-${sectionCounter}`;

    if (sType === "references") {
      sections.push({
        id: sId,
        type: sType,
        heading,
        content: parseReferences(rawContent),
      });
    } else {
      sections.push({
        id: sId,
        type: sType,
        heading,
        content: parseBlocks(rawContent),
      });
    }
  }

  // If there's content between abstract and first section, add as introduction
  if (abstractMatch && sectionStarts.length > 0) {
    const afterAbstract = body.indexOf("\\end{abstract}") + "\\end{abstract}".length;
    const beforeFirstSection = body.indexOf("\\section*{");
    if (beforeFirstSection > afterAbstract) {
      const introContent = body.slice(afterAbstract, beforeFirstSection).trim();
      if (introContent.length > 100) {
        const introBlocks = parseBlocks(introContent);
        if (introBlocks.length > 0) {
          sections.splice(1, 0, {
            id: "sec-intro",
            type: "introduction",
            heading: "Introduction",
            content: introBlocks,
          });
        }
      }
    }
  }

  return sections;
}

function guessSectionType(heading: string): SectionType {
  const h = heading.toLowerCase();
  if (h.includes("abstract")) return "abstract";
  if (h.includes("introduction")) return "introduction";
  if (h.includes("method") || h.includes("experimental")) return "methods";
  if (h.includes("result")) return "results";
  if (h.includes("discussion")) return "discussion";
  if (h.includes("reference")) return "references";
  if (h.includes("appendix") || h.includes("supplementary")) return "appendix";
  return "custom";
}

function parseBlocks(raw: string): Block[] {
  const blocks: Block[] = [];
  // Remove \footnotetext blocks entirely
  const cleaned = raw.replace(/\\footnotetext\{[\s\S]*?\}(?=[A-Z\n\\])/g, "");

  // Split by equation and figure environments
  const parts = cleaned.split(/(\\begin\{equation\*?\}[\s\S]*?\\end\{equation\*?\}|\\begin\{figure\}[\s\S]*?\\end\{figure\})/);

  for (const part of parts) {
    const trimmed = part.trim();
    if (!trimmed) continue;

    if (trimmed.startsWith("\\begin{equation")) {
      const texMatch = trimmed.match(/\\begin\{equation\*?\}\s*([\s\S]*?)\s*\\end\{equation\*?\}/);
      if (texMatch) {
        let tex = texMatch[1].trim();
        let label: string | undefined;
        const tagMatch = tex.match(/\\tag\{(\d+)\}/);
        if (tagMatch) {
          label = tagMatch[1];
          tex = tex.replace(/\\tag\{\d+\}/, "").trim();
        }
        blocks.push({ type: "equation", tex, label });
      }
    } else if (trimmed.startsWith("\\begin{figure}")) {
      const figBlock = parseFigure(trimmed);
      if (figBlock) blocks.push(figBlock);
    } else {
      // Paragraph text — split on double newlines
      const paragraphs = trimmed.split(/\n\n+/);
      for (const p of paragraphs) {
        const text = cleanLatexText(p.trim());
        if (text.length > 10) {
          blocks.push({ type: "paragraph", text });
        }
      }
    }
  }

  return blocks;
}

function parseFigure(raw: string): Block | null {
  const srcMatch = raw.match(/\\includegraphics\[.*?\]\{([^}]+)\}/);
  const captionMatch = raw.match(/\\caption\{([\s\S]*?)\}(?=\s*\\end)/);

  if (!captionMatch) return null;

  let caption = cleanLatexText(captionMatch[1].trim());
  let label: string | undefined;

  // Extract "Figure N |" pattern from caption
  const labelMatch = caption.match(/^(Figure \d+)\s*\|\s*/);
  if (labelMatch) {
    label = labelMatch[1];
    caption = caption.slice(labelMatch[0].length);
  }

  return {
    type: "figure",
    src: srcMatch ? srcMatch[1] : "",
    alt: label || "Figure",
    caption,
    label,
  };
}

function parseReferences(raw: string): Block[] {
  const enumMatch = raw.match(/\\begin\{enumerate\}([\s\S]*?)\\end\{enumerate\}/);
  if (!enumMatch) return [{ type: "paragraph", text: cleanLatexText(raw) }];

  const items: string[] = [];
  const itemRegex = /\\item\s+([\s\S]*?)(?=\\item|$)/g;
  let m;
  while ((m = itemRegex.exec(enumMatch[1])) !== null) {
    items.push(cleanLatexText(m[1].trim()));
  }

  return [{ type: "list", ordered: true, items }];
}

// --- text cleaning ---

function cleanLatexText(text: string): string {
  return text
    // Remove \captionsetup
    .replace(/\\captionsetup\{[^}]*\}/g, "")
    // Convert \textbf, \textit, \emph
    .replace(/\\textbf\{([^}]+)\}/g, "$1")
    .replace(/\\textit\{([^}]+)\}/g, "$1")
    .replace(/\\emph\{([^}]+)\}/g, "$1")
    // Convert \href{url}{text} to text
    .replace(/\\href\{[^}]+\}\{([^}]+)\}/g, "$1")
    // Remove \label, \ref patterns
    .replace(/\\label\{[^}]+\}/g, "")
    // Keep \mathrm, \mathring etc. inside $ $ for KaTeX
    // Remove line-continuation backslashes
    .replace(/\\\\\s*$/gm, "")
    // Collapse whitespace
    .replace(/\s+/g, " ")
    .trim();
}
