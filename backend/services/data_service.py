from datetime import date as date_type
from typing import List

from firebase_client import get_db
from schemas import DataPoint, DataPointCreate, DataPointUpdate

COLLECTION = "data"


def _to_data_point(doc_id: str, d: dict) -> DataPoint:
    return DataPoint(
        id=doc_id,
        date=date_type.fromisoformat(d["date"]),
        value=d["value"],
        memo=d.get("memo"),
    )


def create_data_point(payload: DataPointCreate) -> DataPoint:
    db = get_db()
    doc_ref = db.collection(COLLECTION).document()
    doc_ref.set(
        {
            "date": payload.date.isoformat(),
            "value": payload.value,
            "memo": payload.memo,
        }
    )
    return DataPoint(id=doc_ref.id, date=payload.date, value=payload.value, memo=payload.memo)


def list_data_points() -> List[DataPoint]:
    db = get_db()
    docs = db.collection(COLLECTION).stream()
    points = [_to_data_point(doc.id, doc.to_dict()) for doc in docs]
    points.sort(key=lambda p: p.date)
    return points


def update_data_point(doc_id: str, payload: DataPointUpdate) -> DataPoint:
    db = get_db()
    doc_ref = db.collection(COLLECTION).document(doc_id)
    snapshot = doc_ref.get()
    if not snapshot.exists:
        raise ValueError("데이터를 찾을 수 없습니다.")

    updates = {}
    if payload.date is not None:
        updates["date"] = payload.date.isoformat()
    if payload.value is not None:
        updates["value"] = payload.value
    if payload.memo is not None:
        updates["memo"] = payload.memo

    if updates:
        doc_ref.update(updates)

    merged = snapshot.to_dict()
    merged.update(updates)
    return _to_data_point(doc_id, merged)


def delete_data_point(doc_id: str) -> None:
    db = get_db()
    doc_ref = db.collection(COLLECTION).document(doc_id)
    if not doc_ref.get().exists:
        raise ValueError("데이터를 찾을 수 없습니다.")
    doc_ref.delete()
