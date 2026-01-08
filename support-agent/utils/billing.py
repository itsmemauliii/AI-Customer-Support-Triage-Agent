import stripe
import streamlit as st

stripe.api_key = st.secrets["STRIPE_SECRET_KEY"]

def require_subscription(user):
    if not user.get("stripe_customer_id"):
        st.warning("💳 Subscription required")
        if st.button("Upgrade Now"):
            session = stripe.checkout.Session.create(
                customer_email=user["email"],
                mode="subscription",
                line_items=[{
                    "price": st.secrets["STRIPE_PRICE_ID"],
                    "quantity": 1
                }],
                success_url=st.secrets["APP_URL"],
                cancel_url=st.secrets["APP_URL"]
            )
            st.markdown(f"[👉 Pay Now]({session.url})")
        st.stop()
