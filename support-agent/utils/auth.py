import streamlit as st
from utils.supabase_client import supabase

def login():
    st.subheader("🔐 Login")

    email = st.text_input("Email", key="login_email")
    password = st.text_input("Password", type="password", key="login_password")

    if st.button("Login", key="login_btn"):
        res = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password
        })
        st.session_state["user"] = res.user
        st.rerun()


def signup():
    st.subheader("🆕 Sign up")

    email = st.text_input("Email", key="signup_email")
    password = st.text_input("Password", type="password", key="signup_password")

    if st.button("Create account", key="signup_btn"):
        supabase.auth.sign_up({
            "email": email,
            "password": password
        })
        st.success("Account created. Please log in.")
