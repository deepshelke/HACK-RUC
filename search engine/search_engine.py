#!/usr/bin/env python3

"""
3-Layer Search Engine for Domestic Worker Rights
Architecture:
- Layer 1: Jurisdiction detection, prompt refinement, and vectorization
- Layer 2: Vector similarity search in Pinecone
- Layer 3: Response generation with AI validation gate
"""

import os
import sys
from pathlib import Path
from pymongo import MongoClient
from urllib.parse import quote_plus
from dotenv import load_dotenv
from datetime import datetime
import google.generativeai as genai
from pinecone import Pinecone
import json
import re
from typing import Dict, List, Optional, Tuple

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
EMBEDDING_MODEL = "text-embedding-005"  # Gemini embedding model
EMBEDDING_DIMENSION = 3072
GEMINI_MODEL = "gemini-1.5-pro"  # For text generation
TOP_K_RESULTS = 5  # Number of chunks to retrieve
SIMILARITY_THRESHOLD = 0.7  # Minimum similarity score

# Supported jurisdictions
JURISDICTIONS = {
    "fed": "US_FEDERAL",
    "federal": "US_FEDERAL",
    "us federal": "US_FEDERAL",
    "us fed": "US_FEDERAL",
    "ny": "NY",
    "new york": "NY",
    "new york state": "NY",
    "nyc": "NYC",
    "new york city": "NYC",
    "nj": "NJ",
    "new jersey": "NJ",
    "philly": "PHILADELPHIA",
    "philadelphia": "PHILADELPHIA"
}


# ============================================================================
# LAYER 1: PROMPT PROCESSING AND VECTORIZATION
# ============================================================================

