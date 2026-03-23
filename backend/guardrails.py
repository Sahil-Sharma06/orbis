from __future__ import annotations

import os

from llm_client import grok_chat


REJECTION_MESSAGE = (
	"This system is designed to answer questions related to the provided dataset only."
)

DEFAULT_GROK_MODEL = "grok-3-mini"

ALLOWED_TOPICS = {
	"order",
	"orders",
	"delivery",
	"deliveries",
	"invoice",
	"invoices",
	"payment",
	"payments",
	"customer",
	"customers",
	"product",
	"products",
	"billing",
	"shipment",
	"shipments",
	"sales",
	"purchase",
	"purchases",
	"revenue",
	"supply chain",
	"batch",
}

BLOCKED_PATTERNS = {
	"write me a poem",
	"who is the president",
	"what is 2+2",
	"tell me a joke",
}


def is_business_query(message: str) -> bool:
	text = (message or "").strip().lower()
	if not text:
		return False

	if any(pattern in text for pattern in BLOCKED_PATTERNS):
		return False

	if _contains_any_allowed_topic(text):
		return True

	return _classify_with_grok(text)


def _contains_any_allowed_topic(text: str) -> bool:
	return any(topic in text for topic in ALLOWED_TOPICS)


def _classify_with_grok(text: str) -> bool:
	api_key = os.getenv("GROK_API_KEY")
	if not api_key:
		# Fail closed if no keyword match and classifier is unavailable.
		return False

	prompt = (
		"Classify the following user query as RELATED or NOT_RELATED to business data "
		"analysis over orders, deliveries, invoices, payments, customers, products, "
		"addresses, sales, billing, and supply chain. Respond with one token only: "
		"RELATED or NOT_RELATED. Query: "
		f"{text}"
	)
	try:
		answer = grok_chat(
			messages=[
				{
					"role": "system",
					"content": "You are an intent classifier. Return one token only: RELATED or NOT_RELATED.",
				},
				{"role": "user", "content": prompt},
			],
			model=os.getenv("GROK_MODEL", DEFAULT_GROK_MODEL),
			temperature=0,
		).strip().upper()
		return answer.startswith("RELATED")
	except Exception:
		return False
