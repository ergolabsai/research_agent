/**
 * Agent toggle config for mock mode.
 *
 * Each flag controls whether the mock pipeline result includes output for
 * that agent. The UI tabs are always rendered; disabling an agent simply
 * causes that tab to show its empty/fallback state — identical to a real
 * run where that agent produced no output.
 *
 * Set in frontend/.env.mock (or any .env.* Vite mode file):
 *   VITE_MOCK_MATH=false      → math_validations omitted from result
 *   VITE_MOCK_FIGURES=false   → figure_validations omitted from all steps
 *   VITE_MOCK_CITATIONS=false → related_papers omitted from result
 */

function flag(key: string, defaultValue = true): boolean {
  const raw = import.meta.env[key];
  if (raw === undefined || raw === "") return defaultValue;
  return raw !== "false";
}

export const MOCK_AGENTS = {
  math: flag("VITE_MOCK_MATH"),
  figures: flag("VITE_MOCK_FIGURES"),
  citations: flag("VITE_MOCK_CITATIONS"),
} as const;
