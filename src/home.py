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
        
        # Logout button
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.authenticated = False
            st.session_state.username = None
            st.session_state.messages = []
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
        
        # Clear chat button
        if st.button("🗑️ Clear Chat", use_container_width=True):
            st.session_state.messages = []
            st.rerun()
    
    # Main chat interface
    st.title("🤖 Lounge Access Advisor Chatbot")
    st.markdown("Ask me anything about lounge access, flight schedule, or travel tips!")
    
    # Initialize chat history
    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = []
        # Add welcome message
        st.session_state.chat_messages.append({
            "role": "assistant",
            "content": f"Hello {st.session_state.username}! 👋 I'm your Lounge Access Advisor. How can I help you today?"
        })


    start_chat_session()

