"""
Chat endpoints.
"""
from fastapi import APIRouter, HTTPException, status
from api.models import (
    CreateChatRequest, UpdateChatRequest, ApiResponse
)
from api.services.chat_service import ChatService
from api.services.message_service import MessageService

router = APIRouter(prefix="/api/chats", tags=["chats"])

@router.get("", response_model=ApiResponse)
async def get_all_chats():
    """Get all chats."""
    try:
        chats = ChatService.get_all_chats()
        return {"data": chats}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/{chat_id}", response_model=ApiResponse)
async def get_chat(chat_id: str):
    """Get a specific chat."""
    chat = ChatService.get_chat_by_id(chat_id)
    if not chat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat not found"
        )
    return {"data": chat}

@router.post("", response_model=ApiResponse, status_code=status.HTTP_201_CREATED)
async def create_chat(request: CreateChatRequest):
    """Create a new chat."""
    try:
        chat = ChatService.create_chat(request.title)
        return {"data": chat}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.patch("/{chat_id}", response_model=ApiResponse)
async def update_chat(chat_id: str, request: UpdateChatRequest):
    """Update a chat."""
    updates = {}
    if request.title is not None:
        updates["title"] = request.title
    
    if not updates:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields to update"
        )
    
    chat = ChatService.update_chat(chat_id, updates)
    if not chat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat not found"
        )
    return {"data": chat}

@router.delete("/{chat_id}", response_model=ApiResponse)
async def delete_chat(chat_id: str):
    """Delete a chat and all its messages."""
    # Delete all messages first
    try:
        messages = MessageService.get_messages_by_chat_id(chat_id)
        for message in messages:
            MessageService.delete_message(chat_id, message['id'])
    except Exception:
        pass  # Continue even if message deletion fails
    
    deleted = ChatService.delete_chat(chat_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat not found"
        )
    return {"data": None}

