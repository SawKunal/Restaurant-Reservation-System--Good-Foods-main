"""Streamlit frontend for the Restaurant AI Agent."""

import streamlit as st
import os
import sys
from typing import List, Dict

# Add the project root directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.agent.conversation_manager import ConversationManager
from src.config.settings import get_settings
from src.utils.logger import main_logger

# Page configuration
st.set_page_config(
    page_title="Restaurant AI Agent",
    page_icon="🍽️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        text-align: center;
        color: #2E86AB;
        font-size: 2.5rem;
        margin-bottom: 1rem;
    }
    
    .chat-message {
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 10px;
    }
    
    .user-message {
        background-color: #E3F2FD;
        border-left: 4px solid #2196F3;
    }
    
    .assistant-message {
        background-color: #F1F8E9;
        border-left: 4px solid #4CAF50;
    }
    
    .sidebar-info {
        background-color: #F5F5F5;
        padding: 1rem;
        border-radius: 8px;
        margin-bottom: 1rem;
    }
    
    .feature-card {
        background-color: #FAFAFA;
        padding: 1rem;
        border-radius: 8px;
        border: 1px solid #E0E0E0;
        margin-bottom: 1rem;
    }
    
    .status-indicator {
        display: inline-block;
        width: 10px;
        height: 10px;
        border-radius: 50%;
        margin-right: 8px;
    }
    
    .status-connected {
        background-color: #4CAF50;
    }
    
    .status-error {
        background-color: #F44336;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'conversation_manager' not in st.session_state:
    try:
        main_logger.log_session_start({"platform": "streamlit", "user_agent": "web"})
        st.session_state.conversation_manager = ConversationManager()
        st.session_state.connection_status = "connected"
        main_logger.logger.info("✅ STREAMLIT: Conversation manager initialized successfully")
    except Exception as e:
        st.session_state.connection_status = f"error: {str(e)}"
        st.session_state.conversation_manager = None
        main_logger.log_error(e, "streamlit_initialization")

if 'messages' not in st.session_state:
    st.session_state.messages = []

if 'show_sample_queries' not in st.session_state:
    st.session_state.show_sample_queries = True

if 'session_id' not in st.session_state:
    import uuid
    st.session_state.session_id = str(uuid.uuid4())[:8]
    main_logger.logger.info(f"🆔 STREAMLIT SESSION: {st.session_state.session_id}")

def display_chat_message(role: str, content: str):
    """Display a chat message with appropriate styling."""
    if role == "user":
        st.markdown(f"""
        <div class="chat-message user-message">
            <strong>You:</strong> {content}
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class="chat-message assistant-message">
            <strong>Assistant:</strong> {content}
        </div>
        """, unsafe_allow_html=True)

def get_sample_queries() -> List[Dict[str, str]]:
    """Get sample queries for different functionalities."""
    return [
        {
            "category": "🔍 Search Restaurants",
            "queries": [
                "Find romantic Italian restaurants in Downtown",
                "Show me family-friendly Chinese restaurants",
                "I want a restaurant with outdoor seating under $40"
            ]
        },
        {
            "category": "📅 Check Availability", 
            "queries": [
                "Check availability at rest_001 for 4 people on 2024-12-20 at 19:00",
                "Is there a table for 2 on Friday evening at 7 PM?"
            ]
        },
        {
            "category": "📝 Make Reservation",
            "queries": [
                "Make a reservation for 4 people",
                "Book a table for tonight at 8 PM"
            ]
        },
        {
            "category": "❌ Cancel Reservation",
            "queries": [
                "Cancel my reservation",
                "I need to cancel the booking for John Smith"
            ]
        }
    ]

def main():
    """Main application function."""
    
    # Header
    st.markdown('<h1 class="main-header">🍽️ Restaurant AI Agent</h1>', unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.markdown("## 🤖 AI Agent Status")
        
        # Connection status
        if st.session_state.connection_status == "connected":
            st.markdown("""
            <div class="sidebar-info">
                <span class="status-indicator status-connected"></span>
                <strong>Connected</strong><br>
                Ready to help with reservations!
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="sidebar-info">
                <span class="status-indicator status-error"></span>
                <strong>Error</strong><br>
                {st.session_state.connection_status}
            </div>
            """, unsafe_allow_html=True)
            
            if st.button("🔄 Retry Connection"):
                try:
                    st.session_state.conversation_manager = ConversationManager()
                    st.session_state.connection_status = "connected"
                    st.rerun()
                except Exception as e:
                    st.session_state.connection_status = f"error: {str(e)}"
        
        st.markdown("## 🎯 Features")
        
        features = [
            ("🔍", "Search Restaurants", "Find restaurants by cuisine, location, and features"),
            ("📅", "Check Availability", "Real-time availability checking"),
            ("📝", "Make Reservations", "Book tables with confirmation"),
            ("❌", "Cancel Reservations", "Cancel existing bookings")
        ]
        
        for icon, title, description in features:
            st.markdown(f"""
            <div class="feature-card">
                <strong>{icon} {title}</strong><br>
                <small>{description}</small>
            </div>
            """, unsafe_allow_html=True)
        
        # Controls
        st.markdown("## ⚙️ Controls")
        
        if st.button("🗑️ Clear Conversation"):
            st.session_state.messages = []
            if st.session_state.conversation_manager:
                st.session_state.conversation_manager.clear_conversation()
            st.rerun()
        
        # Sample queries section
        st.markdown("## 💡 Sample Queries")
        
        if st.session_state.show_sample_queries:
            sample_queries = get_sample_queries()
            
            for category_info in sample_queries:
                with st.expander(category_info["category"]):
                    for query in category_info["queries"]:
                        if st.button(f"📋 {query[:30]}...", key=f"sample_{query}", help=query):
                            st.session_state.messages.append({"role": "user", "content": query})
                            st.rerun()
        
        # Settings
        with st.expander("⚙️ Settings"):
            st.session_state.show_sample_queries = st.checkbox("Show sample queries", value=st.session_state.show_sample_queries)
            
            # API key status
            settings = get_settings()
            if settings.GROQ_API_KEY:
                st.success("✅ Groq API key configured")
            else:
                st.error("❌ Groq API key not set")
                st.info("Set GROQ_API_KEY in your .env file")
    
    # Main chat area
    col1, col2, col3 = st.columns([1, 3, 1])
    
    with col2:
        # Welcome message
        if not st.session_state.messages:
            st.markdown("""
            ### 👋 Welcome to the Restaurant AI Agent!
            
            I can help you with:
            - 🔍 **Finding restaurants** based on your preferences
            - 📅 **Checking availability** for specific dates and times
            - 📝 **Making reservations** with all the details
            - ❌ **Canceling reservations** when needed
            
            Just type your request below or click on a sample query in the sidebar to get started!
            """)
        
        # Display conversation history
        for message in st.session_state.messages:
            display_chat_message(message["role"], message["content"])
        
        # Chat input
        if st.session_state.connection_status == "connected":
            user_input = st.chat_input("Type your message here...")
            
            if user_input:
                # Add user message to session state first
                st.session_state.messages.append({"role": "user", "content": user_input})
                
                # Immediately rerun to display user message in conversation area
                st.rerun()
        else:
            st.error("⚠️ Cannot send messages: AI agent is not connected")
        
        # Check if we need to process a new message (last message is from user and no processing flag)
        if (st.session_state.messages and 
            st.session_state.messages[-1]["role"] == "user" and 
            not st.session_state.get('processing', False)):
            
            # Set processing flag and get user message
            st.session_state.processing = True
            user_message = st.session_state.messages[-1]["content"]
            
            # Add thinking message to session state so it appears in conversation area
            st.session_state.messages.append({"role": "assistant", "content": "🤔 Thinking..."})
            
            # Rerun to show the thinking message in the conversation area
            st.rerun()
        
        # Process the AI response if we're in processing mode
        if st.session_state.get('processing', False):
            user_message = st.session_state.messages[-2]["content"]  # Get user message (second to last)
            
            try:
                # Get AI response
                response = st.session_state.conversation_manager.process_message(user_message)
                
                # Replace thinking message with actual response
                st.session_state.messages[-1] = {"role": "assistant", "content": response}
                
            except Exception as e:
                error_message = f"Sorry, I encountered an error: {str(e)}"
                # Replace thinking message with error message
                st.session_state.messages[-1] = {"role": "assistant", "content": error_message}
            
            # Clear processing flag and rerun to show final response
            st.session_state.processing = False
            st.rerun()
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #666; font-size: 0.9rem;">
        🍽️ Restaurant AI Agent | Powered by Groq & Streamlit | Built for GoodFoods Chain
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
