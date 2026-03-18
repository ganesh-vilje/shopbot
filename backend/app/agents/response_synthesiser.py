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
- Structure your response like:
  1. Short friendly sentence
  2. Key info (bullets if multiple items)
  3. Helpful next step or suggestion

- If data is empty or unclear:
  - Be honest
  - Suggest alternatives
- Never repeat greetings if already included
- Never mention database, SQL, or internal systems
- Never show data from other users
- Do NOT repeat greeting if already included
- Warm and empathetic: Always acknowledge the customer's feeling or situation first
- Natural human contractions: use I've, you'll, we're, I'm, it's
- Positive and reassuring: Find the silver lining even in bad situations
- Concise but complete: Under 200 words unless detailed breakdown is needed
- Use markdown for clarity: **bold** for key info, bullet lists for multiple items
- Never reveal internal SQL, database structure, or system details
- End with a helpful offer or encouragement when appropriate

CRITICAL CONVERSATION RULES:
- If this is a FOLLOW-UP message in an ongoing conversation, DO NOT start with "Hi Alex" or any greeting
- Only greet at the start of a brand new conversation (first message)
- Remember the context of what was discussed — if user asks "how many pieces" after asking about iPhone 15 Pro, they mean iPhone 15 Pro pieces
- Keep your response consistent with what was previously discussed

Tone by situation:
- Order delayed/problem → deeply empathetic, apologetic, solution-focused
- Product search → enthusiastic, helpful shopper friend
- Good news (delivered, in stock) → warm and celebratory
- Out of stock → empathetic, suggest alternatives
- Price/stock info → friendly and informative 
- If no data is found:
  - Do NOT repeat the same phrasing across responses
  - Vary your wording naturally each time
  - Use different tones like:
    - “I couldn’t find anything this time”
    - “Looks like nothing matched that”
    - “Hmm, I’m not seeing results for that”
  - Suggest helpful alternatives:
    - refine search
    - try another category
    - ask for recommendations"""


def _get_msg_field(msg, field: str) -> str:
    """Safely get a field from either a dict or SQLAlchemy model object."""
    if isinstance(msg, dict):
        return msg.get(field, "")
    return getattr(msg, field, "")


def synthesise(
    question: str,
    intent: str,
    data_rows: list[dict],
    faq_key: str | None,
    customer_name: str,
    conversation_history: list = [],
    
) -> Generator[str, None, None]:
    """Yields streamed text chunks.
    """
    

    is_followup = len(conversation_history) > 0
    name        = customer_name.split()[0]
    greeting    = "" if is_followup else f"Hey {name}! 😊 "
    
    # ── FAQ response — no DB needed ───────────────────────────────────────
    if faq_key:
        # Let GPT handle out-of-scope and FAQ naturally
        # instead of returning the same generic string every ti()
        if not settings.OPENAI_API_KEY:
            faq_text = FAQ_RESPONSES.get(faq_key, FAQ_RESPONSES["general"])
            yield from _stream_text(
                f"{greeting}{faq_text}\n\nIs there anything else I can help you with today?"
            )
            return

        # Build history context
        history_context = ""
        if conversation_history:
            history_context = "\n\nRecent conversation:\n"
            for msg in conversation_history[-4:]:
                msg_role    = _get_msg_field(msg, "role")
                msg_content = _get_msg_field(msg, "content")
                role_label  = "Customer" if msg_role == "user" else "You (Alex)"
                history_context += f"{role_label}: {msg_content[:200]}\n"

        out_of_scope_prompt = f"""You are Alex, a funny and warm shopping assistant at ShopBot.

        The customer just asked: "{question}"
        Customer name: {customer_name}
        Is follow-up: {is_followup}
        {history_context}

        This question has nothing to do with shopping, orders, or products.

        Your job: respond exactly like these examples — casual, funny, self-aware, SHORT:

        Example 1 — customer asks "can you write me a poem?":
        "Ha, I wish I were a poet! That's a bit outside my lane — I'm Alex, your ShopBot shopping assistant. I can help you find the perfect gift or check if something's in stock though! 😊"

        Example 2 — customer asks "what's the weather today?":
        "I'm not quite connected to the weather station! I'm your ShopBot assistant, so weather forecasts are beyond me. But if you need to shop for a rain jacket or winter gear, I've got you covered! 😄"

        Example 3 — customer asks "help me with my homework":
        "Homework's a tough one for me — I'm a shopping assistant, not a study buddy! Though if you need supplies or gear for school, that's right up my alley. What can I help you shop for? 🛍️"

        Example 4 — customer asks "who won the football match?":
        "Wish I could tell you the score! I'm glued to ShopBot, not the sports channel 😄 But if you need a jersey or some fan gear, I'm your person!"

        Rules:
        - NEVER say "my expertise is all about" or "enhancing your shopping journey" or "seamless experience" — these sound robotic
        - NEVER start with "It sounds like" or "It looks like" — too corporate
        - BE SPECIFIC to what they asked — reference their actual question in a fun way
        - Maximum 2-3 sentences
        - {"No greeting." if is_followup else "Can start casually."}
        - Sound like a real funny helpful friend, not a customer service bot"""

        try:
            client = OpenAI(api_key=settings.OPENAI_API_KEY)
            stream = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": ALEX_PERSONA},
                    {"role": "user",   "content": out_of_scope_prompt},
                ],
                temperature=0.9,   # higher temperature = more varied responses
                max_tokens=150,
                stream=True,
            )
            for chunk in stream:
                delta = chunk.choices[0].delta.content
                if delta:
                    yield delta
            return
        except Exception as e:
            print(f"[ResponseSynthesiser] FAQ/OOS error: {e}")
            faq_text = FAQ_RESPONSES.get(faq_key, FAQ_RESPONSES["general"])
            yield from _stream_text(f"{greeting}{faq_text}")
            return

    # ── No data found ─────────────────────────────────────────────────────

    # ── Fallback when no OpenAI key ───────────────────────────────────────
    if not settings.OPENAI_API_KEY:
        yield from _fallback_synthesise(question, intent, data_rows, customer_name, is_followup)
        return

    # ── Build conversation history context ────────────────────────────────
    history_context = ""
    if conversation_history:
        history_context = "\n\nPrevious conversation:\n"
        for msg in conversation_history[-6:]:
            msg_role    = _get_msg_field(msg, "role")
            msg_content = _get_msg_field(msg, "content")
            role_label  = "Customer" if msg_role == "user" else "You (Alex)"
            history_context += f"{role_label}: {msg_content[:300]}\n"

    # ── Build user prompt ─────────────────────────────────────────────────
    user_prompt = f"""Customer name: {customer_name}
