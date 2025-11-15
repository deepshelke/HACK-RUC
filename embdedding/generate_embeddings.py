#!/usr/bin/env python3

"""
Generate embeddings using Gemini gemini-embedding-exp-03-07 model
- Fetches chunks from MongoDB
- Generates 3072-dimensional embeddings using Gemini gemini-embedding-exp-03-07 API
- Stores embeddings in Pinecone with same IDs as MongoDB
"""

import os
import sys
from pathlib import Path
from pymongo import MongoClient
from urllib.parse import quote_plus
from dotenv import load_dotenv
from datetime import datetime
import time
import json
import google.generativeai as genai
from pinecone import Pinecone
import traceback

# Load environment variables
load_dotenv(Path(__file__).parent.parent / ".env")

# MongoDB connection details
MONGODB_USERNAME = os.getenv('MONGODB_USERNAME', 'deep')
MONGODB_PASSWORD = os.getenv('MONGODB_PASSWORD', 'deepshelke123')
MONGODB_CLUSTER = os.getenv('MONGODB_CLUSTER', 'cluster1.hupax8i.mongodb.net')
MONGODB_APP_NAME = os.getenv('MONGODB_APP_NAME', 'Cluster1')
DATABASE_NAME = os.getenv('MONGODB_DATABASE', 'fairly')
COLLECTION_NAME = os.getenv('MONGODB_COLLECTION', 'fairly_chunks')

# Gemini API
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', 'AIzaSyDlyEYEMOWQB8EgnDV0vTCJan8JgYhyno8')

# Pinecone API
PINECONE_API_KEY = os.getenv('PINECONE_API_KEY', 'pcsk_2N3E6V_QHopkTxvTXj957o8w1eCYPyzm9RH3KgGrsfySya3fqwwmX9sWE2znGijnbt1LeH')
PINECONE_INDEX_NAME = os.getenv('PINECONE_INDEX_NAME', 'domestic-worker-rights')

# Configuration
EMBEDDING_MODEL = "gemini-embedding-exp-03-07"  # Gemini embedding model (3072 dimensions)
EMBEDDING_DIMENSION = 3072
BATCH_SIZE = 20  # Process chunks in batches of 20
LOG_FILE = Path(__file__).parent / "embedding_log.txt"
FAILED_CHUNKS_FILE = Path(__file__).parent / "failed_chunks.json"


