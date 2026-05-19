# SPDX-FileCopyrightText: 2026 Chelsea Liekhus-Schmaltz and Johnathon Barhydt
#
# SPDX-License-Identifier: AGPL-3.0-only

"""
CRUD Operations for Formula Management (SQLite / SQLModel)
"""
import json
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone

from sqlmodel import Session, select
from sqlalchemy import Engine

from .models import Formula


class FormulaRepository:
    """Handles all database operations for formulas."""

    def __init__(self, engine: Engine):
        self.engine = engine

    # --- helpers -----------------------------------------------------------

    def _session(self) -> Session:
        return Session(self.engine)

    # ADD
    def add_formula(self, formula: Formula) -> Dict[str, Any]:
        """
        Add a new formula to the database.

        Args:
            formula: Formula object to insert

        Returns:
            Inserted formula as dict
        """
        with self._session() as session:
            session.add(formula)
            session.commit()
            session.refresh(formula)
            return formula.to_dict()

    # READ
    def get_formula_by_id(self, formula_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a formula by its formula_id.

        Args:
            formula_id: Unique formula identifier

        Returns:
            Formula dict or None if not found
        """
        with self._session() as session:
            formula = session.exec(
                select(Formula).where(Formula.formula_id == formula_id)
            ).first()
            return formula.to_dict() if formula else None

    def get_all_formulas(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Retrieve all formulas, optionally filtered by category.

        Args:
            category: Optional category filter

        Returns:
            List of formula dicts
        """
        with self._session() as session:
            stmt = select(Formula)
            if category:
                stmt = stmt.where(Formula.category == category)
            formulas = session.exec(stmt).all()
            return [f.to_dict() for f in formulas]

    def search_formulas(self, search_term: str) -> List[Dict[str, Any]]:
        """
        Search formulas by text (name, description, tags).

        Uses SQL LIKE — sufficient for the expected scale (hundreds of formulas).

        Args:
            search_term: Text to search for

        Returns:
            List of matching formula dicts
        """
        pattern = f"%{search_term}%"
        with self._session() as session:
            stmt = select(Formula).where(
                (Formula.name.ilike(pattern))
                | (Formula.description.ilike(pattern))
                | (Formula.tags_json.ilike(pattern))
            )
            formulas = session.exec(stmt).all()
            return [f.to_dict() for f in formulas]

    def get_formulas_by_tag(self, tag: str) -> List[Dict[str, Any]]:
        """
        Get all formulas that contain a specific tag.

        Args:
            tag: Tag to filter by

        Returns:
            List of formula dicts
        """
        with self._session() as session:
            # Tags are stored as a JSON list e.g. '["physics", "energy"]'
            # A LIKE on the serialized form is sufficient here.
            stmt = select(Formula).where(Formula.tags_json.ilike(f'%"{tag}"%'))
            formulas = session.exec(stmt).all()
            return [f.to_dict() for f in formulas]

    # UPDATE
    def update_formula(self, formula_id: str, updates: Dict[str, Any]) -> bool:
        """
        Update a formula's fields.

        Args:
            formula_id: Formula to update
            updates: Dictionary of fields to update

        Returns:
            True if updated, False if not found
        """
        with self._session() as session:
            formula = session.exec(
                select(Formula).where(Formula.formula_id == formula_id)
            ).first()
            if not formula:
                return False

            for key, value in updates.items():
                if key in ("variables", "variable_details", "tags"):
                    # Use the property setter which serialises to JSON
                    setattr(formula, key, value)
                elif hasattr(formula, key):
                    setattr(formula, key, value)

            formula.updated_at = datetime.now(timezone.utc)
            session.add(formula)
            session.commit()
            return True

    def add_tags(self, formula_id: str, tags: List[str]) -> bool:
        """
        Add tags to a formula (no duplicates).

        Args:
            formula_id: Formula to update
            tags: Tags to add

        Returns:
            True if updated, False if not found
        """
        with self._session() as session:
            formula = session.exec(
                select(Formula).where(Formula.formula_id == formula_id)
            ).first()
            if not formula:
                return False

            existing = set(formula.tags)
            existing.update(tags)
            formula.tags = list(existing)
            formula.updated_at = datetime.now(timezone.utc)
            session.add(formula)
            session.commit()
            return True

    def remove_tags(self, formula_id: str, tags: List[str]) -> bool:
        """
        Remove tags from a formula.

        Args:
            formula_id: Formula to update
            tags: Tags to remove

        Returns:
            True if updated, False if not found
        """
        with self._session() as session:
            formula = session.exec(
                select(Formula).where(Formula.formula_id == formula_id)
            ).first()
            if not formula:
                return False

            formula.tags = [t for t in formula.tags if t not in tags]
            formula.updated_at = datetime.now(timezone.utc)
            session.add(formula)
            session.commit()
            return True

    # DELETE
    def delete_formula(self, formula_id: str) -> bool:
        """
        Delete a formula.

        Args:
            formula_id: Formula to delete

        Returns:
            True if deleted, False if not found
        """
        with self._session() as session:
            formula = session.exec(
                select(Formula).where(Formula.formula_id == formula_id)
            ).first()
            if not formula:
                return False
            session.delete(formula)
            session.commit()
            return True

    def delete_all_formulas(self) -> int:
        """
        Delete all formulas.

        Returns:
            Number of formulas deleted
        """
        with self._session() as session:
            formulas = session.exec(select(Formula)).all()
            count = len(formulas)
            for f in formulas:
                session.delete(f)
            session.commit()
            return count

    # UTILITY
    def count_formulas(self, category: Optional[str] = None) -> int:
        """
        Count formulas, optionally by category.

        Args:
            category: Optional category filter

        Returns:
            Count of formulas
        """
        with self._session() as session:
            stmt = select(Formula)
            if category:
                stmt = stmt.where(Formula.category == category)
            return len(session.exec(stmt).all())

    def get_categories(self) -> List[str]:
        """
        Get list of all unique categories.

        Returns:
            Sorted list of category names
        """
        with self._session() as session:
            formulas = session.exec(select(Formula.category).distinct()).all()
            return sorted([c for c in formulas if c])

    def get_all_tags(self) -> List[str]:
        """
        Get list of all unique tags across all formulas.

        Returns:
            Sorted list of tags
        """
        with self._session() as session:
            formulas = session.exec(select(Formula)).all()
            all_tags: set[str] = set()
            for f in formulas:
                all_tags.update(f.tags)
            return sorted(all_tags)
