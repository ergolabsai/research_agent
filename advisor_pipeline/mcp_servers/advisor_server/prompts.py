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
# Citation Checking (from citation_checker_agent.py)
# ---------------------------------------------------------------------------

CITATION_VERIFIER = """Verify this citation and assess whether it genuinely supports the claim.

Citation reference: {citation_location}
Full citation: {full_citation}
Claim it supports: {claim}
How the citing paper uses this source: {citation_description}

Tasks:
1. Extract the DOI if available
2. Search for the paper in academic databases
3. Get the abstract (which includes the Semantic Scholar URL and open-access PDF URL)
4. If a URL is available, use fetch_paper_content to read the source's actual content
5. **Critically compare** what the citing paper claims about this source vs. what the source actually says
6. Assess whether the citation is used consistently with the source — does the source actually support the specific claim being made?

Focus on identifying any misrepresentations, overstatements, or unsupported extrapolations from the cited source.
"""

CITATION_REPORTER = """Create a citation verification report:

Citation: {citation_location}
Full citation details: {full_citation}
Supports step {supports_step}: {claim}

Agent's investigation:
{agent_result}

Determine:
1. Whether the citation is accessible
2. Whether the source content is consistent with how it's referenced in the citing paper
3. Whether the source actually supports the specific claim being made
4. Any misrepresentations, overstatements, or unsupported extrapolations
5. Overall assessment: does this citation genuinely support the claim?

Include detailed notes about the consistency between the source and how it is cited.
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
- Citation checks: {num_citation_checks}

Detailed Results by Step:
{step_validations_text}

Figure Evaluation Results:
{figure_results_text}

Math Validation Results:
{math_results_text}

Citation Verification Results:
{citation_results_text}

Write a comprehensive review that:
1. Assesses the overall validity of the paper's claims
2. Highlights strong evidence and weak evidence
3. Notes any contradictions or unsupported claims
4. Discusses the quality of the logical argument structure
5. Provides an overall assessment
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
    "citation_verifier": CITATION_VERIFIER,
    "citation_reporter": CITATION_REPORTER,
    "results_compiler": RESULTS_COMPILER,
    "librarian": CONTEXT_MAKER,
}
