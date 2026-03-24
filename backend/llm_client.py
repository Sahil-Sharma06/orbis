from __future__ import annotations

import os

import httpx


DEFAULT_GEMINI_MODEL = "gemini-2.5-flash"
DEFAULT_GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta"


def gemini_chat(
	messages: list[dict[str, str]],
	model: str | None = None,
	temperature: float = 0.1,
	timeout_seconds: float = 60.0,
) -> str:
	api_key = os.getenv("GEMINI_API_KEY")
	if not api_key:
		raise ValueError("GEMINI_API_KEY is not configured")

	base_url = os.getenv("GEMINI_BASE_URL", DEFAULT_GEMINI_BASE_URL).rstrip("/")
	selected_model = model or os.getenv("GEMINI_MODEL", DEFAULT_GEMINI_MODEL)

	system_messages: list[str] = []
	contents: list[dict[str, object]] = []
	for message in messages:
		role = str(message.get("role", "user")).lower()
		content = str(message.get("content", "")).strip()
		if not content:
			continue

		if role == "system":
			system_messages.append(content)
			continue

		gemini_role = "model" if role == "assistant" else "user"
		contents.append({"role": gemini_role, "parts": [{"text": content}]})

	if not contents:
		raise ValueError("No valid chat messages were provided")

	payload = {
		"contents": contents,
		"generationConfig": {"temperature": temperature},
	}
	if system_messages:
		payload["systemInstruction"] = {
			"parts": [{"text": "\n\n".join(system_messages)}]
		}

	headers = {"Content-Type": "application/json"}

	with httpx.Client(timeout=timeout_seconds) as client:
		response = client.post(
			f"{base_url}/models/{selected_model}:generateContent",
			params={"key": api_key},
			json=payload,
			headers=headers,
		)

	if response.status_code >= 400:
		raise ValueError(
			f"Gemini request failed ({response.status_code}): {response.text}"
		)

	data = response.json()
	candidates = data.get("candidates") or []
	if not candidates:
		raise ValueError("Gemini response did not include candidates")

	parts = ((candidates[0].get("content") or {}).get("parts") or [])
	message = "".join(str(part.get("text", "")) for part in parts).strip()
	if not message:
		raise ValueError("Gemini response did not include message content")

	return message