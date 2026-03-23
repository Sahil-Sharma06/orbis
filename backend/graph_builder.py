from __future__ import annotations

import sqlite3
from typing import Any


TABLE_CONFIG = (
	("customers", "customer", "customer_id"),
	("products", "product", "product_id"),
	("orders", "order", "order_id"),
	("order_items", "order_item", "item_id"),
	("deliveries", "delivery", "delivery_id"),
	("invoices", "invoice", "invoice_id"),
	("payments", "payment", "payment_id"),
	("addresses", "address", "address_id"),
)


def build_graph_payload(conn: sqlite3.Connection, batch: str = "merged") -> dict[str, Any]:
	nodes: list[dict[str, Any]] = []
	edges: list[dict[str, str]] = []

	table_rows = {
		table_name: _fetch_rows(conn, table_name, batch)
		for table_name, _, _ in TABLE_CONFIG
	}

	for table_name, node_type, id_field in TABLE_CONFIG:
		for row in table_rows[table_name]:
			row_data = dict(row)
			row_id = row_data.get(id_field)
			if row_id is None:
				continue

			nodes.append(
				{
					"id": f"{node_type}_{row_id}",
					"label": str(row_id),
					"type": node_type,
					"data": row_data,
				}
			)

	edge_set: set[tuple[str, str, str]] = set()

	for row in table_rows["orders"]:
		if row["customer_id"]:
			edge_set.add(
				(
					f"customer_{row['customer_id']}",
					f"order_{row['order_id']}",
					"PLACED",
				)
			)

	for row in table_rows["order_items"]:
		edge_set.add(
			(
				f"order_{row['order_id']}",
				f"order_item_{row['item_id']}",
				"CONTAINS",
			)
		)
		if row["product_id"]:
			edge_set.add(
				(
					f"order_item_{row['item_id']}",
					f"product_{row['product_id']}",
					"REFERENCES",
				)
			)

	for row in table_rows["deliveries"]:
		edge_set.add(
			(
				f"order_{row['order_id']}",
				f"delivery_{row['delivery_id']}",
				"HAS_DELIVERY",
			)
		)
		if row["address_id"]:
			edge_set.add(
				(
					f"delivery_{row['delivery_id']}",
					f"address_{row['address_id']}",
					"DELIVERED_TO",
				)
			)

	for row in table_rows["invoices"]:
		edge_set.add(
			(
				f"order_{row['order_id']}",
				f"invoice_{row['invoice_id']}",
				"BILLED_AS",
			)
		)

	for row in table_rows["payments"]:
		if row["invoice_id"]:
			edge_set.add(
				(
					f"invoice_{row['invoice_id']}",
					f"payment_{row['payment_id']}",
					"PAID_BY",
				)
			)

	edges = [
		{"source": source, "target": target, "relationship": relationship}
		for source, target, relationship in sorted(edge_set)
	]

	return {"nodes": nodes, "edges": edges}


def _fetch_rows(conn: sqlite3.Connection, table_name: str, batch: str):
	if batch == "merged":
		return conn.execute(f"SELECT * FROM {table_name}").fetchall()
	return conn.execute(
		f"SELECT * FROM {table_name} WHERE batch_id = ?", (batch,)
	).fetchall()
