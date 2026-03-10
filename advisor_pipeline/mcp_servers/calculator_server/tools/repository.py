"""
CRUD Operations for Formula Management
"""
from typing import List, Dict, Any, Optional
from datetime import datetime
from pymongo.collection import Collection
from pymongo import ASCENDING, TEXT
from .models import Formula


class FormulaRepository:
    """Handles all database operations for formulas"""
    
    def __init__(self, collection: Collection):
        """
        Initialize repository with MongoDB collection
        
        Args:
            collection: MongoDB collection for formulas
        """
        self.collection = collection
        self._create_indexes()
    
    def _create_indexes(self):
        """Create database indexes for better performance"""
        # Unique index on formula_id
        self.collection.create_index([("formula_id", ASCENDING)], unique=True)
        
        # Text index for searching
        self.collection.create_index([
            ("name", TEXT),
            ("description", TEXT),
            ("tags", TEXT)
        ])
        
        # Category index
        self.collection.create_index([("category", ASCENDING)])
    
    # ADD
    def add_formula(self, formula: Formula) -> Dict[str, Any]:
        """
        Add a new formula to the database
        
        Args:
            formula: Formula object to insert
            
        Returns:
            Inserted formula with MongoDB _id
        """
        formula_dict = formula.model_dump()
        result = self.collection.insert_one(formula_dict)
        formula_dict['_id'] = str(result.inserted_id)
        return formula_dict
    
    # READ
    def get_formula_by_id(self, formula_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a formula by its ID
        
        Args:
            formula_id: Unique formula identifier
            
        Returns:
            Formula document or None if not found
        """
        formula = self.collection.find_one({"formula_id": formula_id})
        if formula:
            formula['_id'] = str(formula['_id'])
        return formula
    
    def get_all_formulas(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Retrieve all formulas, optionally filtered by category
        
        Args:
            category: Optional category filter
            
        Returns:
            List of formula documents
        """
        query = {"category": category} if category else {}
        formulas = list(self.collection.find(query))
        
        # Convert ObjectId to string
        for formula in formulas:
            formula['_id'] = str(formula['_id'])
        
        return formulas
    
    def search_formulas(self, search_term: str) -> List[Dict[str, Any]]:
        """
        Search formulas by text (name, description, tags)
        
        Args:
            search_term: Text to search for
            
        Returns:
            List of matching formula documents
        """
        formulas = list(self.collection.find(
            {"$text": {"$search": search_term}}
        ))
        
        for formula in formulas:
            formula['_id'] = str(formula['_id'])
        
        return formulas
    
    def get_formulas_by_tag(self, tag: str) -> List[Dict[str, Any]]:
        """
        Get all formulas with a specific tag
        
        Args:
            tag: Tag to filter by
            
        Returns:
            List of formula documents
        """
        formulas = list(self.collection.find({"tags": tag}))
        
        for formula in formulas:
            formula['_id'] = str(formula['_id'])
        
        return formulas
    
    # UPDATE
    def update_formula(self, formula_id: str, updates: Dict[str, Any]) -> bool:
        """
        Update a formula's fields
        
        Args:
            formula_id: Formula to update
            updates: Dictionary of fields to update
            
        Returns:
            True if updated, False if not found
        """
        # Always update the updated_at timestamp
        updates['updated_at'] = datetime.utcnow()
        
        result = self.collection.update_one(
            {"formula_id": formula_id},
            {"$set": updates}
        )
        
        return result.modified_count > 0
    
    def add_tags(self, formula_id: str, tags: List[str]) -> bool:
        """
        Add tags to a formula
        
        Args:
            formula_id: Formula to update
            tags: List of tags to add
            
        Returns:
            True if updated, False if not found
        """
        result = self.collection.update_one(
            {"formula_id": formula_id},
            {
                "$addToSet": {"tags": {"$each": tags}},
                "$set": {"updated_at": datetime.utcnow()}
            }
        )
        
        return result.modified_count > 0
    
    def remove_tags(self, formula_id: str, tags: List[str]) -> bool:
        """
        Remove tags from a formula
        
        Args:
            formula_id: Formula to update
            tags: List of tags to remove
            
        Returns:
            True if updated, False if not found
        """
        result = self.collection.update_one(
            {"formula_id": formula_id},
            {
                "$pull": {"tags": {"$in": tags}},
                "$set": {"updated_at": datetime.utcnow()}
            }
        )
        
        return result.modified_count > 0
    
    # DELETE
    def delete_formula(self, formula_id: str) -> bool:
        """
        Delete a formula from the database
        
        Args:
            formula_id: Formula to delete
            
        Returns:
            True if deleted, False if not found
        """
        result = self.collection.delete_one({"formula_id": formula_id})
        return result.deleted_count > 0
    
    def delete_all_formulas(self) -> int:
        """
        Delete all formulas (use with caution!)
        
        Returns:
            Number of formulas deleted
        """
        result = self.collection.delete_many({})
        return result.deleted_count
    
    # UTILITY
    def count_formulas(self, category: Optional[str] = None) -> int:
        """
        Count formulas, optionally by category
        
        Args:
            category: Optional category filter
            
        Returns:
            Count of formulas
        """
        query = {"category": category} if category else {}
        return self.collection.count_documents(query)
    
    def get_categories(self) -> List[str]:
        """
        Get list of all unique categories
        
        Returns:
            List of category names
        """
        return self.collection.distinct("category")
    
    def get_all_tags(self) -> List[str]:
        """
        Get list of all unique tags
        
        Returns:
            List of tags
        """
        return self.collection.distinct("tags")
