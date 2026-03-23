from __future__ import annotations

from fastapi import APIRouter, File, HTTPException, UploadFile

from database import get_available_batches
from ingestion import ingest_csv_bytes
from models import BatchesResponse, IngestResponse


router = APIRouter(prefix="/api", tags=["ingest"])


@router.post("/ingest", response_model=IngestResponse)
async def ingest_csv(file: UploadFile = File(...)) -> IngestResponse:
	if not file.filename or not file.filename.lower().endswith(".csv"):
		raise HTTPException(status_code=400, detail="Only CSV files are supported")

	content = await file.read()
	if not content:
		raise HTTPException(status_code=400, detail="Uploaded file is empty")

	try:
		result = ingest_csv_bytes(content)
	except ValueError as exc:
		raise HTTPException(status_code=400, detail=str(exc)) from exc
	except Exception as exc:
		raise HTTPException(status_code=500, detail="Failed to ingest CSV") from exc

	return IngestResponse(**result)


@router.get("/batches", response_model=BatchesResponse)
def list_batches() -> BatchesResponse:
	return BatchesResponse(batches=get_available_batches())