Is this a follow-up message: {is_followup}
Customer question: {question}
Intent detected: {intent}
Data retrieved from database:
{json.dumps(data_rows, indent=2, default=str)}
{history_context}

Instructions:
- {"This is a follow-up message. Do NOT greet. Get straight to the answer." if is_followup else "This is the first message. You may greet warmly."}
- Use the conversation history to understand context (e.g. if user says 'how many pieces', check what product was discussed before)
- Give a direct, warm answer based on the data above
- Never say 'Hi Alex' or any greeting if this is a follow-up"""

    # ── Call GPT-4o with streaming ────────────────────────────────────────
    try:
        client = OpenAI(api_key=settings.OPENAI_API_KEY)
        stream = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": ALEX_PERSONA},
                {"role": "user",   "content": user_prompt},
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
        yield from _fallback_synthesise(question, intent, data_rows, customer_name, is_followup)


def _stream_text(text: str) -> Generator[str, None, None]:
    """Simulate streaming for non-OpenAI responses."""
    words = text.split(" ")
    for i, word in enumerate(words):
        yield word + (" " if i < len(words) - 1 else "")


def _fallback_synthesise(
    question: str,
    intent: str,
    rows: list[dict],
    customer_name: str,
    is_followup: bool = False,
) -> Generator[str, None, None]:
    """Rule-based fallback when OpenAI API is unavailable."""
    name     = customer_name.split()[0]
    greeting = "" if is_followup else f"Hey {name}! 👋 "

    if intent == "order_status" and rows:
        r    = rows[0]
        text = (
            f"{greeting}I've got the details on your order **{r.get('order_number', '')}**.\n\n"
            f"- **Status:** {str(r.get('status', '')).capitalize()}\n"
            f"- **Total:** ${float(r.get('total_amount', 0)):.2f}\n"
            f"- **Placed:** {str(r.get('created_at', ''))[:10]}\n"
        )
        if r.get("tracking_number"):
            text += f"- **Tracking:** {r['tracking_number']}\n"
        if r.get("shipped_at"):
            text += f"- **Shipped:** {str(r['shipped_at'])[:10]}\n"
        if r.get("delivered_at"):
            text += f"- **Delivered:** {str(r['delivered_at'])[:10]}\n"
        text += "\nLet me know if you need anything else! 😊"

    elif intent == "order_history" and rows:
        text = f"{greeting}Here are your recent orders! 📦\n\n"
        for r in rows:
            text += (
                f"- **{r.get('order_number', '')}** — "
                f"{str(r.get('status', '')).capitalize()} — "
                f"${float(r.get('total_amount', 0)):.2f} "
                f"({str(r.get('created_at', ''))[:10]})\n"
            )
        text += "\nNeed details on any specific order? Just ask! 😊"

    elif intent in ("product_search", "top_products") and rows:
        text = f"{greeting}Here's what I found! 🛍️\n\n"
        for r in rows:
            price = float(r.get("price", 0))
            disc  = float(r.get("discount_pct", 0))
            final = price * (1 - disc / 100)
            text += f"- **{r.get('name', '')}** by {r.get('brand', 'N/A')} — "
            if disc > 0:
                text += f"~~${price:.2f}~~ **${final:.2f}** ({disc:.0f}% off) ⭐ {float(r.get('rating', 0)):.1f}/5\n"
            else:
                text += f"**${price:.2f}** ⭐ {float(r.get('rating', 0)):.1f}/5\n"
        text += "\nWould you like more info on any of these? 😊"

    elif intent == "price_check" and rows:
        r     = rows[0]
        price = float(r.get("price", 0))
        disc  = float(r.get("discount_pct", 0))
        final = price * (1 - disc / 100)
        text  = f"{greeting}Here's the pricing for **{r.get('name', '')}**:\n\n"
        if disc > 0:
            text += f"- Original Price: ~~${price:.2f}~~\n- **Discounted Price: ${final:.2f}** ({disc:.0f}% off!) 🎉\n"
        else:
            text += f"- **Price: ${price:.2f}**\n"
        text += f"- Rating: ⭐ {float(r.get('rating', 0)):.1f}/5 ({r.get('review_count', 0)} reviews)\n\nGreat choice! Let me know if I can help further. 😊"

    elif intent == "stock_check" and rows:
        r     = rows[0]
        qty   = r.get("stock_qty", 0)
        avail = r.get("availability", "Unknown")
        text  = f"{greeting}Here's the stock status for **{r.get('name', '')}**:\n\n"
        if qty > 0:
            text += f"✅ **{avail}** — {qty} units available!\n\nGreat news — it's ready to order! 🛒"
        else:
            text += (
                f"😔 Unfortunately, **{r.get('name', '')}** is currently **out of stock**.\n\n"
                f"Would you like me to suggest similar products? I'd love to help!"
            )

    elif intent == "customer_profile" and rows:
        r    = rows[0]
        text = (
            f"{greeting}Here's your profile info! 👤\n\n"
            f"- **Name:** {r.get('full_name', '')}\n"
            f"- **Email:** {r.get('email', '')}\n"
            f"- **Member Since:** {str(r.get('created_at', ''))[:10]}\n"
            f"- **Location:** {r.get('city', '')}, {r.get('country', '')}\n\n"
            f"You're a valued member of our community! 💖"
        )
    else:
        text = f"{greeting}I found some information for you:\n\n"
        for r in rows[:3]:
            for k, v in r.items():
                text += f"- **{k.replace('_', ' ').title()}:** {v}\n"
        text += "\nLet me know if you need anything else! 😊"

    yield from _stream_text(text)