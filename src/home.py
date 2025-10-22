"""
Home page for the chatbot application
"""


import streamlit as st
from src.chat import start_chat_session


def show_home_page():
    """Display the main chatbot interface"""
    
    # Sidebar
    with st.sidebar:
        st.title("✈️ Lounge Access Advisor")
        st.success(f"👤 Logged in as: **{st.session_state.username}**")
        st.markdown("---")
        
        
        # Controls
        if st.button("🚪 Logout", use_container_width=True):
            # Clear all session data
            st.session_state.authenticated = False
            st.session_state.username = None
            st.session_state.chat_messages = []

            st.session_state.clear()
            st.rerun()
        
        st.markdown("---")
        st.markdown("### About")
        st.info("""
        This AI chatbot helps you:
        - Find lounge access information
        - Check eligibility
        - Get personalized recommendations
        - Answer travel-related queries
        """)

        st.caption("Your personalized lounge access advisor")
        if st.button("🗑️ Clear Chat", use_container_width=True):
            st.session_state.chat_messages = []
            st.rerun()
        
    
    # Main chat interface
    st.title("🤖 Lounge Access Advisor")
    st.markdown(f"Hello {st.session_state.username}! 👋 I'm your personalized Lounge Access Advisor. How can I help you today?")
    
    # Initialize chat
    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = []
    start_chat_session()