class Layer1_Processor:
    """First layer: Jurisdiction detection, prompt refinement, and vectorization."""
    
    def __init__(self):
        """Initialize Layer 1 processor."""
        genai.configure(api_key=GEMINI_API_KEY)
        self.model = genai.GenerativeModel(GEMINI_MODEL)
        print("✅ Layer 1 initialized")
    
    def detect_jurisdiction_need(self, query: str) -> Tuple[bool, Optional[str]]:
        """
        Detect if query needs jurisdiction clarification.
        Returns: (needs_clarification, detected_jurisdiction)
        """
        query_lower = query.lower()
        
        # Check if query mentions multiple jurisdictions or is ambiguous
        mentioned_jurisdictions = []
        for key, value in JURISDICTIONS.items():
            if key in query_lower:
                mentioned_jurisdictions.append(value)
        
        # If multiple jurisdictions mentioned or none clearly specified
        if len(set(mentioned_jurisdictions)) > 1:
            return True, None  # Needs clarification
        elif len(mentioned_jurisdictions) == 1:
            return False, mentioned_jurisdictions[0]  # Clear jurisdiction
        elif any(word in query_lower for word in ["us", "united states", "federal", "state", "city"]):
            # Query mentions US/state/city but not specific jurisdiction
            return True, None
        else:
            # No jurisdiction mentioned - might need clarification
            return True, None
    
    def ask_jurisdiction(self) -> str:
        """Ask user to specify jurisdiction."""
        return "Which jurisdiction would you like to access information for?\n" \
               "Please specify: US Federal, NY (New York State), NYC (New York City), NJ (New Jersey), or Philadelphia"
    
    def refine_prompt(self, query: str, jurisdiction: Optional[str] = None) -> str:
        """
        Refine user query into a better search prompt using AI.
        """
        system_prompt = """You are a query refinement assistant for a domestic worker rights search system.
Your task is to convert user queries into optimized search prompts that will retrieve relevant information.

Guidelines:
1. Preserve the core intent of the user's question
2. Expand abbreviations and clarify ambiguous terms
3. Add relevant context about domestic worker rights if needed
4. Make the query more specific and searchable
5. Keep it concise (1-2 sentences max)

User Query: {query}
Jurisdiction: {jurisdiction}

Refined Search Prompt:"""

        try:
            prompt = system_prompt.format(
                query=query,
                jurisdiction=jurisdiction or "Any"
            )
            
            response = self.model.generate_content(
                prompt,
                generation_config={
                    "temperature": 0.3,
                    "max_output_tokens": 200,
                }
            )
            
            refined = response.text.strip()
            print(f"   🔍 Refined prompt: {refined}")
            return refined
        except Exception as e:
            print(f"   ⚠️  Error refining prompt: {e}, using original query")
            return query
    
    def generate_embedding(self, text: str) -> List[float]:
        """
        Generate 3072-dimensional embedding using Gemini text-embedding-005.
        """
        try:
            result = genai.embed_content(
                model=f"models/{EMBEDDING_MODEL}",
                content=text,
                task_type="RETRIEVAL_QUERY",  # For query embedding
                output_dimensionality=EMBEDDING_DIMENSION
            )
            
            # Extract embedding
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
                print(f"   ⚠️  Warning: Embedding dimension is {len(embedding)}, expected {EMBEDDING_DIMENSION}")
            
            return embedding
        except Exception as e:
            print(f"   ❌ Error generating embedding: {e}")
            raise
    
    def process(self, query: str, jurisdiction: Optional[str] = None) -> Tuple[List[float], str, Optional[str]]:
        """
        Main Layer 1 processing.
        Returns: (embedding_vector, refined_prompt, jurisdiction)
        """
        print("\n" + "="*70)
        print("LAYER 1: PROMPT PROCESSING & VECTORIZATION")
        print("="*70)
        
        # Step 1: Check if jurisdiction clarification needed
        needs_clarification, detected_jurisdiction = self.detect_jurisdiction_need(query)
        
        if needs_clarification and jurisdiction is None:
            print("   📍 Jurisdiction clarification needed")
            return None, self.ask_jurisdiction(), None
        
        # Use provided jurisdiction or detected one
        final_jurisdiction = jurisdiction or detected_jurisdiction
        
        # Step 2: Refine prompt
        print(f"   🔧 Refining prompt...")
        refined_prompt = self.refine_prompt(query, final_jurisdiction)
        
        # Step 3: Generate embedding
        print(f"   🧮 Generating embedding (3072 dimensions)...")
        embedding = self.generate_embedding(refined_prompt)
        
        print(f"   ✅ Layer 1 complete: Embedding generated, jurisdiction={final_jurisdiction}")
        
        return embedding, refined_prompt, final_jurisdiction


# ============================================================================
# LAYER 2: VECTOR SIMILARITY SEARCH
# ============================================================================

