"""
Message endpoints.
"""
from fastapi import APIRouter, HTTPException, status, BackgroundTasks
from api.models import (
    CreateMessageRequest, UpdateMessageRequest, ApiResponse
)
from api.services.message_service import MessageService
from api.services.ai_service import AIService
from api.services.chat_service import ChatService

router = APIRouter(prefix="/api/chats", tags=["messages"])

@router.get("/{chat_id}/messages", response_model=ApiResponse)
async def get_messages(chat_id: str):
    """Get all messages for a chat."""
    try:
        messages = MessageService.get_messages_by_chat_id(chat_id)
        return {"data": messages}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

def generate_and_save_ai_response(chat_id: str, user_message: str):
    """Background task to generate and save AI response."""
    try:
        # Get stored jurisdiction from chat
        jurisdiction = ChatService.get_chat_jurisdiction(chat_id)
        if jurisdiction:
            print(f"✅ Using stored jurisdiction for chat {chat_id}: {jurisdiction}")
        else:
            print(f"ℹ️  No stored jurisdiction for chat {chat_id}, will detect from query if needed")
        ai_response = AIService.generate_response(user_message, jurisdiction)
        MessageService.create_message(chat_id, ai_response, "assistant")
    except Exception as e:
        print(f"Error generating AI response: {e}")

@router.post("/{chat_id}/messages", response_model=ApiResponse, status_code=status.HTTP_201_CREATED)
async def create_message(chat_id: str, request: CreateMessageRequest, background_tasks: BackgroundTasks):
    """Create a new message."""
    try:
        # Create user message
        message = MessageService.create_message(
            chat_id, request.content, request.role
        )
        
        # If it's a user message, generate assistant response in background
        if request.role == "user":
            # Generate AI response asynchronously (non-blocking)
            background_tasks.add_task(
                generate_and_save_ai_response,
                chat_id,
                request.content
            )
        
        return {"data": message}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.patch("/{chat_id}/messages/{message_id}", response_model=ApiResponse)
async def update_message(chat_id: str, message_id: str, request: UpdateMessageRequest):
    """Update a message."""
    message = MessageService.update_message(chat_id, message_id, request.content)
    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message not found"
        )
    return {"data": message}

@router.delete("/{chat_id}/messages/{message_id}", response_model=ApiResponse)
async def delete_message(chat_id: str, message_id: str):
    """Delete a message."""
    deleted = MessageService.delete_message(chat_id, message_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message not found"
        )
    return {"data": None}

