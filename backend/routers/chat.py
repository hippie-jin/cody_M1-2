from fastapi import APIRouter, HTTPException

from schemas import ChatRequest, ChatResponse
from services import chat_service

router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
def chat(payload: ChatRequest):
    try:
        reply, conversation_id = chat_service.ask(payload.message, payload.conversation_id)
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    return ChatResponse(reply=reply, conversation_id=conversation_id)
