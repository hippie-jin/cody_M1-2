from datetime import datetime, timezone
from typing import List, Optional

from firebase_admin import firestore

from firebase_client import get_db
from schemas import ChatMessage, Conversation, ConversationSummary

COLLECTION = "conversations"


def create_conversation(messages: List[ChatMessage], title: Optional[str] = None) -> str:
    db = get_db()
    doc_ref = db.collection(COLLECTION).document()
    resolved_title = title or (messages[0].content[:30] if messages else "새 대화")
    doc_ref.set(
        {
            "title": resolved_title,
            "messages": [m.model_dump() for m in messages],
            "created_at": datetime.now(timezone.utc),
        }
    )
    return doc_ref.id


def append_messages(conversation_id: str, messages: List[ChatMessage]) -> None:
    db = get_db()
    doc_ref = db.collection(COLLECTION).document(conversation_id)
    snapshot = doc_ref.get()
    if not snapshot.exists:
        raise ValueError("대화를 찾을 수 없습니다.")
    existing = snapshot.to_dict().get("messages", [])
    existing.extend([m.model_dump() for m in messages])
    doc_ref.update({"messages": existing})


def list_conversations() -> List[ConversationSummary]:
    db = get_db()
    docs = (
        db.collection(COLLECTION)
        .order_by("created_at", direction=firestore.Query.DESCENDING)
        .stream()
    )
    result = []
    for doc in docs:
        d = doc.to_dict()
        result.append(
            ConversationSummary(
                id=doc.id,
                title=d.get("title", "제목 없음"),
                created_at=d.get("created_at"),
                message_count=len(d.get("messages", [])),
            )
        )
    return result


def get_conversation(conversation_id: str) -> Conversation:
    db = get_db()
    doc_ref = db.collection(COLLECTION).document(conversation_id)
    snapshot = doc_ref.get()
    if not snapshot.exists:
        raise ValueError("대화를 찾을 수 없습니다.")
    d = snapshot.to_dict()
    return Conversation(
        id=doc_ref.id,
        title=d.get("title", "제목 없음"),
        created_at=d.get("created_at"),
        messages=[ChatMessage(**m) for m in d.get("messages", [])],
    )


def delete_conversation(conversation_id: str) -> None:
    db = get_db()
    doc_ref = db.collection(COLLECTION).document(conversation_id)
    if not doc_ref.get().exists:
        raise ValueError("대화를 찾을 수 없습니다.")
    doc_ref.delete()
