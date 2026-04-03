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
  "A Multi-Agent Framework for Evidence-Grounded Scientific Claim Verification";

export const paperAuthors = [
  "Maya Chen",
  "Leandro Ruiz",
  "Nadia Patel",
  "Ergo Labs Research Group",
];

export const paperHighlights = [
  "142 benchmark manuscripts evaluated",
  "37.4% reduction in unsupported claim carry-through",
  "8-stage transparent agent workflow",
];

export const paperSections = [
  {
    heading: "Abstract",
    body: "We present an eight-stage advisor pipeline that decomposes claim verification into context extraction, structural mapping, evidence matching, visual consistency checks, symbolic validation, literature comparison, and confidence synthesis. Across 142 benchmark manuscripts, our framework reduces unsupported claim carry-through by 37.4% compared to single-pass reviewers.",
  },
  {
    heading: "1. Introduction",
    body: "Scientific writing increasingly mixes narrative argumentation, empirical visualizations, and symbolic derivations. Conventional reviewers are fast but brittle when claims depend on linked artifacts spread across sections. We propose a workflow where each stage produces typed artifacts for downstream checks and explicit contradiction tracking.",
  },
  {
    heading: "2. Method",
    body: "The orchestrator executes: make_context, gather_papers, map_logic, find_evidence, evaluate_figures, evaluate_math, score_papers, compile_results. Every stage logs intermediate outputs to preserve transparency. The global confidence is computed with weighted reliability factors for evidence density, visual agreement, symbolic validity, and citation convergence.",
  },
  {
    heading: "3. Key Equations",
    body: "Confidence aggregation uses Eq. (1) and convergence correction uses Eq. (2). Figure trend quality uses Eq. (3). Penalty for unresolved contradictions follows Eq. (4).",
  },
  {
    heading: "4. Results",
    body: "Our strongest gains appear in papers with dense figure references and nested equation dependencies. The largest residual errors occur when plots report smoothed values but equations are fit on unsmoothed measurements.",
  },
  {
    heading: "5. Discussion",
    body: "Agent disagreement is useful: false certainty drops when figure and math evaluators report mismatch. Citation scoring improves when convergence and relevance are jointly evaluated instead of relevance-only ranking.",
  },
];

// ---------------------------------------------------------------------------
// Validation result fixture — matches backend ValidationResult shape exactly,
// extended with `equation_text` and `formula_used` on math_validations.
// ---------------------------------------------------------------------------

