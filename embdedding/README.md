# Embedding Generation for RAG Pipeline

## Overview
This script generates embeddings using Gemini Large 5 text embedding model (3072 dimensions) and stores them in Pinecone.

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Environment variables are configured in `.env` file:
- `GEMINI_API_KEY`: Your Gemini API key
- `PINECONE_API_KEY`: Your Pinecone API key
- `PINECONE_INDEX_NAME`: Name of Pinecone index (default: `domestic-worker-rights`)

## Usage

```bash
python generate_embeddings.py
```

## Features

- Fetches chunks from MongoDB
- Generates 3072-dimensional embeddings using Gemini `text-embedding-005` model
- Uses same IDs as MongoDB chunks for correct retrieval
- Uploads embeddings to Pinecone in batches
- Comprehensive logging
- Error handling for failed embeddings

## Output

- Embeddings stored in Pinecone index
- Log file: `embedding_log.txt`
- Each vector uses the same `_id` as MongoDB chunk for retrieval

