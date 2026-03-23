from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import ensure_seeded, init_db
from ingestion import ingest_csv_path
from routes import ingest_router


app = FastAPI(title="Orbis API", version="1.0.0")


app.add_middleware(
	CORSMiddleware,
	allow_origins=[
		"http://localhost:5173",
		"https://your-vercel-app.vercel.app",
	],
	allow_credentials=True,
	allow_methods=["*"],
	allow_headers=["*"],
)

app.include_router(ingest_router)


@app.on_event("startup")
def startup_event() -> None:
	init_db()
	ensure_seeded(seed_loader=lambda path: ingest_csv_path(path, batch_id="batch_1"))


@app.get("/health")
def healthcheck() -> dict[str, str]:
	return {"status": "ok"}
