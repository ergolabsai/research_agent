# SPDX-FileCopyrightText: 2026 Chelsea Liekhus-Schmaltz and Johnathon Barhydt
#
# SPDX-License-Identifier: AGPL-3.0-only

"""
Formula Data Model and Schema
"""
import json
from typing import List, Dict, Optional
from datetime import datetime, timezone
from sqlmodel import SQLModel, Field, Column
from sqlalchemy import Text


class Formula(SQLModel, table=True):
    """Formula stored in the shared SQLite database."""

    __tablename__ = "formula"

    id: Optional[int] = Field(default=None, primary_key=True)
    formula_id: str = Field(unique=True, index=True, description="Unique identifier for the formula")
    name: str = Field(description="Human-readable name")
    description: str = Field(description="Description with equation notation")
    equation: str = Field(description="Python-evaluable equation string")
    variables_json: str = Field(
        sa_column=Column(Text), description="JSON list of variable names"
    )
    variable_details_json: Optional[str] = Field(
        default=None, sa_column=Column(Text),
        description="JSON list of dicts with name/description/unit per variable",
    )
    category: Optional[str] = Field(default="general", index=True, description="Formula category")
    tags_json: Optional[str] = Field(
        default=None, sa_column=Column(Text), description="JSON list of searchable tags"
    )
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # --- helpers for JSON columns ------------------------------------------

    @property
    def variables(self) -> List[str]:
        return json.loads(self.variables_json) if self.variables_json else []

    @variables.setter
    def variables(self, value: List[str]) -> None:
        self.variables_json = json.dumps(value)

    @property
    def variable_details(self) -> Optional[List[Dict[str, str]]]:
        return json.loads(self.variable_details_json) if self.variable_details_json else None

    @variable_details.setter
    def variable_details(self, value: Optional[List[Dict[str, str]]]) -> None:
        self.variable_details_json = json.dumps(value) if value is not None else None

    @property
    def tags(self) -> List[str]:
        return json.loads(self.tags_json) if self.tags_json else []

    @tags.setter
    def tags(self, value: List[str]) -> None:
        self.tags_json = json.dumps(value)

    def to_dict(self) -> dict:
        """Return a plain dict matching the shape the solver/MCP tools expect."""
        return {
            "formula_id": self.formula_id,
            "name": self.name,
            "description": self.description,
            "equation": self.equation,
            "variables": self.variables,
            "variable_details": self.variable_details,
            "category": self.category,
            "tags": self.tags,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
