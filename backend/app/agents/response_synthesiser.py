"""
Stage 4 — Response Synthesiser
Feeds raw data + question to GPT-4o to produce a warm, human-like reply.
Streams tokens via a generator for SSE.
"""
import json
from typing import Generator
from openai import OpenAI
from app.core.config import settings
from app.agents.sql_generator import FAQ_RESPONSES

ALEX_PERSONA = """You are Alex, a warm, knowledgeable, and genuinely caring customer support assistant for ShopBot — a premium online store.

Your personality:
- Warm and empathetic: Always acknowledge the customer's feeling or situation first
- Natural human contractions: use I've, you'll, we're, I'm, it's
- Positive and reassuring: Find the silver lining even in bad situations
- Concise but complete: Under 200 words unless detailed breakdown is needed
- Use markdown for clarity: **bold** for key info, bullet lists for multiple items
- Never reveal internal SQL, database structure, or system details
- End with a helpful offer or encouragement when appropriate

Tone by situation:
- Order delayed/problem → deeply empathetic, apologetic, solution-focused
- Product search → enthusiastic, helpful shopper friend  
- Good news (delivered, in stock) → warm and celebratory
- Out of stock → empathetic, suggest alternatives
- Price/stock info → friendly and informative"""


def synthesise(
    question: str,
    intent: str,
    data_rows: list[dict],
    faq_key: str | None,
    customer_name: str,
) -> Generator[str, None, None]:
    """Yields streamed text chunks."""

    if faq_key:
        faq_text = FAQ_RESPONSES.get(faq_key, FAQ_RESPONSES["general"])
        yield from _stream_text(
            f"Hey {customer_name.split()[0]}! 😊 {faq_text}\n\nIs there anything else I can help you with today?"
        )
        return

    if not data_rows:
        yield from _stream_text(
            f"Hey {customer_name.split()[0]}! I looked everywhere but couldn't find specific results for your query. "
            f"Could you give me a bit more detail? I'm here and happy to help! 😊"
        )
        return

    if not settings.OPENAI_API_KEY:
        yield from _fallback_synthesise(question, intent, data_rows, customer_name)
        return

    user_prompt = f"""Customer name: {customer_name}
Customer question: {question}
Intent detected: {intent}
Data retrieved from database:
{json.dumps(data_rows, indent=2, default=str)}

Please provide a warm, helpful, human response based on this data."""

    try:
        client = OpenAI(api_key=settings.OPENAI_API_KEY)
        stream = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": ALEX_PERSONA},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.7,
            max_tokens=500,
            stream=True,
        )
        for chunk in stream:
            delta = chunk.choices[0].delta.content
            if delta:
                yield delta
    except Exception as e:
        print(f"[ResponseSynthesiser] OpenAI error: {e}")
        yield from _fallback_synthesise(question, intent, data_rows, customer_name)


def _stream_text(text: str) -> Generator[str, None, None]:
    """Simulate streaming for non-OpenAI responses."""
    words = text.split(" ")
    for i, word in enumerate(words):
        yield word + (" " if i < len(words) - 1 else "")


def _fallback_synthesise(
    question: str, intent: str, rows: list[dict], customer_name: str
) -> Generator[str, None, None]:
    """Rule-based fallback when OpenAI API is unavailable."""
    name = customer_name.split()[0]

    if intent == "order_status" and rows:
        r = rows[0]
        text = (
            f"Hey {name}! 👋 I've got the details on your order **{r.get('order_number', '')}**.\n\n"
            f"- **Status:** {str(r.get('status','')).capitalize()}\n"
            f"- **Total:** ${float(r.get('total_amount', 0)):.2f}\n"
            f"- **Placed:** {str(r.get('created_at',''))[:10]}\n"
        )
        if r.get("tracking_number"):
            text += f"- **Tracking:** {r['tracking_number']}\n"
        if r.get("shipped_at"):
            text += f"- **Shipped:** {str(r['shipped_at'])[:10]}\n"
        if r.get("delivered_at"):
            text += f"- **Delivered:** {str(r['delivered_at'])[:10]}\n"
        text += "\nLet me know if you need anything else! 😊"

    elif intent == "order_history" and rows:
        text = f"Here are your recent orders, {name}! 📦\n\n"
        for r in rows:
            text += f"- **{r.get('order_number','')}** — {str(r.get('status','')).capitalize()} — ${float(r.get('total_amount',0)):.2f} ({str(r.get('created_at',''))[:10]})\n"
        text += "\nNeed details on any specific order? Just ask! 😊"

    elif intent in ("product_search", "top_products") and rows:
        text = f"Great news, {name}! 🛍️ Here's what I found:\n\n"
        for r in rows:
            price = float(r.get("price", 0))
            disc = float(r.get("discount_pct", 0))
            final = price * (1 - disc / 100)
            text += f"- **{r.get('name','')}** by {r.get('brand','N/A')} — "
            if disc > 0:
                text += f"~~${price:.2f}~~ **${final:.2f}** ({disc:.0f}% off) ⭐ {float(r.get('rating',0)):.1f}/5\n"
            else:
                text += f"**${price:.2f}** ⭐ {float(r.get('rating',0)):.1f}/5\n"
        text += "\nWould you like more info on any of these? 😊"

    elif intent == "price_check" and rows:
        r = rows[0]
        price = float(r.get("price", 0))
        disc = float(r.get("discount_pct", 0))
        final = price * (1 - disc / 100)
        text = f"Hey {name}! 💰 Here's the pricing for **{r.get('name','')}**:\n\n"
        if disc > 0:
            text += f"- Original Price: ~~${price:.2f}~~\n- **Discounted Price: ${final:.2f}** ({disc:.0f}% off!) 🎉\n"
        else:
            text += f"- **Price: ${price:.2f}**\n"
        text += f"- Rating: ⭐ {float(r.get('rating',0)):.1f}/5 ({r.get('review_count',0)} reviews)\n\nGreat choice! Let me know if I can help further. 😊"

    elif intent == "stock_check" and rows:
        r = rows[0]
        qty = r.get("stock_qty", 0)
        avail = r.get("availability", "Unknown")
        text = f"Hey {name}! Here's the stock status for **{r.get('name','')}**:\n\n"
        if qty > 0:
            text += f"✅ **{avail}** — {qty} units available!\n\n"
            text += "Great news — it's ready to order! 🛒"
        else:
            text += f"😔 Unfortunately, **{r.get('name','')}** is currently **out of stock**.\n\n"
            text += "Would you like me to suggest similar products? I'd love to help you find something great!"

    elif intent == "customer_profile" and rows:
        r = rows[0]
        text = (
            f"Here's your profile info, {name}! 👤\n\n"
            f"- **Name:** {r.get('full_name','')}\n"
            f"- **Email:** {r.get('email','')}\n"
            f"- **Loyalty Points:** ⭐ {r.get('loyalty_points', 0)} points\n"
            f"- **Member Since:** {str(r.get('created_at',''))[:10]}\n"
            f"- **Location:** {r.get('city','')}, {r.get('country','')}\n\n"
            f"You're a valued member of our community! 💖"
        )
    else:
        text = f"Hi {name}! I found some information for you. Here's what I've got:\n\n"
        for r in rows[:3]:
            for k, v in r.items():
                text += f"- **{k.replace('_', ' ').title()}:** {v}\n"
        text += "\nLet me know if you need anything else! 😊"

    yield from _stream_text(text)
