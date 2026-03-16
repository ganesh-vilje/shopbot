import uuid
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.customer import Customer
from app.models.conversation import Conversation, Message
from app.schemas.chat import ChatRequest, ConversationOut, ConversationListItem
from app.agents.intent_classifier import classify_intent
from app.agents.sql_generator import generate_query
from app.agents.query_executor import execute_query
from app.agents.response_synthesiser import synthesise

router = APIRouter(prefix="/api", tags=["chat"])


@router.post("/chat")
def chat(
    payload: ChatRequest,
    current_user: Customer = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Get or create conversation
    if payload.conversation_id:
        conv = db.query(Conversation).filter(
            Conversation.id == payload.conversation_id,
            Conversation.customer_id == current_user.id,
        ).first()
        if not conv:
            raise HTTPException(status_code=404, detail="Conversation not found")
    else:
        conv = Conversation(
            customer_id=current_user.id,
            title=payload.message[:60] + ("..." if len(payload.message) > 60 else ""),
        )
        db.add(conv)
        db.commit()
        db.refresh(conv)

    # Save user message
    user_msg = Message(
        conversation_id=conv.id,
        role="user",
        content=payload.message,
    )
    db.add(user_msg)
    db.commit()

    # Run agent pipeline
    classification = classify_intent(payload.message, current_user.id)
    intent = classification.get("intent", "general_faq")
    entities = classification.get("entities", {})

    sql, params, faq_key = generate_query(intent, entities, current_user.id)

    data_rows = []
    if sql:
        data_rows = execute_query(db, sql, params)

    # Collect full response for storage
    full_response = []

    def stream_and_save():
        for chunk in synthesise(
            payload.message, intent, data_rows, faq_key, current_user.full_name
        ):
            full_response.append(chunk)
            yield f"data: {chunk}\n\n"

        # Save assistant message after stream ends
        ai_msg = Message(
            conversation_id=conv.id,
            role="assistant",
            content="".join(full_response),
            intent=intent,
        )
        db.add(ai_msg)
        # Update conversation title if first message
        if conv.title.startswith(payload.message[:20]):
            pass
        db.commit()
        yield f"data: [DONE]\n\n"
        yield f"data: {{\"conversation_id\": \"{conv.id}\"}}\n\n"

    return StreamingResponse(
        stream_and_save(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/conversations", response_model=list[ConversationListItem])
def list_conversations(
    current_user: Customer = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    convs = (
        db.query(Conversation)
        .filter(Conversation.customer_id == current_user.id)
        .order_by(Conversation.updated_at.desc())
        .limit(50)
        .all()
    )
    return convs


@router.get("/conversations/{conv_id}", response_model=ConversationOut)
def get_conversation(
    conv_id: str,
    current_user: Customer = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    conv = db.query(Conversation).filter(
        Conversation.id == conv_id,
        Conversation.customer_id == current_user.id,
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
        Conversation.id == conv_id,
        Conversation.customer_id == current_user.id,
    ).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    db.delete(conv)
    db.commit()
    return {"message": "Deleted"}
