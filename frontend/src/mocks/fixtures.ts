/**
 * Preloaded fixture data for mock mode (VITE_MOCK_API=true).
 *
 * This is the single source of truth for the demo paper used in the
 * frontend's mock pipeline. The formula entries mirror rows in the
 * backend SQLite `formula` table (ml_validation category) so that
 * mock math_validations can correctly reference real formula_ids.
 */

// ---------------------------------------------------------------------------
// Formula table fixtures (mirrors backend `formula` rows, ml_validation cat)
// ---------------------------------------------------------------------------

export interface FormulaFixture {
  formula_id: string;
  name: string;
  description: string;
  /** Python-evaluable equation string stored in the DB */
  equation: string;
  /** Display-friendly version for the UI equation hero */
  equation_display: string;
  variables: string[];
  category: string;
  tags: string[];
}

export const formulas: FormulaFixture[] = [
  {
    formula_id: "confidence_aggregation",
    name: "Confidence Aggregation",
    description:
      "Weighted sum of sub-scores into a final confidence value C_final ∈ [0,1].",
    equation:
      "C_final = 0.35 * S_evidence + 0.25 * S_figure + 0.25 * S_math + 0.15 * S_citation",
    equation_display:
      "C_final = 0.35·S_evidence + 0.25·S_figure + 0.25·S_math + 0.15·S_citation",
    variables: ["C_final", "S_evidence", "S_figure", "S_math", "S_citation"],
    category: "ml_validation",
    tags: ["confidence", "aggregation", "scoring", "ml_validation"],
  },
  {
    formula_id: "citation_scoring",
    name: "Citation Scoring",
    description:
      "Combines semantic relevancy and directional convergence into a single citation score.",
    equation: "S_citation = mean(relevancy_i * (1 + convergence_i))",
    equation_display: "S_citation = mean(relevancy_i · (1 + convergence_i))",
    variables: ["S_citation", "relevancy_i", "convergence_i"],
    category: "ml_validation",
    tags: ["citation", "scoring", "convergence", "ml_validation"],
  },
  {
    formula_id: "plot_agreement",
    name: "Plot Agreement",
    description:
      "Scores trend agreement between extracted and predicted curves; 1 = perfect match.",
    equation:
      "E_plot = 1 - abs(slope_true - slope_pred) / max(abs(slope_true), 1e-6)",
    equation_display:
      "E_plot = 1 − |slope_true − slope_pred| / max(|slope_true|, ε)",
    variables: ["E_plot", "slope_true", "slope_pred"],
    category: "ml_validation",
    tags: ["figures", "plot", "agreement", "ml_validation"],
  },
  {
    formula_id: "contradiction_penalty",
    name: "Contradiction Penalty",
    description:
      "Reduces final confidence based on unverified claims and inconsistent figures. Clipped at 0.35.",
    equation:
      "Penalty = 0.1 * N_unverified_claims + 0.07 * N_inconsistent_figures",
    equation_display: "Penalty = 0.1·N_unverified + 0.07·N_inconsistent",
    variables: ["Penalty", "N_unverified_claims", "N_inconsistent_figures"],
    category: "ml_validation",
    tags: ["penalty", "contradiction", "confidence", "ml_validation"],
  },
];

/** Look up display equation text by formula_id. */
export function getEquationDisplay(formulaId: string): string | undefined {
  return formulas.find((f) => f.formula_id === formulaId)?.equation_display;
}

// ---------------------------------------------------------------------------
// Paper fixture
// ---------------------------------------------------------------------------

export const paperTitle =
  "Ultrafast isomerization initiated by X-ray core ionization";

export const paperAuthors = [
  "B. Erk",
  "R. Boll",
  "S. Trippel",
  "D. Anielski",
  "L. Foucar",
  "B. Rudek",
  "S. W. Epp",
  "R. Coffee",
  "et al.",
];

export const paperHighlights = [
  "First X-ray pump / X-ray probe measurement at an X-ray FEL",
  "Proton migration begins within 12 fs of core ionization",
  "Four-particle coincident detection with Coulomb explosion imaging",
];

