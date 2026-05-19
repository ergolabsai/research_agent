// SPDX-FileCopyrightText: 2026 Chelsea Liekhus-Schmaltz and Johnathon Barhydt
//
// SPDX-License-Identifier: AGPL-3.0-only

/**
 * Pre-converted demo paper fixture.
 *
 * Imports demo_paper.tex as a raw string and converts it to ContentJson
 * at module-load time. Used by mockApi.ts to populate the demo document.
 */

import demoTexRaw from "./demo_paper.tex?raw";
import { latexToContentJson } from "../utils/contentJsonUtils";

export const demoPaperContentJson = latexToContentJson(demoTexRaw);

export const demoPaperContentString = JSON.stringify(demoPaperContentJson);

export const demoPaperTitle =
  "Ultrafast isomerization initiated by X-ray core ionization";
