"""
Chat service for business logic.
"""
from api.database import Database, CHATS_COLLECTION
from datetime import datetime
from typing import List, Optional
from bson import ObjectId

def to_iso_string(dt: datetime) -> str:
    """Convert datetime to ISO 8601 string."""
    return dt.isoformat() + 'Z'

class ChatService:
    @staticmethod
    def get_all_chats() -> List[dict]:
        """Get all chats."""
        collection = Database.get_collection(CHATS_COLLECTION)
        chats = list(collection.find().sort("updatedAt", -1))
        
        # Convert ObjectId to string and format dates
        for chat in chats:
            chat['id'] = str(chat.pop('_id'))
            chat['createdAt'] = to_iso_string(chat['createdAt'])
            chat['updatedAt'] = to_iso_string(chat['updatedAt'])
            if chat.get('lastMessageAt'):
                chat['lastMessageAt'] = to_iso_string(chat['lastMessageAt'])
        
        return chats
    
    @staticmethod
    def get_chat_by_id(chat_id: str) -> Optional[dict]:
        """Get chat by ID."""
        try:
            collection = Database.get_collection(CHATS_COLLECTION)
            chat = collection.find_one({"_id": ObjectId(chat_id)})
            
            if not chat:
                return None
            
            chat['id'] = str(chat.pop('_id'))
            chat['createdAt'] = to_iso_string(chat['createdAt'])
            chat['updatedAt'] = to_iso_string(chat['updatedAt'])
            if chat.get('lastMessageAt'):
                chat['lastMessageAt'] = to_iso_string(chat['lastMessageAt'])
            
            # Ensure jurisdiction field exists (for backward compatibility)
            if 'jurisdiction' not in chat:
                chat['jurisdiction'] = None
            
            return chat
        except Exception:
            return None
    
    @staticmethod
    def get_chat_jurisdiction(chat_id: str) -> Optional[str]:
        """Get the stored jurisdiction for a chat."""
        try:
            collection = Database.get_collection(CHATS_COLLECTION)
            chat = collection.find_one({"_id": ObjectId(chat_id)}, {"jurisdiction": 1})
            if chat:
                return chat.get("jurisdiction")
            return None
        except Exception:
            return None
    
    @staticmethod
    def create_chat(title: Optional[str] = None) -> dict:
        """Create a new chat."""
        collection = Database.get_collection(CHATS_COLLECTION)
        now = datetime.utcnow()
        
        if not title:
            # Generate default title
            count = collection.count_documents({})
            title = f"New Chat {count + 1}"
        
        chat = {
            "_id": ObjectId(),
            "title": title,
            "createdAt": now,
            "updatedAt": now,
            "messageCount": 0,
            "userId": "anonymous",
            "jurisdiction": None  # Store last specified jurisdiction
        }
        
        collection.insert_one(chat)
        chat['id'] = str(chat.pop('_id'))
        chat['createdAt'] = to_iso_string(chat['createdAt'])
        chat['updatedAt'] = to_iso_string(chat['updatedAt'])
        
        return chat
    
    @staticmethod
    def update_chat(chat_id: str, updates: dict) -> Optional[dict]:
        """Update a chat."""
        try:
            collection = Database.get_collection(CHATS_COLLECTION)
            updates['updatedAt'] = datetime.utcnow()
            
            result = collection.find_one_and_update(
                {"_id": ObjectId(chat_id)},
                {"$set": updates},
                return_document=True
            )
            
            if not result:
                return None
            
            result['id'] = str(result.pop('_id'))
            result['createdAt'] = to_iso_string(result['createdAt'])
            result['updatedAt'] = to_iso_string(result['updatedAt'])
            if result.get('lastMessageAt'):
                result['lastMessageAt'] = to_iso_string(result['lastMessageAt'])
            
            return result
        except Exception:
            return None
    
    @staticmethod
    def delete_chat(chat_id: str) -> bool:
        """Delete a chat."""
        try:
            collection = Database.get_collection(CHATS_COLLECTION)
            result = collection.delete_one({"_id": ObjectId(chat_id)})
            return result.deleted_count > 0
        except Exception:
            return False
    
    @staticmethod
    def update_chat_metadata(chat_id: str, last_message: str, message_count: int):
        """Update chat metadata after message operations."""
        try:
            collection = Database.get_collection(CHATS_COLLECTION)
            now = datetime.utcnow()
            
            collection.update_one(
                {"_id": ObjectId(chat_id)},
                {
                    "$set": {
                        "lastMessage": last_message[:100] if last_message else None,
                        "lastMessageAt": now,
                        "updatedAt": now,
                        "messageCount": message_count
                    }
                }
            )
        except Exception:
            pass  # Silently fail if chat doesn't exist