export const paperSections = [
  {
    heading: "Abstract",
    body: "We report the first X-ray pump / X-ray probe measurement of ultrafast molecular dynamics using four-particle coincident detection at an X-ray free-electron laser. By core-ionizing carbon K-shell electrons in deuterated acetylene (C₂D₂) and probing the resulting nuclear dynamics via Coulomb explosion imaging, we observe that significant proton (deuteron) migration associated with acetylene-to-vinylidene isomerization begins within the first 12 femtoseconds following X-ray core ionization.",
  },
  {
    heading: "1. Introduction",
    body: "Acetylene-to-vinylidene isomerization on the dication potential energy surface has been observed following inner-shell ionization, but previous measurements lacked time resolution. Transition-state theory applied to the 2.3 eV barrier on the ¹Σ_g⁺ surface predicts picosecond timescales, yet strong-field experiments suggest isomerization occurs within ~90 fs. We use X-ray pump / X-ray probe at LCLS to directly measure the timescale of this process.",
  },
  {
    heading: "2. Experimental Method",
    body: "A 400 eV X-ray pump pulse (up to 10 fs, 100 μJ) core-ionizes C₂D₂, producing C₂D₂⁺ via carbon 1s photoionization. Auger relaxation creates the dication C₂D₂²⁺. A second X-ray pulse produces C₂D₂⁴⁺ which Coulomb-explodes into C⁺/C⁺/D⁺/D⁺. All four fragments are detected in coincidence using momentum imaging with conservation constraints.",
  },
  {
    heading: "3. Observable Definition",
    body: "The CCD angle θ, defined via deuteron momenta using Equation 1, serves as an approximate measure of the molecular bending angle. Acetylene-like events (θ near 180°) and vinylidene-like events (θ < 180°) are separated. The angle is approximate: fragment momenta in four-body Coulomb explosion need not point along instantaneous bond directions.",
  },
  {
    heading: "4. Results",
    body: "At zero delay, maximum momentum localization is observed consistent with near-linear geometry. At 12 fs, an increase in CCD bending angle spread indicates onset of isomerization. Progressive delocalization continues at 25, 50, and 100 fs. The signal ratio shows possible vibrational coherence signatures. Three-fragment coincidence analysis corroborates these findings.",
  },
  {
    heading: "5. Mechanistic Interpretation",
    body: "We propose that geometry change during the ~6 fs core-hole lifetime contributes to the ultrafast isomerization. Calculations show the bending potential in the core-ionized cation has decreased vibrational constant and increased anharmonicity, leading to wavepacket broadening before Auger decay. This implies the standard Franck-Condon picture gives distorted initial conditions on the dication surface, and transition-state theory is insufficient to account for the observed dynamics.",
  },
];

// ---------------------------------------------------------------------------
// Validation result fixture — matches backend ValidationResult shape exactly.
// Data from real pipeline output for "Ultrafast isomerization initiated by
// X-ray core ionization" (validation_results.md).
// ---------------------------------------------------------------------------

