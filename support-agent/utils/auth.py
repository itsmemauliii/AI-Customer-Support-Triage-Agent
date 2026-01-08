import streamlit as st
from utils.supabase_client import supabase

def login():
    st.subheader("🔐 Login")

    email = st.text_input("Email")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        res = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password
        })
        st.session_state["user"] = res.user
        st.rerun()

def signup():
    st.subheader("🆕 Sign up")

    email = st.text_input("Email")
    password = st.text_input("Password", type="password")

    if st.button("Create account"):
        supabase.auth.sign_up({
            "email": email,
            "password": password
        })
        st.success("Account created. Please log in.")