class Layer2_Search:
    """Second layer: Vector similarity search in Pinecone."""
    
    def __init__(self):
        """Initialize Layer 2 search."""
        self.pinecone_index = self._connect_to_pinecone()
        self.mongo_collection = self._connect_to_mongodb()
        print("✅ Layer 2 initialized")
    
    def _connect_to_pinecone(self):
        """Connect to Pinecone."""
        try:
            pc = Pinecone(api_key=PINECONE_API_KEY)
            existing_indexes = [idx.name for idx in pc.list_indexes()]
            
            if PINECONE_INDEX_NAME in existing_indexes:
                index = pc.Index(PINECONE_INDEX_NAME)
                print(f"   ✅ Connected to Pinecone index: {PINECONE_INDEX_NAME}")
                return index
            else:
                raise Exception(f"Index '{PINECONE_INDEX_NAME}' not found")
        except Exception as e:
            print(f"   ❌ Failed to connect to Pinecone: {e}")
            raise
    
    def _connect_to_mongodb(self):
        """Connect to MongoDB."""
        try:
            password_encoded = quote_plus(MONGODB_PASSWORD)
            connection_string = f"mongodb+srv://{MONGODB_USERNAME}:{password_encoded}@{MONGODB_CLUSTER}/?appName={MONGODB_APP_NAME}"
            
            client = MongoClient(
                connection_string,
                serverSelectionTimeoutMS=10000,
                connectTimeoutMS=10000,
                socketTimeoutMS=10000,
                retryWrites=True
            )
            client.admin.command('ping')
            
            db = client[DATABASE_NAME]
            collection = db[COLLECTION_NAME]
            print(f"   ✅ Connected to MongoDB: {DATABASE_NAME}.{COLLECTION_NAME}")
            return collection
        except Exception as e:
            print(f"   ❌ Failed to connect to MongoDB: {e}")
            raise
    
    def search(self, embedding: List[float], jurisdiction: Optional[str] = None, top_k: int = TOP_K_RESULTS) -> List[Dict]:
        """
        Perform cosine similarity search in Pinecone.
        Returns list of relevant chunks with metadata.
        """
        print("\n" + "="*70)
        print("LAYER 2: VECTOR SIMILARITY SEARCH")
        print("="*70)
        
        try:
            # Build filter if jurisdiction specified
            filter_dict = {}
            if jurisdiction:
                filter_dict = {"jurisdiction": jurisdiction.lower()}
                print(f"   🔍 Searching with jurisdiction filter: {jurisdiction}")
            
            # Query Pinecone
            print(f"   🔎 Querying Pinecone (top_k={top_k})...")
            query_results = self.pinecone_index.query(
                vector=embedding,
                top_k=top_k,
                include_metadata=True,
                filter=filter_dict if filter_dict else None
            )
            
            # Process results
            results = []
            for match in query_results.matches:
                if match.score < SIMILARITY_THRESHOLD:
                    continue  # Skip low similarity results
                
                chunk_id = match.id
                similarity_score = match.score
                metadata = match.metadata
                
                # Fetch full text from MongoDB
                chunk_doc = self.mongo_collection.find_one({"_id": chunk_id})
                
                if chunk_doc:
                    result = {
                        "id": chunk_id,
                        "text": chunk_doc.get("text", ""),
                        "source_file": chunk_doc.get("source_file", ""),
                        "jurisdiction": chunk_doc.get("jurisdiction", ""),
                        "topic": chunk_doc.get("topic", ""),
                        "similarity_score": similarity_score,
                        "metadata": metadata
                    }
                    results.append(result)
                    print(f"   ✅ Found: {chunk_id[:50]}... (score: {similarity_score:.3f})")
            
            print(f"   ✅ Layer 2 complete: Found {len(results)} relevant chunks")
            return results
            
        except Exception as e:
            print(f"   ❌ Error in vector search: {e}")
            import traceback
            traceback.print_exc()
            return []


# ============================================================================
# LAYER 3: RESPONSE GENERATION WITH AI VALIDATION GATE
# ============================================================================

