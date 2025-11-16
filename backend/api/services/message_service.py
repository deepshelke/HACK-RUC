"""
Message service for business logic.
"""
from api.database import Database, MESSAGES_COLLECTION, CHATS_COLLECTION
from datetime import datetime
from typing import List, Optional
from bson import ObjectId
from api.services.chat_service import ChatService

# Jurisdiction mapping for detection
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

def detect_jurisdiction_in_message(content: str) -> Optional[str]:
    """Detect if message contains only a jurisdiction specification."""
    content_lower = content.lower().strip()
    
    # Check for exact matches
    for key, value in JURISDICTIONS.items():
        if content_lower == key or content_lower == value.lower():
            return value
    
    # Check for common variations
    if content_lower in ["us federal", "us fed", "federal", "fed"]:
        return "US_FEDERAL"
    elif content_lower in ["ny", "nyc", "nj"]:
        return content_lower.upper()
    elif "new york" in content_lower:
        return "NYC" if "city" in content_lower or content_lower == "nyc" else "NY"
    elif "new jersey" in content_lower or content_lower == "nj":
        return "NJ"
    elif "philadelphia" in content_lower or "philly" in content_lower:
        return "PHILADELPHIA"
    
    return None

def to_iso_string(dt: datetime) -> str:
    """Convert datetime to ISO 8601 string."""
    return dt.isoformat() + 'Z'

class MessageService:
    @staticmethod
    def get_messages_by_chat_id(chat_id: str) -> List[dict]:
        """Get all messages for a chat."""
        try:
            collection = Database.get_collection(MESSAGES_COLLECTION)
            messages = list(collection.find({"chatId": chat_id}).sort("timestamp", 1))
            
            for message in messages:
                message['id'] = str(message.pop('_id'))
                message['timestamp'] = to_iso_string(message['timestamp'])
            
            return messages
        except Exception:
            return []
    
    @staticmethod
    def create_message(chat_id: str, content: str, role: str) -> dict:
        """Create a new message."""
        collection = Database.get_collection(MESSAGES_COLLECTION)
        now = datetime.utcnow()
        
        message = {
            "_id": ObjectId(),
            "content": content,
            "role": role,
            "timestamp": now,
            "chatId": chat_id
        }
        
        collection.insert_one(message)
        
        # If user message contains only jurisdiction, store it in chat
        if role == "user":
            detected_jurisdiction = detect_jurisdiction_in_message(content)
            if detected_jurisdiction:
                # Update chat with jurisdiction
                chat_collection = Database.get_collection(CHATS_COLLECTION)
                chat_collection.update_one(
                    {"_id": ObjectId(chat_id)},
                    {"$set": {"jurisdiction": detected_jurisdiction}}
                )
                print(f"✅ Stored jurisdiction '{detected_jurisdiction}' for chat {chat_id}")
        
        # Update chat metadata
        messages = MessageService.get_messages_by_chat_id(chat_id)
        ChatService.update_chat_metadata(chat_id, content, len(messages))
        
        message['id'] = str(message.pop('_id'))
        message['timestamp'] = to_iso_string(message['timestamp'])
        
        return message
    
    @staticmethod
    def update_message(chat_id: str, message_id: str, content: str) -> Optional[dict]:
        """Update a message."""
        try:
            collection = Database.get_collection(MESSAGES_COLLECTION)
            
            result = collection.find_one_and_update(
                {"_id": ObjectId(message_id), "chatId": chat_id},
                {"$set": {"content": content}},
                return_document=True
            )
            
            if not result:
                return None
            
            # Update chat's lastMessage if this is the last message
            messages = MessageService.get_messages_by_chat_id(chat_id)
            if messages and messages[-1]['id'] == message_id:
                ChatService.update_chat_metadata(chat_id, content, len(messages))
            
            result['id'] = str(result.pop('_id'))
            result['timestamp'] = to_iso_string(result['timestamp'])
            
            return result
        except Exception:
            return None
    
    @staticmethod
    def delete_message(chat_id: str, message_id: str) -> bool:
        """Delete a message."""
        try:
            collection = Database.get_collection(MESSAGES_COLLECTION)
            result = collection.delete_one({"_id": ObjectId(message_id), "chatId": chat_id})
            
            if result.deleted_count > 0:
                # Update chat metadata
                messages = MessageService.get_messages_by_chat_id(chat_id)
                if messages:
                    last_message = messages[-1]['content']
                    ChatService.update_chat_metadata(chat_id, last_message, len(messages))
                else:
                    # No messages left, clear lastMessage
                    ChatService.update_chat_metadata(chat_id, "", 0)
            
            return result.deleted_count > 0
        except Exception:
            return False

