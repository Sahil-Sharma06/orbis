# Orbis

## Orbis - Project Overview

Orbis is a full-stack context graph system for business operations data.

It ingests CSV data for customers, products, orders, deliveries, invoices, payments, and addresses, stores it in SQLite, models relationships as a graph, renders the graph in a React UI, and supports natural-language analytics through a Gemini-powered chat endpoint.

Core capabilities:

- Batch-based ingestion with automatic `batch_1`, `batch_2`, ... tracking
- Merged or batch-specific graph visualization
- Data-grounded NL-to-SQL querying with SQL/result transparency
- Guardrails to reject off-topic or non-dataset questions

## Architecture Diagram (Text-Based)

```text
CSV Upload (frontend)
		|
		v
POST /api/ingest (FastAPI)
		|
		v
Pandas Parser -> Deduped Inserts -> SQLite (batch_id tagged rows)
		|
		+--------------------+
		|                    |
		v                    v
GET /api/graph      POST /api/chat
		|                    |
		|                    +-> Guardrails (keywords + Gemini intent fallback)
		|                    +-> Gemini (SQL JSON generation)
		|                    +-> SQLite SQL execution (SELECT-only, row-limited)
		|                    +-> Gemini grounded answer synthesis
		v                    v
Graph JSON          Chat response (answer + sql + data)
		|                    |
		+---------> React frontend (Cytoscape + chat panel)
```

## Database Schema

All tables include `batch_id` (`TEXT NOT NULL`) to preserve ingestion provenance.

- `customers(customer_id PK, name, email, phone, batch_id)`
- `addresses(address_id PK, street, city, country, batch_id)`
- `products(product_id PK, name, category, price, batch_id)`
- `orders(order_id PK, customer_id FK->customers, order_date, status, total_amount, batch_id)`
- `order_items(item_id PK, order_id FK->orders, product_id FK->products, quantity, unit_price, batch_id)`
- `deliveries(delivery_id PK, order_id FK->orders, address_id FK->addresses, delivery_date, status, batch_id)`
- `invoices(invoice_id PK, order_id FK->orders, invoice_date, amount, status, batch_id)`
- `payments(payment_id PK, invoice_id FK->invoices, payment_date, amount, method, batch_id)`

Startup behavior:

- DB schema is auto-created at application boot.
- If all domain tables are empty, `backend/data/seed.csv` is ingested automatically as `batch_1`.

## Graph Modeling Decisions

Node types:

- customer
- product
- order
- order_item
- delivery
- invoice
- payment
- address

Edge relationships:

- `customer -> order` (`PLACED`)
- `order -> order_item` (`CONTAINS`)
- `order_item -> product` (`REFERENCES`)
- `order -> delivery` (`HAS_DELIVERY`)
- `delivery -> address` (`DELIVERED_TO`)
- `order -> invoice` (`BILLED_AS`)
- `invoice -> payment` (`PAID_BY`)

Batch filtering behavior:

- `batch=merged` returns graph entities across all batches.
- `batch=batch_n` limits nodes/edges to rows tagged with that batch.

## LLM Prompting Strategy

The chat pipeline uses Gemini (`gemini-1.5-flash`) in two stages:

1. SQL generation:
	 - Prompt includes explicit schema and active batch context.
	 - Model must return strict JSON with keys `sql` and `answer`.
2. Grounded answer generation:
	 - SQL result rows are passed back to Gemini.
	 - Final answer must be concise and based only on returned data.

Safety and grounding controls:

- Batch-specific enforcement injects `batch_id` filtering when needed.
- Only `SELECT`/read-safe SQL is allowed.
- Unsafe SQL tokens are blocked.
- Default `LIMIT` is enforced when omitted.

## Guardrails Implementation

Guardrails are implemented in `backend/guardrails.py`.

Validation path:

1. Hard reject known off-topic prompts (poems, jokes, trivia, politics, basic arithmetic).
2. Allow known business-domain topics (orders, deliveries, invoices, payments, products, etc.).
3. For ambiguous messages, use Gemini intent classification (`RELATED` vs `NOT_RELATED`).
4. If not related, respond with:

`This system is designed to answer questions related to the provided dataset only.`

## API Endpoints

- `POST /api/ingest`
	- Multipart CSV upload
	- Returns `{"batch_id": "batch_n", "records_inserted": <int>}`

- `GET /api/batches`
	- Returns `{"batches": ["merged", "batch_1", ...]}`

- `GET /api/graph?batch=merged|batch_n`
	- Returns graph payload with nodes and edges

- `POST /api/chat`
	- Input: `{"message": "...", "batch": "merged|batch_n"}`
	- Output: `{"response": "...", "sql": "...", "data": [...]}`

## Local Setup (Backend)

From `backend/`:

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

Required environment variable for chat:

- `GEMINI_API_KEY=<your_google_ai_studio_key>`

Health check:

- `GET http://localhost:8000/health`

## Local Setup (Frontend)

From `frontend/`:

```bash
npm install
npm run dev
```

Environment configuration (`frontend/.env`):

```env
VITE_API_BASE_URL=http://localhost:8000
```

Frontend runs by default at:

- `http://localhost:5173`

## Deployment Guide (Render + Vercel)

### Backend on Render

Settings:

- Runtime: Python
- Root directory: `backend`
- Build command: `pip install -r requirements.txt`
- Start command: `uvicorn main:app --host 0.0.0.0 --port 8000`
- Env vars:
	- `GEMINI_API_KEY`

Also update CORS allow-list in `backend/main.py` with your Vercel URL.

### Frontend on Vercel

Settings:

- Root directory: `frontend`
- Build command: `npm run build`
- Output directory: `dist`
- Env vars:
	- `VITE_API_BASE_URL=https://<your-render-service>.onrender.com`

## Production Notes

- Keep Gemini API keys server-side only.
- Upload only trusted CSV structures matching required schema columns.
- SQLite is appropriate for lightweight workloads; migrate to managed Postgres for high concurrency.
- Add automated tests for ingestion mappings and NL query edge cases before scaling.
