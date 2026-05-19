// SPDX-FileCopyrightText: 2026 Chelsea Liekhus-Schmaltz and Johnathon Barhydt
//
// SPDX-License-Identifier: AGPL-3.0-only

import { createContext, useContext, useState, useCallback, type ReactNode } from "react";

export interface EvidenceHighlight {
  /** The text excerpt to highlight in the RichView */
  excerpt: string;
  /** Node ID from the graph (e.g. "evidence:citation:Introduction, first paragraph:1") */
  nodeId: string;
}

interface HighlightContextValue {
  highlight: EvidenceHighlight | null;
  setHighlight: (h: EvidenceHighlight | null) => void;
  clearHighlight: () => void;
}

const HighlightContext = createContext<HighlightContextValue | null>(null);

export function HighlightProvider({ children }: { children: ReactNode }) {
  const [highlight, setHighlight] = useState<EvidenceHighlight | null>(null);
  const clearHighlight = useCallback(() => setHighlight(null), []);

  return (
    <HighlightContext.Provider value={{ highlight, setHighlight, clearHighlight }}>
      {children}
    </HighlightContext.Provider>
  );
}

const noop = () => {};
const fallback: HighlightContextValue = {
  highlight: null,
  setHighlight: noop,
  clearHighlight: noop,
};

/** Returns highlight state. Safe to call outside a HighlightProvider (returns inert fallback). */
export function useHighlight(): HighlightContextValue {
  const ctx = useContext(HighlightContext);
  return ctx ?? fallback;
}
