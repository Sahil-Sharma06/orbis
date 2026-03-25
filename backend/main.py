from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from database import BASE_DIR, init_db, is_database_empty
from ingestion import ingest_csv_path, ingest_sap_o2c_directory
from routes import chat_router, graph_router, ingest_router


# Load env from workspace root first, then backend-local .env if present.
load_dotenv(BASE_DIR.parent / ".env")
load_dotenv(BASE_DIR / ".env")


app = FastAPI(title="Orbis API", version="1.0.0")


app.add_middleware(
	CORSMiddleware,
	allow_origins=["*"],
	allow_credentials=True,
	allow_methods=["*"],
	allow_headers=["*"],
)

app.include_router(ingest_router)
app.include_router(graph_router)
app.include_router(chat_router)


@app.on_event("startup")
def startup_event() -> None:
	init_db()

	if not is_database_empty():
		return

	sap_data_dir = BASE_DIR / "data" / "sap-o2c-data"
	if sap_data_dir.exists() and any(sap_data_dir.rglob("*.jsonl")):
		ingest_sap_o2c_directory(Path(sap_data_dir), batch_id="batch_1")
	else:
		ingest_csv_path(BASE_DIR / "data" / "seed.csv", batch_id="batch_1")


@app.get("/health")
def healthcheck() -> dict[str, str]:
	return {"status": "ok"}
