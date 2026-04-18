"""
Lavu — FastAPI Main Application
Run: uvicorn main:app --reload
"""

import os
import base64
import httpx
from datetime import datetime, timedelta
from typing import List

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from database import get_db, engine
from models import Base, User, Subscription, SubscriptionPlan, Order, Payment, OrderStatusHistory
from models import OrderStatus, PaymentStatus
from schemas import (
    CreateOrderRequest, UpdateOrderStatusRequest, OrderOut,
    InitiatePaymentRequest, MpesaCallbackRequest, PaymentOut,
    SelectPlanRequest, SubscriptionPlanOut, SubscriptionOut,
    SubscriberUsageOut
)
from email_service import email_service

# Create tables on startup
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Lavu Laundry API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # tighten this in production
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─────────────────────────────────────────
#  M-PESA CONFIG
#  ↓ Replace these with your Daraja credentials
#  Get them at: https://developer.safaricom.co.ke
# ─────────────────────────────────────────

MPESA_CONSUMER_KEY = os.getenv("MPESA_CONSUMER_KEY", "YOUR_CONSUMER_KEY_HERE")
MPESA_CONSUMER_SECRET = os.getenv(
    "MPESA_CONSUMER_SECRET", "YOUR_CONSUMER_SECRET_HERE")
MPESA_SHORTCODE = os.getenv(
    "MPESA_SHORTCODE", "174379")        # Sandbox shortcode
MPESA_PASSKEY = os.getenv("MPESA_PASSKEY", "YOUR_PASSKEY_HERE")
MPESA_CALLBACK_URL = os.getenv(
    "MPESA_CALLBACK_URL", "https://your-domain.com/api/mpesa/callback")

# Toggle between sandbox and production:
# change to api.safaricom.co.ke in prod
MPESA_BASE_URL = "https://sandbox.safaricom.co.ke"


# ─────────────────────────────────────────
#  M-PESA HELPERS
# ─────────────────────────────────────────

async def get_mpesa_token() -> str:
    """Fetch OAuth token from Safaricom Daraja."""
    credentials = base64.b64encode(
        f"{MPESA_CONSUMER_KEY}:{MPESA_CONSUMER_SECRET}".encode()
    ).decode()

    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{MPESA_BASE_URL}/oauth/v1/generate?grant_type=client_credentials",
            headers={"Authorization": f"Basic {credentials}"}
        )
        response.raise_for_status()
        return response.json()["access_token"]


async def initiate_stk_push(phone: str, amount: float, account_ref: str) -> dict:
    """
    Trigger M-Pesa STK Push to the customer's phone.
    Returns the raw Daraja response containing CheckoutRequestID.
    """
    token = await get_mpesa_token()
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    password = base64.b64encode(
        f"{MPESA_SHORTCODE}{MPESA_PASSKEY}{timestamp}".encode()
    ).decode()

    payload = {
        "BusinessShortCode": MPESA_SHORTCODE,
        "Password":          password,
        "Timestamp":         timestamp,
        "TransactionType":   "CustomerPayBillOnline",
        "Amount":            int(amount),       # M-Pesa requires integer
        "PartyA":            phone,             # customer phone 254XXXXXXXXX
        "PartyB":            MPESA_SHORTCODE,
        "PhoneNumber":       phone,
        "CallBackURL":       MPESA_CALLBACK_URL,
        "AccountReference":  account_ref,       # e.g. "Lavu-SUB-42"
        "TransactionDesc":   "Lavu Monthly Subscription"
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{MPESA_BASE_URL}/mpesa/stkpush/v1/processrequest",
            json=payload,
            headers={"Authorization": f"Bearer {token}"}
        )
        response.raise_for_status()
        return response.json()


# ─────────────────────────────────────────
#  SUBSCRIPTION PLAN ROUTES
# ─────────────────────────────────────────

@app.get("/api/plans", response_model=List[SubscriptionPlanOut])
def get_plans(db: Session = Depends(get_db)):
    """Return all available subscription tiers."""
    return db.query(SubscriptionPlan).all()


