# SPDX-FileCopyrightText: 2026 Chelsea Liekhus-Schmaltz and Johnathon Barhydt
#
# SPDX-License-Identifier: AGPL-3.0-only

"""
Seed the SQLite database with the starter set of formulas.
"""
import json
import math

from sqlmodel import Session, select

from .db_config import get_engine, init_db
from .models import Formula


def get_formula_data():
    """
    Define all formulas with complete metadata
    This is your existing formula data, now enriched with categories and tags
    """
    return [
        # Mechanics - Energy
        {
            "formula_id": "kinetic_energy",
            "name": "Kinetic Energy",
            "description": "Kinetic energy: KE = ½mv²",
            "equation": "energy = 0.5 * mass * velocity**2",
            "variables": ["energy", "mass", "velocity"],
            "variable_details": [
                {"name": "energy", "description": "Kinetic energy", "unit": "J"},
                {"name": "mass", "description": "Object mass", "unit": "kg"},
                {"name": "velocity", "description": "Object velocity", "unit": "m/s"}
            ],
            "category": "mechanics",
            "tags": ["physics", "energy", "motion", "mechanics"]
        },
        
        # Mechanics - Forces and Motion
        {
            "formula_id": "force",
            "name": "Newton's Second Law",
            "description": "Newton's second law: F = ma",
            "equation": "force = mass * acceleration",
            "variables": ["force", "mass", "acceleration"],
            "variable_details": [
                {"name": "force", "description": "Net force", "unit": "N"},
                {"name": "mass", "description": "Object mass", "unit": "kg"},
                {"name": "acceleration", "description": "Acceleration", "unit": "m/s²"}
            ],
            "category": "mechanics",
            "tags": ["physics", "force", "motion", "mechanics", "newton"]
        },
        {
            "formula_id": "momentum",
            "name": "Momentum",
            "description": "Momentum: p = mv",
            "equation": "momentum = mass * velocity",
            "variables": ["momentum", "mass", "velocity"],
            "variable_details": [
                {"name": "momentum", "description": "Linear momentum", "unit": "kg·m/s"},
                {"name": "mass", "description": "Object mass", "unit": "kg"},
                {"name": "velocity", "description": "Object velocity", "unit": "m/s"}
            ],
            "category": "mechanics",
            "tags": ["physics", "momentum", "motion", "mechanics"]
        },
        
        # Wave Physics
        {
            "formula_id": "wave_equation",
            "name": "Wave Equation",
            "description": "Wave equation: v = fλ",
            "equation": "speed = frequency * wavelength",
            "variables": ["speed", "frequency", "wavelength"],
            "variable_details": [
                {"name": "speed", "description": "Wave speed", "unit": "m/s"},
                {"name": "frequency", "description": "Wave frequency", "unit": "Hz"},
                {"name": "wavelength", "description": "Wavelength", "unit": "m"}
            ],
            "category": "waves",
            "tags": ["physics", "waves", "oscillation"]
        },
        {
            "formula_id": "angular_wavenumber",
            "name": "Angular Wavenumber",
            "description": "Angular wavenumber: k = 2π/λ",
            "equation": f"wavenumber = 2 * {math.pi} / wavelength",
            "variables": ["wavenumber", "wavelength"],
            "variable_details": [
                {"name": "wavenumber", "description": "Angular wavenumber", "unit": "rad/m"},
                {"name": "wavelength", "description": "Wavelength", "unit": "m"}
            ],
            "category": "waves",
            "tags": ["physics", "waves", "wavenumber"]
        },
        {
            "formula_id": "angular_frequency",
            "name": "Angular Frequency",
            "description": "Angular frequency: ω = 2πf",
            "equation": f"angular_frequency = 2 * {math.pi} * frequency",
            "variables": ["angular_frequency", "frequency"],
            "variable_details": [
                {"name": "angular_frequency", "description": "Angular frequency", "unit": "rad/s"},
                {"name": "frequency", "description": "Frequency", "unit": "Hz"}
            ],
            "category": "waves",
            "tags": ["physics", "waves", "oscillation"]
        },
        
        # Plasma Physics
        {
            "formula_id": "alfven_speed",
            "name": "Alfvén Speed",
            "description": "Alfvén speed: v_A = B/√(μ₀ρ)",
            "equation": f"alfven_speed = magnetic_field / (4e-7 * {math.pi} * mass_density)**0.5",
            "variables": ["alfven_speed", "magnetic_field", "mass_density"],
            "variable_details": [
                {"name": "alfven_speed", "description": "Alfvén wave speed", "unit": "m/s"},
                {"name": "magnetic_field", "description": "Magnetic field strength", "unit": "T"},
                {"name": "mass_density", "description": "Mass density", "unit": "kg/m³"}
            ],
            "category": "plasma",
            "tags": ["physics", "plasma", "magnetohydrodynamics", "MHD"]
        },
        {
            "formula_id": "kink_mode_growth_time",
            "name": "Kink Mode Growth Time",
            "description": "Kink mode growth time: τ = 1/(v_A × k)",
            "equation": "growth_time = 1 / (alfven_speed * wavenumber)",
            "variables": ["growth_time", "alfven_speed", "wavenumber"],
            "variable_details": [
                {"name": "growth_time", "description": "Instability growth time", "unit": "s"},
                {"name": "alfven_speed", "description": "Alfvén wave speed", "unit": "m/s"},
                {"name": "wavenumber", "description": "Wavenumber", "unit": "rad/m"}
            ],
            "category": "plasma",
            "tags": ["physics", "plasma", "instability", "MHD"]
        },
        {
            "formula_id": "mass_density",
            "name": "Mass Density",
            "description": "Mass density: ρ = n × m",
            "equation": "mass_density = number_density * particle_mass",
            "variables": ["mass_density", "number_density", "particle_mass"],
            "variable_details": [
                {"name": "mass_density", "description": "Mass density", "unit": "kg/m³"},
                {"name": "number_density", "description": "Number density", "unit": "1/m³"},
                {"name": "particle_mass", "description": "Particle mass", "unit": "kg"}
            ],
            "category": "plasma",
            "tags": ["physics", "plasma", "density"]
        },
        
        # Geometry - Circle
        {
            "formula_id": "diameter",
            "name": "Circle Diameter",
            "description": "Diameter: d = 2r",
            "equation": "diameter = 2 * radius",
            "variables": ["diameter", "radius"],
            "variable_details": [
                {"name": "diameter", "description": "Circle diameter", "unit": "m"},
                {"name": "radius", "description": "Circle radius", "unit": "m"}
            ],
            "category": "geometry",
            "tags": ["math", "geometry", "circle"]
        },
        {
            "formula_id": "circumference",
            "name": "Circle Circumference",
            "description": "Circumference: C = 2πr",
            "equation": f"circumference = 2 * {math.pi} * radius",
            "variables": ["circumference", "radius"],
            "variable_details": [
                {"name": "circumference", "description": "Circle circumference", "unit": "m"},
                {"name": "radius", "description": "Circle radius", "unit": "m"}
            ],
            "category": "geometry",
            "tags": ["math", "geometry", "circle"]
        },
        {
            "formula_id": "circle_area",
            "name": "Circle Area",
            "description": "Circle area: A = πr²",
            "equation": f"area = {math.pi} * radius**2",
            "variables": ["area", "radius"],
            "variable_details": [
                {"name": "area", "description": "Circle area", "unit": "m²"},
                {"name": "radius", "description": "Circle radius", "unit": "m"}
            ],
            "category": "geometry",
            "tags": ["math", "geometry", "circle", "area"]
        },
        
        # Mathematics - Percentages
        {
            "formula_id": "percent_change",
            "name": "Percent Change",
            "description": "Percent change: Δ% = (new - old)/old × 100",
            "equation": "percent_change = (new_value - original_value) / original_value * 100",
            "variables": ["percent_change", "original_value", "new_value"],
            "variable_details": [
                {"name": "percent_change", "description": "Percentage change", "unit": "%"},
                {"name": "original_value", "description": "Original value", "unit": "various"},
                {"name": "new_value", "description": "New value", "unit": "various"}
            ],
            "category": "mathematics",
            "tags": ["math", "percentage", "percent"]
        },
        {
            "formula_id": "percent_of",
            "name": "Percent Of",
            "description": "Percent of: % = part/whole × 100",
            "equation": "percentage = part / whole * 100",
            "variables": ["percentage", "part", "whole"],
            "variable_details": [
                {"name": "percentage", "description": "Percentage value", "unit": "%"},
                {"name": "part", "description": "Part value", "unit": "various"},
                {"name": "whole", "description": "Whole value", "unit": "various"}
            ],
            "category": "mathematics",
            "tags": ["math", "percentage", "percent"]
        },
        {
            "formula_id": "calculate_percentage",
            "name": "Calculate Percentage",
            "description": "Calculate percentage: result = %/100 × number",
            "equation": "result = percentage / 100 * number",
            "variables": ["result", "percentage", "number"],
            "variable_details": [
                {"name": "result", "description": "Calculated result", "unit": "various"},
                {"name": "percentage", "description": "Percentage value", "unit": "%"},
                {"name": "number", "description": "Number to calculate percentage of", "unit": "various"}
            ],
            "category": "mathematics",
            "tags": ["math", "percentage", "percent"]
        },

        # ML Validation — formulas used by the paper validation pipeline
        {
            "formula_id": "confidence_aggregation",
            "name": "Confidence Aggregation",
            "description": "Weighted sum of sub-scores into final confidence: C_final = 0.35·S_evidence + 0.25·S_figure + 0.25·S_math + 0.15·S_citation",
            "equation": "C_final = 0.35 * S_evidence + 0.25 * S_figure + 0.25 * S_math + 0.15 * S_citation",
            "variables": ["C_final", "S_evidence", "S_figure", "S_math", "S_citation"],
            "variable_details": [
                {"name": "C_final", "description": "Final confidence score in [0, 1]", "unit": "dimensionless"},
                {"name": "S_evidence", "description": "Evidence density sub-score", "unit": "dimensionless"},
                {"name": "S_figure", "description": "Figure agreement sub-score", "unit": "dimensionless"},
                {"name": "S_math", "description": "Symbolic validity sub-score", "unit": "dimensionless"},
                {"name": "S_citation", "description": "Citation convergence sub-score", "unit": "dimensionless"}
            ],
            "category": "ml_validation",
            "tags": ["confidence", "aggregation", "scoring", "ml_validation", "pipeline"]
        },
        {
            "formula_id": "citation_scoring",
            "name": "Citation Scoring",
            "description": "Combines semantic relevancy and directional convergence: S_citation = mean(relevancy_i × (1 + convergence_i))",
            "equation": "S_citation = sum(relevancy_i * (1 + convergence_i)) / n_papers",
            "variables": ["S_citation", "relevancy_i", "convergence_i", "n_papers"],
            "variable_details": [
                {"name": "S_citation", "description": "Aggregated citation score in [0, 2]", "unit": "dimensionless"},
                {"name": "relevancy_i", "description": "Relevancy score for paper i in [0, 1]", "unit": "dimensionless"},
                {"name": "convergence_i", "description": "Convergence score for paper i in [-1, 1]", "unit": "dimensionless"},
                {"name": "n_papers", "description": "Number of related papers", "unit": "count"}
            ],
            "category": "ml_validation",
            "tags": ["citation", "scoring", "convergence", "ml_validation", "pipeline"]
        },
        {
            "formula_id": "plot_agreement",
            "name": "Plot Agreement",
            "description": "Scores slope trend agreement between extracted and predicted curves: E_plot = 1 − |slope_true − slope_pred| / max(|slope_true|, ε)",
            "equation": "E_plot = 1 - abs(slope_true - slope_pred) / max(abs(slope_true), 1e-6)",
            "variables": ["E_plot", "slope_true", "slope_pred"],
            "variable_details": [
                {"name": "E_plot", "description": "Plot agreement score in [0, 1]; 1 = perfect", "unit": "dimensionless"},
                {"name": "slope_true", "description": "Slope extracted from actual figure", "unit": "dimensionless"},
                {"name": "slope_pred", "description": "Slope predicted from paper narrative", "unit": "dimensionless"}
            ],
            "category": "ml_validation",
            "tags": ["figures", "plot", "agreement", "slope", "ml_validation", "pipeline"]
        },
        {
            "formula_id": "contradiction_penalty",
            "name": "Contradiction Penalty",
            "description": "Reduces confidence for unresolved contradictions (clipped at 0.35): Penalty = 0.1·N_unverified + 0.07·N_inconsistent",
            "equation": "Penalty = min(0.35, 0.1 * N_unverified_claims + 0.07 * N_inconsistent_figures)",
            "variables": ["Penalty", "N_unverified_claims", "N_inconsistent_figures"],
            "variable_details": [
                {"name": "Penalty", "description": "Confidence penalty in [0, 0.35]", "unit": "dimensionless"},
                {"name": "N_unverified_claims", "description": "Count of claims without supporting evidence", "unit": "count"},
                {"name": "N_inconsistent_figures", "description": "Count of figures with contradictions", "unit": "count"}
            ],
            "category": "ml_validation",
            "tags": ["penalty", "contradiction", "confidence", "ml_validation", "pipeline"]
        }
    ]


def seed_formulas_if_empty(engine=None):
    """Populate the formula table with the starter set if it is empty.

    Safe to call on every startup — does nothing when formulas already exist.
    """
    if engine is None:
        engine = get_engine()

    init_db()  # ensure table exists

    with Session(engine) as session:
        existing = session.exec(select(Formula)).first()
        if existing is not None:
            return  # already seeded

        for data in get_formula_data():
            formula = Formula(
                formula_id=data["formula_id"],
                name=data["name"],
                description=data["description"],
                equation=data["equation"],
                variables_json=json.dumps(data["variables"]),
                variable_details_json=json.dumps(data.get("variable_details")),
                category=data.get("category", "general"),
                tags_json=json.dumps(data.get("tags", [])),
            )
            session.add(formula)

        session.commit()
        print(f"Seeded {len(get_formula_data())} formulas into SQLite.")


if __name__ == "__main__":
    seed_formulas_if_empty()
