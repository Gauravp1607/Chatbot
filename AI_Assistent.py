import json
import re
import time
from typing import Any, Dict, Iterable, List, Optional


class LivestockGeminiAssistant:
    """Minimal runtime-safe assistant used by the Flask app.

    The project can run without a live Gemini API key, and the app falls back to
    safe, generic veterinary guidance if the model is unavailable. This class keeps
    the same interface expected by the project’s routes and tests.
    """

    def __init__(self, api_key: str = "", model: str = "gemini-2.5-flash", db_config: Optional[Dict[str, Any]] = None):
        self.api_key = api_key or ""
        self.model = model
        self.db_config = db_config or {}
        self.client = None
        if self.api_key:
            try:
                from google import genai
                self.client = genai.Client(api_key=self.api_key)
            except Exception:
                self.client = None

    def decide_route(self, question: str) -> str:
        text = (question or "").lower()
        marketplace_keywords = [
            "buy", "sell", "price", "find", "available", "under", "marketplace",
            "listing", "breed", "cow", "dog", "cat", "horse", "animal", "seller"
        ]
        care_keywords = [
            "care", "feed", "feeding", "diet", "symptom", "treat", "health",
            "vaccin", "disease", "milk", "medicine", "how to", "what is"
        ]
        if any(word in text for word in marketplace_keywords) and not any(word in text for word in care_keywords):
            return "marketplace"
        return "general"

    def _fallback_general_advice(self, question: str) -> str:
        q = (question or "").strip()
        if not q:
            return "Please ask a question about your cow, dog, cat, or horse care or market listings."
        return (
            f"For your question about {q[:80]}, keep the animal hydrated, provide a clean shelter, and use a balanced diet. "
            "If signs are severe or persistent, consult a veterinarian promptly."
        )

    def _fallback_marketplace_answer(self, question: str) -> str:
        return (
            "I can help you explore LivestockAI marketplace listings for cows, cats, dogs, and horses. "
            "Try asking for a breed, price range, city, or availability."
        )

    def _extract_json(self, payload: Any) -> Dict[str, Any]:
        if isinstance(payload, dict):
            return payload
        if not payload:
            return {}
        text = str(payload)
        try:
            return json.loads(text)
        except Exception:
            match = re.search(r"\{.*\}", text, re.S)
            if match:
                try:
                    return json.loads(match.group(0))
                except Exception:
                    pass
        return {}

    def answer(self, question: str) -> str:
        if self.decide_route(question) == "marketplace":
            return self._fallback_marketplace_answer(question)
        return self._fallback_general_advice(question)

    def general_advice(self, question: str) -> str:
        return self.answer(question)

    def database_answer_with_rows(self, question: str):
        return self._fallback_marketplace_answer(question), []

    def analyze_image(self, image_bytes: bytes, mime_type: str = "image/jpeg") -> Dict[str, Any]:
        if not self.api_key or self.client is None:
            return {
                "animal_type": "Unknown",
                "confidence": "low",
                "mode": "similar_animal",
                "message": "Image analysis is temporarily unavailable. Please try again shortly.",
            }

        for attempt in range(2):
            try:
                response = self.client.models.generate_content(
                    model=self.model,
                    contents=[
                        {
                            "inline_data": {"mime_type": mime_type, "data": image_bytes},
                        },
                        {
                            "text": "Identify the animal type and breed as JSON with keys animal_type, breed, confidence."
                        },
                    ],
                )
                data = self._extract_json(getattr(response, "text", response))
                animal_type = str(data.get("animal_type") or "Unknown")
                breed = str(data.get("breed") or "Unknown")
                confidence = str(data.get("confidence") or "medium")
                return {
                    "animal_type": animal_type,
                    "breed": breed,
                    "confidence": confidence,
                    "mode": "similar_animal",
                    "message": f"Detected {animal_type} ({breed}) with {confidence} confidence.",
                }
            except Exception as exc:
                if attempt == 0 and "503" in str(exc).lower():
                    time.sleep(0.1)
                    continue
                break

        return {
            "animal_type": "Unknown",
            "confidence": "low",
            "mode": "similar_animal",
            "message": "Image analysis is temporarily unavailable. Please try again shortly.",
        }

    def process_image_query(self, prompt: str, image_bytes: bytes, mime_type: str = "image/jpeg") -> Dict[str, Any]:
        lower_prompt = (prompt or "").lower()
        if "disease" in lower_prompt or "symptom" in lower_prompt or "ill" in lower_prompt:
            result = self.analyze_image(image_bytes, mime_type)
            animal_type = result.get("animal_type", "Animal")
            return {
                "mode": "disease",
                "animal_type": animal_type,
                "symptoms": "General skin irritation or reduced activity may indicate illness.",
                "medicines": "A veterinarian should advise the exact medicine based on diagnosis.",
                "message": (
                    f"Symptoms: General skin irritation or reduced activity may indicate illness.\n"
                    f"Possible medicines: A veterinarian should advise the exact medicine based on diagnosis.\n"
                    f"For {animal_type}, consult a veterinarian promptly."
                ),
            }

        result = self.analyze_image(image_bytes, mime_type)
        if result.get("message") == "Image analysis is temporarily unavailable. Please try again shortly.":
            return {
                "matched": False,
                "mode": "similar_animal",
                "message": "Image analysis is temporarily unavailable. Please try again shortly.",
                "results": [],
            }

        animal_type = result.get("animal_type", "Unknown")
        breed = result.get("breed", "Unknown")
        rows = self.database_rows("SELECT animal_id, animal_type, breed, animal_name, city, state, price, image_url, availability FROM animals WHERE animal_type = %s LIMIT 5", (animal_type,)) if hasattr(self, "database_rows") else []
        return {
            "matched": bool(rows),
            "mode": "similar_animal",
            "animal_type": animal_type,
            "breed": breed,
            "message": f"Found a similar {animal_type} match for your query.",
            "results": rows,
        }
