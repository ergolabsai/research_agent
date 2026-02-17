from typing import Any, Dict, List

from advisor_pipeline.agents.base_agent import BaseAgent
from advisor_pipeline.models.schemas import (
    PaperStructure,
    StepEvidence,
    FigureEvaluation,
    FigureClaimAssessment,
    MathEvaluation,
    CitationCheck,
    ValidationResult,
    OverAllReview
)


class ResultsCompilerAgent(BaseAgent):
    """
    Agent responsible for compiling all validation results into final assessment.
    
    Input: All previous agent outputs
    Output: ValidationResult with overall assessment
    """
    
    def __init__(self):
        super().__init__(
            name="ResultsCompiler",
            description="Synthesizes all evidence validations into overall paper assessment"
        )
        # This agent doesn't need tools - it's purely synthesis
        self.tools = []
        
        # We won't use the full agent executor for this one
        # Just direct LLM calls with Instructor
    
    def get_tools(self):
        """No tools needed for synthesis."""
        return []
    
    def run(self, input_data: Dict[str, Any]) -> ValidationResult:
        """
        Compile all validation results.
        
        Args:
            input_data: Must contain:
                - 'paper_id': str
                - 'paper_structure': PaperStructure
                - 'step_evidence': List[StepEvidence]
                - 'figure_evaluations': List[FigureEvaluation]
                - 'math_evaluations': List[MathEvaluation]
                - 'citation_checks': List[CitationCheck]
                
        Returns:
            ValidationResult with complete assessment
        """
        paper_id: str = input_data.get("paper_id", "unknown")
        paper_structure: PaperStructure = input_data.get("paper_structure")
        step_evidence: List[StepEvidence] = input_data.get("step_evidence", [])
        figure_evals: List[FigureEvaluation] = input_data.get("figure_evaluations", [])
        math_evals: List[MathEvaluation] = input_data.get("math_evaluations", [])
        citation_checks: List[CitationCheck] = input_data.get("citation_checks", [])
        
        if not paper_structure:
            raise ValueError("paper_structure is required")
        
        # Organize validations by step
        step_validations = self._organize_by_step(
            step_evidence,
            figure_evals,
            math_evals,
            citation_checks
        )
        
        # Generate overall review using Instructor
        review_prompt = f"""Synthesize the validation results for this paper:

Paper: {paper_structure.title}
Main Claim: {paper_structure.main_claim}

Logical Steps Analyzed: {len(paper_structure.logical_steps)}

Validation Summary:
- Figure evaluations: {len(figure_evals)}
- Math evaluations: {len(math_evals)}
- Citation checks: {len(citation_checks)}

Detailed Results by Step:
{self._format_step_validations(step_validations, paper_structure)}

Figure Evaluation Results:
{self._format_figure_results(figure_evals)}

Math Validation Results:
{self._format_math_results(math_evals)}

Citation Verification Results:
{self._format_citation_results(citation_checks)}

Write a comprehensive review that:
1. Assesses the overall validity of the paper's claims
2. Highlights strong evidence and weak evidence
3. Notes any contradictions or unsupported claims
4. Discusses the quality of the logical argument structure
5. Provides an overall assessment
"""
        
        overall_review = self.get_structured_output(
            prompt=review_prompt,
            response_model=OverAllReview
        )
        
        # Calculate confidence score
        confidence_score = self._calculate_confidence(
            figure_evals,
            math_evals,
            citation_checks,
            step_validations
        )
        
        # Compile final result
        result = ValidationResult(
            paper_id=paper_id,
            paper_structure=paper_structure,
            step_validations=step_validations,
            overall_assessment=overall_review,
            confidence_score=confidence_score
        )
        
        return result
    
    def _organize_by_step(
        self,
        step_evidence: List[StepEvidence],
        figure_evals: List[FigureEvaluation],
        math_evals: List[MathEvaluation],
        citation_checks: List[CitationCheck]
    ) -> Dict[int, Dict[str, any]]:
        """Organize all validations by which step they support."""
        
        step_validations = {}
        
        # Add evidence for each step
        for step_ev in step_evidence:
            step_num = step_ev.step_number
            step_validations[step_num] = {
                "evidence_count": len(step_ev.evidence_list),
                "evidence": step_ev.evidence_list,
                "figure_validations": [],
                "math_validations": [],
                "citation_validations": []
            }
        
        # Add figure evaluations (each figure may have multiple claim assessments for different steps)
        for fig_eval in figure_evals:
            for assessment in fig_eval.claim_assessments:
                step_num = assessment.supports_step
                if step_num in step_validations:
                    step_validations[step_num]["figure_validations"].append(fig_eval)
        
        # Add math evaluations
        for math_eval in math_evals:
            step_num = math_eval.supports_step
            if step_num in step_validations:
                step_validations[step_num]["math_validations"].append(math_eval)
        
        # Add citation checks
        for cit_check in citation_checks:
            step_num = cit_check.supports_step
            if step_num in step_validations:
                step_validations[step_num]["citation_validations"].append(cit_check)
        
        return step_validations
    
    def _format_step_validations(
        self,
        step_validations: Dict[int, Dict],
        paper_structure: PaperStructure
    ) -> str:
        """Format step validations for prompt."""
        lines = []
        
        for step in paper_structure.logical_steps:
            step_num = step.step_number
            validation = step_validations.get(step_num, {})
            
            lines.append(f"\nStep {step_num}: {step.description}")
            lines.append(f"  Evidence pieces: {validation.get('evidence_count', 0)}")
            lines.append(f"  Figure validations: {len(validation.get('figure_validations', []))}")
            lines.append(f"  Math validations: {len(validation.get('math_validations', []))}")
            lines.append(f"  Citation checks: {len(validation.get('citation_validations', []))}")
        
        return "\n".join(lines)
    
    def _format_figure_results(self, figure_evals: List[FigureEvaluation]) -> str:
        """Format figure evaluation results."""
        if not figure_evals:
            return "No figure evaluations performed"

        lines = []
        for fig in figure_evals:
            lines.append(f"\n- {fig.figure_name}:")
            lines.append(f"  Actual: {fig.actual_description[:150]}...")
            lines.append(f"  Expected: {fig.expected_description[:150]}...")
            lines.append(f"  Similarities: {len(fig.comparison.similarities)}, Differences: {len(fig.comparison.differences)}")
            for assessment in fig.claim_assessments:
                conf_count = len(assessment.validity.confirmations)
                cont_count = len(assessment.validity.contradictions)
                lines.append(f"  Step {assessment.supports_step}: {conf_count} confirmations, {cont_count} contradictions")

        return "\n".join(lines)
    
    def _format_math_results(self, math_evals: List[MathEvaluation]) -> str:
        """Format math validation results."""
        if not math_evals:
            return "No math evaluations performed"
        
        lines = []
        valid_count = sum(1 for m in math_evals if m.calculation_valid)
        lines.append(f"Valid calculations: {valid_count}/{len(math_evals)}")
        
        for math in math_evals:
            status = "✓ Valid" if math.calculation_valid else "✗ Invalid"
            lines.append(f"- {math.equation_reference}: {status}")
        
        return "\n".join(lines)
    
    def _format_citation_results(self, citation_checks: List[CitationCheck]) -> str:
        """Format citation check results."""
        if not citation_checks:
            return "No citation checks performed"
        
        accessible_count = sum(1 for c in citation_checks if c.accessible)
        supported_count = sum(1 for c in citation_checks if c.supports_claim is True)
        
        lines = [
            f"Accessible citations: {accessible_count}/{len(citation_checks)}",
            f"Citations supporting claims: {supported_count}/{accessible_count if accessible_count > 0 else 'N/A'}"
        ]
        
        return "\n".join(lines)
    
    def _calculate_confidence(
        self,
        figure_evals: List[FigureEvaluation],
        math_evals: List[MathEvaluation],
        citation_checks: List[CitationCheck],
        step_validations: Dict
    ) -> float:
        """
        Calculate overall confidence score (0-1).
        
        Based on:
        - Percentage of math validations that passed
        - Ratio of confirmations to contradictions in figures
        - Percentage of accessible and supporting citations
        - Coverage of evidence for each logical step
        """
        scores = []
        
        # Math validation score
        if math_evals:
            math_score = sum(1 for m in math_evals if m.calculation_valid) / len(math_evals)
            scores.append(math_score)
        
        # Figure validation score (across all claim assessments)
        if figure_evals:
            total_confirmations = sum(
                len(a.validity.confirmations)
                for f in figure_evals for a in f.claim_assessments
            )
            total_contradictions = sum(
                len(a.validity.contradictions)
                for f in figure_evals for a in f.claim_assessments
            )
            if total_confirmations + total_contradictions > 0:
                fig_score = total_confirmations / (total_confirmations + total_contradictions)
                scores.append(fig_score)
        
        # Citation score
        if citation_checks:
            accessible = [c for c in citation_checks if c.accessible]
            if accessible:
                cit_score = sum(1 for c in accessible if c.supports_claim) / len(accessible)
                scores.append(cit_score)
        
        # Evidence coverage score
        if step_validations:
            steps_with_evidence = sum(
                1 for v in step_validations.values()
                if v.get('evidence_count', 0) > 0
            )
            coverage_score = steps_with_evidence / len(step_validations)
            scores.append(coverage_score)
        
        # Average all scores
        return sum(scores) / len(scores) if scores else 0.5