@app.post("/api/subscriptions/select")
def select_plan(request: SelectPlanRequest, db: Session = Depends(get_db)):
    """
    User selects a subscription plan.
    TODO: Add JWT auth dependency and get current_user from token.
    """
    plan = db.query(SubscriptionPlan).filter(
        SubscriptionPlan.id == request.plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")

    # TODO: Replace hardcoded user_id=1 with current_user.id from JWT
    user_id = 1

    subscription = Subscription(
        user_id=user_id,
        plan_id=plan.id,
        renewal_date=datetime.utcnow() + timedelta(days=30)
    )
    db.add(subscription)
    db.commit()
    db.refresh(subscription)
    return {"message": "Plan selected", "subscription_id": subscription.id}


# ─────────────────────────────────────────
#  ORDER ROUTES
# ─────────────────────────────────────────

@app.post("/api/orders", response_model=OrderOut)
def create_order(request: CreateOrderRequest, db: Session = Depends(get_db)):
    """Schedule a laundry pickup."""
    # TODO: Replace with JWT current_user
    user_id = 1

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    order = Order(
        user_id=user_id,
        scheduled_pickup=request.scheduled_pickup,
        pickup_address=request.pickup_address,
        delivery_address=request.delivery_address,
        notes=request.notes,
    )
    db.add(order)
    db.commit()
    db.refresh(order)

    # Send order confirmation email
    if user.email:
        scheduled_date = order.scheduled_pickup.strftime(
            '%A, %B %d, %Y at %I:%M %p')
        email_service.send_order_confirmation(
            customer_email=user.email,
            customer_name=user.full_name,
            order_id=order.id,
            pickup_address=order.pickup_address,
            pickup_date=scheduled_date,
            order_notes=order.notes
        )

    return order


@app.get("/api/orders/{order_id}", response_model=OrderOut)
def get_order(order_id: int, db: Session = Depends(get_db)):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order


@app.patch("/api/orders/{order_id}/status")
def update_order_status(
    order_id: int,
    request: UpdateOrderStatusRequest,
    db: Session = Depends(get_db)
):
    """Admin endpoint: move an order through its lifecycle."""
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    order.status = request.status
    order.updated_at = datetime.utcnow()
    db.commit()
    return {"message": f"Order {order_id} updated to {request.status}"}


# ─────────────────────────────────────────
#  PAYMENT ROUTES (M-PESA)
# ─────────────────────────────────────────

@app.post("/api/payments/initiate", response_model=PaymentOut)
async def initiate_payment(request: InitiatePaymentRequest, db: Session = Depends(get_db)):
    """
    Trigger STK Push for the user's monthly subscription.
    The customer's phone will prompt them to enter their M-Pesa PIN.
    """
    # TODO: Replace with JWT current_user
    user_id = 1

    subscription = db.query(Subscription).filter(
        Subscription.user_id == user_id).first()
    if not subscription or not subscription.is_active:
        raise HTTPException(
            status_code=400, detail="No active subscription found")

    amount = subscription.plan.price_kes

    # Create a pending payment record first
    payment = Payment(
        subscription_id=subscription.id,
        amount_kes=amount,
        phone_number=request.phone_number,
        status=PaymentStatus.PENDING
    )
    db.add(payment)
    db.commit()
    db.refresh(payment)

    # Trigger the STK Push
    try:
        daraja_response = await initiate_stk_push(
            phone=request.phone_number,
            amount=amount,
            account_ref=f"Lavu-SUB-{subscription.id}"
        )
        # Store the Daraja IDs for callback matching
        payment.merchant_request_id = daraja_response.get("MerchantRequestID")
        payment.checkout_request_id = daraja_response.get("CheckoutRequestID")
        db.commit()
        db.refresh(payment)
    except Exception as e:
        payment.status = PaymentStatus.FAILED
        db.commit()
        raise HTTPException(status_code=502, detail=f"M-Pesa error: {str(e)}")

    return payment


@app.post("/api/mpesa/callback")
async def mpesa_callback(payload: MpesaCallbackRequest, db: Session = Depends(get_db)):
    """
    Safaricom calls this URL after the customer completes (or cancels) payment.
    Register this URL in your Daraja app settings.
    """
    callback = payload.Body.get("stkCallback", {})
    result_code = callback.get("ResultCode")
    checkout_request_id = callback.get("CheckoutRequestID")

    payment = db.query(Payment).filter(
        Payment.checkout_request_id == checkout_request_id
    ).first()

    if not payment:
        return {"message": "Payment record not found"}

    if result_code == 0:
        # Success — extract receipt number from callback metadata
        items = callback.get("CallbackMetadata", {}).get("Item", [])
        receipt = next((i["Value"] for i in items if i["Name"]
                       == "MpesaReceiptNumber"), None)

        payment.status = PaymentStatus.COMPLETED
        payment.mpesa_receipt_number = receipt
        payment.completed_at = datetime.utcnow()

        # Renew the subscription by 30 days
        subscription = payment.subscription
        subscription.renewal_date = datetime.utcnow() + timedelta(days=30)
        subscription.kg_used_this_month = 0.0   # reset monthly usage

        # Send payment confirmation email
        user = subscription.user
        if user and user.email:
            email_service.send_payment_confirmation(
                customer_email=user.email,
                customer_name=user.full_name,
                amount=payment.amount_kes,
                receipt_number=receipt or "N/A",
                plan_tier=subscription.plan.tier.value
            )
    else:
        payment.status = PaymentStatus.FAILED

    db.commit()
    return {"ResultCode": 0, "ResultDesc": "Accepted"}


# ─────────────────────────────────────────
#  ADMIN ROUTES
# ─────────────────────────────────────────

@app.get("/api/admin/orders", response_model=List[OrderOut])
def admin_get_all_orders(db: Session = Depends(get_db)):
    """Admin: view all active (non-delivered) orders."""
    return db.query(Order).filter(
        Order.status != OrderStatus.DELIVERED
    ).order_by(Order.scheduled_pickup).all()


@app.get("/api/admin/analytics", response_model=List[SubscriberUsageOut])
def admin_analytics(db: Session = Depends(get_db)):
    """Admin: see KG usage per subscriber this month."""
    subscriptions = db.query(Subscription).filter(
        Subscription.is_active == True).all()
    result = []
    for sub in subscriptions:
        kg_limit = sub.plan.kg_limit
        kg_used = sub.kg_used_this_month
        result.append(SubscriberUsageOut(
            user_id=sub.user_id,
            full_name=sub.user.full_name,
            phone_number=sub.user.phone_number,
            plan_tier=sub.plan.tier,
            kg_limit=kg_limit,
            kg_used_this_month=kg_used,
            usage_percent=round((kg_used / kg_limit) * 100,
                                1) if kg_limit > 0 else 0
        ))
    return result


@app.put("/api/admin/orders/{order_id}")
def admin_update_order(
    order_id: int,
    request: UpdateOrderStatusRequest,
    db: Session = Depends(get_db)
):
    """Admin endpoint: update order status."""
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    user = db.query(User).filter(User.id == order.user_id).first()

    # Record status change in history
    status_history = OrderStatusHistory(
        order_id=order.id,
        status=request.status,
        note=request.note
    )

    old_status = order.status
    order.status = request.status
    order.updated_at = datetime.utcnow()
    db.add(status_history)
    db.commit()

    # Send email notifications based on status change
    if user and user.email:
        if request.status == OrderStatus.PICKED_UP:
            email_service.send_pickup_confirmation(
                customer_email=user.email,
                customer_name=user.full_name,
                order_id=order.id,
                weight=order.kg_weight or 0
            )
        elif request.status == OrderStatus.DELIVERED:
            email_service.send_delivery_confirmation(
                customer_email=user.email,
                customer_name=user.full_name,
                order_id=order.id,
                delivery_address=order.delivery_address
            )

    return {"message": f"Order {order_id} updated from {old_status} to {request.status}"}
