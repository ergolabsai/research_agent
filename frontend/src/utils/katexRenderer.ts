// SPDX-FileCopyrightText: 2026 Chelsea Liekhus-Schmaltz and Johnathon Barhydt
//
// SPDX-License-Identifier: AGPL-3.0-only

import katex from "katex";
import "katex/dist/katex.min.css";

/**
 * Render a LaTeX math string to an HTML string via KaTeX.
 * Returns an error placeholder on failure so the UI never crashes.
 */
export function renderMathToHtml(
  tex: string,
  displayMode: boolean,
): string {
  try {
    return katex.renderToString(tex, {
      displayMode,
      throwOnError: false,
      trust: true,
    });
  } catch (err) {
    const msg = err instanceof Error ? err.message : String(err);
    return `<span style="color:red;" title="${msg}">[math error]</span>`;
  }
}

/**
 * Replace all inline $...$ math in a text string with rendered KaTeX HTML.
 * Ignores escaped dollars (\$).
 */
export function renderInlineMath(text: string): string {
  // Match $...$ but not \$ or $$
  return text.replace(
    /(?<![\\$])\$(?!\$)(.+?)(?<![\\$])\$/g,
    (_match, tex: string) => renderMathToHtml(tex.trim(), false),
  );
}
