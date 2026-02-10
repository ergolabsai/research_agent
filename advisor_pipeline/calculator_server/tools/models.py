"""
Formula Data Model and Schema
"""
from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class FormulaVariable(BaseModel):
    """Represents a variable in a formula"""
    name: str
    description: Optional[str] = None
    unit: Optional[str] = None
    

class Formula(BaseModel):
    """
    Formula document schema for MongoDB
    
    Example:
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
        "tags": ["physics", "energy", "motion"],
        "created_at": "2025-01-28T...",
        "updated_at": "2025-01-28T..."
    }
    """
    formula_id: str = Field(..., description="Unique identifier for the formula")
    name: str = Field(..., description="Human-readable name")
    description: str = Field(..., description="Description with equation notation")
    equation: str = Field(..., description="Python-evaluable equation string")
    variables: List[str] = Field(..., description="List of variable names in the equation")
    variable_details: Optional[List[Dict[str, str]]] = Field(
        default=None, 
        description="Detailed info about each variable (name, description, unit)"
    )
    category: Optional[str] = Field(default="general", description="Formula category")
    tags: Optional[List[str]] = Field(default_factory=list, description="Searchable tags")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_schema_extra = {
            "example": {
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
                "tags": ["physics", "energy", "motion"]
            }
        }
