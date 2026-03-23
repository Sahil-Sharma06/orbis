from __future__ import annotations

from fastapi import APIRouter, HTTPException

from guardrails import REJECTION_MESSAGE, is_business_query
from models import ChatRequest, ChatResponse
from query_engine import run_nl_query


router = APIRouter(prefix="/api", tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
	if not is_business_query(request.message):
		return ChatResponse(response=REJECTION_MESSAGE, sql=None, data=[])

	try:
		result = run_nl_query(request.message, batch=request.batch)
		return ChatResponse(**result)
	except Exception as exc:
		raise HTTPException(status_code=500, detail=f"Chat query failed: {exc}") from exc
