from __future__ import annotations

import json
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


def ingest_sap_o2c_directory(root_dir: Path, batch_id: str | None = None) -> dict:
	if not root_dir.exists():
		raise ValueError(f"SAP data directory not found: {root_dir}")

	partners = _read_jsonl_records(root_dir / "business_partners")
	partner_addresses = _read_jsonl_records(root_dir / "business_partner_addresses")
	products = _read_jsonl_records(root_dir / "products")
	product_descriptions = _read_jsonl_records(root_dir / "product_descriptions")
	sales_order_headers = _read_jsonl_records(root_dir / "sales_order_headers")
	sales_order_items = _read_jsonl_records(root_dir / "sales_order_items")
	delivery_headers = _read_jsonl_records(root_dir / "outbound_delivery_headers")
	delivery_items = _read_jsonl_records(root_dir / "outbound_delivery_items")
	billing_headers = _read_jsonl_records(root_dir / "billing_document_headers")
	billing_items = _read_jsonl_records(root_dir / "billing_document_items")
	payments = _read_jsonl_records(root_dir / "payments_accounts_receivable")

	delivery_to_order = _build_delivery_to_order_map(delivery_items)
	billing_to_order = _build_billing_to_order_map(billing_items, delivery_to_order)
	accounting_to_invoice = {
		str(row.get("accountingDocument")): str(row.get("billingDocument"))
		for row in billing_headers
		if row.get("accountingDocument") and row.get("billingDocument")
	}
	description_by_product = {
		str(row.get("product")): str(row.get("productDescription"))
		for row in product_descriptions
		if row.get("product") and row.get("productDescription")
	}

	customer_to_address: dict[str, str] = {}
	for row in partner_addresses:
		business_partner = _to_str(row.get("businessPartner"))
		address_id = _to_str(row.get("addressId"))
		if business_partner and address_id and business_partner not in customer_to_address:
			customer_to_address[business_partner] = address_id

	order_to_customer = {
		_to_str(row.get("salesOrder")): _to_str(row.get("soldToParty"))
		for row in sales_order_headers
		if row.get("salesOrder") and row.get("soldToParty")
	}

	with get_connection() as conn:
		batch_id = batch_id or get_next_batch_id(conn)
		records_inserted = 0

		for row in partners:
			customer_id = _to_str(row.get("customer") or row.get("businessPartner"))
			records_inserted += _insert_customer(
				conn,
				{
					"customer_id": customer_id,
					"name": _to_str(
						row.get("businessPartnerFullName")
						or row.get("businessPartnerName")
						or row.get("organizationBpName1")
					),
					"email": None,
					"phone": None,
				},
				batch_id,
			)

		for row in partner_addresses:
			records_inserted += _insert_address(
				conn,
				{
					"address_id": _to_str(row.get("addressId")),
					"street": _to_str(row.get("streetName") or row.get("poBox")),
					"city": _to_str(row.get("cityName")),
					"country": _to_str(row.get("country")),
				},
				batch_id,
			)

		for row in products:
			product_id = _to_str(row.get("product"))
			records_inserted += _insert_product(
				conn,
				{
					"product_id": product_id,
					"product_name": _to_str(
						description_by_product.get(product_id)
						or row.get("productOldId")
						or row.get("product")
					),
					"category": _to_str(row.get("productType") or row.get("productGroup")),
					"price": None,
				},
				batch_id,
			)

		for row in sales_order_headers:
			records_inserted += _insert_order(
				conn,
				{
					"order_id": _to_str(row.get("salesOrder")),
					"customer_id": _to_str(row.get("soldToParty")),
					"order_date": _to_date_str(row.get("creationDate")),
					"order_status": _to_str(
						row.get("overallDeliveryStatus")
						or row.get("overallOrdReltdBillgStatus")
						or "UNKNOWN"
					),
					"total_amount": row.get("totalNetAmount"),
				},
				batch_id,
			)

		for row in sales_order_items:
			order_id = _to_str(row.get("salesOrder"))
			item_number = _to_str(row.get("salesOrderItem"))
			quantity = _to_float(row.get("requestedQuantity"))
			net_amount = _to_float(row.get("netAmount"))
			unit_price = _safe_div(net_amount, quantity)

			records_inserted += _insert_order_item(
				conn,
				{
					"item_id": f"{order_id}_{item_number}" if order_id and item_number else None,
					"order_id": order_id,
					"product_id": _to_str(row.get("material")),
					"quantity": row.get("requestedQuantity"),
					"unit_price": unit_price,
				},
				batch_id,
			)

		for row in delivery_headers:
			delivery_id = _to_str(row.get("deliveryDocument"))
			order_id = delivery_to_order.get(delivery_id)
			address_id = customer_to_address.get(order_to_customer.get(order_id, ""), None)

			records_inserted += _insert_delivery(
				conn,
				{
					"delivery_id": delivery_id,
					"order_id": order_id,
					"address_id": address_id,
					"delivery_date": _to_date_str(row.get("creationDate")),
					"delivery_status": _to_str(
						row.get("overallGoodsMovementStatus")
						or row.get("hdrGeneralIncompletionStatus")
						or "UNKNOWN"
					),
				},
				batch_id,
			)

		for row in billing_headers:
			invoice_id = _to_str(row.get("billingDocument"))
			records_inserted += _insert_invoice(
				conn,
				{
					"invoice_id": invoice_id,
					"order_id": billing_to_order.get(invoice_id),
					"invoice_date": _to_date_str(row.get("billingDocumentDate") or row.get("creationDate")),
					"invoice_amount": row.get("totalNetAmount"),
					"invoice_status": "cancelled"
					if row.get("billingDocumentIsCancelled")
					else "active",
				},
				batch_id,
			)

		for row in payments:
			accounting_document = _to_str(row.get("accountingDocument"))
			invoice_id = _to_str(
				row.get("invoiceReference")
				or accounting_to_invoice.get(accounting_document)
				or accounting_to_invoice.get(_to_str(row.get("clearingAccountingDocument")))
			)
			payment_id = _to_str(
				f"{accounting_document}_{_to_str(row.get('accountingDocumentItem'))}"
				if accounting_document and row.get("accountingDocumentItem")
				else accounting_document
			)

			records_inserted += _insert_payment(
				conn,
				{
					"payment_id": payment_id,
					"invoice_id": invoice_id,
					"payment_date": _to_date_str(row.get("postingDate") or row.get("documentDate")),
					"payment_amount": row.get("amountInTransactionCurrency"),
					"payment_method": _to_str(row.get("financialAccountType") or "AR"),
				},
				batch_id,
			)

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


