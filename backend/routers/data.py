from typing import List

from fastapi import APIRouter, HTTPException

from schemas import DataPoint, DataPointCreate, DataPointUpdate, DataSummary
from services import data_service
from services.analysis_service import build_summary

router = APIRouter(prefix="/api/data", tags=["data"])


@router.post("", response_model=DataPoint)
def create_data(payload: DataPointCreate):
    return data_service.create_data_point(payload)


@router.get("", response_model=List[DataPoint])
def list_data():
    return data_service.list_data_points()


@router.get("/summary", response_model=DataSummary)
def get_summary():
    points = data_service.list_data_points()
    return build_summary(points)


@router.put("/{data_id}", response_model=DataPoint)
def update_data(data_id: str, payload: DataPointUpdate):
    try:
        return data_service.update_data_point(data_id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.delete("/{data_id}")
def delete_data(data_id: str):
    try:
        data_service.delete_data_point(data_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    return {"deleted": data_id}
