#!/usr/bin/env python3
"""
Example usage of The Advisor pipeline.

This script demonstrates how to:
1. Set up the orchestrator with database
2. Run validation on a paper
3. Retrieve and display results
"""

from pathlib import Path

from advisor_pipeline.orchestrator import AdvisorOrchestrator
from utils import load_paper


def example_basic_usage():
    """Basic example: Run pipeline on a paper without database."""

    paper_folder = Path('/Users/chelsea/python_projects/project_files/shumlak2009_latex')

    loaded_paper = load_paper.load_paper_from_file(
        paper_file=paper_folder / 'main_text.tex',
        figure_folder=paper_folder / 'images',
        bib_file=paper_folder / 'bib.tex')

    # Initialize orchestrator (no database for this basic example)
    orchestrator = AdvisorOrchestrator()

    # Run validation

    result = orchestrator.run(
        paper_text=loaded_paper["paper_text"],
        figures=loaded_paper["figures"],
        paper_bib=loaded_paper["bib_text"],
        output_folder=paper_folder,
    )

    # Display results
    print("\n" + "=" * 60)
    print("VALIDATION RESULTS")
    print("=" * 60)
    print(f"Main Claim: {result.paper_structure.main_claim}")
    print(f"Logical Steps: {len(result.paper_structure.logical_steps)}")
    print(f"Confidence Score: {result.confidence_score:.2%}")
    print(f"\nOverall Review:\n{result.overall_assessment.review}")
    print("=" * 60 + "\n")

    return result


if __name__ == "__main__":
    print("The Advisor Pipeline - Example Usage\n")

    # Choose which example to run
    print("Running basic example...")
    result = example_basic_usage()

    print("\nDone!")