const overallReview = `## Comprehensive Review: "Ultrafast isomerization initiated by X-ray core ionization"

### 1. Summary of the Main Claim

The paper claims that proton (deuteron) migration associated with acetylene-to-vinylidene isomerization begins within the first 12 femtoseconds following X-ray core ionization of carbon K-shell electrons — a timescale comparable to the Auger decay lifetime (~6 fs). The authors argue this implies that molecular geometry changes during the core-hole lifetime itself, and that transition-state theory applied solely to the dication potential energy surface cannot account for the observed ultrafast dynamics.

### 2. Strengths of the Paper

**Experimental Design (Steps 3–6):**
The X-ray pump / X-ray probe scheme at LCLS is cleverly designed. The use of a second X-ray pulse to produce a tetracation (4+) that Coulomb-explodes into four fragments is an elegant way to achieve time-resolved structural information. The argument that the 4+ charge state is essentially inaccessible from a single X-ray photon (Step 5) is well-supported and provides a clean separation of pump-probe events from single-pulse background. The use of deuterated acetylene (C₂D₂) to eliminate proton contamination from water/contaminants (Step 4) is a sensible experimental precaution.

**Mathematical Rigor:**
All seven mathematical validations returned as valid, covering the momentum analysis equations, the angular definitions (Equations 1–2), and the Franck-Condon overlap argument. This is a strong indicator that the quantitative framework is internally consistent and correctly implemented.

**Four-body Coincidence Detection (Step 6):**
The momentum conservation and charge conservation constraints applied to identify true tetracation fragmentation events are rigorous. The corroboration from three-fragment coincidence analysis (Step 14) adds an independent check on the main findings.

**Consistency with Prior Work (Steps 1, 9–10):**
The KER distributions showing lower mean KER for V-like events compared to A-like events are consistent with Osipov et al.'s earlier synchrotron measurements. The argument that the same dicationic state distribution is created (Step 10) because the same non-resonant core ionization mechanism is used is logically sound.

**Time-resolved Data (Steps 11–13):**
The observation of maximum momentum localization at zero delay, followed by progressive delocalization at 12, 25, 50, and 100 fs, provides a compelling qualitative picture of nuclear dynamics unfolding in time.

---

### 3. Weaknesses and Concerns

**Approximate Nature of the Observable (Steps 7–8):**
The authors commendably acknowledge that the angle θ is only an approximate measure of the CCD bond angle, since fragment momenta in four-body Coulomb explosion are not required to point along instantaneous bond directions. This is a significant caveat. The possibility that relative rotation of CCD⁺ fragments could produce apparent V-like angles without true isomerization (Step 8) is a serious systematic concern that is acknowledged but not quantitatively bounded.

**Figure Evaluation Concerns:**
The figure evaluations reveal a notable number of contradictions alongside confirmations:

- Figure 1 (excitation_scheme.jpg): 12 similarities but 12 differences between actual and expected content. This is a concerning 1:1 ratio.
- Figure 3 (temporal_evolution): 19 similarities vs. 16 differences — a substantial number of discrepancies.
- Figure 2 (acetylene-vinylidene differentiation): 8 similarities vs. 10 differences, with more differences than similarities.

These discrepancy counts are high and suggest potential inconsistencies between the figures and the textual claims.

**The Core-Hole Dynamics Argument (Steps 16–18):**
The central mechanistic proposal — that geometry change during the ~6 fs core-hole lifetime contributes to the ultrafast isomerization — is physically plausible but rests on relatively thin direct evidence. The calculations of the bending potential in the core-excited singly charged ion (Step 17) show decreased vibrational constant and increased anharmonicity, which is suggestive but not conclusive.

The logical leap from "the potential is softer in the core-ionized state" to "this explains the ultrafast isomerization" (Steps 17→18→19) involves several assumptions:
- That the wavepacket evolution during ~6 fs produces geometrically significant displacement
- That this displacement and acquired momentum persist coherently through the Auger decay
- That the resulting initial conditions on the dication surface are sufficiently different from Franck-Condon predictions to overcome the 2.3 eV barrier

None of these are quantitatively demonstrated. The argument is suggestive rather than definitive.

**Vibrational Coherence Claim (Step 13):**
The suggestion that the increase at 12 fs followed by a decrease at 25 fs could be a signature of vibrational coherence is intriguing but speculative. With only a few time points and limited statistics, this oscillatory behavior could also be a statistical fluctuation.

**Transition-State Theory Argument (Step 19):**
The conclusion that transition-state theory is "insufficient" is logically valid given the premises, but the argument is somewhat circular: the observation of fast isomerization is used to argue that TST fails, and the core-hole dynamics are invoked to explain why TST fails.

---

### 4. Assessment of Related Literature

The librarian search returned 9 papers, all with near-zero relevancy scores (max 0.04) and zero convergence. All 9 are classified as neutral, and none are from the field of ultrafast molecular dynamics, X-ray science, or chemical physics.

This is a significant limitation of the validation: **the literature search completely failed to retrieve relevant work**. Key papers that should have been found include:
- Osipov et al.'s synchrotron work on acetylene dication isomerization
- Ibrahim et al. or similar work on strong-field acetylene isomerization (~90 fs timescale)
- Theoretical work on acetylene dication potential energy surfaces
- Work on core-hole dynamics and nuclear motion during Auger lifetimes

---

### 5. Logical Structure Assessment

The paper's logical structure is generally well-constructed across 20 steps:

- **Steps 1–2** establish the scientific gap (unexplained fast isomerization, no time resolution)
- **Steps 3–6** describe the experimental approach and its validity
- **Steps 7–8** define the observable and its limitations
- **Steps 9–10** connect to prior work for validation
- **Steps 11–14** present the time-resolved results
- **Step 15** addresses a potential systematic
- **Steps 16–19** provide the mechanistic interpretation
- **Step 20** discusses broader implications

The dependencies are logical: the interpretation (Steps 16–19) depends on the experimental results (Steps 11–14), which depend on the methodology (Steps 3–8), which is motivated by the gap (Steps 1–2). However, the interpretive chain from Steps 16 through 19 involves the weakest links.

---

### 6. Overall Assessment

**The paper presents a technically impressive experiment** — the first X-ray pump / X-ray probe measurement with four-particle coincident detection at an X-ray FEL. The experimental design is sound, the mathematical framework is valid, and the qualitative observation of ultrafast deuteron migration is convincing.

**The central observational claim** — that significant geometry change occurs within 12 fs — is reasonably well-supported by the data, though the approximate nature of the Coulomb explosion momentum-to-geometry mapping and the limited number of time points introduce uncertainty.

**The mechanistic interpretation** — that core-hole dynamics during the Auger lifetime drive the initial geometry change — is physically plausible and represents an interesting hypothesis, but it is not rigorously demonstrated.

**The literature validation is uninformative** due to the complete failure of the search to retrieve relevant papers from the correct field.

**Rating: The paper makes a significant experimental contribution with a plausible but incompletely demonstrated mechanistic interpretation. The observational claims are moderately strong; the mechanistic claims are suggestive but would benefit from more rigorous theoretical support.**`;

