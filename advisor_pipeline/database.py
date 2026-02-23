from typing import Dict, List, Optional

from pymongo import MongoClient

from advisor_pipeline.config.settings import settings
from advisor_pipeline.models.schemas import PaperDocument, ValidationDocument, ValidationResult


class Database:
    """MongoDB interface for The Advisor pipeline."""
    
    def __init__(self, uri: str = None, database_name: str = None):
        self.uri = uri or settings.mongodb_uri
        self.database_name = database_name or settings.database_name
        
        self.client: MongoClient = None
        self.db = None
        self.papers_collection = None
        self.validations_collection = None
    
    def connect(self):
        """Establish MongoDB connection."""
        self.client = MongoClient(self.uri)
        self.db = self.client[self.database_name]
        
        self.papers_collection = self.db["papers"]
        self.validations_collection = self.db["validations"]
        
        # Create indexes
        self.papers_collection.create_index("paper_id", unique=True)
        self.validations_collection.create_index("paper_id")
        self.validations_collection.create_index("created_at")
        
        print(f"Connected to MongoDB database: {self.database_name}")
    
    def disconnect(self):
        """Close MongoDB connection."""
        if self.client:
            self.client.close()
            print("Disconnected from MongoDB")
    
    # ===== Paper Operations =====
    
    def save_paper(self, paper: PaperDocument) -> str:
        """Save a paper document."""
        paper_dict = paper.model_dump()
        self.papers_collection.update_one(
            {"paper_id": paper.paper_id},
            {"$set": paper_dict},
            upsert=True
        )
        return paper.paper_id
    
    def get_paper(self, paper_id: str) -> Optional[PaperDocument]:
        """Retrieve a paper by ID."""
        doc = self.papers_collection.find_one({"paper_id": paper_id})
        if doc:
            doc.pop("_id", None)  # Remove MongoDB ID
            return PaperDocument(**doc)
        return None
    
    def list_papers(self, limit: int = 100) -> List[PaperDocument]:
        """List all papers."""
        papers = []
        for doc in self.papers_collection.find().limit(limit):
            doc.pop("_id", None)
            papers.append(PaperDocument(**doc))
        return papers
    
    # ===== Validation Operations =====
    
    def save_validation(self, validation: ValidationResult, paper_id: str) -> str:
        """Save a validation result."""
        validation_doc = ValidationDocument(
            paper_id=paper_id,
            validation_result=validation
        )
        
        doc_dict = validation_doc.model_dump()
        result = self.validations_collection.insert_one(doc_dict)
        return str(result.inserted_id)
    
    def get_latest_validation(self, paper_id: str) -> Optional[ValidationResult]:
        """Get the most recent validation for a paper."""
        doc = self.validations_collection.find_one(
            {"paper_id": paper_id},
            sort=[("created_at", -1)]
        )
        if doc:
            doc.pop("_id", None)
            validation_doc = ValidationDocument(**doc)
            return validation_doc.validation_result
        return None
    
    def get_all_validations(self, paper_id: str) -> List[ValidationResult]:
        """Get all validations for a paper."""
        validations = []
        for doc in self.validations_collection.find(
            {"paper_id": paper_id}
        ).sort("created_at", -1):
            doc.pop("_id", None)
            validation_doc = ValidationDocument(**doc)
            validations.append(validation_doc.validation_result)
        return validations
    
    def delete_paper(self, paper_id: str):
        """Delete a paper and all its validations."""
        self.papers_collection.delete_one({"paper_id": paper_id})
        self.validations_collection.delete_many({"paper_id": paper_id})
        print(f"Deleted paper {paper_id} and all its validations")
    
    # ===== Utility Methods =====
    
    def get_statistics(self) -> Dict:
        """Get database statistics."""
        return {
            "total_papers": self.papers_collection.count_documents({}),
            "total_validations": self.validations_collection.count_documents({}),
            "average_confidence": self._calculate_average_confidence()
        }
    
    def _calculate_average_confidence(self) -> float:
        """Calculate average confidence score across all validations."""
        pipeline = [
            {"$group": {
                "_id": None,
                "avg_confidence": {"$avg": "$validation_result.confidence_score"}
            }}
        ]
        
        result = list(self.validations_collection.aggregate(pipeline))
        if result:
            return result[0].get("avg_confidence", 0.0)
        return 0.0
