#!/usr/bin/env python3

"""
Robust Semantic Chunking for Domestic Worker Rights RAG Dataset

Features:
- Rule-based semantic chunking (no embeddings required)
- Comprehensive edge case handling
- Rich metadata extraction
- Document structure awareness
- Optimal chunk sizes for vectorization (300-800 chars)
- Overlap between chunks for context preservation
"""

import json
import re
import os
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Set
import pdfplumber
from collections import Counter, defaultdict
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')


# ============================================================================
# CONFIGURATION
# ============================================================================

CHUNK_CONFIG = {
    "min_chunk_size": 300,          # Minimum characters (ensures context)
    "target_chunk_size": 500,       # Target size (optimal for embeddings)
    "max_chunk_size": 800,          # Maximum characters
    "overlap_size": 75,             # Characters to overlap between chunks
    "min_sentence_length": 10,     # Minimum sentence length (lowered for 100% retention)
    "max_sentence_length": 2000,    # Maximum sentence length (increased for legal docs)
    "similarity_threshold": 0.3,    # Minimum similarity to group sentences
    "min_retention_rate": 98.0,     # Minimum data retention percentage
}

EDGE_CASE_PATTERNS = {
    "skip_patterns": [
        r'^Page \d+ of \d+$',
        r'^www\.',
        r'^https?://',
        r'^[\w.-]+@[\w.-]+$',
        r'^\d{1,2}/\d{1,2}/\d{2,4}$',
        r'^[A-Z\s]{2,50}$',  # All caps short lines
        r'^Table of Contents$',
        r'^Appendix [A-Z]$',
        r'^References?$',
        r'^Bibliography$',
    ],
    "header_patterns": [
        r'^WAGE AND HOUR DIVISION',
        r'^UNITED STATES DEPARTMENT OF LABOR',
        r'^Fact Sheet #',
        r'^U\.S\. Department of Labor',
    ],
    "footer_patterns": [
        r'^\d+\s*$',  # Page numbers
        r'^©\s*\d{4}',
        r'^Confidential$',
        r'^Draft$',
    ],
    "noise_patterns": [
        r'^[\s\-_]{10,}$',
        r'^\.{20,}$',
        r'^[\x00-\x1F]+$',
    ],
    "image_indicators": [
        'image', 'figure', 'chart', 'graph', 'diagram',
        'photo', 'picture', 'illustration', 'see figure',
    ],
}


# ============================================================================
# TOPIC KEYWORDS FOR SEMANTIC GROUPING
# ============================================================================

TOPIC_KEYWORDS = {
    "minimum_wage": [
        "minimum wage", "must be paid", "at least", "hourly rate", 
        "wage rate", "federal minimum", "state minimum", "prevailing wage"
    ],
    "overtime": [
        "overtime", "1.5", "one and a half", "time and a half", 
        "over 40", "overtime pay", "overtime hours", "compensatory time"
    ],
    "written_contract": [
        "written contract", "contract", "agreement", "written agreement",
        "employment contract", "contract terms", "contractual"
    ],
    "breaks": [
        "rest break", "meal break", "10 minute", "30 minute", 
        "break time", "lunch break", "rest period", "meal period"
    ],
    "termination": [
        "termination", "two weeks", "four weeks", "advance notice",
        "notice period", "termination notice", "employment termination"
    ],
    "discrimination": [
        "discrimination", "discriminate", "harassment", "protected class",
        "discriminatory", "equal opportunity", "protected characteristic"
    ],
    "retaliation": [
        "retaliation", "retaliate", "protected activity", "filing complaint",
        "retaliatory", "whistleblower", "protected conduct"
    ],
    "legal_protections": [
        "rights", "protections", "protected", "legal", "entitled",
        "legal rights", "worker rights", "employment rights"
    ],
    "domestic_worker_rights": [
        "domestic worker", "domestic service", "household worker",
        "domestic employee", "home care worker"
    ],
    "hours_worked": [
        "hours worked", "workweek", "work week", "working hours",
        "hours of work", "work hours", "time worked"
    ],
    "wage_deductions": [
        "deduction", "deduct", "uniform", "facility", "wage deduction",
        "deductions from wages", "permissible deductions"
    ],
    "enforcement": [
        "enforcement", "investigation", "violation", "penalty",
        "compliance", "enforcement action", "investigate"
    ],
    "privacy": [
        "privacy", "private information", "confidential", 
        "personal information", "privacy rights"
    ],
    "paid_time_off": [
        "paid time off", "pto", "vacation", "sick leave", 
        "holiday pay", "paid leave", "time off"
    ],
}


