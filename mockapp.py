import streamlit as st
import firebase_admin
from firebase_admin import credentials, auth
import time
import webbrowser
import os  # For opening URLs

# Initialize Firebase Admin SDK
if not firebase_admin._apps:
    cred = credentials.Certificate(r"C:\Users\aadik\OneDrive\Documents\Desktop\finalhari.py\codewHari.py\mock-20306-firebase-adminsdk-fbsvc-e03a8e8956.json")
    firebase_admin.initialize_app(cred)

# Streamlit App
st.title("AI Mock Interview System")

# Page Routing
if 'page' not in st.session_state:
    st.session_state.page = "login"

# Login Button
if 'login_clicked' not in st.session_state:
    st.session_state.login_clicked = False

if st.button("Login"):
    st.session_state.login_clicked = True

if st.session_state.login_clicked:
    option = st.radio("Select your role:", ("Candidate", "Recruiter"))

    if option == "Candidate":
        action = st.radio("Action:", ("Login", "Sign Up"))

        email = st.text_input("Email")
        password = st.text_input("Password", type="password")

        if action == "Sign Up":
            if st.button("Register", key="candidate_register"):
                try:
                    user = auth.create_user(email=email, password=password)
                    st.success("User registered successfully! Please login.")
                except Exception as e:
                    st.error(f"Error: {e}")

        elif action == "Login":
            if st.button("Login", key="candidate_login"):
                try:
                    user = auth.get_user_by_email(email)
                    st.success("Login Successful! Redirecting to interview platform...")
                    time.sleep(2)

                    # Redirect candidate to React app
                    REACT_APP_URL = "http://localhost:5173"  # Change to deployed URL if hosted
                    webbrowser.open(REACT_APP_URL)

                except Exception as e:
                    st.error(f"Login Failed: {e}")

    elif option == "Recruiter":
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")

        if st.button("Login", key="recruiter_login"):
            try:
                user = auth.get_user_by_email(email)
                if user.email == email:
                    st.success("Recruiter Login Successful! Redirecting...")
                    time.sleep(2)
                    os.system("streamlit run app.py")
                else:
                    st.error("Invalid credentials")
            except Exception as e:
                st.error(f"Login Failed: {e}")
