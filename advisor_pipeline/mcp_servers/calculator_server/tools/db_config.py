"""
MongoDB Configuration and Connection Management
"""
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
import os
from typing import Optional

class MongoDBConnection:
    """Manages MongoDB connection"""
    
    def __init__(self, connection_string: Optional[str] = None):
        """
        Initialize MongoDB connection
        
        Args:
            connection_string: MongoDB connection string. 
                             Defaults to MONGODB_URI env variable or localhost
        """
        self.connection_string = connection_string or os.getenv(
            'MONGODB_URI', 
            'mongodb://localhost:27017/'
        )
        self.client = None
        self.db = None
        
    def connect(self, database_name: str = 'equations_db'):
        """Connect to MongoDB and return database instance"""
        try:
            self.client = MongoClient(self.connection_string)
            # Test connection
            self.client.admin.command('ping')
            self.db = self.client[database_name]
            print(f"✓ Connected to MongoDB database: {database_name}")
            return self.db
        except ConnectionFailure as e:
            print(f"✗ Failed to connect to MongoDB: {e}")
            raise
    
    def close(self):
        """Close MongoDB connection"""
        if self.client:
            self.client.close()
            print("✓ MongoDB connection closed")
    
    def get_collection(self, collection_name: str):
        """Get a specific collection from the database"""
        if not self.db:
            raise RuntimeError("Database not connected. Call connect() first.")
        return self.db[collection_name]


# Database and collection names
DB_NAME = 'equations_db'
FORMULAS_COLLECTION = 'formulas'
