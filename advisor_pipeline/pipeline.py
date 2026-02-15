from typing import Callable, Dict, Any, Optional
from pathlib import Path
import json

from advisor_pipeline.agents.logic_mapping_agent import LogicMappingAgent
from advisor_pipeline.agents.evidence_finder_agent import EvidenceFinderAgent
from advisor_pipeline.agents.figure_evaluator_agent import FigureEvaluatorAgent
from advisor_pipeline.agents.math_evaluator_agent import MathEvaluatorAgent
from advisor_pipeline.agents.citation_checker_agent import CitationCheckerAgent
from advisor_pipeline.agents.results_compiler_agent import ResultsCompilerAgent

from advisor_pipeline.models.schemas import (
    PaperDocument,
    ValidationResult,
    PaperStructure,
    StepEvidence
)
from advisor_pipeline.database import Database


class AdvisorPipeline:
    """
    Main orchestrator for The Advisor validation pipeline.
    
    Runs all 6 steps in sequence:
    1. Logic Mapper - identify logical steps
    2. Evidence Finder - find supporting evidence
    3. Figure Evaluator - validate figure evidence
    4. Math Evaluator - validate mathematical evidence
    5. Citation Checker - verify citations
    6. Results Compiler - synthesize final assessment
    """
    
    def __init__(self, mcp_client=None, db: Database = None):
        """
        Initialize the pipeline with all agents.

        Args:
            mcp_client: MCP calculator client (required for math validation)
            db: Database instance (optional, for persistence)
            on_step: Callback(step_number, step_name) called at the start of each step
        """
        print("Initializing Advisor Pipeline...")
        
        # Initialize database
        self.db = db
        if self.db:
            self.db.connect()
        
        # Initialize all agents
        print("Loading agents...")
        self.logic_mapper = LogicMappingAgent()
        self.evidence_finder = EvidenceFinderAgent()
        self.figure_evaluator = FigureEvaluatorAgent()
        self.math_evaluator = MathEvaluatorAgent(mcp_client=mcp_client)
        self.citation_checker = CitationCheckerAgent()
        self.results_compiler = ResultsCompilerAgent()
        
        print("✓ Pipeline initialized successfully")
    
    def run(self, paper_id: str, paper_text: str, title: str, figures: Dict[str, str] = None, authors: list[str] = None,
            abstract: str = "", bibliography: Dict[str, str] = None, save_to_db: bool = True) -> ValidationResult:
        """
        Run the complete validation pipeline on a paper.
        
        Args:
            paper_id: Unique identifier for the paper
            paper_text: Full text of the paper
            title: Paper title
            figures: Dict mapping figure names to file paths
            authors: List of author names
            abstract: Paper abstract
            bibliography: Dict of citation references
            save_to_db: Whether to save to database
            
        Returns:
            ValidationResult with complete assessment
        """
        print(f"\n{'='*60}")
        print(f"Running validation pipeline for: {title}")
        print(f"Paper ID: {paper_id}")
        print(f"{'='*60}\n")
        
        # Save paper to database if requested
        if save_to_db and self.db:
            paper_doc = PaperDocument(
                paper_id=paper_id,
                title=title,
                authors=authors or [],
                abstract=abstract,
                full_text=paper_text,
                figures=figures or {}
            )
            self.db.save_paper(paper_doc)
            print("✓ Paper saved to database\n")
        
        # Step 1: Read paper and identify logical steps
        print("STEP 1: Reading paper and identifying logical steps...")
        paper_structure = self._run_step_1(paper_text, title)
        print(f"✓ Identified {len(paper_structure.logical_steps)} logical steps\n")
        
        # Step 2: Find evidence for each step
        print("STEP 2: Finding evidence for each logical step...")
        step_evidence = self._run_step_2(paper_structure, paper_text)
        total_evidence = sum(len(se.evidence_list) for se in step_evidence)
        print(f"✓ Found {total_evidence} pieces of evidence across all steps\n")
        
        # Step 3: Evaluate figure-based evidence
        if self._on_step:
            self._on_step(3, "Evaluating figures")
        print("STEP 3: Evaluating figure-based evidence...")
        figure_evaluations = self._run_step_3(step_evidence, figures or {}, paper_structure)
        print(f"✓ Evaluated {len(figure_evaluations)} figures\n")
        
        # Step 4: Evaluate mathematical evidence
        if self._on_step:
            self._on_step(4, "Validating math")
        print("STEP 4: Validating mathematical evidence...")
        math_evaluations = self._run_step_4(step_evidence, paper_text, paper_structure)
        print(f"✓ Validated {len(math_evaluations)} mathematical claims\n")
        
        # Step 5: Check citations
        if self._on_step:
            self._on_step(5, "Checking citations")
        print("STEP 5: Verifying citations...")
        citation_checks = self._run_step_5(step_evidence, paper_text, bibliography or {}, paper_structure)
        print(f"✓ Checked {len(citation_checks)} citations\n")
        
        # Step 6: Compile results
        if self._on_step:
            self._on_step(6, "Compiling results")
        print("STEP 6: Compiling final assessment...")
        validation_result = self._run_step_6(
            paper_id,
            paper_structure,
            step_evidence,
            figure_evaluations,
            math_evaluations,
            citation_checks
        )
        print(f"✓ Final confidence score: {validation_result.confidence_score:.2%}\n")
        
        # Save validation to database
        if save_to_db and self.db:
            self.db.save_validation(validation_result, paper_id)
            print("✓ Validation saved to database\n")
        
        print(f"{'='*60}")
        print("Pipeline complete!")
        print(f"{'='*60}\n")
        
        return validation_result
    
    def _run_step_1(self, paper_text: str, title: str) -> PaperStructure:
        """Step 1: Read paper and identify logical steps."""
        return self.logic_mapper.run({
            "paper_text": paper_text,
            "title": title
        })
    
    def _run_step_2(self, paper_structure: PaperStructure, paper_text: str) -> list[StepEvidence]:
        """Step 2: Find evidence for each step."""
        return self.evidence_finder.run({
            "paper_structure": paper_structure,
            "paper_text": paper_text
        })
    
    def _run_step_3(
        self,
        step_evidence: list[StepEvidence],
        figures: Dict[str, str],
        paper_structure: PaperStructure
    ) -> list:
        """Step 3: Evaluate figure evidence."""
        # Collect all evidence
        all_evidence = []
        for se in step_evidence:
            all_evidence.extend(se.evidence_list)
        
        # Create claims dict
        claims = {
            step.step_number: step.description
            for step in paper_structure.logical_steps
        }
        
        return self.figure_evaluator.run({
            "evidence_list": all_evidence,
            "figures": figures,
            "claims": claims
        })
    
    def _run_step_4(
        self,
        step_evidence: list[StepEvidence],
        paper_text: str,
        paper_structure: PaperStructure
    ) -> list:
        """Step 4: Validate mathematical evidence."""
        # Collect all evidence
        all_evidence = []
        for se in step_evidence:
            all_evidence.extend(se.evidence_list)
        
        # Create claims dict
        claims = {
            step.step_number: step.description
            for step in paper_structure.logical_steps
        }
        
        return self.math_evaluator.run({
            "evidence_list": all_evidence,
            "paper_text": paper_text,
            "claims": claims
        })
    
    def _run_step_5(
        self,
        step_evidence: list[StepEvidence],
        paper_text: str,
        bibliography: Dict[str, str],
        paper_structure: PaperStructure
    ) -> list:
        """Step 5: Check citations."""
        # Collect all evidence
        all_evidence = []
        for se in step_evidence:
            all_evidence.extend(se.evidence_list)
        
        # Create claims dict
        claims = {
            step.step_number: step.description
            for step in paper_structure.logical_steps
        }
        
        return self.citation_checker.run({
            "evidence_list": all_evidence,
            "paper_text": paper_text,
            "bibliography": bibliography,
            "claims": claims
        })
    
    def _run_step_6(
        self,
        paper_id: str,
        paper_structure: PaperStructure,
        step_evidence: list[StepEvidence],
        figure_evaluations: list,
        math_evaluations: list,
        citation_checks: list
    ) -> ValidationResult:
        """Step 6: Compile results."""
        return self.results_compiler.run({
            "paper_id": paper_id,
            "paper_structure": paper_structure,
            "step_evidence": step_evidence,
            "figure_evaluations": figure_evaluations,
            "math_evaluations": math_evaluations,
            "citation_checks": citation_checks
        })
    
    def load_from_database(self, paper_id: str) -> Optional[ValidationResult]:
        """Load the latest validation for a paper from database."""
        if not self.db:
            raise ValueError("Database not initialized")
        
        return self.db.get_latest_validation(paper_id)
    
    def __del__(self):
        """Cleanup on deletion."""
        if self.db:
            self.db.disconnect()
