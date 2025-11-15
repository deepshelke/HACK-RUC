#!/usr/bin/env python3

"""
Test script: Fetch one chunk from MongoDB, generate embedding, and upload to Pinecone
"""

import os
import sys
from pathlib import Path
from pymongo import MongoClient
from urllib.parse import quote_plus
from dotenv import load_dotenv
import google.generativeai as genai
from pinecone import Pinecone
import time

# Load environment variables
load_dotenv(Path(__file__).parent.parent / ".env")

# MongoDB connection
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

EMBEDDING_MODEL = "text-embedding-005"
EMBEDDING_DIMENSION = 3072

print("="*70)
print("TEST: SINGLE CHUNK EMBEDDING AND PINECONE UPLOAD")
print("="*70)

# 1. Connect to MongoDB
print("\n1. Connecting to MongoDB...")
password_encoded = quote_plus(MONGODB_PASSWORD)
connection_string = f"mongodb+srv://{MONGODB_USERNAME}:{password_encoded}@{MONGODB_CLUSTER}/?appName={MONGODB_APP_NAME}"

try:
    mongo_client = MongoClient(connection_string, serverSelectionTimeoutMS=10000)
    mongo_client.admin.command('ping')
    print("✅ Connected to MongoDB!")
    
    db = mongo_client[DATABASE_NAME]
    collection = db[COLLECTION_NAME]
    
    # Fetch one chunk
    chunk = collection.find_one({})
    if not chunk:
        print("❌ No chunks found in MongoDB")
        exit(1)
    
    chunk_id = chunk.get('_id') or chunk.get('id')
    chunk_text = chunk.get('text', '')
    
    print(f"\n✅ Fetched chunk:")
    print(f"   ID: {chunk_id}")
    print(f"   Source: {chunk.get('source_file', 'unknown')}")
    print(f"   Text length: {len(chunk_text)} chars")
    print(f"   Text preview: {chunk_text[:150]}...")
    
except Exception as e:
    print(f"❌ MongoDB error: {e}")
    exit(1)

# 2. Initialize Gemini
print("\n2. Initializing Gemini API...")
try:
    genai.configure(api_key=GEMINI_API_KEY)
    print("✅ Gemini API initialized!")
except Exception as e:
    print(f"❌ Gemini error: {e}")
    exit(1)

# 3. Generate embedding
print("\n3. Generating embedding...")
try:
    # Use the correct API format for google-generativeai package
    result = genai.embed_content(
        model="models/gemini-embedding-001",
        content=chunk_text,
        task_type="RETRIEVAL_DOCUMENT",
        output_dimensionality=EMBEDDING_DIMENSION
    )
    
    # Extract embedding from result
    # The result structure may vary, try different access patterns
    if hasattr(result, 'embedding'):
        embedding = result.embedding
    elif isinstance(result, dict):
        embedding = result.get('embedding', result.get('values', []))
    elif isinstance(result, list):
        embedding = result
    else:
        # Try accessing as attribute
        embedding = getattr(result, 'values', list(result) if hasattr(result, '__iter__') else [])
    
    # Convert to list if needed
    if not isinstance(embedding, list):
        embedding = list(embedding)
    
    print(f"✅ Embedding generated!")
    print(f"   Dimension: {len(embedding)}")
    print(f"   Expected: {EMBEDDING_DIMENSION}")
    
    if len(embedding) != EMBEDDING_DIMENSION:
        print(f"⚠️  Warning: Dimension mismatch! Got {len(embedding)}, expected {EMBEDDING_DIMENSION}")
        # If dimension is wrong, try without output_dimensionality parameter
        print("   Trying without output_dimensionality parameter...")
        result2 = genai.embed_content(
            model="models/gemini-embedding-001",
            content=chunk_text,
            task_type="RETRIEVAL_DOCUMENT"
        )
        if hasattr(result2, 'embedding'):
            embedding = result2.embedding
        elif isinstance(result2, dict):
            embedding = result2.get('embedding', result2.get('values', []))
        embedding = list(embedding) if not isinstance(embedding, list) else embedding
        print(f"   New dimension: {len(embedding)}")
    else:
        print(f"   ✅ Dimension matches!")
    
except Exception as e:
    print(f"❌ Embedding error: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

# 4. Connect to Pinecone
print("\n4. Connecting to Pinecone...")
try:
    pc = Pinecone(api_key=PINECONE_API_KEY)
    print("✅ Connected to Pinecone!")
    
    # Check if index exists
    existing_indexes = [idx.name for idx in pc.list_indexes()]
    
    if PINECONE_INDEX_NAME in existing_indexes:
        print(f"✅ Index '{PINECONE_INDEX_NAME}' exists")
        index = pc.Index(PINECONE_INDEX_NAME)
    else:
        print(f"📇 Creating index '{PINECONE_INDEX_NAME}'...")
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
        print(f"✅ Index created! Waiting for it to be ready...")
        time.sleep(10)  # Wait for index to be ready
        index = pc.Index(PINECONE_INDEX_NAME)
    
except Exception as e:
    print(f"❌ Pinecone error: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

# 5. Upload to Pinecone
print("\n5. Uploading to Pinecone...")
try:
    # Prepare vector
    vector_entry = (
        chunk_id,  # Use same ID as MongoDB
        embedding,
        {
            'text': chunk_text[:1000],  # Truncate for metadata
            'source_file': chunk.get('source_file', 'unknown'),
            'jurisdiction': chunk.get('jurisdiction', 'unknown'),
            'topic': chunk.get('topic', 'general'),
            'chunk_index': chunk.get('chunk_index', 0),
            'chunk_size': chunk.get('chunk_size', 0),
        }
    )
    
    # Upload
    index.upsert(vectors=[vector_entry])
    print(f"✅ Successfully uploaded to Pinecone!")
    print(f"   Vector ID: {chunk_id}")
    
    # Verify upload
    stats = index.describe_index_stats()
    print(f"\n📊 Pinecone Index Stats:")
    print(f"   Total vectors: {stats.get('total_vector_count', 0)}")
    print(f"   Dimension: {stats.get('dimension', 0)}")
    
    # Try to fetch it back
    fetched = index.fetch(ids=[chunk_id])
    if chunk_id in fetched['vectors']:
        print(f"\n✅ Verified: Vector retrieved from Pinecone!")
        print(f"   Retrieved ID: {chunk_id}")
        print(f"   Metadata: {fetched['vectors'][chunk_id].get('metadata', {})}")
    else:
        print(f"\n⚠️  Warning: Could not retrieve vector after upload")
    
except Exception as e:
    print(f"❌ Upload error: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

print("\n" + "="*70)
print("✅ TEST COMPLETE - Single chunk successfully processed!")
print("="*70)

mongo_client.close()