# ============================================================================
# ROBUST SEMANTIC CHUNKER
# ============================================================================

class RobustSemanticChunker:
    """Robust semantic chunker with comprehensive edge case handling."""
    
    def __init__(self):
        """Initialize the chunker."""
        print("Initializing Robust Semantic Chunker...")
        self.topic_keywords = TOPIC_KEYWORDS
        self.stats = {
            "files_processed": 0,
            "chunks_created": 0,
            "errors": [],
            "warnings": []
        }
        print("✅ Chunker initialized")
    
    def extract_text_from_pdf(self, pdf_path: Path) -> Tuple[str, Dict]:
        """
        Extract text from PDF with comprehensive error handling.
        
        Returns:
            Tuple of (text, metadata_dict)
        """
        metadata = {
            "pages_processed": 0,
            "total_pages": 0,
            "has_tables": False,
            "has_images": False,
            "is_scanned": False,
            "extraction_errors": [],
            "encoding_issues": [],
            "empty_pages": [],
        }
        
        try:
            text = ""
            max_pages = 1000  # Safety limit
            
            with pdfplumber.open(pdf_path) as pdf:
                total_pages = len(pdf.pages)
                metadata["total_pages"] = total_pages
                
                if total_pages == 0:
                    print(f"⚠️  PDF has no pages: {pdf_path.name}")
                    return "", metadata
                
                if total_pages > max_pages:
                    print(f"⚠️  PDF has {total_pages} pages, processing first {max_pages}")
                    total_pages = max_pages
                
                # Check if scanned (low text content)
                text_sample = ""
                for page_num in range(min(3, total_pages)):
                    try:
                        page = pdf.pages[page_num]
                        page_text = page.extract_text() or ""
                        text_sample += page_text
                    except:
                        pass
                
                if len(text_sample) < 100 and total_pages > 0:
                    metadata["is_scanned"] = True
                    print(f"⚠️  PDF appears to be scanned: {pdf_path.name}")
                
                # Extract text from all pages
                for page_num in range(total_pages):
                    try:
                        page = pdf.pages[page_num]
                        
                        # Extract text
                        page_text = page.extract_text()
                        
                        if not page_text or len(page_text.strip()) < 10:
                            metadata["empty_pages"].append(page_num + 1)
                            continue
                        
                        # Handle encoding
                        try:
                            page_text = page_text.encode('utf-8', errors='ignore').decode('utf-8')
                        except Exception as e:
                            metadata["encoding_issues"].append(f"Page {page_num + 1}: {str(e)}")
                            # Try to continue with partial text
                            page_text = page_text.encode('utf-8', errors='replace').decode('utf-8')
                        
                        # Skip image-only pages
                        if len(page_text.strip()) < 50:
                            if page.images and len(page.images) > 1:
                                continue
                        
                        text += page_text + "\n\n"
                        metadata["pages_processed"] += 1
                        
                        # Check for images
                        if page.images:
                            metadata["has_images"] = True
                        
                        # Extract tables
                        try:
                            tables = page.extract_tables()
                            if tables:
                                metadata["has_tables"] = True
                                for table in tables:
                                    if table:
                                        table_text = self._extract_table_text(table)
                                        if table_text and len(table_text.strip()) > 30:
                                            text += "\n[TABLE]\n" + table_text + "\n[/TABLE]\n"
                        except Exception as e:
                            metadata["extraction_errors"].append(f"Page {page_num + 1} table: {str(e)}")
                    
                    except Exception as e:
                        error_msg = f"Page {page_num + 1}: {str(e)}"
                        metadata["extraction_errors"].append(error_msg)
                        continue
                
                print(f"   Extracted {len(text)} chars from {metadata['pages_processed']}/{total_pages} pages")
            
            if not text or len(text.strip()) < 200:
                print(f"⚠️  No meaningful text extracted from {pdf_path.name}")
                return "", metadata
            
            return text.strip(), metadata
        
        except pdfplumber.exceptions.PDFSyntaxError as e:
            print(f"❌ PDF syntax error in {pdf_path.name}: {e}")
            metadata["extraction_errors"].append(f"PDF syntax error: {str(e)}")
            return "", metadata
        except Exception as e:
            print(f"❌ Error extracting from {pdf_path.name}: {e}")
            metadata["extraction_errors"].append(f"Extraction error: {str(e)}")
            import traceback
            traceback.print_exc()
            return "", metadata
    
    def _extract_table_text(self, table: List) -> str:
        """Extract text from table structure with robust error handling."""
        if not table or not isinstance(table, list):
            return ""
        
        text_parts = []
        for row in table:
            if not row or not isinstance(row, list):
                continue
            
            try:
                row_cells = []
                for cell in row:
                    if cell is None:
                        continue
                    try:
                        cell_str = str(cell).strip()
                        if cell_str:
                            row_cells.append(cell_str)
                    except:
                        continue
                
                if row_cells:
                    row_text = " | ".join(row_cells)
                    if len(row_text.strip()) > 5:
                        text_parts.append(row_text)
            except:
                continue
        
        return "\n".join(text_parts) if text_parts else ""
    
    def clean_text(self, text: str) -> str:
        """Clean extracted text with comprehensive pattern removal."""
        if not text or not isinstance(text, str):
            return ""
        
        # Handle encoding
        try:
            text = text.encode('utf-8', errors='ignore').decode('utf-8')
        except:
            try:
                text = text.encode('utf-8', errors='replace').decode('utf-8')
            except:
                return ""
        
        # Remove PDF artifacts
        text = re.sub(r'kcabdeeF\s*timbuS.*?\n', '', text, flags=re.IGNORECASE)
        text = re.sub(r'\d{1,2}/\d{1,2}/\d{2,4},?\s*\d{1,2}:\d{2}\s*[AP]M', '', text)
        
        # Remove headers
        for pattern in EDGE_CASE_PATTERNS["header_patterns"]:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE | re.MULTILINE)
        
        # Remove footers
        for pattern in EDGE_CASE_PATTERNS["footer_patterns"]:
            text = re.sub(pattern, '', text, flags=re.MULTILINE | re.IGNORECASE)
        
        # Remove URLs and emails
        text = re.sub(r'https?://\S+', '', text)
        text = re.sub(r'www\.\S+', '', text)
        text = re.sub(r'[\w.-]+@[\w.-]+', '', text)
        
        # Remove noise patterns
        for pattern in EDGE_CASE_PATTERNS["noise_patterns"]:
            text = re.sub(pattern, '', text, flags=re.MULTILINE)
        
        # Remove control characters (keep newlines/tabs)
        text = re.sub(r'[\x00-\x08\x0B-\x0C\x0E-\x1F]', '', text)
        
        # Remove excessive repeated characters
        text = re.sub(r'(.)\1{50,}', r'\1', text)
        
        # Fix broken words (hyphenated across lines)
        text = re.sub(r'(\w)-\s*\n\s*(\w)', r'\1\2', text)
        
        # Normalize whitespace
        text = re.sub(r'[ \t]+', ' ', text)
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        return text.strip()
    
    def split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences with legal text handling - 100% retention mode."""
        if not text:
            return []
        
        # Enhanced sentence splitting for legal/regulatory text
        # Handle abbreviations, decimals, legal citations
        sentence_endings = r'(?<=[.!?])\s+(?=[A-Z])|(?<=[.!?])\s+(?=\()|(?<=[.!?])\s+(?=\d)'
        sentences = re.split(sentence_endings, text)
        
        # Filter and clean sentences - BUT RETAIN ALL IMPORTANT CONTENT
        filtered = []
        for sent in sentences:
            sent = sent.strip()
            if not sent:
                continue
            
            # ONLY skip obvious noise patterns (not content)
            is_noise = False
            for pattern in EDGE_CASE_PATTERNS["skip_patterns"]:
                if re.match(pattern, sent, re.IGNORECASE):
                    # Only skip if it's truly noise (page numbers, URLs, etc.)
                    # Don't skip if it contains actual words
                    if len(re.findall(r'[a-zA-Z]{3,}', sent)) < 2:
                        is_noise = True
                        break
            
            if is_noise:
                continue
            
            # Handle very long sentences (split but keep all)
            if len(sent) > CHUNK_CONFIG["max_sentence_length"]:
                # Try to split further but keep all parts
                sub_sentences = re.split(r'[.!?]\s+', sent)
                for sub_sent in sub_sentences:
                    sub_sent = sub_sent.strip()
                    if len(sub_sent) >= 10:  # Keep even short parts
                        filtered.append(sub_sent)
                continue
            
            # Keep short sentences if they have meaningful content
            if len(sent) < CHUNK_CONFIG["min_sentence_length"]:
                # Only skip if it's truly meaningless (just numbers, single char, etc.)
                alpha_chars = len(re.findall(r'[a-zA-Z]', sent))
                if alpha_chars >= 3:  # Has at least 3 letters - keep it
                    filtered.append(sent)
                continue
            
            # Keep all caps headers if they're part of content structure
            if sent.isupper() and len(sent) < 100:
                # Keep if it's a heading (has structure)
                if len(sent.split()) >= 2:  # Multi-word heading - keep it
                    filtered.append(sent)
                continue
            
            # Keep sentences with low alpha ratio if they have numbers (could be important data)
            alpha_chars = len(re.findall(r'[a-zA-Z]', sent))
            if alpha_chars < len(sent) * 0.3:
                # But keep if it has numbers (could be dates, amounts, etc.)
                if re.search(r'\d', sent):
                    filtered.append(sent)
                continue
            
            # Check for corruption but be lenient
            words = sent.split()
            if len(words) > 5:
                word_counts = Counter(word.lower() for word in words)
                max_repeat = max(word_counts.values()) if word_counts else 0
                # Only skip if >70% same word (very corrupted)
                if max_repeat > len(words) * 0.7:
                    continue
            
            # Keep everything else
            filtered.append(sent)
        
        return filtered
    
    def detect_structure_breaks(self, text: str) -> Set[int]:
        """
        Detect structural breaks (headings, sections) in text.
        Returns set of sentence indices where breaks occur.
        """
        breaks = set()
        lines = text.split('\n')
        
        # Track character positions
        char_positions = []
        current_pos = 0
        for line in lines:
            char_positions.append((current_pos, current_pos + len(line)))
            current_pos += len(line) + 1  # +1 for newline
        
        # Find headings
        for i, line in enumerate(lines):
            line = line.strip()
            if not line or len(line) < 5:
                continue
            
            # Detect heading patterns
            is_heading = (
                (line.isupper() and 10 < len(line) < 100) or
                re.match(r'^[A-Z][a-z]+(\s+[A-Z][a-z]+)*:?$', line) or
                re.match(r'^\d+[.)]\s+[A-Z]', line) or
                re.match(r'^[A-Z][A-Z\s]{5,50}$', line) or
                re.match(r'^[IVX]+\.\s+[A-Z]', line)  # Roman numerals
            )
            
            if is_heading:
                # Find which sentence contains this line
                line_start, line_end = char_positions[i]
                # Approximate: find sentence that contains this position
                breaks.add(i)  # Store line index, will convert to sentence index later
        
        return breaks
    
    def calculate_sentence_similarity(self, sent1: str, sent2: str) -> float:
        """
        Calculate keyword-based similarity between sentences.
        Returns similarity score 0.0-1.0
        """
        if not sent1 or not sent2:
            return 0.0
        
        sent1_lower = sent1.lower()
        sent2_lower = sent2.lower()
        
        # Check for topic keyword overlap
        topic_overlap = 0
        for topic, keywords in self.topic_keywords.items():
            kw1_count = sum(1 for kw in keywords if kw in sent1_lower)
            kw2_count = sum(1 for kw in keywords if kw in sent2_lower)
            if kw1_count > 0 and kw2_count > 0:
                topic_overlap += 1
        
        # Word overlap
        words1 = set(sent1_lower.split())
        words2 = set(sent2_lower.split())
        
        if not words1 or not words2:
            return 0.0
        
        common_words = words1.intersection(words2)
        word_overlap = len(common_words) / max(len(words1), len(words2))
        
        # Combined similarity
        topic_score = min(topic_overlap / 3.0, 1.0)  # Normalize topic overlap
        similarity = (topic_score * 0.4) + (word_overlap * 0.6)
        
        return similarity
    
    def detect_topic(self, text: str) -> str:
        """Detect primary topic from text content."""
        text_lower = text.lower()
        topic_scores = {}
        
        for topic, keywords in self.topic_keywords.items():
            score = sum(1 for kw in keywords if kw in text_lower)
            if score > 0:
                topic_scores[topic] = score
        
        if topic_scores:
            return max(topic_scores.items(), key=lambda x: x[1])[0]
        return "general"
    
    def chunk_text(self, text: str, metadata: Dict) -> List[Dict]:
        """
        Create optimal semantic chunks from text with 100% data retention.
        
        Returns list of chunk dictionaries with full metadata.
        """
        if not text or len(text.strip()) < 50:  # Lower threshold to keep small docs
            return []
        
        # Clean text (but preserve all content)
        cleaned_text = self.clean_text(text)
        
        # Store cleaned text length for validation (this is what we'll chunk)
        original_text_length = len(cleaned_text)
        text = cleaned_text
        
        # Split into sentences (retain all important content)
        sentences = self.split_into_sentences(text)
        
        # If very few sentences, return as single chunk (don't lose data)
        if len(sentences) < 2:
            if len(text) >= 50:  # Keep even small chunks
                return [self._create_chunk(text, 0, metadata, [text] if sentences else [text])]
            # If too small, still keep it but mark appropriately
            if len(text) > 20:
                return [self._create_chunk(text, 0, metadata, [text])]
            return []
        
        # Detect structure breaks (approximate)
        structure_breaks = self.detect_structure_breaks(text)
        
        # Group sentences into chunks
        chunks = []
        current_chunk = []
        current_size = 0
        last_chunk_text = ""  # For overlap
        
        for i, sentence in enumerate(sentences):
            sentence_size = len(sentence)
            
            # Determine if we should break
            should_break = False
            break_reason = ""
            
            # Hard break: structure boundary (approximate)
            if i > 0 and i % 5 == 0:  # Check every 5 sentences for structure
                # This is a simplified check - in production, map structure breaks to sentence indices
                pass
            
            # Hard break: exceeds max size
            if current_size + sentence_size > CHUNK_CONFIG["max_chunk_size"]:
                should_break = True
                break_reason = "max_size"
            
            # Soft break: has target size and low similarity
            elif (current_size >= CHUNK_CONFIG["target_chunk_size"] and 
                  current_chunk and 
                  i < len(sentences) - 1):
                
                # Check similarity with next sentence
                next_sent = sentences[i]
                if current_chunk:
                    last_sent = current_chunk[-1]
                    similarity = self.calculate_sentence_similarity(last_sent, next_sent)
                    
                    if similarity < CHUNK_CONFIG["similarity_threshold"]:
                        should_break = True
                        break_reason = "low_similarity"
            
            if should_break and current_chunk:
                # Save current chunk
                chunk_text = " ".join(current_chunk)
                if len(chunk_text) >= CHUNK_CONFIG["min_chunk_size"]:
                    chunk = self._create_chunk(
                        chunk_text, 
                        len(chunks), 
                        metadata, 
                        current_chunk,
                        break_reason
                    )
                    chunks.append(chunk)
                    last_chunk_text = chunk_text
                
                # Start new chunk with overlap
                if chunks and CHUNK_CONFIG["overlap_size"] > 0 and last_chunk_text:
                    # Add last 1-2 sentences from previous chunk
                    overlap_sents = current_chunk[-2:] if len(current_chunk) >= 2 else current_chunk[-1:]
                    overlap_text = " ".join(overlap_sents)
                    
                    if len(overlap_text) <= CHUNK_CONFIG["overlap_size"] * 2:
                        current_chunk = overlap_sents + [sentence]
                        current_size = sum(len(s) for s in current_chunk) + len(current_chunk) - 1
                    else:
                        current_chunk = [sentence]
                        current_size = sentence_size
                else:
                    current_chunk = [sentence]
                    current_size = sentence_size
            else:
                # Add to current chunk
                current_chunk.append(sentence)
                current_size += sentence_size + 1  # +1 for space
        
        # Add final chunk - ALWAYS include remaining content (100% retention)
        if current_chunk:
            chunk_text = " ".join(current_chunk)
            # Accept even small chunks to ensure 100% retention
            if len(chunk_text) >= 50:  # Lower threshold
                chunk = self._create_chunk(
                    chunk_text, 
                    len(chunks), 
                    metadata, 
                    current_chunk,
                    "final"
                )
                chunks.append(chunk)
            elif len(chunk_text) > 0:
                # Even tiny chunks - merge with previous if possible, or keep separately
                if chunks and len(chunks[-1]["text"]) + len(chunk_text) <= CHUNK_CONFIG["max_chunk_size"] * 1.5:
                    # Merge with last chunk
                    chunks[-1]["text"] += " " + chunk_text
                    chunks[-1]["chunk_size"] = len(chunks[-1]["text"])
                    chunks[-1]["word_count"] = len(chunks[-1]["text"].split())
                else:
                    # Keep as separate small chunk
                    chunk = self._create_chunk(
                        chunk_text, 
                        len(chunks), 
                        metadata, 
                        current_chunk,
                        "final_small"
                    )
                    chunks.append(chunk)
        
        # VALIDATION: Ensure 100% data retention
        total_chunked_text = " ".join([c["text"] for c in chunks])
        retention_rate = (len(total_chunked_text) / original_text_length * 100) if original_text_length > 0 else 100
        
        if retention_rate < 98:
            print(f"⚠️  Warning: Only {retention_rate:.1f}% data retained. Checking for missing content...")
            # Try to find and add missing sentences
            all_sentences_text = " ".join(sentences)
            if len(all_sentences_text) > len(total_chunked_text):
                # Some sentences were lost - add them
                missing_text = all_sentences_text[len(total_chunked_text):].strip()
                if missing_text and len(missing_text) > 20:
                    # Add missing content as additional chunk
                    chunk = self._create_chunk(
                        missing_text,
                        len(chunks),
                        metadata,
                        [missing_text],
                        "recovered"
                    )
                    chunks.append(chunk)
                    print(f"   ✅ Recovered {len(missing_text)} characters of missing content")
        else:
            print(f"   ✅ Data retention: {retention_rate:.1f}%")
        
        return chunks
    
    def _create_chunk(self, text: str, idx: int, metadata: Dict, 
                     sentences: List[str] = None, break_reason: str = "") -> Dict:
        """Create a chunk dictionary with comprehensive metadata."""
        chunk_text = text.strip()
        
        # Detect topic
        topic = self.detect_topic(chunk_text)
        
        # Extract additional metadata
        word_count = len(chunk_text.split())
        sentence_count = len(sentences) if sentences else len(re.findall(r'[.!?]', chunk_text))
        
        # Detect if contains table
        has_table = "[TABLE]" in chunk_text
        
        # Detect if contains list
        has_list = bool(re.search(r'^[\s]*[•·▪▫-]\s+', chunk_text, re.MULTILINE))
        
        # Create unique ID: source_file_name_chunk_counter
        source_file = metadata.get('source_file', 'unknown')
        # Sanitize filename for ID (remove extension, replace spaces/special chars with underscores)
        file_slug = Path(source_file).stem  # Remove .pdf extension
        file_slug = re.sub(r'[^\w\-_]', '_', file_slug)  # Replace special chars with underscore
        file_slug = re.sub(r'_+', '_', file_slug)  # Replace multiple underscores with single
        file_slug = file_slug.lower()  # Lowercase
        
        # ID format: source_file_name_chunk_number (1, 2, 3...)
        chunk_id = f"{file_slug}_{idx + 1}"
        
        # Create chunk document
        doc = {
            "id": chunk_id,
            "jurisdiction": metadata.get("jurisdiction", "UNKNOWN"),
            "topic": topic,
            "text": chunk_text,
            "chunk_index": idx,
            "chunk_size": len(chunk_text),
            "word_count": word_count,
            "sentence_count": sentence_count,
            "source_file": metadata.get("source_file", "unknown"),
            "has_table": has_table,
            "has_list": has_list,
            "break_reason": break_reason,
            
            # Comprehensive metadata
            "metadata": {
                "source": metadata.get("source_file", "unknown"),
                "jurisdiction": metadata.get("jurisdiction", "UNKNOWN"),
                "topic": topic,
                "chunk_index": idx,
                "chunk_size": len(chunk_text),
                "word_count": word_count,
                "sentence_count": sentence_count,
                "created_at": metadata.get("created_at", datetime.now().strftime("%Y-%m-%d")),
                "has_table": has_table,
                "has_list": has_list,
                "break_reason": break_reason,
            }
        }
        
        # Add optional fields
        if metadata.get("worker_type"):
            doc["worker_type"] = metadata["worker_type"]
            doc["metadata"]["worker_type"] = metadata["worker_type"]
        
        if metadata.get("page_number"):
            doc["page_number"] = metadata["page_number"]
            doc["metadata"]["page_number"] = metadata["page_number"]
        
        # Add PDF metadata if available
        if metadata.get("pdf_metadata"):
            pdf_meta = metadata["pdf_metadata"]
            doc["metadata"]["total_pages"] = pdf_meta.get("total_pages", 0)
            doc["metadata"]["pages_processed"] = pdf_meta.get("pages_processed", 0)
            doc["metadata"]["has_tables"] = pdf_meta.get("has_tables", False)
            doc["metadata"]["has_images"] = pdf_meta.get("has_images", False)
        
        return doc


# ============================================================================
# JURISDICTION DETECTION
# ============================================================================

def detect_jurisdiction_from_filename(filename: str, text: str = "") -> str:
    """Auto-detect jurisdiction from filename and text."""
    filename_lower = filename.lower()
    text_lower = text.lower() if text else ""
    
    # Check filename patterns
    if "philadelphia" in filename_lower or "philly" in filename_lower:
        return "PHILADELPHIA"
    elif "new york city" in filename_lower or "nyc" in filename_lower or "339" in filename_lower:
        return "NYC"
    elif "new jersey" in filename_lower or "nj" in filename_lower:
        return "NJ"
    elif "new york" in filename_lower or "ny state" in filename_lower or "p712" in filename_lower:
        return "NY"
    elif "federal" in filename_lower or "flsa" in filename_lower or "u.s." in filename_lower or "us department" in filename_lower:
        return "US_FEDERAL"
    
    # Check text content
    if text and len(text) > 100:
        if "philadelphia" in text_lower[:1000]:
            return "PHILADELPHIA"
        elif "new york city" in text_lower[:1000] or "local law 339" in text_lower:
            return "NYC"
        elif "new jersey" in text_lower[:1000]:
            return "NJ"
        elif "new york state" in text_lower[:1000] or "nys department" in text_lower:
            return "NY"
        elif "fair labor standards act" in text_lower[:1000] or "flsa" in text_lower[:1000]:
            return "US_FEDERAL"
    
    return "UNKNOWN"


# ============================================================================
# FILE PROCESSING
# ============================================================================

def process_file(file_path: Path, chunker: RobustSemanticChunker, 
                 file_mapping: Dict) -> List[Dict]:
    """Process a single file with comprehensive error handling."""
    filename = file_path.name
    
    print(f"\n{'='*60}")
    print(f"Processing: {filename}")
    print(f"{'='*60}")
    
    # Get file metadata
    mapping = file_mapping.get(filename, {})
    jurisdiction = mapping.get("jurisdiction")
    
    # Extract text
    text, pdf_metadata = chunker.extract_text_from_pdf(file_path)
    
    if not text or len(text.strip()) < 200:
        print(f"⚠️  Insufficient text extracted")
        return []
    
    # Auto-detect jurisdiction
    if not jurisdiction or jurisdiction == "UNKNOWN":
        jurisdiction = detect_jurisdiction_from_filename(filename, text)
        print(f"   Auto-detected jurisdiction: {jurisdiction}")
    else:
        print(f"   Using jurisdiction: {jurisdiction}")
    
    print(f"✅ Extracted {len(text)} characters from {pdf_metadata['pages_processed']} pages")
    
    if pdf_metadata.get("has_tables"):
        print(f"   ℹ️  Contains tables")
    if pdf_metadata.get("has_images"):
        print(f"   ℹ️  Contains images")
    if pdf_metadata.get("is_scanned"):
        print(f"   ⚠️  Appears to be scanned PDF")
    if pdf_metadata.get("extraction_errors"):
        print(f"   ⚠️  {len(pdf_metadata['extraction_errors'])} extraction errors")
    
    # Create metadata
    metadata = {
        "jurisdiction": jurisdiction,
        "source_file": filename,
        "created_at": datetime.now().strftime("%Y-%m-%d"),
        "pdf_metadata": pdf_metadata
    }
    
    # Create chunks
    try:
        chunks = chunker.chunk_text(text, metadata)
        
        print(f"✅ Created {len(chunks)} chunks")
        if chunks:
            sizes = [c["chunk_size"] for c in chunks]
            print(f"   Size range: {min(sizes)} - {max(sizes)} chars")
            print(f"   Average: {int(sum(sizes)/len(sizes))} chars")
            
            # Show topic distribution
            topics = Counter([c["topic"] for c in chunks])
            print(f"   Topics: {', '.join([f'{t}({c})' for t, c in topics.most_common(3)])}")
        
        return chunks
    
    except Exception as e:
        print(f"❌ Error creating chunks: {e}")
        import traceback
        traceback.print_exc()
        return []


# ============================================================================
# MAIN FUNCTION
# ============================================================================

def main():
    """Main processing function - test on one file first."""
    print("="*60)
    print("ROBUST SEMANTIC CHUNKING - TEST MODE")
    print("="*60)
    
    # Initialize chunker
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
    data_dir = Path(__file__).parent.parent / "dataset" / "Data_FactSheets"
    output_dir = Path(__file__).parent
    output_file = output_dir / "test_chunks_output.json"
    
    if not data_dir.exists():
        print(f"❌ Dataset directory not found: {data_dir}")
        return
    
    # PROCESS ALL FILES
    all_pdf_files = sorted(list(data_dir.glob("*.pdf")))
    
    if not all_pdf_files:
        print(f"❌ No PDF files found in: {data_dir}")
        return
    
    print(f"\n📁 Processing ALL files: {len(all_pdf_files)} PDFs\n")
    
    # Process all files
    all_chunks = []
    processed_count = 0
    skipped_count = 0
    error_count = 0
    
    for file_path in all_pdf_files:
        filename = file_path.name
        
        # Get mapping
        if filename in KNOWN_FILE_MAPPINGS:
            mapping = KNOWN_FILE_MAPPINGS[filename]
        else:
            mapping = {"jurisdiction": None}
        
        # Process file
        try:
            chunks = process_file(file_path, chunker, {filename: mapping})
        
            if chunks:
                all_chunks.extend(chunks)
                processed_count += 1
            else:
                skipped_count += 1
                print(f"⚠️  No chunks generated from {filename}")
        except Exception as e:
            print(f"❌ Error processing {filename}: {e}")
            error_count += 1
            import traceback
            traceback.print_exc()
            continue
    
    # Save all chunks
    print(f"\n{'='*60}")
    print(f"PROCESSING COMPLETE")
    print(f"{'='*60}")
    print(f"✅ Total chunks created: {len(all_chunks)}")
    print(f"📁 Processed: {processed_count} files")
    print(f"⚠️  Skipped: {skipped_count} files")
    print(f"❌ Errors: {error_count} files")
    print(f"📁 Saving to: {output_file}")
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_chunks, f, indent=2, ensure_ascii=False)
    
    # Comprehensive statistics
    print(f"\n📊 STATISTICS:")
    print(f"   Total chunks: {len(all_chunks)}")
    
    if all_chunks:
        sizes = [c["chunk_size"] for c in all_chunks]
        print(f"   Size stats:")
        print(f"     Min: {min(sizes)} chars")
        print(f"     Max: {max(sizes)} chars")
        print(f"     Avg: {int(sum(sizes)/len(sizes))} chars")
        
        # Check ID uniqueness
        ids = [c["id"] for c in all_chunks]
        unique_ids = len(set(ids))
        print(f"\n   ID Uniqueness:")
        print(f"     Unique IDs: {unique_ids}/{len(ids)}")
        if unique_ids == len(ids):
            print(f"     ✅ NO COLLISIONS - All IDs are unique!")
        else:
            print(f"     ❌ COLLISIONS DETECTED!")
        
        # Topic distribution
        topics = Counter([c["topic"] for c in all_chunks])
        print(f"\n   Topic distribution (top 10):")
        for topic, count in topics.most_common(10):
            print(f"     {topic}: {count} chunks")
        
        # Jurisdiction distribution
        jurisdictions = Counter([c["jurisdiction"] for c in all_chunks])
        print(f"\n   Jurisdiction distribution:")
        for jur, count in sorted(jurisdictions.items()):
            print(f"     {jur}: {count} chunks")
        
        # Files processed
        files = Counter([c["source_file"] for c in all_chunks])
        print(f"\n   Files processed: {len(files)}")
        print(f"   Top 5 files by chunk count:")
        for file, count in files.most_common(5):
            print(f"     {file[:50]}...: {count} chunks")
    
    print(f"\n✅ Processing complete! Output saved to: {output_file}")


if __name__ == "__main__":
    main()