class Layer3_Response:
    """Third layer: Response generation with AI validation gate."""
    
    def __init__(self):
        """Initialize Layer 3 response generator."""
        genai.configure(api_key=GEMINI_API_KEY)
        self.model = genai.GenerativeModel(GEMINI_MODEL)
        print("✅ Layer 3 initialized")
    
    def validate_query_match(self, original_query: str, retrieved_chunks: List[Dict]) -> Tuple[bool, str]:
        """
        AI Gate: Validate if retrieved chunks match the original query.
        Returns: (is_valid, validation_reason)
        """
        print("\n" + "="*70)
        print("LAYER 3: RESPONSE GENERATION & VALIDATION")
        print("="*70)
        
        # Prepare context from retrieved chunks
        context_text = "\n\n".join([
            f"[Chunk {i+1} from {chunk['source_file']}]:\n{chunk['text'][:500]}..."
            for i, chunk in enumerate(retrieved_chunks[:3])  # Use top 3 for validation
        ])
        
        validation_prompt = f"""You are an AI validation gate for a search system.
Your task is to determine if the retrieved information is relevant to the user's query.

User Query: "{original_query}"

Retrieved Information:
{context_text}

Analyze if the retrieved information is relevant and can answer the user's query.

Respond in JSON format:
{{
    "is_relevant": true/false,
    "confidence": 0.0-1.0,
    "reason": "brief explanation"
}}

Only respond with the JSON, no additional text."""

        try:
            response = self.model.generate_content(
                validation_prompt,
                generation_config={
                    "temperature": 0.1,
                    "max_output_tokens": 200,
                }
            )
            
            # Parse JSON response
            response_text = response.text.strip()
            # Extract JSON if wrapped in markdown
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()
            
            validation_result = json.loads(response_text)
            
            is_valid = validation_result.get("is_relevant", False)
            confidence = validation_result.get("confidence", 0.0)
            reason = validation_result.get("reason", "No reason provided")
            
            print(f"   🔍 Validation: is_relevant={is_valid}, confidence={confidence:.2f}")
            print(f"   📝 Reason: {reason}")
            
            # Consider valid if confidence > 0.5
            final_valid = is_valid and confidence > 0.5
            
            return final_valid, reason
            
        except Exception as e:
            print(f"   ⚠️  Validation error: {e}, proceeding with response")
            # If validation fails, still proceed but warn
            return True, "Validation check failed, proceeding anyway"
    
    def generate_response(self, query: str, chunks: List[Dict], jurisdiction: Optional[str] = None) -> str:
        """
        Generate response using Gemini with retrieved context.
        """
        print(f"   🤖 Generating response...")
        
        # Prepare context
        context_parts = []
        for i, chunk in enumerate(chunks, 1):
            context_parts.append(
                f"[Source {i}: {chunk.get('source_file', 'Unknown')} - {chunk.get('jurisdiction', 'Unknown')} jurisdiction]\n"
                f"{chunk.get('text', '')}\n"
            )
        
        context = "\n---\n".join(context_parts)
        
        # Build prompt
        system_prompt = f"""You are a helpful assistant providing information about domestic worker rights and labor laws.
Answer the user's question based ONLY on the provided context from official documents.
If the information is not in the context, say so clearly.

Jurisdiction: {jurisdiction or "Multiple/Not specified"}

Context from documents:
{context}

User Question: {query}

Instructions:
1. Answer based ONLY on the provided context
2. Cite the source document when possible
3. Be accurate and specific
4. If information is not available, clearly state that
5. Use clear, professional language

Answer:"""

        try:
            response = self.model.generate_content(
                system_prompt,
                generation_config={
                    "temperature": 0.3,
                    "max_output_tokens": 1000,
                }
            )
            
            answer = response.text.strip()
            print(f"   ✅ Response generated ({len(answer)} characters)")
            return answer
            
        except Exception as e:
            print(f"   ❌ Error generating response: {e}")
            return f"I apologize, but I encountered an error while generating a response. Please try again."
    
    def process(self, original_query: str, refined_query: str, chunks: List[Dict], jurisdiction: Optional[str] = None) -> Optional[str]:
        """
        Main Layer 3 processing with validation gate.
        """
        if not chunks:
            return "I couldn't find any relevant information to answer your question. Please try rephrasing your query."
        
        # Step 1: Validate query match
        is_valid, validation_reason = self.validate_query_match(original_query, chunks)
        
        if not is_valid:
            return f"I found some information, but it doesn't seem directly relevant to your question: '{original_query}'. " \
                   f"Validation reason: {validation_reason}. Please try rephrasing your question or being more specific."
        
        # Step 2: Generate response
        response = self.generate_response(refined_query, chunks, jurisdiction)
        
        print(f"   ✅ Layer 3 complete: Response generated and validated")
        return response


# ============================================================================
# MAIN SEARCH ENGINE
# ============================================================================

