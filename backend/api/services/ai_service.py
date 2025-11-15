"""
AI service to integrate with search engine.
"""
import sys
from pathlib import Path
from typing import Optional

class AIService:
    _engine = None
    
    @classmethod
    def get_engine(cls):
        """Get or initialize search engine."""
        if cls._engine is None:
            try:
                # Add search engine to path
                # Handle folder name with space: "search engine"
                backend_path = Path(__file__).parent.parent.parent
                search_engine_path = backend_path / "search engine"
                if not search_engine_path.exists():
                    # Try alternative path
                    search_engine_path = backend_path / "search_engine"
                
                sys.path.insert(0, str(search_engine_path))
                
                from search_engine import SearchEngine
                cls._engine = SearchEngine()
                print("✅ Search Engine initialized for AI service")
            except Exception as e:
                print(f"⚠️  Warning: Could not initialize search engine: {e}")
                print("   AI responses will be disabled")
                cls._engine = None
        
        return cls._engine
    
    @staticmethod
    def generate_response(user_message: str, jurisdiction: Optional[str] = None) -> str:
        """Generate AI response using search engine."""
        try:
            engine = AIService.get_engine()
            if engine is None:
                return "I apologize, but the AI service is currently unavailable. Please try again later."
            
            result = engine.search(user_message, jurisdiction)
            
            if result.get("success") and result.get("response"):
                return result["response"]
            elif result.get("needs_clarification"):
                return result.get("message", "I need more information to help you.")
            else:
                return result.get("message", "I apologize, but I couldn't generate a response. Please try again.")
        except Exception as e:
            print(f"❌ Error generating AI response: {e}")
            import traceback
            traceback.print_exc()
            return "I apologize, but I encountered an error while generating a response. Please try again."

