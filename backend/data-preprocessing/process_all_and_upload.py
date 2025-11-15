#!/usr/bin/env python3

"""
Process all PDF files and upload chunks to MongoDB
- Processes all 42 files in dataset
- Comprehensive logging for failures
- Uploads all chunks to MongoDB with correct _id format
"""

import json
import os
import sys
from pathlib import Path
from pymongo import MongoClient
from urllib.parse import quote_plus
from dotenv import load_dotenv
from datetime import datetime
from collections import Counter
import traceback

# Load environment variables
load_dotenv()

# Import chunking functions
sys.path.insert(0, str(Path(__file__).parent))
from robust_semantic_chunking import RobustSemanticChunker, process_file, detect_jurisdiction_from_filename

# MongoDB connection details
MONGODB_USERNAME = os.getenv('MONGODB_USERNAME', 'deep')
MONGODB_PASSWORD = os.getenv('MONGODB_PASSWORD', 'deepshelke123')
MONGODB_CLUSTER = os.getenv('MONGODB_CLUSTER', 'cluster1.hupax8i.mongodb.net')
MONGODB_APP_NAME = os.getenv('MONGODB_APP_NAME', 'Cluster1')
DATABASE_NAME = os.getenv('MONGODB_DATABASE', 'fairly')
COLLECTION_NAME = os.getenv('MONGODB_COLLECTION', 'fairly_chunks')

# Logging setup
LOG_FILE = Path(__file__).parent / "processing_log.txt"

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
    
    log_message("Connecting to MongoDB...")
    try:
        client = MongoClient(
            connection_string,
            serverSelectionTimeoutMS=10000,
            connectTimeoutMS=10000,
            socketTimeoutMS=10000,
            retryWrites=True
        )
        client.admin.command('ping')
        log_message("✅ Connected to MongoDB successfully!")
        
        db = client[DATABASE_NAME]
        collection = db[COLLECTION_NAME]
        
        log_message(f"✅ Using database: {DATABASE_NAME}")
        log_message(f"✅ Using collection: {COLLECTION_NAME}")
        
        return client, collection
    except Exception as e:
        log_message(f"❌ Failed to connect to MongoDB: {e}")
        raise

def create_indexes(collection):
    """Create indexes for efficient querying."""
    log_message("\n📇 Creating indexes...")
    try:
        collection.create_index("source_file")
        collection.create_index("jurisdiction")
        collection.create_index("topic")
        collection.create_index("chunk_index")
        collection.create_index([("source_file", 1), ("chunk_index", 1)])
        log_message("✅ Indexes created successfully!")
    except Exception as e:
        log_message(f"⚠️  Error creating indexes: {e}")

def upload_chunks(collection, chunks, source_file):
    """Upload chunks to MongoDB collection."""
    if not chunks:
        log_message(f"⚠️  No chunks to upload for {source_file}")
        return 0
    
    log_message(f"📤 Uploading {len(chunks)} chunks from {source_file}...")
    
    # Prepare documents for insertion
    documents = []
    for chunk in chunks:
        chunk_id = chunk["id"]
        
        doc = {
            "_id": chunk_id,  # Use chunk ID as MongoDB _id
            "id": chunk_id,
            "text": chunk["text"],
            "source_file": chunk["source_file"],
            "document_title": chunk["source_file"],
            "jurisdiction": chunk["jurisdiction"].lower(),
            "topic": chunk["topic"],
            "chunk_index": chunk["chunk_index"],
            "chunk_size": chunk["chunk_size"],
            "word_count": chunk["word_count"],
            "sentence_count": chunk["sentence_count"],
            "has_table": chunk.get("has_table", False),
            "has_list": chunk.get("has_list", False),
            "break_reason": chunk.get("break_reason", ""),
            "section": "Full Document",
            "document_type": "fact_sheet" if "fact sheet" in chunk["source_file"].lower() else "document",
            "metadata": chunk.get("metadata", {}),
        }
        
        # Add page_number if available
        if chunk.get("metadata", {}).get("pages_processed"):
            doc["page_number"] = 1
            doc["total_pages"] = chunk.get("metadata", {}).get("total_pages", 0)
        
        documents.append(doc)
    
    try:
        # Delete existing chunks from this file first
        delete_result = collection.delete_many({"source_file": source_file})
        if delete_result.deleted_count > 0:
            log_message(f"   🗑️  Deleted {delete_result.deleted_count} existing chunks from this file")
        
        # Insert documents
        result = collection.insert_many(documents, ordered=False)
        log_message(f"   ✅ Successfully uploaded {len(result.inserted_ids)} chunks!")
        return len(result.inserted_ids)
    except Exception as e:
        if "duplicate key" in str(e).lower() or "E11000" in str(e):
            log_message(f"   ⚠️  Duplicate key error. Using upsert...")
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
                    log_message(f"   ⚠️  Error with chunk {doc['_id']}: {e2}")
            log_message(f"   ✅ Upserted {inserted}/{len(documents)} chunks")
            return inserted
        else:
            log_message(f"   ❌ Error uploading chunks: {e}")
            raise

