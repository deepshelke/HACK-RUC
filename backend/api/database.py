"""
MongoDB connection and database utilities.
"""
from pymongo import MongoClient
from urllib.parse import quote_plus
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

# MongoDB connection details
MONGODB_USERNAME = os.getenv('MONGODB_USERNAME')
MONGODB_PASSWORD = os.getenv('MONGODB_PASSWORD')
MONGODB_CLUSTER = os.getenv('MONGODB_CLUSTER')
MONGODB_APP_NAME = os.getenv('MONGODB_APP_NAME')
DATABASE_NAME = os.getenv('MONGODB_DATABASE', 'fairly')

# Collections
CHATS_COLLECTION = 'chats'
MESSAGES_COLLECTION = 'messages'

class Database:
    _client = None
    _db = None
    
    @classmethod
    def connect(cls):
        """Connect to MongoDB."""
        if cls._client is None:
            password_encoded = quote_plus(MONGODB_PASSWORD)
            connection_string = f"mongodb+srv://{MONGODB_USERNAME}:{password_encoded}@{MONGODB_CLUSTER}/?appName={MONGODB_APP_NAME}"
            
            cls._client = MongoClient(
                connection_string,
                serverSelectionTimeoutMS=10000,
                connectTimeoutMS=10000,
                socketTimeoutMS=10000,
                retryWrites=True
            )
            cls._db = cls._client[DATABASE_NAME]
            print(f"✅ Connected to MongoDB: {DATABASE_NAME}")
        
        return cls._db
    
    @classmethod
    def get_collection(cls, collection_name):
        """Get a collection."""
        if cls._db is None:
            cls.connect()
        return cls._db[collection_name]
    
    @classmethod
    def close(cls):
        """Close MongoDB connection."""
        if cls._client:
            cls._client.close()
            cls._client = None
            cls._db = None

# Initialize connection
Database.connect()

