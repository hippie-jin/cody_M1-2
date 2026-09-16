from typing import List

from fastapi import APIRouter, HTTPException

from schemas import Conversation, ConversationCreate, ConversationSummary
from services import conversation_service

router = APIRouter(prefix="/api/conversations", tags=["conversations"])


@router.post("")
def create_conversation(payload: ConversationCreate):
    conversation_id = conversation_service.create_conversation(payload.messages, payload.title)
    return {"id": conversation_id}


@router.get("", response_model=List[ConversationSummary])
def list_conversations():
    return conversation_service.list_conversations()


@router.get("/{conversation_id}", response_model=Conversation)
def get_conversation(conversation_id: str):
    try:
        return conversation_service.get_conversation(conversation_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.delete("/{conversation_id}")
def delete_conversation(conversation_id: str):
    try:
        conversation_service.delete_conversation(conversation_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    return {"deleted": conversation_id}
