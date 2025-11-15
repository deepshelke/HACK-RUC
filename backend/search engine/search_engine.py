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
import requests
from bs4 import BeautifulSoup

# Load environment variables
load_dotenv(Path(__file__).parent.parent / ".env")

# MongoDB connection details
MONGODB_USERNAME = os.getenv('MONGODB_USERNAME')
MONGODB_PASSWORD = os.getenv('MONGODB_PASSWORD')
MONGODB_CLUSTER = os.getenv('MONGODB_CLUSTER')
MONGODB_APP_NAME = os.getenv('MONGODB_APP_NAME')
DATABASE_NAME = os.getenv('MONGODB_DATABASE')  # Uses MONGODB_DATABASE from .env
COLLECTION_NAME = os.getenv('MONGODB_COLLECTION')  # Uses MONGODB_COLLECTION from .env

# Gemini API
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

# Pinecone API
PINECONE_API_KEY = os.getenv('PINECONE_API_KEY')
PINECONE_INDEX_NAME = os.getenv('PINECONE_INDEX_NAME')

# Configuration - all from environment variables
EMBEDDING_MODEL = os.getenv('EMBEDDING_MODEL', 'gemini-embedding-exp-03-07')  # Gemini embedding model
EMBEDDING_DIMENSION = int(os.getenv('EMBEDDING_DIMENSION', '3072'))  # Embedding dimension
GEMINI_MODEL = os.getenv('GEMINI_MODEL', 'gemini-2.0-flash-exp')  # For text generation (Flash model for faster responses)
TOP_K_RESULTS = int(os.getenv('TOP_K_RESULTS', '8'))  # Number of chunks to retrieve
SIMILARITY_THRESHOLD = float(os.getenv('SIMILARITY_THRESHOLD', '0.65'))  # Minimum similarity score (reduced for better recall)

# Validate required environment variables
required_vars = [
    'MONGODB_USERNAME', 'MONGODB_PASSWORD', 'MONGODB_CLUSTER', 'MONGODB_APP_NAME',
    'MONGODB_DATABASE', 'MONGODB_COLLECTION', 'GEMINI_API_KEY', 'PINECONE_API_KEY', 'PINECONE_INDEX_NAME'
]
missing_vars = [var for var in required_vars if not os.getenv(var)]
if missing_vars:
    raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")

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

# Supported jurisdictions for our dataset
SUPPORTED_JURISDICTIONS = {"US_FEDERAL", "NY", "NYC", "NJ", "PHILADELPHIA"}

