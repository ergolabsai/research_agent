/**
 * Structured document schema for scientific papers.
 *
 * Documents using this format store JSON.stringify(ContentJson) in the
 * existing `content` field.  Detection: if `content` parses as JSON with
 * a `version` field, it is structured; otherwise it is legacy plain text.
 */

// ---------------------------------------------------------------------------
// Section types — maps to journal template required-section lists
// ---------------------------------------------------------------------------

export type SectionType =
  | "abstract"
  | "introduction"
  | "methods"
  | "results"
  | "discussion"
  | "references"
  | "appendix"
  | "custom";

// ---------------------------------------------------------------------------
// Block types — content units within a section
// ---------------------------------------------------------------------------

export interface ParagraphBlock {
  type: "paragraph";
  /** Plain text, may contain inline $...$ math markers. */
  text: string;
}

export interface EquationBlock {
  type: "equation";
  /** Display-mode LaTeX source. */
  tex: string;
  /** Equation number label, e.g. "1" for Eq. (1). */
  label?: string;
}

export interface FigureBlock {
  type: "figure";
  src: string;
  alt: string;
  caption: string;
  label?: string;
}

export interface ListBlock {
  type: "list";
  ordered: boolean;
  items: string[];
}

export type Block = ParagraphBlock | EquationBlock | FigureBlock | ListBlock;

// ---------------------------------------------------------------------------
// Section
// ---------------------------------------------------------------------------

export interface Section {
  id: string;
  type: SectionType;
  heading: string;
  content: Block[];
}

// ---------------------------------------------------------------------------
// Author & metadata
// ---------------------------------------------------------------------------

export interface Author {
  name: string;
  affiliations?: number[];
  email?: string;
}

export interface DocumentMetadata {
  authors: Author[];
  /** Raw author line with LaTeX markup (superscript affiliations etc). */
  authors_raw?: string;
  affiliations?: string[];
  keywords?: string[];
  /** Future: journal template reference. */
  template_id?: string;
}

// ---------------------------------------------------------------------------
// Top-level document
// ---------------------------------------------------------------------------

export interface ContentJson {
  version: 1;
  metadata: DocumentMetadata;
  sections: Section[];
}