export const validationResult = {
  paper_id: "demo-paper-001",
  confidence_score: 0.776,
  overall_assessment: {
    review: overallReview,
  },
  paper_structure: {
    title: paperTitle,
    main_claim:
      "Significant proton (deuteron) migration associated with acetylene-to-vinylidene isomerization begins within the first 12 femtoseconds following X-ray core ionization of carbon K-shell electrons, occurring on a timescale comparable to the Auger relaxation that refills the K-shell vacancy (~6 fs), implying that molecular geometry changes during the core-hole lifetime and that transition-state theory applied to the dication potential energy surface alone is insufficient to account for the ultrafast proton migration.",
    logical_steps: [
      { step_number: 1, description: "Prior synchrotron measurements observed acetylene-to-vinylidene isomerization on the dication surface but lacked time resolution.", section: "Introduction" },
      { step_number: 2, description: "Strong-field experiments suggest isomerization within ~90 fs, but the mechanism and role of core-hole dynamics remain unknown.", section: "Introduction" },
      { step_number: 3, description: "X-ray pump / X-ray probe scheme at LCLS using 400 eV photons to core-ionize C₂D₂.", section: "Experimental Method" },
      { step_number: 4, description: "C₂D₂ (deuterated acetylene) was used instead of C₂H₂ to eliminate potential background contamination.", section: "Experimental Method" },
      { step_number: 5, description: "The 4+ charge state is nearly inaccessible from a single X-ray photon, providing clean pump-probe separation.", section: "Experimental Method" },
      { step_number: 6, description: "All four fragments (C⁺/C⁺/D⁺/D⁺) detected in coincidence using momentum imaging with conservation constraints.", section: "Experimental Method" },
      { step_number: 7, description: "The CCD angle θ is defined via deuteron momenta as an approximate measure of the molecular bending angle.", section: "Observable Definition" },
      { step_number: 8, description: "θ is only an approximate measure; fragment rotation could produce apparent V-like angles without true isomerization.", section: "Observable Definition" },
      { step_number: 9, description: "KER distributions show lower mean KER for V-like events compared to A-like events, consistent with Osipov et al.", section: "Results" },
      { step_number: 10, description: "The same dicationic state distribution is created because the same non-resonant core ionization mechanism is used.", section: "Results" },
      { step_number: 11, description: "At zero delay, maximum momentum localization is observed consistent with near-linear geometry.", section: "Results" },
      { step_number: 12, description: "At 12 fs, an increase in CCD bending angle spread indicates onset of isomerization.", section: "Results" },
      { step_number: 13, description: "Signal ratio shows possible vibrational coherence signature: increase at 12 fs followed by decrease at 25 fs.", section: "Results" },
      { step_number: 14, description: "Three-fragment coincidence analysis corroborates the four-fragment results.", section: "Results" },
      { step_number: 15, description: "Cross-correlation between X-ray pulses affects zero-delay calibration; double-core-hole formation is possible.", section: "Systematics" },
      { step_number: 16, description: "Geometry change during the ~6 fs core-hole lifetime of C₂D₂⁺ is non-negligible for light nuclei.", section: "Mechanistic Interpretation" },
      { step_number: 17, description: "Bending potential in the core-ionized cation shows decreased vibrational constant and increased anharmonicity.", section: "Mechanistic Interpretation" },
      { step_number: 18, description: "Wavepacket broadening before Auger decay distorts the Franck-Condon overlap with dication states.", section: "Mechanistic Interpretation" },
      { step_number: 19, description: "Transition-state theory applied to the dication surface alone is insufficient to explain the observed 12 fs onset.", section: "Mechanistic Interpretation" },
      { step_number: 20, description: "This demonstrates X-ray pump / X-ray probe with four-particle coincident detection as a 'molecular movie' technique at FELs.", section: "Broader Implications" },
    ],
  },
  step_validations: Object.fromEntries(
    Array.from({ length: 20 }, (_, i) => [
      String(i + 1),
      { evidence_count: Math.ceil(97 / 20) + (i < 17 ? 1 : 0), figure_validations: [], math_validations: [] },
    ]),
  ),
  related_papers: [] as Array<{
    paper_id: string;
    title: string;
    authors: string;
    abstract: string;
    source: string;
    venue: string;
    year: number;
    relevancy_score: number;
    relevancy_reasoning: string;
    convergence_score: number;
    convergence_reasoning: string;
  }>,
};

// ---------------------------------------------------------------------------
// Paper graph fixture — mirrors NetworkX node_link_data format produced by
// advisor_pipeline/models/paper_graph.py: build_paper_graph(),
// add_figure_evaluations(), add_math_evaluations(), add_librarian_results().
// ---------------------------------------------------------------------------