class SearchEngine:
    """Main 3-layer search engine."""
    
    def __init__(self):
        """Initialize the search engine."""
        print("="*70)
        print("INITIALIZING 3-LAYER SEARCH ENGINE")
        print("="*70)
        self.layer1 = Layer1_Processor()
        self.layer2 = Layer2_Search()
        self.layer3 = Layer3_Response()
        print("\n✅ Search Engine initialized and ready!")
    
    def search(self, query: str, jurisdiction: Optional[str] = None) -> Dict:
        """
        Main search function.
        
        Args:
            query: User's search query
            jurisdiction: Optional jurisdiction (fed, ny, nj, nyc, philly)
        
        Returns:
            Dictionary with search results
        """
        print("\n" + "="*70)
        print("SEARCH REQUEST")
        print("="*70)
        print(f"Query: {query}")
        if jurisdiction:
            print(f"Jurisdiction: {jurisdiction}")
        
        try:
            # Normalize jurisdiction if provided
            normalized_jurisdiction = None
            if jurisdiction:
                jurisdiction_lower = jurisdiction.lower()
                normalized_jurisdiction = JURISDICTIONS.get(jurisdiction_lower)
            
            # LAYER 1: Process query and generate embedding
            embedding, refined_prompt, detected_jurisdiction = self.layer1.process(
                query, 
                normalized_jurisdiction
            )
            
            # If jurisdiction clarification needed
            if embedding is None:
                return {
                    "success": False,
                    "needs_clarification": True,
                    "message": refined_prompt,
                    "response": None
                }
            
            # Use detected or provided jurisdiction
            final_jurisdiction = normalized_jurisdiction or detected_jurisdiction
            
            # LAYER 2: Vector similarity search
            chunks = self.layer2.search(embedding, final_jurisdiction)
            
            if not chunks:
                return {
                    "success": False,
                    "needs_clarification": False,
                    "message": "No relevant information found. Please try rephrasing your query.",
                    "response": None,
                    "chunks_found": 0
                }
            
            # LAYER 3: Generate response with validation
            response = self.layer3.process(
                query,
                refined_prompt,
                chunks,
                final_jurisdiction
            )
            
            return {
                "success": True,
                "needs_clarification": False,
                "query": query,
                "refined_query": refined_prompt,
                "jurisdiction": final_jurisdiction,
                "response": response,
                "chunks_found": len(chunks),
                "chunks": chunks[:3]  # Include top 3 chunks for reference
            }
            
        except Exception as e:
            print(f"\n❌ Error in search: {e}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "needs_clarification": False,
                "message": f"An error occurred: {str(e)}",
                "response": None
            }


# ============================================================================
# INTERACTIVE CLI
# ============================================================================

def main():
    """Interactive CLI for testing the search engine."""
    print("\n" + "="*70)
    print("DOMESTIC WORKER RIGHTS SEARCH ENGINE")
    print("="*70)
    print("\nType your questions about domestic worker rights.")
    print("Type 'quit' or 'exit' to stop.\n")
    
    # Initialize search engine
    engine = SearchEngine()
    
    # Track conversation state
    pending_jurisdiction = None
    
    while True:
        try:
            # Get user input
            user_input = input("\n🔍 Your question: ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("\n👋 Goodbye!")
                break
            
            if not user_input:
                continue
            
            # Check if this is a jurisdiction response
            if pending_jurisdiction:
                # User is responding to jurisdiction question
                jurisdiction_input = user_input.lower()
                normalized = JURISDICTIONS.get(jurisdiction_input)
                
                if normalized:
                    # Process original query with jurisdiction
                    result = engine.search(pending_jurisdiction, normalized)
                    pending_jurisdiction = None
                else:
                    print("⚠️  Please specify a valid jurisdiction: US Federal, NY, NYC, NJ, or Philadelphia")
                    continue
            else:
                # Normal query
                result = engine.search(user_input)
            
            # Handle result
            if result.get("needs_clarification"):
                print(f"\n📋 {result['message']}")
                pending_jurisdiction = user_input  # Store original query
            elif result.get("success"):
                print(f"\n✅ Answer ({result['chunks_found']} sources found):")
                print(f"\n{result['response']}")
                if result.get('jurisdiction'):
                    print(f"\n📍 Jurisdiction: {result['jurisdiction']}")
            else:
                print(f"\n❌ {result.get('message', 'No results found')}")
        
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    main()

