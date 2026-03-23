from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Callable


BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "orbis.db"
SEED_CSV_PATH = BASE_DIR / "data" / "seed.csv"


TABLES_SQL: tuple[str, ...] = (
	"""
	CREATE TABLE IF NOT EXISTS customers (
		customer_id TEXT PRIMARY KEY,
		name TEXT,
		email TEXT,
		phone TEXT,
		batch_id TEXT NOT NULL
	)
	""",
	"""
	CREATE TABLE IF NOT EXISTS addresses (
		address_id TEXT PRIMARY KEY,
		street TEXT,
		city TEXT,
		country TEXT,
		batch_id TEXT NOT NULL
	)
	""",
	"""
	CREATE TABLE IF NOT EXISTS products (
		product_id TEXT PRIMARY KEY,
		name TEXT,
		category TEXT,
		price REAL,
		batch_id TEXT NOT NULL
	)
	""",
	"""
	CREATE TABLE IF NOT EXISTS orders (
		order_id TEXT PRIMARY KEY,
		customer_id TEXT,
		order_date TEXT,
		status TEXT,
		total_amount REAL,
		batch_id TEXT NOT NULL,
		FOREIGN KEY(customer_id) REFERENCES customers(customer_id)
	)
	""",
	"""
	CREATE TABLE IF NOT EXISTS order_items (
		item_id TEXT PRIMARY KEY,
		order_id TEXT,
		product_id TEXT,
		quantity INTEGER,
		unit_price REAL,
		batch_id TEXT NOT NULL,
		FOREIGN KEY(order_id) REFERENCES orders(order_id),
		FOREIGN KEY(product_id) REFERENCES products(product_id)
	)
	""",
	"""
	CREATE TABLE IF NOT EXISTS deliveries (
		delivery_id TEXT PRIMARY KEY,
		order_id TEXT,
		address_id TEXT,
		delivery_date TEXT,
		status TEXT,
		batch_id TEXT NOT NULL,
		FOREIGN KEY(order_id) REFERENCES orders(order_id),
		FOREIGN KEY(address_id) REFERENCES addresses(address_id)
	)
	""",
	"""
	CREATE TABLE IF NOT EXISTS invoices (
		invoice_id TEXT PRIMARY KEY,
		order_id TEXT,
		invoice_date TEXT,
		amount REAL,
		status TEXT,
		batch_id TEXT NOT NULL,
		FOREIGN KEY(order_id) REFERENCES orders(order_id)
	)
	""",
	"""
	CREATE TABLE IF NOT EXISTS payments (
		payment_id TEXT PRIMARY KEY,
		invoice_id TEXT,
		payment_date TEXT,
		amount REAL,
		method TEXT,
		batch_id TEXT NOT NULL,
		FOREIGN KEY(invoice_id) REFERENCES invoices(invoice_id)
	)
	""",
)


def get_connection() -> sqlite3.Connection:
	conn = sqlite3.connect(DB_PATH)
	conn.row_factory = sqlite3.Row
	conn.execute("PRAGMA foreign_keys = ON")
	return conn


def init_db() -> None:
	with get_connection() as conn:
		for ddl in TABLES_SQL:
			conn.execute(ddl)
		_create_indexes(conn)
		conn.commit()


def _create_indexes(conn: sqlite3.Connection) -> None:
	for table in (
		"customers",
		"addresses",
		"products",
		"orders",
		"order_items",
		"deliveries",
		"invoices",
		"payments",
	):
		conn.execute(
			f"CREATE INDEX IF NOT EXISTS idx_{table}_batch_id ON {table}(batch_id)"
		)


def get_available_batches(conn: sqlite3.Connection | None = None) -> list[str]:
	own_conn = conn is None
	conn = conn or get_connection()
	try:
		query = " UNION ".join(
			f"SELECT DISTINCT batch_id FROM {table}"
			for table in (
				"customers",
				"addresses",
				"products",
				"orders",
				"order_items",
				"deliveries",
				"invoices",
				"payments",
			)
		)
		rows = conn.execute(query).fetchall()
		batches = sorted(
			{row["batch_id"] for row in rows if row["batch_id"]},
			key=_batch_sort_key,
		)
		return ["merged", *batches]
	finally:
		if own_conn:
			conn.close()


def get_next_batch_id(conn: sqlite3.Connection | None = None) -> str:
	own_conn = conn is None
	conn = conn or get_connection()
	try:
		batches = get_available_batches(conn)
		numeric_suffixes = []
		for batch in batches:
			if batch.startswith("batch_"):
				try:
					numeric_suffixes.append(int(batch.split("_", 1)[1]))
				except (IndexError, ValueError):
					continue
		next_idx = max(numeric_suffixes, default=0) + 1
		return f"batch_{next_idx}"
	finally:
		if own_conn:
			conn.close()


def is_database_empty(conn: sqlite3.Connection | None = None) -> bool:
	own_conn = conn is None
	conn = conn or get_connection()
	try:
		for table in (
			"customers",
			"addresses",
			"products",
			"orders",
			"order_items",
			"deliveries",
			"invoices",
			"payments",
		):
			count = conn.execute(f"SELECT COUNT(*) AS c FROM {table}").fetchone()["c"]
			if count > 0:
				return False
		return True
	finally:
		if own_conn:
			conn.close()


def _batch_sort_key(batch_id: str) -> tuple[int, str]:
	if not batch_id.startswith("batch_"):
		return (10**9, batch_id)
	try:
		return (int(batch_id.split("_", 1)[1]), batch_id)
	except (IndexError, ValueError):
		return (10**9, batch_id)


def ensure_seeded(seed_loader: Callable[[Path], dict] | None = None) -> bool:
	"""Seed the database once on startup if all domain tables are empty."""
	with get_connection() as conn:
		if not is_database_empty(conn):
			return False

	if seed_loader is None:
		return False

	seed_loader(SEED_CSV_PATH)
	return True
