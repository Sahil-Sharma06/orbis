from __future__ import annotations

import json
import os
import re
import sqlite3
from typing import Any

import google.generativeai as genai

from database import get_connection


SCHEMA_DESCRIPTION = """
customers(customer_id, name, email, phone, batch_id)
addresses(address_id, street, city, country, batch_id)
products(product_id, name, category, price, batch_id)
orders(order_id, customer_id, order_date, status, total_amount, batch_id)
order_items(item_id, order_id, product_id, quantity, unit_price, batch_id)
deliveries(delivery_id, order_id, address_id, delivery_date, status, batch_id)
invoices(invoice_id, order_id, invoice_date, amount, status, batch_id)
payments(payment_id, invoice_id, payment_date, amount, method, batch_id)
""".strip()


def run_nl_query(message: str, batch: str = "merged") -> dict[str, Any]:
	api_key = os.getenv("GEMINI_API_KEY")
	if not api_key:
		return {
			"response": "GEMINI_API_KEY is not configured. Please set it to enable chat queries.",
			"sql": None,
			"data": [],
		}

	genai.configure(api_key=api_key)
	model = genai.GenerativeModel("gemini-1.5-flash")

	sql_payload = _generate_sql(model, message, batch)
	sql = _normalize_sql(sql_payload.get("sql", ""), batch)
	rows = _execute_sql(sql)
	answer = _generate_grounded_answer(model, message, batch, sql, rows)

	return {"response": answer, "sql": sql, "data": rows}


def _generate_sql(model, message: str, batch: str) -> dict[str, str]:
	batch_context = (
		"merged (all batches)" if batch == "merged" else f"batch_id = '{batch}'"
	)
	system_prompt = (
		"You are a data analyst assistant for Orbis. You have access to a SQLite "
		f"database with the following schema: {SCHEMA_DESCRIPTION}. The user is currently "
		f"viewing data from: {batch_context}. Your job is to answer the user's question "
		"by writing a valid SQLite SQL query and returning the result as a natural "
		"language answer. Rules: 1) Only query the provided schema. 2) Never make up data. "
		"3) If you cannot answer from the data, say so. 4) Return your response strictly as "
		"JSON in this format: {'sql': 'your SQL here', 'answer': 'your explanation here'}. "
		"5) For batch-specific queries always add WHERE batch_id = '{batch_id}' unless the "
		"user is in merged view."
	)

	result = model.generate_content(
		[
			{"role": "user", "parts": [system_prompt]},
			{"role": "user", "parts": [f"User question: {message}"]},
		]
	)

	raw_text = (result.text or "").strip()
	payload = _extract_json(raw_text)
	if "sql" not in payload:
		raise ValueError("Model did not return SQL")
	return payload


def _normalize_sql(sql: str, batch: str) -> str:
	cleaned = (sql or "").strip().strip("`")
	if not cleaned:
		raise ValueError("Generated SQL is empty")

	cleaned = cleaned.rstrip(";")

	if batch == "merged" or "batch_id" in cleaned.lower():
		return f"{cleaned};"

	lower_sql = cleaned.lower()
	split_pattern = re.search(r"\b(group\s+by|order\s+by|having|limit)\b", lower_sql)

	if split_pattern:
		idx = split_pattern.start()
		base = cleaned[:idx].rstrip()
		tail = cleaned[idx:].lstrip()
	else:
		base = cleaned
		tail = ""

	if " where " in base.lower():
		base = f"{base} AND batch_id = '{batch}'"
	else:
		base = f"{base} WHERE batch_id = '{batch}'"

	final_sql = f"{base} {tail}".strip()
	return f"{final_sql};"


def _execute_sql(sql: str) -> list[dict[str, Any]]:
	with get_connection() as conn:
		cursor = conn.execute(sql)
		rows = cursor.fetchall()
		return [dict(row) for row in rows]


def _generate_grounded_answer(
	model,
	user_message: str,
	batch: str,
	sql: str,
	rows: list[dict[str, Any]],
) -> str:
	prompt = (
		"You are Orbis, a data analyst assistant. Generate a concise answer grounded "
		"strictly in the SQL results. If rows are empty, clearly say the dataset has no "
		"matching records. Do not invent facts.\n"
		f"User message: {user_message}\n"
		f"Batch context: {batch}\n"
		f"SQL: {sql}\n"
		f"Rows: {json.dumps(rows)}"
	)
	response = model.generate_content(prompt)
	return (response.text or "No answer available.").strip()


def _extract_json(raw_text: str) -> dict[str, str]:
	if raw_text.startswith("```"):
		raw_text = raw_text.strip("`")
		raw_text = raw_text.replace("json", "", 1).strip()

	try:
		return json.loads(raw_text)
	except json.JSONDecodeError:
		match = re.search(r"\{.*\}", raw_text, re.DOTALL)
		if not match:
			raise
		return json.loads(match.group(0))
