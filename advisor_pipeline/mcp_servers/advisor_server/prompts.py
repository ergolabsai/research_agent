"""Prompt templates for the Advisor MCP server.

All prompts extracted from the original agent implementations and organized
as reusable templates that can be served via MCP or used directly.
"""

SYSTEM_PROMPT = """You are a scientist reviewing a new paper. Your job is to:
1. Identify the paper's main claim or thesis
2. Break down the argument into discrete logical steps
3. Identify dependencies between steps (which steps build on which)
4. Note which section each step appears in

Be precise and capture the logical flow of the argument, not just a summary.

You're job is also to remain highly skeptical of the author's conclusions.
You are looking for mistakes in logic and you should not assume their results are conclusive."""


# ---------------------------------------------------------------------------
# Context Enrichment (new — librarian)
# ---------------------------------------------------------------------------

CONTEXT_MAKER = """You are a research librarian helping to gather context for paper evaluation.
Generate context that will not bias you towards the authors conclusions by looking through papers that are related to this paper's topic.
Avoid including papers that include the authors in this paper.

Paper text:
{paper_text}
"""


# ---------------------------------------------------------------------------
# Logic Mapping (from logic_mapping_agent.py)
# ---------------------------------------------------------------------------

LOGIC_MAPPER = """Analyze the following research paper. Identify:
1. The paper's title
2. The paper's primary claim or thesis
3. The ordered logical steps of the argument, including what each step claims,
   which previous steps it depends on, and which section it appears in

Paper text:
{paper_text}"""


# ---------------------------------------------------------------------------
# Evidence Finding (from evidence_finder_agent.py)
# ---------------------------------------------------------------------------

EVIDENCE_FINDER = """Extract all evidence supporting this logical step from the research paper.

Step {step_number}: {step_description}
Section: {step_section}

Available figure files: {figure_names}

Paper text:
{paper_text}

List ALL evidence for this step. Each piece of evidence must have an evidence_type \
of "figure", "math", or "citation" — do NOT use "text" as a type.
- Figures (with figure numbers). When referencing a figure, use the exact filename \
from the available figure files list above.
- Math/equations (with equation numbers)
- Citations (with citation info)

For every evidence item, populate the `excerpt` field with a short verbatim quote \
(1-3 sentences) copied exactly from the paper text that directly supports the claim. \
This is especially important for capturing textual arguments — instead of listing them \
as separate "text" evidence, attach a supporting excerpt to the most relevant figure, \
math, or citation evidence item.

Be thorough - one step may have multiple pieces of evidence."""


# ---------------------------------------------------------------------------
# Figure Evaluation (from figure_evaluator_agent.py)
# ---------------------------------------------------------------------------

FIGURE_DESCRIBER = """Describe this scientific figure in detail in such a way \
that you think someone could reproduce it from your description.

Include:
1. The type of figure (plot, diagram, photograph, schematic, etc.)
2. Axes labels and ranges (if applicable)
3. Data trends, patterns, and key features
4. Any specific numerical values visible
5. Legends, annotations, or labels

Be precise and objective. Only describe what you can actually see."""

FIGURE_EXPECTED = """Based ONLY on the paper text below, describe what the \
figure "{figure_name}" should show.
Do NOT guess or infer beyond what the text explicitly states about this figure.
Include any specific values, trends, or features the text mentions about this figure.

Paper text:
{paper_text}"""

FIGURE_COMPARATOR = """Compare these two descriptions of a figure.

ACTUAL (from looking at the figure):
{actual_description}

EXPECTED (from the paper text):
{expected_description}

List the similarities (things that match between actual and expected) and
differences (things that don't match, are missing, or are unexpected).
Be specific and reference concrete details from both descriptions."""

CLAIM_ASSESSOR = """Assess whether the following claim is supported by figure "{figure_name}",
given the comparison between what the figure actually shows and what was expected.

Claim (step {supports_step}): {claim}

Actual figure description: {actual_description}
Expected figure description: {expected_description}

Similarities found:
{similarities}

Differences found:
{differences}

Full paper text:
{paper_text}

Based on the comparison above and the full paper text, list:
- Confirmations: specific ways the figure supports this claim
- Contradictions: specific ways the figure undermines or fails to support this claim"""


# ---------------------------------------------------------------------------
# Math Evaluation (from math_evaluator_agent.py)
# ---------------------------------------------------------------------------

MATH_VERIFIER = """Analyze this mathematical evidence:

Equation reference: {equation_location}
Purpose: {equation_description}
Supporting claim: {claim}

Context from paper:
{equation_context}

Tasks:
1. First, list available formulas to see what's in the calculator
2. Identify which formula matches this equation
3. Extract the numerical values and units from the paper
4. Use the calculator to verify the math
"""

