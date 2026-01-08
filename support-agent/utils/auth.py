import streamlit as st
from utils.supabase_client import supabase

def login():
    st.subheader("🔐 Login")

    email = st.text_input("Email", key="login_email")
    password = st.text_input("Password", type="password", key="login_password")

    if st.button("Login"):
        try:
            res = supabase.auth.sign_in_with_password({
                "email": email,
                "password": password
            })

            if res.user:
                st.session_state["user"] = {
                    "id": res.user.id,
                    "email": res.user.email,
                    "role": get_user_role(res.user.id)
                }
                st.success("✅ Logged in successfully")
                st.rerun()
            else:
                st.error("Invalid credentials")

        except Exception as e:
            st.error("❌ Login failed. Check email & password.")
            st.caption(str(e))


def signup():
    st.subheader("🆕 Create Account")

    email = st.text_input("Email", key="signup_email")
    password = st.text_input("Password", type="password", key="signup_password")

    if st.button("Sign up"):
        try:
            res = supabase.auth.sign_up({
                "email": email,
                "password": password
            })

            if res.user:
                st.success("🎉 Account created! Please login.")
            else:
                st.error("Signup failed")

        except Exception as e:
            st.error("❌ Signup error")
            st.caption(str(e))


def logout():
    if st.sidebar.button("🚪 Logout"):
        supabase.auth.sign_out()
        st.session_state.clear()
        st.rerun()


def get_user_role(user_id):
    res = (
        supabase
        .table("users")
        .select("role")
        .eq("id", user_id)
        .execute()
    )

    if res.data and len(res.data) > 0:
        return res.data[0]["role"]

    return "agent"
