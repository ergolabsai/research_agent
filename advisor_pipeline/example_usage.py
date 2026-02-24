#!/usr/bin/env python3
"""
Example usage of The Advisor pipeline.

This script demonstrates how to:
1. Set up the orchestrator with database
2. Run validation on a paper
3. Retrieve and display results
"""

from pathlib import Path

from advisor_pipeline.database import Database
from advisor_pipeline.orchestrator import AdvisorOrchestrator
from utils import load_paper


def example_basic_usage():
    """Basic example: Run pipeline on a paper without database."""

    loaded_paper = load_paper.load_paper_from_file(
        paper_file=Path('/Users/chelsea/python_projects/project_files/shumlak2009_latex/main_text.tex'),
        figure_folder=Path('/Users/chelsea/python_projects/project_files/shumlak2009_latex/images'),
        bib_file=Path('/Users/chelsea/python_projects/project_files/shumlak2009_latex/bib.tex'))

    # Initialize orchestrator (no database for this basic example)
    orchestrator = AdvisorOrchestrator()

    # Run validation
    result = orchestrator.run(
        paper_text=loaded_paper["paper_text"],
        figures=loaded_paper["figures"],
        paper_bib=loaded_paper["bib_text"],
        save_to_db=False,
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


def example_with_database():
    """Example with MongoDB persistence."""

    # Initialize database
    db = Database()

    # Initialize orchestrator with database
    orchestrator = AdvisorOrchestrator(db=db)

    # Run validation
    result = orchestrator.run(
        paper_id="paper_001",
        paper_folder=Path("/path/to/paper/folder"),
        save_to_db=True,
    )

    print("Validation saved to database")
    print(f"Confidence: {result.confidence_score:.2%}")

    # Later: retrieve the validation
    loaded_result = orchestrator.load_from_database("paper_001")
    if loaded_result:
        print(f"\nLoaded from DB - Confidence: {loaded_result.confidence_score:.2%}")

    # Get database stats
    stats = db.get_statistics()
    print("\nDatabase Statistics:")
    print(f"  Total papers: {stats['total_papers']}")
    print(f"  Total validations: {stats['total_validations']}")
    print(f"  Average confidence: {stats['average_confidence']:.2%}")

    return result


def example_full_pipeline():
    """Complete example with all features."""

    # Initialize everything
    db = Database()
    orchestrator = AdvisorOrchestrator(db=db)

    # Bibliography (optional)
    bibliography = {
        "[1]": "Smith, J. et al. (2023). Important Work. Nature, 123:456.",
        "[2]": "Jones, A. (2022). Related Research. Science, 789:012.",
    }

    # Run complete pipeline
    result = orchestrator.run(
        paper_id="full_example_001",
        paper_folder=Path("/path/to/paper/folder"),
        bibliography=bibliography,
        save_to_db=True,
    )

    # Analyze results
    print("\n" + "=" * 60)
    print("DETAILED RESULTS")
    print("=" * 60)

    print("\nPaper Structure:")
    print(f"  Main claim: {result.paper_structure.main_claim}")
    print(f"  Logical steps: {len(result.paper_structure.logical_steps)}")

    for step in result.paper_structure.logical_steps:
        print(f"\n  Step {step.step_number}: {step.description[:80]}...")
        validations = result.step_validations.get(step.step_number, {})
        print(f"    Evidence: {validations.get('evidence_count', 0)} pieces")
        print(f"    Figures: {len(validations.get('figure_validations', []))} evaluated")
        print(f"    Math: {len(validations.get('math_validations', []))} validated")
        print(f"    Citations: {len(validations.get('citation_validations', []))} checked")

    print("\nFinal Assessment:")
    print(f"  Confidence: {result.confidence_score:.2%}")
    print(f"  Review: {result.overall_assessment.review[:200]}...")

    print("=" * 60 + "\n")

    return result


if __name__ == "__main__":
    print("The Advisor Pipeline - Example Usage\n")

    # Choose which example to run
    print("Running basic example...")
    result = example_basic_usage()

    # Uncomment to run other examples:
    # result = example_with_database()
    # result = example_full_pipeline()

    print("\nDone!")
