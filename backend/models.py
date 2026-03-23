from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class IngestResponse(BaseModel):
	batch_id: str
	records_inserted: int


class BatchesResponse(BaseModel):
	batches: list[str]


class GraphNode(BaseModel):
	id: str
	label: str
	type: str
	data: dict[str, Any]


class GraphEdge(BaseModel):
	source: str
	target: str
	relationship: str


class GraphResponse(BaseModel):
	nodes: list[GraphNode]
	edges: list[GraphEdge]


class ChatRequest(BaseModel):
	message: str = Field(min_length=1)
	batch: str = "merged"


class ChatResponse(BaseModel):
	response: str
	sql: str | None = None
	data: list[dict[str, Any]] | None = None
