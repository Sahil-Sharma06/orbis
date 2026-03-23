from __future__ import annotations

import json
import os
import re
from typing import Any

from database import get_connection
from llm_client import DEFAULT_GROK_MODEL, grok_chat


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
	api_key = os.getenv("GROK_API_KEY")
	if not api_key:
		return {
			"response": "GROK_API_KEY is not configured. Please set it to enable chat queries.",
			"sql": None,
			"data": [],
		}

	try:
		model_name = os.getenv("GROK_MODEL", DEFAULT_GROK_MODEL)

		sql_payload = _generate_sql(message, batch, model_name)
		sql = _normalize_sql(sql_payload.get("sql", ""), batch)
		rows = _execute_sql(sql)
		answer = _generate_grounded_answer(message, batch, sql, rows, model_name)

		return {"response": answer, "sql": sql, "data": rows}
	except Exception as exc:
		return {
			"response": _friendly_llm_error(str(exc)),
			"sql": None,
			"data": [],
		}


def _friendly_llm_error(error_text: str) -> str:
	text = (error_text or "").lower()
	if "quota" in text or "429" in text or "rate limit" in text:
		return (
			"Grok quota is currently exhausted for this API key. "
			"Please check xAI usage/billing or try again later."
		)
	if "401" in text or "unauthorized" in text or "invalid api key" in text:
		return "Grok API key appears invalid or unauthorized. Please verify GROK_API_KEY."
	if "403" in text or "does not have permission" in text or "credits" in text:
		return (
			"Grok API key is valid but this xAI team has no active credits/license. "
			"Add credits in xAI console, then retry."
		)
	if "model" in text and "not found" in text:
		return (
			"Configured Grok model is unavailable for this key. "
			"Set GROK_MODEL to a supported model, e.g. grok-3-mini."
		)
	if "404" in text and "chat/completions" in text:
		return (
			"xAI API endpoint is not reachable with current settings. "
			"Check XAI_BASE_URL (default should be https://api.x.ai/v1)."
		)
	return "Unable to process the question with Grok right now. Please try again shortly."


def _generate_sql(message: str, batch: str, model_name: str) -> dict[str, str]:
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

	raw_text = grok_chat(
		messages=[
			{"role": "system", "content": "You are a precise SQL generation assistant."},
			{"role": "user", "content": system_prompt},
			{"role": "user", "content": f"User question: {message}"},
		],
		model=model_name,
		temperature=0,
	)

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
	final_sql = _ensure_select_only(final_sql)
	final_sql = _ensure_limit(final_sql, max_rows=200)
	return f"{final_sql.rstrip(';')};"


def _execute_sql(sql: str) -> list[dict[str, Any]]:
	with get_connection() as conn:
		cursor = conn.execute(sql)
		rows = cursor.fetchall()
		return [dict(row) for row in rows]


def _ensure_select_only(sql: str) -> str:
	candidate = sql.strip()
	lowered = candidate.lower()
	if not lowered.startswith("select") and not lowered.startswith("with"):
		raise ValueError("Only SELECT queries are allowed")

	blocked = [
		" insert ",
		" update ",
		" delete ",
		" drop ",
		" alter ",
		" create ",
		" attach ",
		" detach ",
		" pragma ",
		" vacuum ",
	]
	wrapped = f" {lowered} "
	if any(token in wrapped for token in blocked):
		raise ValueError("Unsafe SQL operation detected")
	return candidate


def _ensure_limit(sql: str, max_rows: int = 200) -> str:
	lowered = sql.lower()
	if " limit " in f" {lowered} ":
		return sql
	return f"{sql.rstrip(';')} LIMIT {max_rows}"


def _generate_grounded_answer(
	user_message: str,
	batch: str,
	sql: str,
	rows: list[dict[str, Any]],
	model_name: str,
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
	response = grok_chat(
		[
			{"role": "system", "content": "You are a grounded data analysis assistant."},
			{"role": "user", "content": prompt},
		],
		model=model_name,
		temperature=0.1,
	)
	return response or "No answer available."


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