def _to_str(value) -> str | None:
	if value is None:
		return None
	result = str(value).strip()
	return result if result else None


def _to_date_str(value) -> str | None:
	text = _to_str(value)
	if text is None:
		return None
	return text.split("T", 1)[0]


def _safe_div(numerator: float | None, denominator: float | None) -> float | None:
	if numerator is None or denominator in (None, 0):
		return None
	return numerator / denominator


def _read_jsonl_records(folder: Path) -> list[dict]:
	if not folder.exists():
		return []

	records: list[dict] = []
	for jsonl_file in sorted(folder.glob("*.jsonl")):
		with jsonl_file.open("r", encoding="utf-8") as handle:
			for line in handle:
				line = line.strip()
				if not line:
					continue
				records.append(json.loads(line))
	return records


def _build_delivery_to_order_map(delivery_items: list[dict]) -> dict[str, str]:
	mapping: dict[str, str] = {}
	for item in delivery_items:
		delivery_id = _to_str(item.get("deliveryDocument"))
		order_id = _to_str(item.get("referenceSdDocument"))
		if delivery_id and order_id and delivery_id not in mapping:
			mapping[delivery_id] = order_id
	return mapping


def _build_billing_to_order_map(
	billing_items: list[dict],
	delivery_to_order: dict[str, str],
) -> dict[str, str]:
	mapping: dict[str, str] = {}
	for item in billing_items:
		billing_id = _to_str(item.get("billingDocument"))
		reference_document = _to_str(item.get("referenceSdDocument"))
		if not billing_id or not reference_document:
			continue

		order_id = delivery_to_order.get(reference_document)
		if order_id and billing_id not in mapping:
			mapping[billing_id] = order_id
	return mapping