MATH_REPORTER = """Create a mathematical validation report:

Equation: {equation_location}
Context: {equation_description}
Supports step {supports_step}: {claim}

Agent verification:
{agent_result}

Based on the agent's work with the MCP calculator, determine:
1. Whether the calculation is valid
2. What formula was used (if applicable)
3. Detailed explanation of findings
"""


# ---------------------------------------------------------------------------
# Librarian (replaces Citation Checking)
# ---------------------------------------------------------------------------

LIBRARIAN_QUERY_CRAFTER = """You are a research librarian. Given the following paper, generate 3–5 diverse,
high-quality search queries that would help find the most relevant related work
in an academic paper database.

Each query should target a different facet of the paper:
- Core methodology or technique
- Domain / application area
- Theoretical foundations or key equations
- Competing or alternative approaches
- Specific phenomena or datasets studied

Paper title: {title}
Main claim: {main_claim}

Abstract / key text:
{paper_text_excerpt}

Return ONLY the search queries, one per line. Make them natural-language
descriptions (not keyword lists) because they will be embedded for vector
similarity search."""

LIBRARIAN_SCORER = """You are a research analyst comparing two papers.

== USER-SUBMITTED PAPER ==
Title: {user_title}
Main claim: {user_main_claim}
Key text excerpt:
{user_excerpt}

== RELATED PAPER ==
Title: {related_title}
Authors: {related_authors}
Abstract: {related_abstract}
Source: {related_source}

Score this related paper on two dimensions:

1. **Relevancy** (0.0 – 1.0): How important is this related paper for
   evaluating the user's paper?  Consider topical overlap, methodological
   similarity, shared datasets, and whether the related paper's findings
   could confirm or challenge the user's claims.

2. **Convergence** (-1.0 – +1.0): How well do the conclusions align?
   +1.0 = the related paper strongly supports / agrees with the user's
   conclusions.
   0.0 = neutral or unrelated conclusions.
   -1.0 = the related paper strongly contradicts the user's conclusions.

   IMPORTANT: Both strongly positive AND strongly negative convergence
   scores are valuable.  Be precise and justify your score.

Provide reasoning for both scores."""

LIBRARIAN_CONTEXT = """You are a research librarian synthesising context for paper evaluation.

Below are related papers found for the user-submitted paper.  Summarise the
key themes, agreements, and disagreements across these related works so that
downstream evaluation agents can use this context to assess the user's paper
more rigorously.

Do NOT bias towards the user's conclusions — present the landscape neutrally.

User paper title: {user_title}
User main claim: {user_main_claim}

Related papers:
{related_papers_text}

Write a concise context summary (300–500 words) covering:
1. Common methodologies and findings in the related work
2. Where the related work agrees with the user's claims
3. Where the related work contradicts or challenges the user's claims
4. Notable gaps that the user's paper addresses (or fails to address)
"""


# ---------------------------------------------------------------------------
# Results Compilation (from results_compiler_agent.py)
# ---------------------------------------------------------------------------

RESULTS_COMPILER = """Synthesize the validation results for this paper:

Paper: {paper_title}
Main Claim: {main_claim}

Logical Steps Analyzed: {num_steps}

Validation Summary:
- Figure evaluations: {num_figure_evals}
- Math evaluations: {num_math_evals}
- Related papers found: {num_related_papers}

Detailed Results by Step:
{step_validations_text}

Figure Evaluation Results:
{figure_results_text}

Math Validation Results:
{math_results_text}

Librarian Results (Related Papers):
{librarian_results_text}

Write a comprehensive review that:
1. Assesses the overall validity of the paper's claims
2. Highlights strong evidence and weak evidence
3. Notes any contradictions or unsupported claims
4. Discusses the quality of the logical argument structure
5. Considers how related work (with relevancy and convergence scores) supports or undermines the claims
6. Provides an overall assessment
"""


# ---------------------------------------------------------------------------
# MCP Prompt registry (name -> template mapping)
# ---------------------------------------------------------------------------

PROMPT_REGISTRY = {
    "logic_mapper": LOGIC_MAPPER,
    "evidence_finder": EVIDENCE_FINDER,
    "figure_describer": FIGURE_DESCRIBER,
    "figure_expected": FIGURE_EXPECTED,
    "figure_comparator": FIGURE_COMPARATOR,
    "claim_assessor": CLAIM_ASSESSOR,
    "math_verifier": MATH_VERIFIER,
    "math_reporter": MATH_REPORTER,
    "librarian_query_crafter": LIBRARIAN_QUERY_CRAFTER,
    "librarian_scorer": LIBRARIAN_SCORER,
    "librarian_context": LIBRARIAN_CONTEXT,
    "results_compiler": RESULTS_COMPILER,
    "librarian": CONTEXT_MAKER,
}
