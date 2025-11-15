#!/usr/bin/env python3

"""
Process new PDF files from new_data folder
- Chunk the PDFs
- Upload to MongoDB
- Generate embeddings and upload to Pinecone
"""

import json
import os
import sys
from pathlib import Path
from pymongo import MongoClient
from urllib.parse import quote_plus
from dotenv import load_dotenv
from datetime import datetime
import traceback

# Load environment variables
load_dotenv()

# Import chunking functions
sys.path.insert(0, str(Path(__file__).parent))
from robust_semantic_chunking import RobustSemanticChunker, process_file, detect_jurisdiction_from_filename

# MongoDB connection details
MONGODB_USERNAME = os.getenv('MONGODB_USERNAME')
MONGODB_PASSWORD = os.getenv('MONGODB_PASSWORD')
MONGODB_CLUSTER = os.getenv('MONGODB_CLUSTER')
MONGODB_APP_NAME = os.getenv('MONGODB_APP_NAME')
DATABASE_NAME = os.getenv('MONGODB_DATABASE')
COLLECTION_NAME = os.getenv('MONGODB_COLLECTION')

# Logging setup
LOG_FILE = Path(__file__).parent / "new_data_processing_log.txt"

def log_message(message, log_file=LOG_FILE):
    """Log message to file and print to console."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] {message}\n"
    print(message)
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(log_entry)

def connect_to_mongodb():
    """Connect to MongoDB Atlas."""
    password_encoded = quote_plus(MONGODB_PASSWORD)
    connection_string = f"mongodb+srv://{MONGODB_USERNAME}:{password_encoded}@{MONGODB_CLUSTER}/?appName={MONGODB_APP_NAME}"
    
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
        
        db = client[DATABASE_NAME]
        collection = db[COLLECTION_NAME]
        
        return client, collection
    except Exception as e:
        log_message(f"❌ MongoDB connection error: {e}")
        raise

def create_indexes(collection):
    """Create indexes for efficient queries."""
    try:
        collection.create_index([("source_file", 1)])
        collection.create_index([("jurisdiction", 1)])
        collection.create_index([("topic", 1)])
        collection.create_index([("source_file", 1), ("chunk_index", 1)])
    except Exception as e:
        log_message(f"⚠️  Error creating indexes: {e}")

def upload_chunks(collection, chunks, source_file):
    """Upload chunks to MongoDB."""
    if not chunks:
        return 0
    
    try:
        # Delete existing chunks from this source file
        delete_result = collection.delete_many({"source_file": source_file})
        if delete_result.deleted_count > 0:
            log_message(f"   🗑️  Deleted {delete_result.deleted_count} existing chunks from {source_file}")
        
        # Prepare documents
        documents = []
        for chunk in chunks:
            doc = {
                "_id": chunk["id"],
                "text": chunk["text"],
                "source_file": source_file,
                "chunk_index": chunk.get("chunk_index", 0),
                "chunk_size": len(chunk["text"]),
                "token_count": chunk.get("token_count", 0),
                "document_type": chunk.get("document_type", "unknown"),
                "jurisdiction": chunk.get("jurisdiction", "unknown"),
                "document_title": chunk.get("document_title", ""),
                "section": chunk.get("section", "Full Document"),
                "page_number": chunk.get("page_number", 0),
                "total_pages": chunk.get("total_pages", 0),
                "topic": chunk.get("topic", ""),
                "headings_count": chunk.get("headings_count", 0),
                "metadata": chunk.get("metadata", {}),
                "created_at": datetime.utcnow()
            }
            documents.append(doc)
        
        # Insert documents
        if documents:
            result = collection.insert_many(documents, ordered=False)
            log_message(f"   ✅ Uploaded {len(result.inserted_ids)} chunks to MongoDB")
            return len(result.inserted_ids)
        return 0
        
    except Exception as e:
        log_message(f"   ❌ Error uploading chunks: {e}")
        # Try individual inserts for better error handling
        inserted = 0
        for doc in documents:
            try:
                collection.insert_one(doc)
                inserted += 1
            except Exception as e2:
                log_message(f"   ⚠️  Error with chunk {doc['_id']}: {e2}")
        log_message(f"   ✅ Upserted {inserted}/{len(documents)} chunks")
        return inserted

def main():
    """Main function - process new data folder."""
    # Clear log file
    if LOG_FILE.exists():
        LOG_FILE.unlink()
    
    log_message("="*70)
    log_message("PROCESS NEW DATA FOLDER")
    log_message("="*70)
    
    # Initialize chunker
    log_message("\nInitializing chunker...")
    chunker = RobustSemanticChunker()
    
    # Point to new_data folder
    data_dir = Path("/Users/deepshelke/Desktop/HACK-RUC/new_data")
    
    if not data_dir.exists():
        log_message(f"❌ Directory not found: {data_dir}")
        return
    
    # Get all PDF files
    all_pdf_files = sorted(list(data_dir.glob("*.pdf")))
    
    if not all_pdf_files:
        log_message(f"❌ No PDF files found in: {data_dir}")
        return
    
    log_message(f"\n📁 Found {len(all_pdf_files)} PDF file(s) to process")
    
    # Connect to MongoDB
    try:
        log_message("\nConnecting to MongoDB...")
        client, collection = connect_to_mongodb()
        log_message("✅ Connected to MongoDB")
        
        # Create indexes
        log_message("\nCreating indexes...")
        create_indexes(collection)
        log_message("✅ Indexes created")
        
    except Exception as e:
        log_message(f"❌ Failed to connect to MongoDB: {e}")
        return
    
    # Process each file
    total_chunks = 0
    successful_files = 0
    failed_files = 0
    
    for file_path in all_pdf_files:
        log_message("\n" + "="*70)
        log_message(f"Processing: {file_path.name}")
        log_message("="*70)
        
        try:
            # Detect jurisdiction from filename
            jurisdiction = detect_jurisdiction_from_filename(file_path.name)
            log_message(f"   📍 Detected jurisdiction: {jurisdiction}")
            
            # File mapping (can be customized)
            file_mapping = {
                file_path.name: {"jurisdiction": jurisdiction}
            }
            
            # Process file
            log_message(f"   🔄 Processing file...")
            chunks = process_file(file_path, chunker, file_mapping)
            
            if not chunks:
                log_message(f"   ⚠️  No chunks created from {file_path.name}")
                failed_files += 1
                continue
            
            log_message(f"   ✅ Created {len(chunks)} chunks")
            total_chunks += len(chunks)
            
            # Upload to MongoDB
            log_message(f"   📤 Uploading to MongoDB...")
            uploaded = upload_chunks(collection, chunks, file_path.name)
            
            if uploaded > 0:
                log_message(f"   ✅ Successfully processed {file_path.name}")
                successful_files += 1
            else:
                log_message(f"   ⚠️  Failed to upload chunks for {file_path.name}")
                failed_files += 1
                
        except Exception as e:
            log_message(f"   ❌ Error processing {file_path.name}: {e}")
            log_message(f"   Traceback: {traceback.format_exc()}")
            failed_files += 1
    
    # Summary
    log_message("\n" + "="*70)
    log_message("PROCESSING SUMMARY")
    log_message("="*70)
    log_message(f"Total files: {len(all_pdf_files)}")
    log_message(f"✅ Successful: {successful_files}")
    log_message(f"❌ Failed: {failed_files}")
    log_message(f"📊 Total chunks created: {total_chunks}")
    log_message("="*70)
    
    client.close()
    log_message("\n✅ Processing complete!")
    log_message(f"📝 Log saved to: {LOG_FILE}")
    log_message("\n⚠️  Next step: Run embedding generation to vectorize these chunks")

if __name__ == "__main__":
    main()