export const validationResult = {
  paper_id: "demo-paper-001",
  confidence_score: 0.82,
  overall_assessment: {
    review:
      "The paper presents a coherent main claim with strong evidence density. Figure support is mostly " +
      "consistent, but one plot trend is overstated relative to numeric variance. Mathematical derivations " +
      "are valid after correcting a normalization constant in Eq. (1). Citation convergence is favorable " +
      "with one dissenting source that reflects a narrower sampling context.",
  },
  paper_structure: {
    title: paperTitle,
    main_claim:
      "A structured multi-agent pipeline improves the accuracy and transparency of scientific claim verification compared to single-pass review.",
    logical_steps: [
      {
        step_number: 1,
        description:
          "Establish baseline performance of unassisted reviewer pipelines.",
        section: "Introduction",
      },
      {
        step_number: 2,
        description:
          "Decompose verification into typed artifact-producing stages.",
        section: "Method",
      },
      {
        step_number: 3,
        description:
          "Validate confidence aggregation formula against benchmark papers.",
        section: "Key Equations",
      },
      {
        step_number: 4,
        description: "Measure reduction in unsupported claim carry-through.",
        section: "Results",
      },
    ],
  },
  step_validations: {
    "1": {
      evidence_count: 3,
      figure_validations: [
        {
          figure_name: "Figure 1: Baseline Reviewer Performance (Box Plot)",
          supports_step: 1,
          validity: {
            confirmations: [
              "Median accuracy of single-pass reviewers (72%) aligns with reported institutional benchmarks.",
              "Interquartile range shows consistency across domain categories.",
              "Outliers labeled and correspond to rare edge-case papers in the analysis.",
            ],
            contradictions: [],
          },
        },
        {
          figure_name: "Figure 1b: Reviewer Performance by Domain (Heatmap)",
          supports_step: 1,
          validity: {
            confirmations: [
              "Cell intensities correctly reflect performance deltas across 6 domains.",
            ],
            contradictions: [
              "Legend colormap doesn't match reported numeric ranges—appears shifted 0.05 units higher.",
            ],
          },
        },
      ],
      math_validations: [],
    },
    "2": {
      evidence_count: 4,
      figure_validations: [
        {
          figure_name: "Figure 2: Pipeline Stage Outputs (Stacked Bar)",
          supports_step: 2,
          validity: {
            confirmations: [
              "Total bar heights represent correct cumulative evidence counts per stage.",
              "Color segmentation by artifact type (context, query, logic, evidence) is accurate.",
              "Error bars reflect ±1 std dev across the 142 benchmark runs.",
            ],
            contradictions: [],
          },
        },
        {
          figure_name: "Figure 3: Residual Error Trend (Line Plot)",
          supports_step: 2,
          validity: {
            confirmations: [
              "Trendline shows expected efficiency gain in multi-stage vs single-pass.",
              "Shaded confidence band depicts ±2 std err correctly.",
            ],
            contradictions: [
              "Variance spike around epoch 20 contradicts the claim of 'strictly monotonic improvement'.",
              "Crossing event near epoch 30 suggests transient stage dependency not discussed in text.",
            ],
          },
        },
        {
          figure_name:
            "Figure 4: Convergence Decomposition (Pie Charts, 2×2 Grid)",
          supports_step: 2,
          validity: {
            confirmations: [
              "Citation convergence contribution is visible in all four subplots.",
              "Pie slice proportions sum correctly to 100% per subplot.",
              "Legend correctly labels all five components (evidence, figure, math, citation, other).",
            ],
            contradictions: [
              "Manuscript claims 'citation contributes ~40%' but Figure 4 shows 28–35% across panels.",
            ],
          },
        },
      ],
      math_validations: [],
    },
    "3": {
      evidence_count: 2,
      figure_validations: [
        {
          figure_name: "Figure 5: Confidence Aggregation Ablation (Line Plot)",
          supports_step: 3,
          validity: {
            confirmations: [
              "Final score (0.82) matches the reported weighted combination of sub-scores.",
              "Ablation curves show expected sensitivity across four weighting scenarios.",
            ],
            contradictions: [],
          },
        },
        {
          figure_name: "Figure 6: Coefficient Sensitivity Matrix (Heatmap)",
          supports_step: 3,
          validity: {
            confirmations: [
              "Diagonal entries correctly reflect variance in each sub-score dimension.",
              "Off-diagonal correlations are low (<0.15), supporting independence assumptions.",
            ],
            contradictions: [
              "Text claims 'near-orthogonal sub-scores', but several pairwise correlations reach 0.32.",
            ],
          },
        },
      ],
      math_validations: [
        {
          equation_reference: "Eq. (1)",
          equation_text:
            "C_final = 0.35·S_evidence + 0.25·S_figure + 0.25·S_math + 0.15·S_citation",
          formula_used: "confidence_aggregation",
          calculation_valid: true,
          details:
            "Weights verified to sum to 1.0. Validated against three benchmark results " +
            "using the confidence_aggregation formula from the MCP calculator.",
        },
        {
          equation_reference: "Eq. (3)",
          equation_text:
            "E_plot = 1 − |slope_true − slope_pred| / max(|slope_true|, ε)",
          formula_used: "plot_agreement",
          calculation_valid: false,
          details:
            "Inflection point offset is not accounted for in the current slope-ratio formulation. " +
            "The plot_agreement formula flags this as out-of-bounds for three figures.",
        },
        {
          equation_reference: "Eq. (4)",
          equation_text: "Penalty = 0.1·N_unverified + 0.07·N_inconsistent",
          formula_used: "contradiction_penalty",
          calculation_valid: true,
          details:
            "Penalty capped at 0.35 as documented. Verified with N_unverified=2, N_inconsistent=1 " +
            "producing Penalty=0.27, consistent with the reported 0.82 final confidence score.",
        },
      ],
    },
    "4": {
      evidence_count: 2,
      figure_validations: [
        {
          figure_name:
            "Figure 7: Benchmark Results—Unsupported Claim Reduction (Bar Chart)",
          supports_step: 4,
          validity: {
            confirmations: [
              "37.4% reduction achieved by multi-agent pipeline is clearly shown vs baseline.",
              "Error bars indicate 95% CI, non-overlapping with baseline confidence range.",
              "Results broken down by paper domain with consistent gains across categories.",
            ],
            contradictions: [],
          },
        },
        {
          figure_name: "Figure 8: Pipeline Runtime Scaling (Log-Log Plot)",
          supports_step: 4,
          validity: {
            confirmations: [
              "Runtime increases sub-linearly with paper length (exponent ≈ 0.78).",
              "Median cost per paper (~12 sec) aligns with reported inference budget.",
            ],
            contradictions: [
              "Outlier cluster at 2000 tokens suggests unaccounted-for stage dependency or queue effects.",
            ],
          },
        },
        {
          figure_name:
            "Figure 9: Confidence Distribution Across Benchmarks (Violin Plot)",
          supports_step: 4,
          validity: {
            confirmations: [
              "Mean confidence (0.73) and distribution shape support the reported variance across papers.",
              "Modal range (0.65–0.80) captures 68% of results, consistent with Gaussian fit.",
            ],
            contradictions: [],
          },
        },
      ],
      math_validations: [
        {
          equation_reference: "Eq. (2)",
          equation_text: "S_citation = mean(relevancy_i · (1 + convergence_i))",
          formula_used: "citation_scoring",
          calculation_valid: true,
          details:
            "Citation scoring formula verified. Mean over 4 papers yields S_citation=0.71, " +
            "consistent with the reported confidence breakdown.",
        },
      ],
    },
  },
  related_papers: [
    {
      paper_id: "cit-1",
      title: "Structured Verification Graphs for Scientific Reasoning",
      authors: "Smith, A., Jones, B., et al.",
      abstract:
        "Reports that typed reasoning graphs reduce unsupported conclusion propagation in review pipelines.",
      source: "semantic_scholar",
      venue: "NeurIPS",
      year: 2024,
      relevancy_score: 0.93,
      relevancy_reasoning:
        "Strongly aligns with our finding that explicit dependency edges improve contradiction detection.",
      convergence_score: 0.78,
      convergence_reasoning:
        "Supports the framework approach to structured claim verification.",
    },
    {
      paper_id: "cit-2",
      title: "Visual Claim Auditing with Latent Trend Models",
      authors: "Patel, N., Chen, M.",
      abstract:
        "Shows trend-based figure auditing succeeds on monotonic dynamics but struggles with abrupt regime shifts.",
      source: "lancedb_vector",
      venue: "ICLR",
      year: 2025,
      relevancy_score: 0.87,
      relevancy_reasoning:
        "Partially agrees. Our discrepancies show similar weakness around inflection-heavy figures.",
      convergence_score: 0.26,
      convergence_reasoning:
        "Partially converges—method agrees on smooth curves, diverges on variance-heavy sections.",
    },
    {
      paper_id: "cit-3",
      title: "Symbolic Consistency Checks in Multi-Agent Review",
      authors: "Ruiz, L., et al.",
      abstract:
        "Demonstrates that equation-context extraction can recover missing assumptions in mathematical claims.",
      source: "lancedb_fts",
      venue: "ACL Findings",
      year: 2025,
      relevancy_score: 0.81,
      relevancy_reasoning:
        "Supports our math assistant workflow where users enrich equation context before re-evaluation.",
      convergence_score: 0.64,
      convergence_reasoning:
        "Strong alignment: both papers advocate for symbolic context enrichment.",
    },
    {
      paper_id: "cit-4",
      title: "When Citation Similarity Misleads Scientific Validation",
      authors: "Garcia, R., Kim, S.",
      abstract:
        "Argues semantic similarity can inflate trust even when methodological assumptions diverge.",
      source: "semantic_scholar",
      venue: "arXiv",
      year: 2023,
      relevancy_score: 0.69,
      relevancy_reasoning:
        "Challenges our current scoring; suggests stronger penalties for methodological mismatch.",
      convergence_score: -0.31,
      convergence_reasoning:
        "Contradicts our approach of weighting semantic relevancy equally with convergence.",
    },
  ],
};

// ---------------------------------------------------------------------------
// Paper graph fixture — mirrors NetworkX node_link_data format produced by
// advisor_pipeline/models/paper_graph.py: build_paper_graph(),
// add_figure_evaluations(), add_math_evaluations(), add_librarian_results().
// ---------------------------------------------------------------------------
