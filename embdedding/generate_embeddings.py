#!/usr/bin/env python3

"""
Generate embeddings using Gemini Large 5 text embedding model
- Fetches chunks from MongoDB
- Generates 3072-dimensional embeddings using Gemini API
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
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', 'AIzaSyCcxXRDJhJVmP446PTRsErjZ3NP7Obpy6o')

# Pinecone API
PINECONE_API_KEY = os.getenv('PINECONE_API_KEY', 'pcsk_2N3E6V_QHopkTxvTXj957o8w1eCYPyzm9RH3KgGrsfySya3fqwwmX9sWE2znGijnbt1LeH')
PINECONE_INDEX_NAME = os.getenv('PINECONE_INDEX_NAME', 'domestic-worker-rights')

# Configuration
EMBEDDING_MODEL = "gemini-embedding-001"  # Gemini embedding model
EMBEDDING_DIMENSION = 3072
BATCH_SIZE = 100  # Process chunks in batches
LOG_FILE = Path(__file__).parent / "embedding_log.txt"


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


def generate_embedding(text: str) -> list:
    """
    Generate embedding using Gemini gemini-embedding-001 model.
    Returns 3072-dimensional embedding vector.
    """
    try:
        # Use Gemini embedding API
        result = genai.embed_content(
            model=f"models/{EMBEDDING_MODEL}",
            content=text,
            task_type="RETRIEVAL_DOCUMENT",  # For RAG retrieval
            output_dimensionality=EMBEDDING_DIMENSION
        )
        
        # Extract embedding from result
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
            log_message(f"⚠️  Warning: Embedding dimension is {len(embedding)}, expected {EMBEDDING_DIMENSION}")
        
        return embedding
    except Exception as e:
        log_message(f"⚠️  Error generating embedding: {e}")
        raise


def generate_embeddings_batch(texts: list) -> list:
    """Generate embeddings for a batch of texts."""
    embeddings = []
    for i, text in enumerate(texts):
        try:
            embedding = generate_embedding(text)
            embeddings.append(embedding)
            if (i + 1) % 10 == 0:
                log_message(f"   Generated {i + 1}/{len(texts)} embeddings in batch...")
        except Exception as e:
            log_message(f"   ⚠️  Error generating embedding for text {i}: {e}")
            # Add None as placeholder (will skip later)
            embeddings.append(None)
    return embeddings


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
    """Upload vectors to Pinecone."""
    if not vectors:
        log_message("⚠️  No vectors to upload")
        return 0
    
    log_message(f"📤 Uploading {len(vectors)} vectors to Pinecone...")
    
    try:
        # Pinecone expects format: [(id, vector, metadata), ...]
        # We'll prepare the data
        vectors_to_upsert = []
        for vector_data in vectors:
            if vector_data['embedding'] is None:
                continue  # Skip failed embeddings
            
            vector_entry = (
                vector_data['id'],  # Use same ID as MongoDB
                vector_data['embedding'],
                {
                    'text': vector_data['text'][:1000],  # Truncate for metadata
                    'source_file': vector_data['source_file'],
                    'jurisdiction': vector_data['jurisdiction'],
                    'topic': vector_data['topic'],
                    'chunk_index': vector_data['chunk_index'],
                    'chunk_size': vector_data['chunk_size'],
                }
            )
            vectors_to_upsert.append(vector_entry)
        
        if not vectors_to_upsert:
            log_message("⚠️  No valid vectors to upload")
            return 0
        
        # Upload in batches (Pinecone recommends batches of 100)
        uploaded = 0
        for i in range(0, len(vectors_to_upsert), 100):
            batch = vectors_to_upsert[i:i + 100]
            index.upsert(vectors=batch)
            uploaded += len(batch)
            log_message(f"   ✅ Uploaded batch {i//100 + 1}: {len(batch)} vectors (Total: {uploaded})")
        
        log_message(f"✅ Successfully uploaded {uploaded} vectors to Pinecone!")
        return uploaded
    except Exception as e:
        log_message(f"❌ Error uploading to Pinecone: {e}")
        traceback.print_exc()
        raise


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
    log_message(f"\n🔄 Processing {len(chunks)} chunks in batches of {BATCH_SIZE}...")
    
    total_processed = 0
    total_uploaded = 0
    failed_chunks = []
    
    for batch_start in range(0, len(chunks), BATCH_SIZE):
        batch_end = min(batch_start + BATCH_SIZE, len(chunks))
        batch_chunks = chunks[batch_start:batch_end]
        
        log_message(f"\n📦 Processing batch {batch_start//BATCH_SIZE + 1} (chunks {batch_start+1}-{batch_end})...")
        
        # Prepare texts for embedding
        texts = []
        chunk_metadata = []
        
        for chunk in batch_chunks:
            chunk_id = chunk.get('_id') or chunk.get('id')
            chunk_text = chunk.get('text', '')
            
            if not chunk_id or not chunk_text:
                log_message(f"   ⚠️  Skipping chunk with missing ID or text")
                continue
            
            texts.append(chunk_text)
            chunk_metadata.append({
                'id': chunk_id,
                'text': chunk_text,
                'source_file': chunk.get('source_file', 'unknown'),
                'jurisdiction': chunk.get('jurisdiction', 'unknown'),
                'topic': chunk.get('topic', 'general'),
                'chunk_index': chunk.get('chunk_index', 0),
                'chunk_size': chunk.get('chunk_size', 0),
            })
        
        if not texts:
            log_message(f"   ⚠️  No valid texts in batch")
            continue
        
        # Generate embeddings
        log_message(f"   🔄 Generating embeddings for {len(texts)} chunks...")
        try:
            embeddings = generate_embeddings_batch(texts)
            
            # Prepare vectors for Pinecone
            vectors = []
            for i, (metadata, embedding) in enumerate(zip(chunk_metadata, embeddings)):
                if embedding is None:
                    failed_chunks.append(metadata['id'])
                    continue
                
                # Verify embedding dimension
                if len(embedding) != EMBEDDING_DIMENSION:
                    log_message(f"   ⚠️  Chunk {metadata['id']}: Wrong dimension {len(embedding)}, expected {EMBEDDING_DIMENSION}")
                    failed_chunks.append(metadata['id'])
                    continue
                
                vectors.append({
                    'id': metadata['id'],
                    'embedding': embedding,
                    'text': metadata['text'],
                    'source_file': metadata['source_file'],
                    'jurisdiction': metadata['jurisdiction'],
                    'topic': metadata['topic'],
                    'chunk_index': metadata['chunk_index'],
                    'chunk_size': metadata['chunk_size'],
                })
            
            log_message(f"   ✅ Generated {len(vectors)} valid embeddings")
            
            # Upload to Pinecone
            uploaded = upload_to_pinecone(pinecone_index, vectors)
            total_uploaded += uploaded
            total_processed += len(vectors)
            
        except Exception as e:
            log_message(f"   ❌ Error processing batch: {e}")
            traceback.print_exc()
            failed_chunks.extend([m['id'] for m in chunk_metadata])
            continue
        
        # Rate limiting - small delay between batches
        if batch_end < len(chunks):
            time.sleep(1)
    
    # Final statistics
    log_message("\n" + "="*70)
    log_message("EMBEDDING GENERATION COMPLETE")
    log_message("="*70)
    log_message(f"✅ Total chunks processed: {total_processed}")
    log_message(f"✅ Total vectors uploaded to Pinecone: {total_uploaded}")
    log_message(f"❌ Failed chunks: {len(failed_chunks)}")
    
    if failed_chunks:
        log_message(f"\n⚠️  Failed chunk IDs (first 10):")
        for chunk_id in failed_chunks[:10]:
            log_message(f"   - {chunk_id}")
    
    # Verify Pinecone index
    try:
        stats = pinecone_index.describe_index_stats()
        log_message(f"\n📊 Pinecone Index Stats:")
        log_message(f"   Total vectors: {stats.get('total_vector_count', 0)}")
        log_message(f"   Dimension: {stats.get('dimension', 0)}")
    except Exception as e:
        log_message(f"   ⚠️  Could not get index stats: {e}")
    
    mongo_client.close()
    log_message(f"\n✅ Processing complete! Log saved to: {LOG_FILE}")
    log_message("="*70)


if __name__ == "__main__":
    main()