def log_message(message, log_file=LOG_FILE):
    """Log message to file and print to console."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] {message}\n"
    print(message)
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(log_entry)


def connect_to_mongodb():
    """Connect to MongoDB and get collection."""
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
        
        return client, collection
    except Exception as e:
        log_message(f"❌ Failed to connect to MongoDB: {e}")
        raise


def initialize_gemini():
    """Initialize Gemini API client."""
    log_message("Initializing Gemini API...")
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        log_message("✅ Gemini API initialized!")
        return True
    except Exception as e:
        log_message(f"❌ Failed to initialize Gemini API: {e}")
        raise


def generate_embedding(text: str, chunk_id: str = None) -> list:
    """
    Generate embedding using Gemini gemini-embedding-exp-03-07 model (3072 dimensions).
    Returns 3072-dimensional embedding vector.
    """
    try:
        # Use Gemini embedding API (same as test_single_chunk.py)
        result = genai.embed_content(
            model=f"models/{EMBEDDING_MODEL}",
            content=text,
            task_type="RETRIEVAL_DOCUMENT",  # For RAG retrieval
            output_dimensionality=EMBEDDING_DIMENSION
        )
        
        # Extract embedding from result (same pattern as test_single_chunk.py)
        if hasattr(result, 'embedding'):
            embedding = result.embedding
        elif isinstance(result, dict):
            embedding = result.get('embedding', result.get('values', []))
        elif isinstance(result, list):
            embedding = result
        else:
            embedding = getattr(result, 'values', list(result) if hasattr(result, '__iter__') else [])
        
        # Convert to list
        if not isinstance(embedding, list):
            embedding = list(embedding)
        
        # Verify dimension
        if len(embedding) != EMBEDDING_DIMENSION:
            log_message(f"⚠️  Chunk {chunk_id}: Embedding dimension is {len(embedding)}, expected {EMBEDDING_DIMENSION}")
            # Try without output_dimensionality if dimension mismatch
            log_message(f"   Retrying without output_dimensionality...")
            result2 = genai.embed_content(
                model=f"models/{EMBEDDING_MODEL}",
                content=text,
                task_type="RETRIEVAL_DOCUMENT"
            )
            if hasattr(result2, 'embedding'):
                embedding = result2.embedding
            elif isinstance(result2, dict):
                embedding = result2.get('embedding', result2.get('values', []))
            embedding = list(embedding) if not isinstance(embedding, list) else embedding
            if len(embedding) != EMBEDDING_DIMENSION:
                raise ValueError(f"Dimension mismatch: got {len(embedding)}, expected {EMBEDDING_DIMENSION}")
        
        return embedding
    except Exception as e:
        error_msg = f"Error generating embedding for chunk {chunk_id}: {e}" if chunk_id else f"Error generating embedding: {e}"
        log_message(f"⚠️  {error_msg}")
        raise


def generate_embeddings_batch(texts: list, chunk_ids: list) -> tuple:
    """
    Generate embeddings for a batch of texts.
    Returns (embeddings, failed_ids)
    """
    embeddings = []
    failed_ids = []
    
    for i, (text, chunk_id) in enumerate(zip(texts, chunk_ids)):
        try:
            embedding = generate_embedding(text, chunk_id)
            embeddings.append(embedding)
            log_message(f"   ✅ Generated embedding {i + 1}/{len(texts)}: {chunk_id}")
        except Exception as e:
            log_message(f"   ❌ FAILED embedding {i + 1}/{len(texts)}: {chunk_id} - {e}")
            embeddings.append(None)
            failed_ids.append(chunk_id)
            traceback.print_exc()
    
    return embeddings, failed_ids


def connect_to_pinecone():
    """Connect to Pinecone and get/create index."""
    log_message("Connecting to Pinecone...")
    try:
        pc = Pinecone(api_key=PINECONE_API_KEY)
        log_message("✅ Connected to Pinecone!")
        
        # Check if index exists
        existing_indexes = [idx.name for idx in pc.list_indexes()]
        
        if PINECONE_INDEX_NAME in existing_indexes:
            log_message(f"✅ Index '{PINECONE_INDEX_NAME}' already exists")
            index = pc.Index(PINECONE_INDEX_NAME)
        else:
            log_message(f"📇 Creating new index '{PINECONE_INDEX_NAME}'...")
            pc.create_index(
                name=PINECONE_INDEX_NAME,
                dimension=EMBEDDING_DIMENSION,
                metric="cosine",
                spec={
                    "serverless": {
                        "cloud": "aws",
                        "region": "us-east-1"
                    }
                }
            )
            log_message(f"✅ Index '{PINECONE_INDEX_NAME}' created!")
            # Wait for index to be ready
            time.sleep(10)
            index = pc.Index(PINECONE_INDEX_NAME)
        
        return index
    except Exception as e:
        log_message(f"❌ Failed to connect to Pinecone: {e}")
        raise


def upload_to_pinecone(index, vectors: list):
    """
    Upload vectors to Pinecone.
    Returns (uploaded_count, failed_ids)
    """
    if not vectors:
        log_message("⚠️  No vectors to upload")
        return 0, []
    
    log_message(f"📤 Uploading {len(vectors)} vectors to Pinecone...")
    
    failed_ids = []
    vectors_to_upsert = []
    
    try:
        # Pinecone expects format: [(id, vector, metadata), ...]
        for vector_data in vectors:
            if vector_data['embedding'] is None:
                failed_ids.append(vector_data['id'])
                log_message(f"   ⚠️  Skipping chunk {vector_data['id']}: No embedding")
                continue
            
            try:
                vector_entry = (
                    vector_data['id'],  # Use same ID as MongoDB
                    vector_data['embedding'],
                    {
                        'text': vector_data['text'][:1000],  # Truncate for metadata
                        'source_file': vector_data.get('source_file', 'unknown'),
                        'jurisdiction': vector_data.get('jurisdiction', 'unknown'),
                        'document_type': vector_data.get('document_type', 'unknown'),
                        'chunk_index': vector_data.get('chunk_index', 0),
                        'chunk_size': vector_data.get('chunk_size', len(vector_data['text'])),
                    }
                )
                vectors_to_upsert.append(vector_entry)
            except Exception as e:
                failed_ids.append(vector_data['id'])
                log_message(f"   ❌ FAILED preparing vector {vector_data['id']}: {e}")
        
        if not vectors_to_upsert:
            log_message("⚠️  No valid vectors to upload")
            return 0, failed_ids
        
        # Upload in batches (Pinecone recommends batches of 100)
        uploaded = 0
        upload_failed = []
        
        try:
            # Upload all at once (Pinecone handles batching internally)
            index.upsert(vectors=vectors_to_upsert)
            uploaded = len(vectors_to_upsert)
            log_message(f"   ✅ Uploaded {uploaded} vectors to Pinecone!")
        except Exception as e:
            log_message(f"   ⚠️  Batch upload failed, trying individual uploads...")
            # Fallback: try individual uploads
            for vector_entry in vectors_to_upsert:
                try:
                    index.upsert(vectors=[vector_entry])
                    uploaded += 1
                except Exception as e2:
                    failed_ids.append(vector_entry[0])  # vector_entry[0] is the ID
                    upload_failed.append(vector_entry[0])
                    log_message(f"   ❌ FAILED uploading {vector_entry[0]}: {e2}")
        
        if upload_failed:
            log_message(f"   ⚠️  {len(upload_failed)} vectors failed to upload")
        
        return uploaded, failed_ids
        
    except Exception as e:
        log_message(f"❌ Error uploading to Pinecone: {e}")
        traceback.print_exc()
        # Mark all as failed
        failed_ids.extend([v['id'] for v in vectors])
        return 0, failed_ids


def main():
    """Main function - generate embeddings and upload to Pinecone."""
    # Clear log file
    if LOG_FILE.exists():
        LOG_FILE.unlink()
    
    log_message("="*70)
    log_message("GENERATE EMBEDDINGS AND UPLOAD TO PINECONE")
    log_message("="*70)
    
    # Initialize APIs
    try:
        # MongoDB
        mongo_client, mongo_collection = connect_to_mongodb()
        
        # Gemini
        initialize_gemini()
        
        # Pinecone
        pinecone_index = connect_to_pinecone()
    except Exception as e:
        log_message(f"❌ Initialization failed: {e}")
        return
    
    # Get all chunks from MongoDB
    log_message("\n📥 Fetching chunks from MongoDB...")
    try:
        chunks = list(mongo_collection.find({}))
        log_message(f"✅ Fetched {len(chunks)} chunks from MongoDB")
    except Exception as e:
        log_message(f"❌ Error fetching chunks: {e}")
        mongo_client.close()
        return
    
    if not chunks:
        log_message("⚠️  No chunks found in MongoDB")
        mongo_client.close()
        return
    
    # Process chunks in batches
    total_batches = (len(chunks) + BATCH_SIZE - 1) // BATCH_SIZE
    log_message(f"\n🔄 Processing {len(chunks)} chunks in {total_batches} batches of {BATCH_SIZE}...")
    
    total_processed = 0
    total_uploaded = 0
    failed_chunks = []  # Track all failed chunk IDs
    
    for batch_num, batch_start in enumerate(range(0, len(chunks), BATCH_SIZE), 1):
        batch_end = min(batch_start + BATCH_SIZE, len(chunks))
        batch_chunks = chunks[batch_start:batch_end]
        
        log_message(f"\n{'='*70}")
        log_message(f"📦 BATCH {batch_num}/{total_batches} (chunks {batch_start+1}-{batch_end} of {len(chunks)})")
        log_message(f"{'='*70}")
        
        # Prepare texts for embedding
        texts = []
        chunk_ids = []
        chunk_metadata = []
        
        for chunk in batch_chunks:
            chunk_id = chunk.get('_id') or chunk.get('id')
            chunk_text = chunk.get('text', '')
            
            if not chunk_id:
                log_message(f"   ⚠️  Skipping chunk: Missing ID")
                failed_chunks.append(f"missing_id_{batch_start + len(texts)}")
                continue
            
            if not chunk_text or len(chunk_text.strip()) == 0:
                log_message(f"   ⚠️  Skipping chunk {chunk_id}: Missing or empty text")
                failed_chunks.append(chunk_id)
                continue
            
            texts.append(chunk_text)
            chunk_ids.append(chunk_id)
            chunk_metadata.append({
                'id': chunk_id,
                'text': chunk_text,
                'source_file': chunk.get('source_file', 'unknown'),
                'jurisdiction': chunk.get('jurisdiction', 'unknown'),
                'document_type': chunk.get('document_type', 'unknown'),
                'chunk_index': chunk.get('chunk_index', 0),
                'chunk_size': len(chunk_text),
            })
        
        if not texts:
            log_message(f"   ⚠️  No valid texts in batch, skipping...")
            continue
        
        # Generate embeddings
        log_message(f"   🔄 Generating embeddings for {len(texts)} chunks...")
        batch_failed_embedding = []
        
        try:
            embeddings, batch_failed_embedding = generate_embeddings_batch(texts, chunk_ids)
            failed_chunks.extend(batch_failed_embedding)
            
            # Prepare vectors for Pinecone
            vectors = []
            for i, (metadata, embedding) in enumerate(zip(chunk_metadata, embeddings)):
                if embedding is None:
                    log_message(f"   ⚠️  Skipping {metadata['id']}: No embedding generated")
                    continue
                
                # Verify embedding dimension
                if len(embedding) != EMBEDDING_DIMENSION:
                    log_message(f"   ❌ FAILED {metadata['id']}: Wrong dimension {len(embedding)}, expected {EMBEDDING_DIMENSION}")
                    failed_chunks.append(metadata['id'])
                    continue
                
                vectors.append({
                    'id': metadata['id'],
                    'embedding': embedding,
                    'text': metadata['text'],
                    'source_file': metadata['source_file'],
                    'jurisdiction': metadata['jurisdiction'],
                    'document_type': metadata['document_type'],
                    'chunk_index': metadata['chunk_index'],
                    'chunk_size': metadata['chunk_size'],
                })
            
            log_message(f"   ✅ Generated {len(vectors)} valid embeddings (out of {len(texts)} chunks)")
            
            # Upload to Pinecone
            uploaded, upload_failed = upload_to_pinecone(pinecone_index, vectors)
            failed_chunks.extend(upload_failed)
            total_uploaded += uploaded
            total_processed += len(vectors)
            
            log_message(f"   📊 Batch {batch_num} Summary:")
            log_message(f"      ✅ Processed: {len(vectors)}")
            log_message(f"      ✅ Uploaded: {uploaded}")
            log_message(f"      ❌ Failed: {len(batch_failed_embedding) + len(upload_failed)}")
            
        except Exception as e:
            log_message(f"   ❌ CRITICAL ERROR processing batch {batch_num}: {e}")
            traceback.print_exc()
            # Mark all chunks in this batch as failed
            failed_chunks.extend(chunk_ids)
            log_message(f"   ⚠️  Marked all {len(chunk_ids)} chunks in batch as failed")
            continue
        
        # Rate limiting - small delay between batches
        if batch_end < len(chunks):
            log_message(f"   ⏳ Waiting 2 seconds before next batch...")
            time.sleep(2)
    
    # Final statistics
    log_message("\n" + "="*70)
    log_message("EMBEDDING GENERATION COMPLETE")
    log_message("="*70)
    log_message(f"📊 FINAL STATISTICS:")
    log_message(f"   Total chunks in MongoDB: {len(chunks)}")
    log_message(f"   ✅ Successfully processed: {total_processed}")
    log_message(f"   ✅ Successfully uploaded to Pinecone: {total_uploaded}")
    log_message(f"   ❌ Failed chunks: {len(failed_chunks)}")
    log_message(f"   📈 Success rate: {(total_processed/len(chunks)*100):.2f}%")
    
    # Save failed chunk IDs to file
    if failed_chunks:
        failed_data = {
            'total_failed': len(failed_chunks),
            'failed_chunk_ids': failed_chunks,
            'timestamp': datetime.now().isoformat()
        }
        with open(FAILED_CHUNKS_FILE, 'w', encoding='utf-8') as f:
            json.dump(failed_data, f, indent=2, ensure_ascii=False)
        log_message(f"\n⚠️  Failed chunk IDs saved to: {FAILED_CHUNKS_FILE}")
        log_message(f"   Total failed: {len(failed_chunks)}")
        log_message(f"   Failed chunk IDs (first 20):")
        for chunk_id in failed_chunks[:20]:
            log_message(f"      - {chunk_id}")
        if len(failed_chunks) > 20:
            log_message(f"   ... and {len(failed_chunks) - 20} more (see {FAILED_CHUNKS_FILE})")
    else:
        log_message(f"\n✅ No failed chunks! All chunks processed successfully.")
    
    # Verify Pinecone index
    try:
        stats = pinecone_index.describe_index_stats()
        log_message(f"\n📊 Pinecone Index Stats:")
        log_message(f"   Total vectors: {stats.get('total_vector_count', 0)}")
        log_message(f"   Dimension: {stats.get('dimension', 0)}")
    except Exception as e:
        log_message(f"   ⚠️  Could not get index stats: {e}")
    
    mongo_client.close()
    log_message(f"\n✅ Processing complete!")
    log_message(f"   Log file: {LOG_FILE}")
    if failed_chunks:
        log_message(f"   Failed chunks file: {FAILED_CHUNKS_FILE}")
    log_message("="*70)


if __name__ == "__main__":
    main()

