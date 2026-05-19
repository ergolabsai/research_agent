// SPDX-FileCopyrightText: 2026 Chelsea Liekhus-Schmaltz and Johnathon Barhydt
//
// SPDX-License-Identifier: AGPL-3.0-only

/** Convert raw math validation details text into well-structured markdown. */
export function formatMathDetails(raw: string): string {
  return raw
    .split("\n")
    .map((line) => {
      const trimmed = line.trim();
      // ALL-CAPS lines ending with ":" → heading (e.g. "CRITICAL FINDINGS:")
      if (/^[A-Z][A-Z\s\-:]+:$/.test(trimmed)) {
        return `### ${trimmed}`;
      }
      // ALL-CAPS status lines like "VALIDATION STATUS: INCOMPLETE - CANNOT VERIFY"
      if (/^[A-Z][A-Z\s\-:]+:\s+[A-Z]/.test(trimmed) && !trimmed.startsWith("✗")) {
        return `### ${trimmed}`;
      }
      // ✗ lines → bold bullet items
      if (trimmed.startsWith("✗")) {
        const colonIdx = trimmed.indexOf(":", 1);
        if (colonIdx !== -1) {
          const label = trimmed.slice(0, colonIdx + 1);
          const rest = trimmed.slice(colonIdx + 1);
          return `- **${label}**${rest}`;
        }
        return `- ${trimmed}`;
      }
      return line;
    })
    .join("\n");
}
