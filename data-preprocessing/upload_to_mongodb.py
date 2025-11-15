#!/usr/bin/env python3

"""
Upload chunks to MongoDB - Single file test
"""

import json
import os
from pathlib import Path
from pymongo import MongoClient
from urllib.parse import quote_plus
from dotenv import load_dotenv
import sys

# Load environment variables
load_dotenv()

# MongoDB connection details
MONGODB_USERNAME = os.getenv('MONGODB_USERNAME', 'deep')
MONGODB_PASSWORD = os.getenv('MONGODB_PASSWORD', 'deepshelke123')
MONGODB_CLUSTER = os.getenv('MONGODB_CLUSTER', 'cluster1.hupax8i.mongodb.net')
MONGODB_APP_NAME = os.getenv('MONGODB_APP_NAME', 'Cluster1')
DATABASE_NAME = os.getenv('MONGODB_DATABASE', 'fairly')
COLLECTION_NAME = os.getenv('MONGODB_COLLECTION', 'fairly_chunks')

def connect_to_mongodb():
    """Connect to MongoDB Atlas."""
    password_encoded = quote_plus(MONGODB_PASSWORD)
    connection_string = f"mongodb+srv://{MONGODB_USERNAME}:{password_encoded}@{MONGODB_CLUSTER}/?appName={MONGODB_APP_NAME}"
    
    print("Connecting to MongoDB...")
    try:
        client = MongoClient(
            connection_string,
            serverSelectionTimeoutMS=10000,
            connectTimeoutMS=10000,
            socketTimeoutMS=10000,
            retryWrites=True
        )
        # Test connection
        client.admin.command('ping')
        print("✅ Connected to MongoDB successfully!")
        
        db = client[DATABASE_NAME]
        collection = db[COLLECTION_NAME]
        
        print(f"✅ Using database: {DATABASE_NAME}")
        print(f"✅ Using collection: {COLLECTION_NAME}")
        
        return client, collection
    except Exception as e:
        print(f"❌ Failed to connect to MongoDB: {e}")
        raise

def upload_chunks(collection, chunks):
    """Upload chunks to MongoDB collection."""
    if not chunks:
        print("⚠️  No chunks to upload")
        return
    
    print(f"\n📤 Uploading {len(chunks)} chunks to MongoDB...")
    
    # Prepare documents for insertion
    documents = []
    for chunk in chunks:
        # MongoDB document structure - use chunk ID as _id
        chunk_id = chunk["id"]  # This is our source_file_name_chunk_number format
        
        doc = {
            "_id": chunk_id,  # CRITICAL: Use chunk ID as MongoDB _id (source_file_name_chunk_number)
            "id": chunk_id,  # Also keep as regular field
            "text": chunk["text"],
            "source_file": chunk["source_file"],
            "document_title": chunk["source_file"],  # Add document_title field
            "jurisdiction": chunk["jurisdiction"].lower(),  # Lowercase for consistency
            "topic": chunk["topic"],
            "chunk_index": chunk["chunk_index"],
            "chunk_size": chunk["chunk_size"],
            "word_count": chunk["word_count"],
            "sentence_count": chunk["sentence_count"],
            "has_table": chunk.get("has_table", False),
            "has_list": chunk.get("has_list", False),
            "break_reason": chunk.get("break_reason", ""),
            "section": "Full Document",  # Default section
            "document_type": "fact_sheet" if "fact sheet" in chunk["source_file"].lower() else "document",
            "metadata": chunk.get("metadata", {}),
        }
        
        # Add page_number if available
        if chunk.get("metadata", {}).get("pages_processed"):
            doc["page_number"] = 1  # Default, can be improved later
            doc["total_pages"] = chunk.get("metadata", {}).get("total_pages", 0)
        
        documents.append(doc)
    
    try:
        # Delete existing chunks from this file first (to avoid duplicates)
        if documents:
            source_file = documents[0]["source_file"]
            delete_result = collection.delete_many({"source_file": source_file})
            if delete_result.deleted_count > 0:
                print(f"   🗑️  Deleted {delete_result.deleted_count} existing chunks from this file")
        
        # Insert documents - MongoDB will use _id field we provided
        result = collection.insert_many(documents, ordered=False)
        print(f"✅ Successfully uploaded {len(result.inserted_ids)} chunks!")
        print(f"   Using IDs: {documents[0]['_id'][:50]}... (sample)")
        return len(result.inserted_ids)
    except Exception as e:
        # Handle duplicate key errors
        if "duplicate key" in str(e).lower() or "E11000" in str(e):
            print(f"⚠️  Some chunks already exist. Trying upsert...")
            # Use upsert for duplicates
            inserted = 0
            for doc in documents:
                try:
                    collection.replace_one(
                        {"_id": doc["_id"]},
                        doc,
                        upsert=True
                    )
                    inserted += 1
                except Exception as e2:
                    print(f"   ⚠️  Error with chunk {doc['_id']}: {e2}")
            print(f"✅ Upserted {inserted}/{len(documents)} chunks")
            return inserted
        else:
            print(f"❌ Error uploading chunks: {e}")
            raise

def create_indexes(collection):
    """Create indexes for efficient querying."""
    print("\n📇 Creating indexes...")
    try:
        # Create indexes
        collection.create_index("source_file")
        collection.create_index("jurisdiction")
        collection.create_index("topic")
        collection.create_index("chunk_index")
        collection.create_index([("source_file", 1), ("chunk_index", 1)])
        print("✅ Indexes created successfully!")
    except Exception as e:
        print(f"⚠️  Error creating indexes: {e}")

def main():
    """Main function - process 1 file and upload to MongoDB."""
    print("="*70)
    print("UPLOAD CHUNKS TO MONGODB - SINGLE FILE TEST")
    print("="*70)
    
    # Import chunking function
    sys.path.insert(0, str(Path(__file__).parent))
    from robust_semantic_chunking import RobustSemanticChunker, process_file, detect_jurisdiction_from_filename
    from datetime import datetime
    
    # Initialize chunker
    chunker = RobustSemanticChunker()
    
    # Select 1 file to process
    data_dir = Path(__file__).parent.parent / "dataset" / "Data_FactSheets"
    test_file = data_dir / "Fact Sheet # 77A_ Prohibiting Retaliation Under the Fair Labor Standards Act (FLSA) _ U.S. Department of Labor.pdf"
    
    if not test_file.exists():
        print(f"❌ Test file not found: {test_file}")
        return
    
    print(f"\n📁 Processing file: {test_file.name}")
    
    # Process file
    file_mapping = {
        test_file.name: {"jurisdiction": "US_FEDERAL"}
    }
    
    chunks = process_file(test_file, chunker, file_mapping)
    
    if not chunks:
        print("❌ No chunks created")
        return
    
    print(f"\n✅ Created {len(chunks)} chunks from file")
    
    # Connect to MongoDB
    try:
        client, collection = connect_to_mongodb()
        
        # Create indexes
        create_indexes(collection)
        
        # Upload chunks
        uploaded = upload_chunks(collection, chunks)
        
        # Verify upload
        count = collection.count_documents({})
        print(f"\n📊 Collection now contains {count} total chunks")
        
        # Show sample
        sample = collection.find_one({"source_file": test_file.name})
        if sample:
            print(f"\n✅ Sample chunk in MongoDB:")
            print(f"   ID: {sample['_id']}")
            print(f"   Source: {sample['source_file']}")
            print(f"   Size: {sample['chunk_size']} chars")
            print(f"   Topic: {sample['topic']}")
        
        client.close()
        print(f"\n✅ Upload complete!")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()

