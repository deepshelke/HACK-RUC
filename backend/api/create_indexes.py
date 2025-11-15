"""
Create indexes for chats and messages collections.
"""
import sys
from pathlib import Path

# Add parent directory to path so we can import api module
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

from api.database import Database

def create_indexes():
    """Create necessary indexes."""
    try:
        chats_collection = Database.get_collection('chats')
        messages_collection = Database.get_collection('messages')
        
        # Indexes for chats
        chats_collection.create_index("userId")
        chats_collection.create_index("updatedAt")
        print("✅ Created indexes for chats collection")
        
        # Indexes for messages
        messages_collection.create_index("chatId")
        messages_collection.create_index([("chatId", 1), ("timestamp", 1)])
        print("✅ Created indexes for messages collection")
        
        print("\n✅ All indexes created successfully!")
    except Exception as e:
        print(f"❌ Error creating indexes: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    create_indexes()

