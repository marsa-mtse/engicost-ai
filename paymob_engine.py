"""
paymob_engine.py — Paymob Egypt Payment Gateway Integration
Supports Card payments (Visa/MC) and Fawry cash payments.

Flow:
  1. authenticate()          → get Paymob auth token
  2. create_order()          → register order in Paymob
  3. get_payment_key()       → get iframe payment key
  4. verify_callback()       → verify HMAC on webhook callback
"""

import requests
import hashlib
import hmac
import streamlit as st
from config import (
    PAYMOB_API_KEY, PAYMOB_HMAC_SECRET,
    PAYMOB_CARD_INTG_ID, PAYMOB_FAWRY_INTG_ID,
    PAYMOB_IFRAME_ID, PAYMOB_BASE_URL
)


# ─── Step 1: Authenticate ────────────────────────────────────────────────────
def authenticate() -> str | None:
    """Get a short-lived auth token from Paymob using the API key."""
    try:
        res = requests.post(
            f"{PAYMOB_BASE_URL}/auth/tokens",
            json={"api_key": PAYMOB_API_KEY},
            timeout=10
        )
        res.raise_for_status()
        return res.json().get("token")
    except Exception as e:
        st.error(f"Paymob Auth Error: {e}")
        return None


# ─── Step 2: Create Order ─────────────────────────────────────────────────────
def create_order(auth_token: str, amount_egp: float, merchant_order_id: str) -> dict | None:
    """Register a new order in Paymob. Amount is in EGP (we send piasters = × 100)."""
    try:
        res = requests.post(
            f"{PAYMOB_BASE_URL}/ecommerce/orders",
            json={
                "auth_token": auth_token,
                "delivery_needed": False,
                "amount_cents": int(amount_egp * 100),
                "currency": "EGP",
                "merchant_order_id": merchant_order_id,
                "items": [],
            },
            timeout=10
        )
        res.raise_for_status()
        return res.json()
    except Exception as e:
        st.error(f"Paymob Order Error: {e}")
        return None


# ─── Step 3: Get Payment Key ─────────────────────────────────────────────────
def get_payment_key(
    auth_token: str,
    order_id: int,
    amount_egp: float,
    user_email: str,
    user_name: str = "EngiCost User",
    integration_id: int = None,
    method: str = "card"
) -> str | None:
    """
    Get a single-use payment key.
    method: 'card' for Visa/MC, 'fawry' for Fawry cash
    """
    intg_id = integration_id or (
        PAYMOB_FAWRY_INTG_ID if method == "fawry" else PAYMOB_CARD_INTG_ID
    )
    try:
        res = requests.post(
            f"{PAYMOB_BASE_URL}/acceptance/payment_keys",
            json={
                "auth_token": auth_token,
                "amount_cents": int(amount_egp * 100),
                "expiration": 3600,
                "order_id": order_id,
                "currency": "EGP",
                "integration_id": intg_id,
                "billing_data": {
                    "first_name": user_name.split()[0],
                    "last_name": user_name.split()[-1] if len(user_name.split()) > 1 else ".",
                    "email": user_email,
                    "phone_number": "NA",
                    "apartment": "NA", "floor": "NA", "street": "NA",
                    "building": "NA", "shipping_method": "NA",
                    "postal_code": "NA", "city": "Cairo",
                    "country": "EG", "state": "Cairo",
                },
                "lock_order_when_paid": True,
            },
            timeout=10
        )
        res.raise_for_status()
        return res.json().get("token")
    except Exception as e:
        st.error(f"Paymob Payment Key Error: {e}")
        return None


# ─── Full Checkout Flow ───────────────────────────────────────────────────────
def create_checkout_url(
    amount_egp: float,
    user_email: str,
    user_name: str,
    merchant_order_id: str,
    method: str = "card"
) -> str | None:
    """
    End-to-end checkout: authenticates, creates order, gets payment key.
    Returns the Paymob iframe URL or Fawry reference.
    """
    token = authenticate()
    if not token:
        return None

    order = create_order(token, amount_egp, merchant_order_id)
    if not order:
        return None

    payment_key = get_payment_key(
        auth_token=token,
        order_id=order["id"],
        amount_egp=amount_egp,
        user_email=user_email,
        user_name=user_name,
        method=method
    )
    if not payment_key:
        return None

    if method == "card":
        return f"https://accept.paymob.com/api/acceptance/iframes/{PAYMOB_IFRAME_ID}?payment_token={payment_key}"
    elif method == "fawry":
        return f"https://accept.paymob.com/api/acceptance/payments/pay?payment_token={payment_key}"

    return None


# ─── HMAC Callback Verification ──────────────────────────────────────────────
def verify_callback(callback_data: dict) -> bool:
    """
    Verify Paymob HMAC signature on webhook/callback.
    Returns True if callback is authentic and payment is successful.
    """
    try:
        # Build the concatenated string Paymob requires
        keys_order = [
            "amount_cents", "created_at", "currency", "error_occured",
            "has_parent_transaction", "id", "integration_id",
            "is_3d_secure", "is_auth", "is_capture", "is_refunded",
            "is_standalone_payment", "is_voided", "order", "owner",
            "pending", "source_data_pan", "source_data_sub_type",
            "source_data_type", "success"
        ]
        obj = callback_data.get("obj", {})
        concat_str = "".join(str(obj.get(k, "")) for k in keys_order)

        expected_hmac = hmac.new(
            PAYMOB_HMAC_SECRET.encode("utf-8"),
            concat_str.encode("utf-8"),
            hashlib.sha512
        ).hexdigest()

        received_hmac = callback_data.get("hmac", "")
        is_valid = hmac.compare_digest(expected_hmac, received_hmac)
        is_success = str(obj.get("success", "")).lower() == "true"

        return is_valid and is_success
    except Exception:
        return False
