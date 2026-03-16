"""
Stage 1 — Intent Classifier
Classifies the user query into one of the defined intents and extracts entities.
"""
import json
import re
from openai import OpenAI
from app.core.config import settings

INTENTS = [
    "order_status",
    "order_history",
    "product_search",
    "price_check",
    "stock_check",
    "customer_profile",
    "top_products",
    "general_faq",
    "out_of_scope",
]

SYSTEM_PROMPT = """You are an intent classifier for an e-commerce customer support chatbot.

Classify the user's message into EXACTLY ONE of these intents:
- order_status: User wants to know the status/tracking of a specific order
- order_history: User wants to see their past orders list
- product_search: User is looking for products (searching by name, category, brand)
- price_check: User wants to know the price of a specific product
- stock_check: User wants to know if a product is in stock / available
- customer_profile: User asking about their own account, points, address
- top_products: User wants best/top/recommended products, highest rated
- general_faq: Return policy, shipping info, payment methods, general questions
- out_of_scope: Anything not related to e-commerce, shopping, or their account

Also extract any relevant entities from the message.

Respond ONLY with valid JSON in this exact format:
{
  "intent": "<intent_key>",
  "confidence": <0.0-1.0>,
  "entities": {
    "product_name": "<if mentioned>",
    "category": "<if mentioned>",
    "brand": "<if mentioned>",
    "order_number": "<if mentioned>",
    "limit": <number if mentioned, else 5>
  }
}

Remove keys from entities if they are not mentioned. Always include "limit"."""


def classify_intent(message: str, user_id: str) -> dict:
    """Returns intent + entities dict."""
    if not settings.OPENAI_API_KEY:
        return _fallback_classify(message)

    try:
        client = OpenAI(api_key=settings.OPENAI_API_KEY)
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": message},
            ],
            temperature=0,
            max_tokens=300,
            response_format={"type": "json_object"},
        )
        raw = response.choices[0].message.content
        result = json.loads(raw)
        if result.get("intent") not in INTENTS:
            result["intent"] = "out_of_scope"
        result.setdefault("entities", {})
        result["entities"].setdefault("limit", 5)
        return result
    except Exception as e:
        print(f"[IntentClassifier] Error: {e}")
        return _fallback_classify(message)


def _fallback_classify(message: str) -> dict:
    """Rule-based fallback when OpenAI is unavailable."""
    msg = message.lower()
    entities: dict = {"limit": 5}

    # Extract order number
    order_match = re.search(r"(ord[-\s]?\d+)", msg, re.IGNORECASE)
    if order_match:
        entities["order_number"] = order_match.group(1).upper().replace(" ", "-")

    if any(w in msg for w in ["where is my order", "track", "status", "shipment", "delivery status"]):
        intent = "order_status"
    elif any(w in msg for w in ["my orders", "order history", "past orders", "previous orders", "recent orders"]):
        intent = "order_history"
    elif any(w in msg for w in ["how much", "price", "cost", "pricing"]):
        intent = "price_check"
    elif any(w in msg for w in ["in stock", "available", "availability", "stock"]):
        intent = "stock_check"
    elif any(w in msg for w in ["best", "top", "popular", "recommended", "highest rated"]):
        intent = "top_products"
    elif any(w in msg for w in ["my account", "loyalty", "points", "profile", "my info"]):
        intent = "customer_profile"
    elif any(w in msg for w in ["return", "refund", "shipping policy", "payment"]):
        intent = "general_faq"
    elif any(w in msg for w in ["search", "find", "looking for", "do you have", "show me", "buy", "purchase"]):
        intent = "product_search"
    else:
        intent = "general_faq"

    return {"intent": intent, "confidence": 0.7, "entities": entities}
