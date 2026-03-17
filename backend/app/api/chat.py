from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from datetime import datetime

from app.api.deps import get_current_user
from app.db.session import get_db, engine
from app.models.customer import Customer
from app.models.conversation import Conversation, Message
from app.schemas.chat import ChatRequest, ConversationOut, ConversationListItem

from app.agents.intent_classifier import classify_intent
from app.agents.sql_generator import generate_sql
from app.agents.query_executor import execute_query
from app.agents.response_synthesiser import synthesise
from app.db.session import SessionLocal

router = APIRouter(prefix="/api", tags=["chat"])


def _escape_for_sse(text: str) -> str:
    return text.replace("\n", "\\n").replace("\r", "")


@router.post("/chat")
def chat(
    payload: ChatRequest,
    current_user: Customer = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    # ── 1. Get or create conversation ─────────────────────────────────────
    if payload.conversation_id:
        conv = db.query(Conversation).filter(
            Conversation.id == payload.conversation_id,
            Conversation.customer_id == current_user.id
        ).first()
        if not conv:
            raise HTTPException(status_code=404, detail="Conversation not found")
    else:
        title = payload.message[:60] + ("..." if len(payload.message) > 60 else "")
        conv = Conversation(customer_id=current_user.id, title=title)
        db.add(conv)
        db.commit()
        db.refresh(conv)

    # ── 2. Save user message ───────────────────────────────────────────────
    db.add(Message(
        conversation_id=conv.id,
        role="user",
        content=payload.message
    ))
    db.commit()

    # ── 3. Classify intent ─────────────────────────────────────────────────
    classification = classify_intent(payload.message, current_user.id)
    intent   = classification.get("intent", "general_faq")
    entities = classification.get("entities", {"limit": 5})

    # ── 4. Generate SQL ────────────────────────────────────────────────────
    sql, faq_key = generate_sql(
        question    = payload.message,
        intent      = intent,
        entities    = entities,
        customer_id = current_user.id,
        engine      = engine
    )

    # ── 5. Execute query ───────────────────────────────────────────────────
    data_rows = []
    if sql:
        data_rows = execute_query(db, sql)

    # ── 6. Stream response ─────────────────────────────────────────────────
    full_response = []

    conv_id = str(conv.id)  # ensure it's a string for the client

    def stream_and_save():

        for chunk in synthesise(
            question      = payload.message,
            intent        = intent,
            data_rows     = data_rows,
            faq_key       = faq_key,
            customer_name = current_user.full_name
        ):
            full_response.append(chunk)
            yield f"data: {_escape_for_sse(chunk)}\n\n"

        # ADD THESE DEBUG PRINTS:
        print(f"[DEBUG] Chunks collected: {len(full_response)}")
        print(f"[DEBUG] Full text: {''.join(full_response)[:80]}")

        save_db = SessionLocal()
        try:
            full_text = "".join(full_response)
            print(f"[DEBUG] full_text empty? {not full_text.strip()}")
            if full_text.strip():
                save_db.add(Message(
                    conversation_id = conv_id,
                    role            = "assistant",
                    content         = full_text,
                    intent          = intent
                ))
                save_conv = save_db.query(Conversation).filter(
                    Conversation.id == conv_id
                ).first()
                if save_conv:
                    save_conv.updated_at = datetime.utcnow()
                save_db.commit()
                print(f"[Chat] ✓ Saved assistant message for conv {conv.id}")
        except Exception as e:
            print(f"[Chat] ✗ Failed to save: {e}")
            save_db.rollback()
        finally:
            save_db.close()

        yield f"data: [DONE]\n\n"
        yield f"data: {{\"conversation_id\": \"{conv_id}\"}}\n\n"

    return StreamingResponse(
        stream_and_save(),
        media_type="text/event-stream",
        headers={
            "Cache-Control"    : "no-cache",
            "X-Accel-Buffering": "no",
            "Connection"       : "keep-alive",
        },
    )


# ─────────────────────────────────────────────────────────────────────────────
# Conversation APIs
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/conversations", response_model=list[ConversationListItem])
def list_conversations(
    current_user: Customer = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return (
        db.query(Conversation)
        .filter(Conversation.customer_id == current_user.id)
        .order_by(Conversation.updated_at.desc())
        .limit(50)
        .all()
    )


@router.get("/conversations/{conv_id}", response_model=ConversationOut)
def get_conversation(
    conv_id: str,
    current_user: Customer = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    conv = db.query(Conversation).filter(
        Conversation.id          == conv_id,
        Conversation.customer_id == current_user.id
    ).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conv


@router.delete("/conversations/{conv_id}")
def delete_conversation(
    conv_id: str,
    current_user: Customer = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    conv = db.query(Conversation).filter(
        Conversation.id          == conv_id,
        Conversation.customer_id == current_user.id
    ).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    db.delete(conv)
    db.commit()
    return {"message": "Deleted"}