def main():
    """Main function - process all files and upload to MongoDB."""
    # Clear log file
    if LOG_FILE.exists():
        LOG_FILE.unlink()
    
    log_message("="*70)
    log_message("PROCESS ALL FILES AND UPLOAD TO MONGODB")
    log_message("="*70)
    
    # Initialize chunker
    log_message("\nInitializing chunker...")
    chunker = RobustSemanticChunker()
    
    # Known file mappings
    KNOWN_FILE_MAPPINGS = {
        "Protections-for-Domestic-Workers-Regulations-for-Public-Comment-with-Cover-Letter-10.07.2024.pdf": {
            "jurisdiction": "PHILADELPHIA",
        },
        "p712-2-20.pdf": {
            "jurisdiction": "NY",
        },
        "Domestic-Workers-339-Fact-Sheet.pdf": {
            "jurisdiction": "NYC",
        },
        "NJ Legislature.pdf": {
            "jurisdiction": "NJ",
        },
        "philadelphia-pa-1.pdf": {
            "jurisdiction": "PHILADELPHIA",
        },
        "Fact Sheet # 77A_ Prohibiting Retaliation Under the Fair Labor Standards Act (FLSA) _ U.S. Department of Labor.pdf": {
            "jurisdiction": "US_FEDERAL",
        },
    }
    
    # Point to dataset
    data_dir = Path("/Users/deepshelke/Desktop/HACK-RUC/dataset/Data_FactSheets")
    
    if not data_dir.exists():
        log_message(f"❌ Dataset directory not found: {data_dir}")
        return
    
    # Get all PDF files
    all_pdf_files = sorted(list(data_dir.glob("*.pdf")))
    
    if not all_pdf_files:
        log_message(f"❌ No PDF files found in: {data_dir}")
        return
    
    log_message(f"\n📁 Found {len(all_pdf_files)} PDF files to process\n")
    
    # Connect to MongoDB
    try:
        client, collection = connect_to_mongodb()
        create_indexes(collection)
    except Exception as e:
        log_message(f"❌ Cannot connect to MongoDB. Exiting.")
        return
    
    # Process all files
    all_chunks = []
    processed_count = 0
    skipped_count = 0
    error_count = 0
    uploaded_count = 0
    failed_files = []
    
    log_message("\n" + "="*70)
    log_message("PROCESSING FILES")
    log_message("="*70)
    
    for file_idx, file_path in enumerate(all_pdf_files, 1):
        filename = file_path.name
        log_message(f"\n[{file_idx}/{len(all_pdf_files)}] Processing: {filename}")
        
        # Get mapping
        if filename in KNOWN_FILE_MAPPINGS:
            mapping = KNOWN_FILE_MAPPINGS[filename]
        else:
            mapping = {"jurisdiction": None}
        
        # Process file
        try:
            chunks = process_file(file_path, chunker, {filename: mapping})
            
            if chunks:
                # Upload to MongoDB
                try:
                    uploaded = upload_chunks(collection, chunks, filename)
                    if uploaded > 0:
                        all_chunks.extend(chunks)
                        processed_count += 1
                        uploaded_count += uploaded
                        log_message(f"   ✅ File {file_idx}: {len(chunks)} chunks created and uploaded")
                    else:
                        skipped_count += 1
                        log_message(f"   ⚠️  File {file_idx}: Chunks created but upload failed")
                        failed_files.append({"file": filename, "reason": "Upload failed", "chunks": len(chunks)})
                except Exception as e:
                    error_count += 1
                    log_message(f"   ❌ File {file_idx}: Upload error - {e}")
                    failed_files.append({"file": filename, "reason": f"Upload error: {str(e)}", "chunks": len(chunks)})
                    traceback.print_exc()
            else:
                skipped_count += 1
                log_message(f"   ⚠️  File {file_idx}: No chunks generated")
                failed_files.append({"file": filename, "reason": "No chunks generated", "chunks": 0})
        
        except Exception as e:
            error_count += 1
            log_message(f"   ❌ File {file_idx}: Processing error - {e}")
            failed_files.append({"file": filename, "reason": f"Processing error: {str(e)}", "chunks": 0})
            traceback.print_exc()
            continue
    
    # Final statistics
    log_message("\n" + "="*70)
    log_message("PROCESSING COMPLETE")
    log_message("="*70)
    log_message(f"✅ Total files processed: {processed_count}/{len(all_pdf_files)}")
    log_message(f"⚠️  Files skipped: {skipped_count}")
    log_message(f"❌ Files with errors: {error_count}")
    log_message(f"📤 Total chunks uploaded: {uploaded_count}")
    
    # Check MongoDB collection
    try:
        total_in_db = collection.count_documents({})
        log_message(f"📊 Total chunks in MongoDB: {total_in_db}")
    except:
        pass
    
    # Failed files summary
    if failed_files:
        log_message(f"\n⚠️  FAILED FILES ({len(failed_files)}):")
        for failed in failed_files:
            log_message(f"   - {failed['file']}: {failed['reason']} ({failed['chunks']} chunks)")
    
    # Statistics
    if all_chunks:
        log_message(f"\n📊 STATISTICS:")
        sizes = [c["chunk_size"] for c in all_chunks]
        log_message(f"   Total chunks: {len(all_chunks)}")
        log_message(f"   Size range: {min(sizes)} - {max(sizes)} chars")
        log_message(f"   Average: {int(sum(sizes)/len(sizes))} chars")
        
        # Check ID uniqueness
        ids = [c["id"] for c in all_chunks]
        unique_ids = len(set(ids))
        log_message(f"   Unique IDs: {unique_ids}/{len(ids)}")
        if unique_ids == len(ids):
            log_message(f"   ✅ NO COLLISIONS - All IDs are unique!")
        
        # Topic distribution
        topics = Counter([c["topic"] for c in all_chunks])
        log_message(f"\n   Topic distribution (top 5):")
        for topic, count in topics.most_common(5):
            log_message(f"     {topic}: {count} chunks")
        
        # Jurisdiction distribution
        jurisdictions = Counter([c["jurisdiction"] for c in all_chunks])
        log_message(f"\n   Jurisdiction distribution:")
        for jur, count in sorted(jurisdictions.items()):
            log_message(f"     {jur}: {count} chunks")
    
    client.close()
    log_message(f"\n✅ Processing complete! Log saved to: {LOG_FILE}")
    log_message("="*70)

if __name__ == "__main__":
    main()

