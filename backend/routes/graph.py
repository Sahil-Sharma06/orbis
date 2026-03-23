from __future__ import annotations

from fastapi import APIRouter, Query

from database import get_connection
from graph_builder import build_graph_payload
from models import GraphResponse


router = APIRouter(prefix="/api", tags=["graph"])


@router.get("/graph", response_model=GraphResponse)
def get_graph(batch: str = Query(default="merged")) -> GraphResponse:
	with get_connection() as conn:
		payload = build_graph_payload(conn, batch=batch)
	return GraphResponse(**payload)
