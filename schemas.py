"""
Lavu — Pydantic Schemas (request/response models)
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, field_validator
from models import OrderStatus, SubscriptionTier, PaymentStatus


# ─────────────────────────────────────────
#  AUTH
# ─────────────────────────────────────────

class UserRegister(BaseModel):
    full_name:    str
    phone_number: str  # must be 254XXXXXXXXX
    password:     str
    email:        Optional[str] = None
    location:     Optional[str] = None

    @field_validator("phone_number")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        if not v.startswith("254") or len(v) != 12:
            raise ValueError("Phone must be in format 254XXXXXXXXX")
        return v


class UserLogin(BaseModel):
    phone_number: str
    password:     str


class TokenResponse(BaseModel):
    access_token: str
    token_type:   str = "bearer"


# ─────────────────────────────────────────
#  SUBSCRIPTION
# ─────────────────────────────────────────

class SubscriptionPlanOut(BaseModel):
    id:               int
    tier:             SubscriptionTier
    display_name:     str
    price_kes:        float
    kg_limit:         float
    pickups_per_week: int
    description:      Optional[str]

    class Config:
        from_attributes = True


class SubscriptionOut(BaseModel):
    id:                  int
    plan:                SubscriptionPlanOut
    start_date:          datetime
    renewal_date:        datetime
    kg_used_this_month:  float
    is_active:           bool

    class Config:
        from_attributes = True


class SelectPlanRequest(BaseModel):
    plan_id: int   # ID of the chosen SubscriptionPlan


# ─────────────────────────────────────────
#  ORDER
# ─────────────────────────────────────────

class CreateOrderRequest(BaseModel):
    scheduled_pickup:  datetime
    pickup_address:    str
    delivery_address:  str
    notes:             Optional[str] = None


class UpdateOrderStatusRequest(BaseModel):
    status:  OrderStatus
    note:    Optional[str] = None


class OrderOut(BaseModel):
    id:               int
    status:           OrderStatus
    scheduled_pickup: datetime
    actual_pickup:    Optional[datetime]
    kg_weight:        Optional[float]
    pickup_address:   str
    delivery_address: str
    notes:            Optional[str]
    created_at:       datetime

    class Config:
        from_attributes = True


# ─────────────────────────────────────────
#  PAYMENT / M-PESA
# ─────────────────────────────────────────

class InitiatePaymentRequest(BaseModel):
    phone_number: str   # 254XXXXXXXXX — can differ from account phone

    @field_validator("phone_number")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        if not v.startswith("254") or len(v) != 12:
            raise ValueError("Phone must be in format 254XXXXXXXXX")
        return v


class MpesaCallbackRequest(BaseModel):
    """Safaricom sends this to your callback URL after STK Push."""
    Body: dict   # raw Daraja callback payload — parsed in the endpoint


class PaymentOut(BaseModel):
    id:                  int
    amount_kes:          float
    status:              PaymentStatus
    mpesa_receipt_number: Optional[str]
    initiated_at:        datetime
    completed_at:        Optional[datetime]

    class Config:
        from_attributes = True


# ─────────────────────────────────────────
#  ADMIN ANALYTICS
# ─────────────────────────────────────────

class SubscriberUsageOut(BaseModel):
    user_id:            int
    full_name:          str
    phone_number:       str
    plan_tier:          SubscriptionTier
    kg_limit:           float
    kg_used_this_month: float
    usage_percent:      float   # (kg_used / kg_limit) * 100
