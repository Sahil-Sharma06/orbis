from __future__ import annotations

from io import BytesIO
from pathlib import Path
import sqlite3

import pandas as pd

from database import get_connection, get_next_batch_id


REQUIRED_COLUMNS = {
	"customer_id",
	"name",
	"email",
	"phone",
	"address_id",
	"street",
	"city",
	"country",
	"order_id",
	"order_date",
	"order_status",
	"total_amount",
	"item_id",
	"product_id",
	"product_name",
	"category",
	"price",
	"quantity",
	"unit_price",
	"delivery_id",
	"delivery_date",
	"delivery_status",
	"invoice_id",
	"invoice_date",
	"invoice_amount",
	"invoice_status",
	"payment_id",
	"payment_date",
	"payment_amount",
	"payment_method",
}


def ingest_csv_bytes(content: bytes, batch_id: str | None = None) -> dict:
	dataframe = pd.read_csv(BytesIO(content))
	return ingest_dataframe(dataframe, batch_id=batch_id)


def ingest_csv_path(csv_path: Path, batch_id: str | None = None) -> dict:
	dataframe = pd.read_csv(csv_path)
	return ingest_dataframe(dataframe, batch_id=batch_id)


def ingest_dataframe(dataframe: pd.DataFrame, batch_id: str | None = None) -> dict:
	_validate_columns(dataframe)
	cleaned = dataframe.where(pd.notnull(dataframe), None)

	with get_connection() as conn:
		batch_id = batch_id or get_next_batch_id(conn)
		records_inserted = _insert_all(cleaned, conn, batch_id)
		conn.commit()

	return {"batch_id": batch_id, "records_inserted": records_inserted}


def _validate_columns(dataframe: pd.DataFrame) -> None:
	incoming_columns = set(dataframe.columns)
	missing = REQUIRED_COLUMNS - incoming_columns
	if missing:
		missing_list = ", ".join(sorted(missing))
		raise ValueError(f"CSV is missing required columns: {missing_list}")


def _insert_all(df: pd.DataFrame, conn: sqlite3.Connection, batch_id: str) -> int:
	inserted = 0

	for row in df.to_dict(orient="records"):
		inserted += _insert_customer(conn, row, batch_id)
		inserted += _insert_address(conn, row, batch_id)
		inserted += _insert_product(conn, row, batch_id)
		inserted += _insert_order(conn, row, batch_id)
		inserted += _insert_order_item(conn, row, batch_id)
		inserted += _insert_delivery(conn, row, batch_id)
		inserted += _insert_invoice(conn, row, batch_id)
		inserted += _insert_payment(conn, row, batch_id)

	return inserted


def _insert_customer(conn: sqlite3.Connection, row: dict, batch_id: str) -> int:
	return _execute_insert(
		conn,
		"""
		INSERT OR IGNORE INTO customers (customer_id, name, email, phone, batch_id)
		VALUES (?, ?, ?, ?, ?)
		""",
		(
			row.get("customer_id"),
			row.get("name"),
			row.get("email"),
			row.get("phone"),
			batch_id,
		),
		required=row.get("customer_id"),
	)


def _insert_address(conn: sqlite3.Connection, row: dict, batch_id: str) -> int:
	return _execute_insert(
		conn,
		"""
		INSERT OR IGNORE INTO addresses (address_id, street, city, country, batch_id)
		VALUES (?, ?, ?, ?, ?)
		""",
		(
			row.get("address_id"),
			row.get("street"),
			row.get("city"),
			row.get("country"),
			batch_id,
		),
		required=row.get("address_id"),
	)


def _insert_product(conn: sqlite3.Connection, row: dict, batch_id: str) -> int:
	return _execute_insert(
		conn,
		"""
		INSERT OR IGNORE INTO products (product_id, name, category, price, batch_id)
		VALUES (?, ?, ?, ?, ?)
		""",
		(
			row.get("product_id"),
			row.get("product_name"),
			row.get("category"),
			_to_float(row.get("price")),
			batch_id,
		),
		required=row.get("product_id"),
	)


def _insert_order(conn: sqlite3.Connection, row: dict, batch_id: str) -> int:
	return _execute_insert(
		conn,
		"""
		INSERT OR IGNORE INTO orders (order_id, customer_id, order_date, status, total_amount, batch_id)
		VALUES (?, ?, ?, ?, ?, ?)
		""",
		(
			row.get("order_id"),
			row.get("customer_id"),
			row.get("order_date"),
			row.get("order_status"),
			_to_float(row.get("total_amount")),
			batch_id,
		),
		required=row.get("order_id"),
	)


def _insert_order_item(conn: sqlite3.Connection, row: dict, batch_id: str) -> int:
	return _execute_insert(
		conn,
		"""
		INSERT OR IGNORE INTO order_items (item_id, order_id, product_id, quantity, unit_price, batch_id)
		VALUES (?, ?, ?, ?, ?, ?)
		""",
		(
			row.get("item_id"),
			row.get("order_id"),
			row.get("product_id"),
			_to_int(row.get("quantity")),
			_to_float(row.get("unit_price")),
			batch_id,
		),
		required=row.get("item_id"),
	)


def _insert_delivery(conn: sqlite3.Connection, row: dict, batch_id: str) -> int:
	return _execute_insert(
		conn,
		"""
		INSERT OR IGNORE INTO deliveries (delivery_id, order_id, address_id, delivery_date, status, batch_id)
		VALUES (?, ?, ?, ?, ?, ?)
		""",
		(
			row.get("delivery_id"),
			row.get("order_id"),
			row.get("address_id"),
			row.get("delivery_date"),
			row.get("delivery_status"),
			batch_id,
		),
		required=row.get("delivery_id"),
	)


def _insert_invoice(conn: sqlite3.Connection, row: dict, batch_id: str) -> int:
	return _execute_insert(
		conn,
		"""
		INSERT OR IGNORE INTO invoices (invoice_id, order_id, invoice_date, amount, status, batch_id)
		VALUES (?, ?, ?, ?, ?, ?)
		""",
		(
			row.get("invoice_id"),
			row.get("order_id"),
			row.get("invoice_date"),
			_to_float(row.get("invoice_amount")),
			row.get("invoice_status"),
			batch_id,
		),
		required=row.get("invoice_id"),
	)


def _insert_payment(conn: sqlite3.Connection, row: dict, batch_id: str) -> int:
	return _execute_insert(
		conn,
		"""
		INSERT OR IGNORE INTO payments (payment_id, invoice_id, payment_date, amount, method, batch_id)
		VALUES (?, ?, ?, ?, ?, ?)
		""",
		(
			row.get("payment_id"),
			row.get("invoice_id"),
			row.get("payment_date"),
			_to_float(row.get("payment_amount")),
			row.get("payment_method"),
			batch_id,
		),
		required=row.get("payment_id"),
	)


def _execute_insert(
	conn: sqlite3.Connection,
	sql: str,
	params: tuple,
	required: str | None,
) -> int:
	if required is None or str(required).strip() == "":
		return 0
	cursor = conn.execute(sql, params)
	return 1 if cursor.rowcount > 0 else 0


def _to_float(value) -> float | None:
	if value is None or str(value).strip() == "":
		return None
	return float(value)


def _to_int(value) -> int | None:
	if value is None or str(value).strip() == "":
		return None
	return int(value)
