#!/usr/bin/env python3
"""
Example usage of The Advisor pipeline.

This script demonstrates how to:
1. Set up the pipeline with database and MCP client
2. Run validation on a paper
3. Retrieve and display results
"""

import os
from pathlib import Path
from database import Database
from pipeline import AdvisorPipeline


def example_basic_usage():
    """Basic example: Run pipeline on a paper without database."""

    # Load paper from LaTeX file
    paper_path = Path("/Users/chelsea/python_projects/project_files/shumlak2009_latex/main_text.tex")
    with open(paper_path, 'r') as f:
        sample_paper = f.read()
    
    # Initialize pipeline (no database, no MCP for this basic example)
    pipeline = AdvisorPipeline()
    
    # Run validation
    result = pipeline.run(
        paper_id="example_001",
        paper_text=sample_paper,
        title="Equilibrium, flow shear and stability measurements in the Z-pinch",
        authors=["U. Shumlak", "C.S. Adams", "J.M. Blakely", "B.-J. Chan", "R.P. Golingo", "S.D. Knecht", "B.A. Nelson",
                 "R.J. Oberto", "M.R. Sybouts", "G.V. Vogman"],
        save_to_db=False  # Don't save since no database
    )
    
    # Display results
    print("\n" + "="*60)
    print("VALIDATION RESULTS")
    print("="*60)
    print(f"Main Claim: {result.paper_structure.main_claim}")
    print(f"Logical Steps: {len(result.paper_structure.logical_steps)}")
    print(f"Confidence Score: {result.confidence_score:.2%}")
    print(f"\nOverall Review:\n{result.overall_assessment.review}")
    print("="*60 + "\n")
    
    return result


def example_with_database():
    """Example with MongoDB persistence."""
    
    # Initialize database
    db = Database()
    
    # Initialize pipeline with database
    pipeline = AdvisorPipeline(db=db)
    
    # Load a paper (in practice, from file)
    paper_text = "Your full paper text here..."
    
    # Run validation
    result = pipeline.run(
        paper_id="paper_001",
        paper_text=paper_text,
        title="Example Paper Title",
        save_to_db=True  # Save to MongoDB
    )
    
    print(f"Validation saved to database")
    print(f"Confidence: {result.confidence_score:.2%}")
    
    # Later: retrieve the validation
    loaded_result = pipeline.load_from_database("paper_001")
    print(f"\nLoaded from DB - Confidence: {loaded_result.confidence_score:.2%}")
    
    # Get database stats
    stats = db.get_statistics()
    print(f"\nDatabase Statistics:")
    print(f"  Total papers: {stats['total_papers']}")
    print(f"  Total validations: {stats['total_validations']}")
    print(f"  Average confidence: {stats['average_confidence']:.2%}")
    
    return result


def example_with_mcp_calculator():
    """Example with MCP calculator for math validation."""
    
    # You'll need to initialize your MCP client here
    # This is a placeholder - use your actual MCP client
    class MockMCPClient:
        def call_tool(self, tool_name, **kwargs):
            # Mock implementation
            if tool_name == "list_formulas":
                return {"formulas": ["wave_equation", "kinetic_energy"]}
            elif tool_name == "calculate":
                return {"result": 42, "unit": "m"}
            elif tool_name == "verify":
                return {"valid": True}
            return {}
    
    mcp_client = MockMCPClient()
    
    # Initialize pipeline with MCP
    pipeline = AdvisorPipeline(mcp_client=mcp_client)
    
    # Run validation - now math evaluation will use the calculator
    result = pipeline.run(
        paper_id="paper_with_math",
        paper_text="Paper with equations...",
        title="Mathematical Analysis Paper",
        save_to_db=False
    )
    
    return result


def example_with_figures():
    """Example with figure files for evaluation."""
    
    # Map figure names to file paths
    figures = {
        "figure_1": "/path/to/figure1.png",
        "figure_2": "/path/to/figure2.png",
        "fig_3a": "/path/to/figure3a.png"
    }
    
    pipeline = AdvisorPipeline()
    
    result = pipeline.run(
        paper_id="paper_with_figs",
        paper_text="Paper text...",
        title="Paper with Figures",
        figures=figures,
        save_to_db=False
    )
    
    # Check figure evaluations
    print(f"\nFigure Evaluations:")
    for step_num, validations in result.step_validations.items():
        fig_vals = validations.get("figure_validations", [])
        if fig_vals:
            print(f"  Step {step_num}: {len(fig_vals)} figures evaluated")
    
    return result


def example_full_pipeline():
    """Complete example with all features."""
    
    # Initialize everything
    db = Database()
    
    # Initialize your MCP client
    # mcp_client = YourMCPClient()  # Replace with actual client
    mcp_client = None  # For now
    
    pipeline = AdvisorPipeline(mcp_client=mcp_client, db=db)
    
    # Load paper from file
    paper_path = Path("sample_papers/example_paper.txt")
    if paper_path.exists():
        with open(paper_path, 'r') as f:
            paper_text = f.read()
    else:
        paper_text = "Sample paper text..."
    
    # Define figures
    figures = {
        "figure_1": "sample_papers/figures/fig1.png",
        "figure_2": "sample_papers/figures/fig2.png"
    }
    
    # Bibliography (optional)
    bibliography = {
        "[1]": "Smith, J. et al. (2023). Important Work. Nature, 123:456.",
        "[2]": "Jones, A. (2022). Related Research. Science, 789:012."
    }
    
    # Run complete pipeline
    result = pipeline.run(
        paper_id="full_example_001",
        paper_text=paper_text,
        title="Complete Example Paper",
        authors=["Author One", "Author Two"],
        abstract="This paper presents...",
        figures=figures,
        bibliography=bibliography,
        save_to_db=True
    )
    
    # Analyze results
    print("\n" + "="*60)
    print("DETAILED RESULTS")
    print("="*60)
    
    print(f"\nPaper Structure:")
    print(f"  Main claim: {result.paper_structure.main_claim}")
    print(f"  Logical steps: {len(result.paper_structure.logical_steps)}")
    
    for step in result.paper_structure.logical_steps:
        print(f"\n  Step {step.step_number}: {step.description[:80]}...")
        validations = result.step_validations.get(step.step_number, {})
        print(f"    Evidence: {validations.get('evidence_count', 0)} pieces")
        print(f"    Figures: {len(validations.get('figure_validations', []))} evaluated")
        print(f"    Math: {len(validations.get('math_validations', []))} validated")
        print(f"    Citations: {len(validations.get('citation_validations', []))} checked")
    
    print(f"\nFinal Assessment:")
    print(f"  Confidence: {result.confidence_score:.2%}")
    print(f"  Review: {result.overall_assessment.review[:200]}...")
    
    print("="*60 + "\n")
    
    return result


if __name__ == "__main__":
    print("The Advisor Pipeline - Example Usage\n")
    
    # Choose which example to run
    print("Running basic example...")
    result = example_basic_usage()
    
    # Uncomment to run other examples:
    # result = example_with_database()
    # result = example_with_mcp_calculator()
    # result = example_with_figures()
    # result = example_full_pipeline()
    
    print("\nDone!")