# State name mappings for DOL website
STATE_MAPPINGS = {
    "new york": "New York",
    "new jersey": "New Jersey",
    "pennsylvania": "Pennsylvania",
    "philadelphia": "Pennsylvania",  # Philadelphia is in PA
    "philly": "Pennsylvania",
    "ny": "New York",
    "nj": "New Jersey",
    "pa": "Pennsylvania",
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
        query_lower = query.lower().strip()
        
        # First, check if the query is ONLY a jurisdiction specification
        # (e.g., "US federal", "NY", "New York", etc.)
        # This handles cases where user responds to jurisdiction prompt
        for key, value in JURISDICTIONS.items():
            # Check for exact match or if query is just the jurisdiction
            if query_lower == key or query_lower == value.lower():
                return False, value  # Clear jurisdiction detected
        
        # Check for "US federal" variations (common user input)
        if query_lower in ["us federal", "us fed", "federal", "fed"]:
            return False, "US_FEDERAL"
        
        # Check if query mentions multiple jurisdictions or is ambiguous
        mentioned_jurisdictions = []
        for key, value in JURISDICTIONS.items():
            if key in query_lower:
                mentioned_jurisdictions.append(value)
        
        # If multiple jurisdictions mentioned
        if len(set(mentioned_jurisdictions)) > 1:
            return True, None  # Needs clarification
        elif len(mentioned_jurisdictions) == 1:
            return False, mentioned_jurisdictions[0]  # Clear jurisdiction
        
        # Check for partial matches (e.g., "federal" alone, "new york" without "state")
        if "federal" in query_lower and "us" in query_lower:
            return False, "US_FEDERAL"
        elif "federal" in query_lower and len(query_lower.split()) <= 3:
            # Short query with just "federal" or "us federal" -> likely jurisdiction
            return False, "US_FEDERAL"
        elif "new york" in query_lower:
            if "city" in query_lower or "nyc" in query_lower:
                return False, "NYC"
            else:
                return False, "NY"
        elif "new jersey" in query_lower or query_lower == "nj":
            return False, "NJ"
        elif "philadelphia" in query_lower or "philly" in query_lower:
            return False, "PHILADELPHIA"
        elif any(word in query_lower for word in ["us", "united states", "state", "city"]):
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
Your task is to convert user queries into optimized search prompts.

Domain Context: This system contains legal documents about:
- Fair Labor Standards Act (FLSA)
- Minimum wage laws
- Overtime regulations
- Worker protections
- State and federal labor laws
- Domestic worker rights and protections
- Retaliation protections
- Wage and hour regulations

Guidelines:
1. Expand legal abbreviations (FLSA → Fair Labor Standards Act)
2. Add jurisdiction context if missing
3. Convert questions to searchable statements
4. Include relevant legal terminology
5. Preserve the core intent of the user's question
6. Make the query more specific and searchable
7. Keep it concise (1-2 sentences max)

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
        Generate 3072-dimensional embedding using Gemini gemini-embedding-exp-03-07.
        Must match the model used for generating document embeddings.
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
        
        # Step 1: Normalize jurisdiction if provided (robust handling)
        final_jurisdiction = None
        if jurisdiction:
            # Use inline normalization (same logic as normalize_jurisdiction_input)
            jurisdiction_lower = jurisdiction.lower().strip()
            normalized = JURISDICTIONS.get(jurisdiction_lower)
            
            # If not found, try common variations
            if not normalized:
                if 'federal' in jurisdiction_lower or 'fed' in jurisdiction_lower or ('us' in jurisdiction_lower and 'federal' in jurisdiction_lower):
                    normalized = 'US_FEDERAL'
                elif 'new york' in jurisdiction_lower:
                    if 'city' in jurisdiction_lower or jurisdiction_lower == 'nyc':
                        normalized = 'NYC'
                    else:
                        normalized = 'NY'
                elif jurisdiction_lower in ['ny', 'nyc']:
                    normalized = 'NYC' if jurisdiction_lower == 'nyc' else 'NY'
                elif 'new jersey' in jurisdiction_lower or jurisdiction_lower == 'nj':
                    normalized = 'NJ'
                elif 'philadelphia' in jurisdiction_lower or 'philly' in jurisdiction_lower:
                    normalized = 'PHILADELPHIA'
            
            # Also check if it's already in normalized format
            if not normalized:
                jurisdiction_upper = jurisdiction.upper().strip()
                if jurisdiction_upper in ['US_FEDERAL', 'NY', 'NYC', 'NJ', 'PHILADELPHIA']:
                    normalized = jurisdiction_upper
            
            final_jurisdiction = normalized
            if not final_jurisdiction:
                print(f"   ⚠️  Could not normalize jurisdiction '{jurisdiction}', treating as None")
        
        # Step 2: Check if jurisdiction clarification needed
        # Only check query if jurisdiction is NOT already provided
        if final_jurisdiction is None:
            needs_clarification, detected_jurisdiction = self.detect_jurisdiction_need(query)
            if needs_clarification:
                print("   📍 Jurisdiction clarification needed")
                return None, self.ask_jurisdiction(), None
            final_jurisdiction = detected_jurisdiction
        
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
                # Normalize jurisdiction to lowercase to match MongoDB storage format
                # MongoDB stores jurisdiction as lowercase (e.g., "us_federal", "ny", "nj")
                normalized_jurisdiction = jurisdiction.lower()
                # Map jurisdiction values to match what's stored in MongoDB
                jurisdiction_map = {
                    "us_federal": "us_federal",
                    "ny": "ny",
                    "nyc": "nyc", 
                    "nj": "nj",
                    "philadelphia": "philadelphia"
                }
                # Use mapped value or original lowercase
                filter_value = jurisdiction_map.get(normalized_jurisdiction, normalized_jurisdiction)
                filter_dict = {"jurisdiction": filter_value}
                print(f"   🔍 Searching with jurisdiction filter: {filter_value}")
            
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
    
    def generate_response_with_dol(self, query: str, chunks: List[Dict], jurisdiction: Optional[str], dol_data: Dict, dol_url: str) -> str:
        """
        Generate response with DOL website data for minimum wage queries.
        """
        print(f"   🤖 Generating response with DOL data...")
        
        # Prepare context from chunks (without source numbers)
        context_parts = []
        for chunk in chunks:
            context_parts.append(chunk.get('text', ''))
        
        context = "\n\n".join(context_parts)
        
        # Prepare DOL data
        dol_text = ""
        if dol_data:
            for state, info in dol_data.items():
                dol_text += f"{state}: {info}\n\n"
        
        # Build prompt
        system_prompt = f"""You are a helpful assistant providing information about minimum wage from official sources.

You have access to:
1. Official U.S. Department of Labor (DOL) website data (most current and authoritative)
2. Local documents from our database

Jurisdiction: {jurisdiction or "Multiple/Not specified"}

OFFICIAL DOL WEBSITE DATA (Most Current):
{dol_text}

LOCAL DATABASE CONTEXT:
{context}

User Question: {query}

Instructions:
1. PRIORITIZE the DOL website data as it is the most current and official source
2. Use local database context to supplement or provide additional details
3. Write in a clear, conversational, and easy-to-understand way
4. Do NOT use markdown formatting like **bold** or ***
5. Do NOT use source citations like "Source 1" or "Source 2"
6. Just provide the information naturally in plain text
7. Include specific dollar amounts from DOL data
8. Be accurate and specific
9. If there are discrepancies, prefer DOL data
10. Mention the DOL website naturally in your response, not as a citation

Answer:"""

        try:
            response = self.model.generate_content(
                system_prompt,
                generation_config={
                    "temperature": 0.3,
                    "max_output_tokens": 1500,
                }
            )
            
            answer = response.text.strip()
            print(f"   ✅ Response generated with DOL data ({len(answer)} characters)")
            return answer
            
        except Exception as e:
            print(f"   ❌ Error generating response: {e}")
            # Fallback to regular response
            return self.generate_response(query, chunks, jurisdiction)
    
    def generate_response(self, query: str, chunks: List[Dict], jurisdiction: Optional[str] = None) -> str:
        """
        Generate response using Gemini with retrieved context.
        """
        print(f"   🤖 Generating response...")
        
        # Prepare context (without source numbers)
        context_parts = []
        for chunk in chunks:
            context_parts.append(chunk.get('text', ''))
        
        context = "\n\n".join(context_parts)
        
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
2. Write in a clear, conversational, and easy-to-understand way
3. Do NOT use markdown formatting like **bold** or *** or bullet points with *
4. Do NOT use source citations like "Source 1" or "Source 2"
5. Just provide the information naturally in plain text
6. Be accurate and specific - include exact dollar amounts, percentages, numbers, and dates when mentioned in the context
7. If asking about wages, salaries, or monetary amounts:
   - Include the specific USD dollar amounts if available in the context
   - If specific amounts are not in the context, clearly state: "The specific dollar amount is not provided in the available documents"
   - Provide any related information that IS available (e.g., "must be paid at least minimum wage", "overtime rates", etc.)
   - Suggest contacting the relevant labor department or official source for current specific amounts
8. If information is not available, clearly state that and provide helpful next steps
9. Use clear, simple language that anyone can understand

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
# DOL WEBSITE FETCHER AND HELPER FUNCTIONS
# ============================================================================

def fetch_dol_minimum_wage(state_name: str = None) -> Dict:
    """
    Fetch minimum wage information from DOL official website.
    Returns a dictionary with state minimum wage data.
    """
    try:
        url = "https://www.dol.gov/agencies/whd/minimum-wage/state"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Find the main content area
        main_content = soup.find('main') or soup.find('div', class_='main-content') or soup
        
        # Extract state information
        state_data = {}
        
        if state_name:
            # Look for specific state
            state_heading = None
            for heading in main_content.find_all(['h2', 'h3', 'h4']):
                if heading.get_text().strip().lower() == state_name.lower():
                    state_heading = heading
                    break
            
            if state_heading:
                # Extract information for this state
                current = state_heading.find_next_sibling()
                state_text = []
                while current and current.name not in ['h2', 'h3', 'h4']:
                    if current.name == 'p':
                        state_text.append(current.get_text().strip())
                    current = current.find_next_sibling()
                
                state_data[state_name] = ' '.join(state_text)
        else:
            # Extract all states (for general minimum wage query)
            # Look for state headings and their content
            for heading in main_content.find_all(['h2', 'h3']):
                heading_text = heading.get_text().strip()
                if heading_text and len(heading_text) < 50:  # Likely a state name
                    current = heading.find_next_sibling()
                    state_text = []
                    while current and current.name not in ['h2', 'h3', 'h4']:
                        if current.name == 'p':
                            state_text.append(current.get_text().strip())
                        current = current.find_next_sibling()
                    
                    if state_text:
                        state_data[heading_text] = ' '.join(state_text)
        
        return {
            'success': True,
            'data': state_data,
            'source': 'U.S. Department of Labor - Official Website',
            'url': url
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'source': 'U.S. Department of Labor - Official Website'
        }


def is_minimum_wage_query(query: str) -> bool:
    """Check if query is about minimum wage."""
    query_lower = query.lower()
    wage_keywords = ['minimum wage', 'min wage', 'wage', 'hourly rate', 'pay rate']
    return any(keyword in query_lower for keyword in wage_keywords)


def is_unsupported_state(jurisdiction: str, query: str) -> bool:
    """Check if query is about an unsupported state - for ANY query, not just minimum wage."""
    if not jurisdiction:
        # Check if query mentions unsupported states even without jurisdiction
        query_lower = query.lower()
        unsupported_states = [
            'california', 'texas', 'florida', 'illinois', 'ohio', 'georgia',
            'north carolina', 'michigan', 'virginia', 'washington', 'arizona',
            'massachusetts', 'tennessee', 'indiana', 'missouri', 'maryland',
            'wisconsin', 'colorado', 'minnesota', 'south carolina', 'alabama',
            'louisiana', 'kentucky', 'oregon', 'oklahoma', 'connecticut',
            'utah', 'iowa', 'nevada', 'arkansas', 'mississippi', 'kansas',
            'new mexico', 'nebraska', 'west virginia', 'idaho', 'hawaii',
            'new hampshire', 'maine', 'montana', 'rhode island', 'delaware',
            'south dakota', 'north dakota', 'alaska', 'vermont', 'wyoming'
        ]
        for state in unsupported_states:
            if state in query_lower:
                return True
        return False
    
    jurisdiction_upper = jurisdiction.upper()
    
    # If it's a supported jurisdiction, return False
    if jurisdiction_upper in SUPPORTED_JURISDICTIONS:
        return False
    
    # Check if query mentions other states
    query_lower = query.lower()
    unsupported_states = [
        'california', 'texas', 'florida', 'illinois', 'ohio', 'georgia',
        'north carolina', 'michigan', 'virginia', 'washington', 'arizona',
        'massachusetts', 'tennessee', 'indiana', 'missouri', 'maryland',
        'wisconsin', 'colorado', 'minnesota', 'south carolina', 'alabama',
        'louisiana', 'kentucky', 'oregon', 'oklahoma', 'connecticut',
        'utah', 'iowa', 'nevada', 'arkansas', 'mississippi', 'kansas',
        'new mexico', 'nebraska', 'west virginia', 'idaho', 'hawaii',
        'new hampshire', 'maine', 'montana', 'rhode island', 'delaware',
        'south dakota', 'north dakota', 'alaska', 'vermont', 'wyoming'
    ]
    
    for state in unsupported_states:
        if state in query_lower and jurisdiction_upper not in SUPPORTED_JURISDICTIONS:
            return True
    
    return False


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
        # Check for unsupported states FIRST (for ANY query, not just minimum wage)
        # This must happen before any processing
        if is_unsupported_state(jurisdiction, query):
            return {
                "success": False,
                "needs_clarification": False,
                "message": "I can only provide information for US Federal, New York (NY), New Jersey (NJ), and Philadelphia jurisdictions. For other states, please visit the official U.S. Department of Labor website: https://www.dol.gov/agencies/whd/minimum-wage/state",
                "response": None,
                "chunks_found": 0
            }
        
        # Check if query is about minimum wage
        dol_context = None
        dol_data = None
        if is_minimum_wage_query(query):
            # Fetch from DOL website
            print("   🌐 Fetching minimum wage data from DOL official website...")
            state_name = None
            if jurisdiction:
                state_name = STATE_MAPPINGS.get(jurisdiction.lower())
            
            dol_data = fetch_dol_minimum_wage(state_name)
            
            if dol_data.get('success'):
                print("   ✅ Successfully fetched DOL data")
                # Continue with normal search but include DOL data in response
                dol_context = dol_data.get('data', {})
            else:
                print(f"   ⚠️  Could not fetch DOL data: {dol_data.get('error')}")
                dol_context = None
        print("\n" + "="*70)
        print("SEARCH REQUEST")
        print("="*70)
        print(f"Query: {query}")
        if jurisdiction:
            print(f"Jurisdiction: {jurisdiction}")
        
        try:
            # Check if query is ONLY a jurisdiction specification (no actual question)
            query_lower = query.lower().strip()
            is_only_jurisdiction = False
            detected_jurisdiction_from_query = None
            
            # Check if query matches jurisdiction patterns exactly
            for key, value in JURISDICTIONS.items():
                if query_lower == key or query_lower == value.lower():
                    is_only_jurisdiction = True
                    detected_jurisdiction_from_query = value
                    break
            
            # Check for common jurisdiction-only inputs
            if not is_only_jurisdiction:
                if query_lower in ["us federal", "us fed", "federal", "fed"]:
                    is_only_jurisdiction = True
                    detected_jurisdiction_from_query = "US_FEDERAL"
                elif query_lower in ["ny", "nyc", "nj"]:
                    is_only_jurisdiction = True
                    detected_jurisdiction_from_query = query_lower.upper()
                elif query_lower in ["new york", "new jersey", "philadelphia", "philly"]:
                    is_only_jurisdiction = True
                    if "new york" in query_lower:
                        detected_jurisdiction_from_query = "NYC" if "city" in query_lower else "NY"
                    elif "new jersey" in query_lower:
                        detected_jurisdiction_from_query = "NJ"
                    elif "philadelphia" in query_lower or "philly" in query_lower:
                        detected_jurisdiction_from_query = "PHILADELPHIA"
            
            # If query is ONLY a jurisdiction, provide helpful message
            if is_only_jurisdiction and not jurisdiction:
                return {
                    "success": False,
                    "needs_clarification": True,
                    "message": f"Thank you for specifying the jurisdiction: {detected_jurisdiction_from_query}. Please provide your question about domestic worker rights, and I'll search for information specific to {detected_jurisdiction_from_query}.",
                    "response": None
                }
            
            # Normalize jurisdiction if provided (use robust normalization)
            normalized_jurisdiction = None
            if jurisdiction:
                normalized_jurisdiction = normalize_jurisdiction_input(jurisdiction)
                if not normalized_jurisdiction:
                    print(f"   ⚠️  Warning: Could not normalize jurisdiction '{jurisdiction}', proceeding without filter")
            elif is_only_jurisdiction and detected_jurisdiction_from_query:
                # Use the jurisdiction detected from the query
                normalized_jurisdiction = detected_jurisdiction_from_query
            
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
            # If we have DOL data for minimum wage queries, include it
            if dol_context and is_minimum_wage_query(query):
                # Use DOL-enhanced response generation
                response = self.layer3.generate_response_with_dol(
                    query,
                    chunks,
                    final_jurisdiction,
                    dol_context,
                    dol_data.get('url', 'https://www.dol.gov/agencies/whd/minimum-wage/state')
                )
            else:
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

def normalize_jurisdiction_input(jurisdiction_input: str) -> Optional[str]:
    """
    Robustly normalize jurisdiction input to standard format.
    Returns normalized jurisdiction or None if invalid.
    """
    if not jurisdiction_input:
        return None
    
    jurisdiction_lower = jurisdiction_input.lower().strip()
    
    # Try direct mapping first
    normalized = JURISDICTIONS.get(jurisdiction_lower)
    
    # If not found, try common variations
    if not normalized:
        if 'federal' in jurisdiction_lower or 'fed' in jurisdiction_lower or ('us' in jurisdiction_lower and 'federal' in jurisdiction_lower):
            normalized = 'US_FEDERAL'
        elif 'new york' in jurisdiction_lower:
            if 'city' in jurisdiction_lower or jurisdiction_lower == 'nyc':
                normalized = 'NYC'
            else:
                normalized = 'NY'
        elif jurisdiction_lower in ['ny', 'nyc']:
            normalized = 'NYC' if jurisdiction_lower == 'nyc' else 'NY'
        elif 'new jersey' in jurisdiction_lower or jurisdiction_lower == 'nj':
            normalized = 'NJ'
        elif 'philadelphia' in jurisdiction_lower or 'philly' in jurisdiction_lower:
            normalized = 'PHILADELPHIA'
    
    # Also check if it's already in normalized format
    if not normalized:
        jurisdiction_upper = jurisdiction_input.upper().strip()
        if jurisdiction_upper in ['US_FEDERAL', 'NY', 'NYC', 'NJ', 'PHILADELPHIA']:
            normalized = jurisdiction_upper
    
    return normalized


def main():
    """Interactive CLI for testing the search engine."""
    print("\n" + "="*70)
    print("DOMESTIC WORKER RIGHTS SEARCH ENGINE")
    print("="*70)
    print("\nWelcome! To provide accurate information, we need to know your jurisdiction.")
    print("Type 'quit' or 'exit' to stop.\n")
    
    # Initialize search engine
    engine = SearchEngine()
    
    # Track conversation state
    current_jurisdiction = None
    pending_query = None  # Store the original query when jurisdiction is needed
    is_new_chat = True
    jurisdiction_attempts = 0  # Prevent infinite loops
    MAX_JURISDICTION_ATTEMPTS = 3
    
    # Ask for jurisdiction at the start of new chat
    print("📍 Please specify your jurisdiction:")
    print("   Options: US Federal, NY (New York State), NYC (New York City), NJ (New Jersey), or Philadelphia")
    print("   You can also type 'change' later to switch jurisdictions.\n")
    
    while True:
        try:
            # Get user input
            if is_new_chat or current_jurisdiction is None:
                prompt = "📍 Select jurisdiction (US Federal/NY/NYC/NJ/Philadelphia): "
            else:
                prompt = f"\n🔍 Your question (jurisdiction: {current_jurisdiction}): "
            
            user_input = input(prompt).strip()
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("\n👋 Goodbye!")
                break
            
            if not user_input:
                continue
            
            # Handle jurisdiction selection or change
            if is_new_chat or current_jurisdiction is None or user_input.lower() == 'change':
                jurisdiction_input = user_input if user_input.lower() != 'change' else None
                
                if user_input.lower() == 'change':
                    print("\n📍 Change jurisdiction to:")
                    print("   Options: US Federal, NY, NYC, NJ, or Philadelphia")
                    jurisdiction_input = input("   New jurisdiction: ").strip()
                
                # Use robust normalization function
                normalized = normalize_jurisdiction_input(jurisdiction_input) if jurisdiction_input else None
                
                if normalized:
                    current_jurisdiction = normalized
                    is_new_chat = False
                    pending_query = None  # Clear any pending query
                    jurisdiction_attempts = 0  # Reset attempts
                    print(f"✅ Jurisdiction set to: {current_jurisdiction}")
                    print("   You can now ask your questions!\n")
                    continue
                else:
                    jurisdiction_attempts += 1
                    if jurisdiction_attempts >= MAX_JURISDICTION_ATTEMPTS:
                        print(f"\n⚠️  Maximum attempts reached. Please try again later.")
                        print("   Valid options: US Federal, NY, NYC, NJ, or Philadelphia")
                        jurisdiction_attempts = 0
                    else:
                        print("⚠️  Please specify a valid jurisdiction: US Federal, NY, NYC, NJ, or Philadelphia")
                    if is_new_chat:
                        continue
                    # If changing jurisdiction failed, continue with current one
            
            # Check if this is a jurisdiction response for a pending query
            if pending_query:
                # User is responding to jurisdiction question
                normalized = normalize_jurisdiction_input(user_input)
                
                if normalized:
                    # Process original query with jurisdiction
                    result = engine.search(pending_query, normalized)
                    current_jurisdiction = normalized  # Set it for future queries
                    pending_query = None
                    jurisdiction_attempts = 0  # Reset attempts
                else:
                    jurisdiction_attempts += 1
                    if jurisdiction_attempts >= MAX_JURISDICTION_ATTEMPTS:
                        print(f"\n⚠️  Maximum attempts reached. Resetting...")
                        pending_query = None
                        current_jurisdiction = None
                        jurisdiction_attempts = 0
                        is_new_chat = True
                        print("📍 Please specify your jurisdiction again:")
                        print("   Options: US Federal, NY, NYC, NJ, or Philadelphia\n")
                    else:
                        print("⚠️  Please specify a valid jurisdiction: US Federal, NY, NYC, NJ, or Philadelphia")
                    continue
            else:
                # Normal query - use current jurisdiction
                result = engine.search(user_input, current_jurisdiction)
            
            # Handle result
            if result.get("needs_clarification"):
                print(f"\n📋 {result['message']}")
                pending_query = user_input  # Store original query
                jurisdiction_attempts = 0  # Reset attempts for new clarification
            elif result.get("success"):
                print(f"\n✅ Answer ({result['chunks_found']} sources found):")
                print(f"\n{result['response']}")
                if result.get('jurisdiction'):
                    # Update current jurisdiction if detected
                    if result['jurisdiction'] and result['jurisdiction'] in SUPPORTED_JURISDICTIONS:
                        current_jurisdiction = result['jurisdiction']
                jurisdiction_attempts = 0  # Reset attempts on success
            else:
                print(f"\n❌ {result.get('message', 'No results found')}")
                # Don't increment attempts for search failures, only for jurisdiction issues
        
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    main()
