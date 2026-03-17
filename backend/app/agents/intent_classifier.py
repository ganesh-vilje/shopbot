"""
Intent Classifier  (Stage 1)
Classifies the user query into a defined intent and extracts entities.
Uses GPT-4o-mini (fast + cheap) with a hardened anti-hallucination prompt.
Falls back to rule-based classification when OpenAI is unavailable.
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

SYSTEM_PROMPT = """You are a precise intent classifier for an e-commerce customer support chatbot.

Your ONLY job is to classify the user message and extract entities.
You MUST respond with valid JSON only — no explanation, no extra text.

INTENT DEFINITIONS (read carefully before choosing):
- order_status     : User asks about status/tracking/location of a SPECIFIC order
- order_history    : User wants a LIST of their past or recent orders (not a specific one)
- product_search   : User is searching/browsing for products by name, category, or brand
- price_check      : User specifically asks about the PRICE or cost of a product
- stock_check      : User asks if a product is IN STOCK or AVAILABLE
- customer_profile : User asks about their own account, address, profile info
- top_products     : User wants BEST/TOP/HIGHEST-RATED/RECOMMENDED/POPULAR products
- general_faq      : Return policy, shipping info, payment methods, store info
- out_of_scope     : ANYTHING unrelated to shopping, orders, or products (jokes, coding, etc.)

ENTITY EXTRACTION RULES:
- product_name  : exact product name or model if mentioned (e.g. "iPhone 15 Pro", "WH-1000XM5")
- brand         : brand/manufacturer if mentioned (e.g. "Sony", "Apple", "Nike")
- category      : product category if mentioned (e.g. "laptops", "shoes", "electronics")
- order_number  : order reference if mentioned (e.g. "ORD-2025001")
- status        : order status filter if mentioned (e.g. "delivered", "pending", "shipped")
- min_price     : minimum price if user mentions a price range
- max_price     : maximum price if user mentions a price range
- limit         : number of results user wants (default 5, max 20)

ANTI-HALLUCINATION RULES:
- Only extract entities that are EXPLICITLY mentioned in the message
- Do NOT infer or assume entities that are not clearly stated
- If no entity of a type is mentioned, omit that key entirely
- Always include "limit" with value 5 as default

RESPOND WITH THIS EXACT JSON FORMAT:
{
  "intent": "<one of the intent keys above>",
  "confidence": <float 0.0 to 1.0>,
  "entities": {
    "limit": <integer, default 5>
  }
}"""


def classify_intent(message: str, user_id: str) -> dict:
    """
    Classify user message into intent + entities.
    Returns a dict with keys: intent, confidence, entities.
    """
    if not settings.OPENAI_API_KEY:
        return _fallback_classify(message)

    try:
        client = OpenAI(api_key=settings.OPENAI_API_KEY)
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user",   "content": message},
            ],
            temperature=0,           # deterministic classification
            max_tokens=300,
            timeout=10,
            response_format={"type": "json_object"},
        )

        raw    = response.choices[0].message.content or "{}"
        result = json.loads(raw)

        # Validate intent is one we know
        if result.get("intent") not in INTENTS:
            print(f"[IntentClassifier] Unknown intent: {result.get('intent')} — defaulting to out_of_scope")
            result["intent"] = "out_of_scope"

        # Ensure confidence is present
        result.setdefault("confidence", 0.9)

        # Ensure entities dict exists with limit
        result.setdefault("entities", {})
        result["entities"].setdefault("limit", 5)

        # Clamp limit to safe range
        result["entities"]["limit"] = min(
            max(int(result["entities"].get("limit", 5)), 1),
            20
        )

        print(f"[IntentClassifier] intent={result['intent']} confidence={result.get('confidence', '?')} entities={result['entities']}")
        return result

    except json.JSONDecodeError as e:
        print(f"[IntentClassifier] JSON parse error: {e}")
        return _fallback_classify(message)
    except Exception as e:
        print(f"[IntentClassifier] Error: {e}")
        return _fallback_classify(message)


def _fallback_classify(message: str) -> dict:
    """
    Rule-based fallback classifier.
    Used when OpenAI API is unavailable or errors out.
    Less accurate than LLM but always available.
    """
    msg      = message.lower().strip()
    entities: dict = {"limit": 5}

    # ── Extract order number ──────────────────────────────────────────────
    order_match = re.search(r"\b(ord[-\s]?\d+)\b", msg, re.IGNORECASE)
    if order_match:
        entities["order_number"] = order_match.group(1).upper().replace(" ", "-")

    # ── Extract price range ───────────────────────────────────────────────
    price_under = re.search(r"under\s+\$?(\d+)", msg)
    price_over  = re.search(r"over\s+\$?(\d+)", msg)
    if price_under:
        entities["max_price"] = price_under.group(1)
    if price_over:
        entities["min_price"] = price_over.group(1)

    # ── Extract limit hint ────────────────────────────────────────────────
    limit_match = re.search(r"\b(top|last|recent|show me)\s+(\d+)\b", msg)
    if limit_match:
        entities["limit"] = min(int(limit_match.group(2)), 20)

    # ── Classify intent ───────────────────────────────────────────────────
    if any(w in msg for w in ["where is my order", "track", "tracking", "shipment", "delivery status", "my order"]) and entities.get("order_number"):
        intent = "order_status"
    elif any(w in msg for w in ["my orders", "order history", "past orders", "previous orders", "recent orders", "all orders"]):
        intent = "order_history"
    elif any(w in msg for w in ["how much", "what is the price", "cost", "pricing", "price of"]):
        intent = "price_check"
    elif any(w in msg for w in ["in stock", "available", "availability", "do you have", "is there"]):
        intent = "stock_check"
    elif any(w in msg for w in ["best", "top", "popular", "recommended", "highest rated", "most rated", "trending"]):
        intent = "top_products"
    elif any(w in msg for w in ["my account", "my profile", "my address", "my info", "my details"]):
        intent = "customer_profile"
    elif any(w in msg for w in ["return", "refund", "exchange", "shipping policy", "payment method", "how long", "when will"]):
        intent = "general_faq"
    elif any(w in msg for w in ["search", "find", "looking for", "show me", "buy", "purchase", "need a", "want a"]):
        intent = "product_search"
    elif any(w in msg for w in ["hello", "hi", "hey", "help", "what can you"]):
        intent = "general_faq"
    else:
        intent = "general_faq"

    print(f"[IntentClassifier:fallback] intent={intent} entities={entities}")
    return {"intent": intent, "confidence": 0.65, "entities": entities}