"""
Lavu Laundry App — SQLAlchemy Models
Database: PostgreSQL (or Supabase — same driver)
"""

import enum
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Float, Boolean,
    DateTime, Enum, ForeignKey, Text
)
from sqlalchemy.orm import relationship, DeclarativeBase


class Base(DeclarativeBase):
    pass


# ─────────────────────────────────────────
#  ENUMS
# ─────────────────────────────────────────

class SubscriptionTier(str, enum.Enum):
    STUDENT  = "student"    # 20 kg/month — budget tier
    BACHELOR = "bachelor"   # 40 kg/month — standard tier
    FAMILY   = "family"     # 80 kg/month — premium tier


class OrderStatus(str, enum.Enum):
    PENDING         = "pending"
    PICKED_UP       = "picked_up"
    WASHING         = "washing"
    IRONING         = "ironing"
    OUT_FOR_DELIVERY= "out_for_delivery"
    DELIVERED       = "delivered"
    CANCELLED       = "cancelled"


class PaymentStatus(str, enum.Enum):
    PENDING   = "pending"
    COMPLETED = "completed"
    FAILED    = "failed"
    REFUNDED  = "refunded"


# ─────────────────────────────────────────
#  USER
# ─────────────────────────────────────────

class User(Base):
    __tablename__ = "users"

    id            = Column(Integer, primary_key=True, index=True)
    full_name     = Column(String(100), nullable=False)
    phone_number  = Column(String(15), unique=True, nullable=False)  # e.g. 254712345678
    email         = Column(String(120), unique=True, nullable=True)
    password_hash = Column(String(255), nullable=False)
    location      = Column(String(255), nullable=True)  # reuse maps logic here
    is_active     = Column(Boolean, default=True)
    is_admin      = Column(Boolean, default=False)
    created_at    = Column(DateTime, default=datetime.utcnow)

    # Relationships
    subscription  = relationship("Subscription", back_populates="user", uselist=False)
    orders        = relationship("Order", back_populates="user")


# ─────────────────────────────────────────
#  SUBSCRIPTION PLAN (static config)
# ─────────────────────────────────────────

class SubscriptionPlan(Base):
    __tablename__ = "subscription_plans"

    id              = Column(Integer, primary_key=True, index=True)
    tier            = Column(Enum(SubscriptionTier), unique=True, nullable=False)
    display_name    = Column(String(50), nullable=False)   # e.g. "Bachelor Plan"
    price_kes       = Column(Float, nullable=False)        # Monthly price in KES
    kg_limit        = Column(Float, nullable=False)        # Monthly KG allowance
    pickups_per_week= Column(Integer, default=1)
    description     = Column(Text, nullable=True)

    subscriptions   = relationship("Subscription", back_populates="plan")


# ─────────────────────────────────────────
#  USER SUBSCRIPTION
# ─────────────────────────────────────────

class Subscription(Base):
    __tablename__ = "subscriptions"

    id              = Column(Integer, primary_key=True, index=True)
    user_id         = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    plan_id         = Column(Integer, ForeignKey("subscription_plans.id"), nullable=False)
    start_date      = Column(DateTime, default=datetime.utcnow)
    renewal_date    = Column(DateTime, nullable=False)       # next billing date
    kg_used_this_month = Column(Float, default=0.0)          # tracked per billing cycle
    is_active       = Column(Boolean, default=True)

    # Relationships
    user            = relationship("User", back_populates="subscription")
    plan            = relationship("SubscriptionPlan", back_populates="subscriptions")
    payments        = relationship("Payment", back_populates="subscription")


# ─────────────────────────────────────────
#  ORDER  (one pickup = one order)
# ─────────────────────────────────────────

class Order(Base):
    __tablename__ = "orders"

    id              = Column(Integer, primary_key=True, index=True)
    user_id         = Column(Integer, ForeignKey("users.id"), nullable=False)
    status          = Column(Enum(OrderStatus), default=OrderStatus.PENDING)
    scheduled_pickup= Column(DateTime, nullable=False)       # chosen by user
    actual_pickup   = Column(DateTime, nullable=True)
    kg_weight       = Column(Float, nullable=True)           # filled after pickup
    pickup_address  = Column(String(255), nullable=False)
    delivery_address= Column(String(255), nullable=False)
    notes           = Column(Text, nullable=True)            # e.g. "no fabric softener"
    created_at      = Column(DateTime, default=datetime.utcnow)
    updated_at      = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user            = relationship("User", back_populates="orders")
    status_history  = relationship("OrderStatusHistory", back_populates="order")


class OrderStatusHistory(Base):
    """Audit trail — every status change is recorded."""
    __tablename__ = "order_status_history"

    id          = Column(Integer, primary_key=True, index=True)
    order_id    = Column(Integer, ForeignKey("orders.id"), nullable=False)
    status      = Column(Enum(OrderStatus), nullable=False)
    changed_at  = Column(DateTime, default=datetime.utcnow)
    changed_by  = Column(Integer, ForeignKey("users.id"), nullable=True)  # admin user
    note        = Column(String(255), nullable=True)

    order       = relationship("Order", back_populates="status_history")


# ─────────────────────────────────────────
#  PAYMENT  (M-Pesa STK Push record)
# ─────────────────────────────────────────

class Payment(Base):
    __tablename__ = "payments"

    id                  = Column(Integer, primary_key=True, index=True)
    subscription_id     = Column(Integer, ForeignKey("subscriptions.id"), nullable=False)
    amount_kes          = Column(Float, nullable=False)
    status              = Column(Enum(PaymentStatus), default=PaymentStatus.PENDING)

    # M-Pesa specific fields
    merchant_request_id = Column(String(100), nullable=True)   # from STK Push response
    checkout_request_id = Column(String(100), nullable=True)   # used to query status
    mpesa_receipt_number= Column(String(50), nullable=True)    # filled on success callback
    phone_number        = Column(String(15), nullable=False)   # 254XXXXXXXXX format

    initiated_at        = Column(DateTime, default=datetime.utcnow)
    completed_at        = Column(DateTime, nullable=True)

    subscription        = relationship("Subscription", back_populates="payments")
