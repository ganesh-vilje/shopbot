from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from app.api.deps import get_current_user, get_db
from app.models.customer import Customer

router = APIRouter(prefix="/api", tags=["users"])


class UpdateProfileRequest(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None


@router.get("/me")
def get_me(current_user: Customer = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "full_name": current_user.full_name,
        "email": current_user.email,
        "phone": current_user.phone,
        "city": current_user.city,
        "country": current_user.country,
        "is_verified": current_user.is_verified,
        "created_at": current_user.created_at,
    }


@router.patch("/me")
def update_me(
    payload: UpdateProfileRequest,
    current_user: Customer = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if payload.full_name:
        current_user.full_name = payload.full_name
    if payload.phone is not None:
        current_user.phone = payload.phone
    if payload.address is not None:
        current_user.address = payload.address
    if payload.city is not None:
        current_user.city = payload.city
    db.commit()
    db.refresh(current_user)
    return {"message": "Profile updated", "user": {
        "full_name": current_user.full_name,
        "email": current_user.email,
        "phone": current_user.phone,
        "city": current_user.city,
    }}
