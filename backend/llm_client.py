from __future__ import annotations

import os

import httpx


DEFAULT_GROK_MODEL = "grok-3-mini"
DEFAULT_XAI_BASE_URL = "https://api.x.ai/v1"


def grok_chat(
	messages: list[dict[str, str]],
	model: str | None = None,
	temperature: float = 0.1,
	timeout_seconds: float = 60.0,
) -> str:
	api_key = os.getenv("GROK_API_KEY")
	if not api_key:
		raise ValueError("GROK_API_KEY is not configured")

	base_url = os.getenv("XAI_BASE_URL", DEFAULT_XAI_BASE_URL).rstrip("/")
	selected_model = model or os.getenv("GROK_MODEL", DEFAULT_GROK_MODEL)

	payload = {
		"model": selected_model,
		"messages": messages,
		"temperature": temperature,
	}

	headers = {
		"Authorization": f"Bearer {api_key}",
		"Content-Type": "application/json",
	}

	with httpx.Client(timeout=timeout_seconds) as client:
		response = client.post(f"{base_url}/chat/completions", json=payload, headers=headers)

	if response.status_code >= 400:
		raise ValueError(f"xAI request failed ({response.status_code}): {response.text}")

	data = response.json()
	choices = data.get("choices") or []
	if not choices:
		raise ValueError("xAI response did not include choices")

	message = (choices[0].get("message") or {}).get("content")
	if not message:
		raise ValueError("xAI response did not include message content")

	return str(message).strip()