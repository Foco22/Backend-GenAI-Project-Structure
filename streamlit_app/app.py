import streamlit as st
import requests
import pandas as pd
import os
import json
import sys
from datetime import datetime

# Add the project root to the Python path to enable imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.agents.agent import call_agent
from src.llm.openai import OpenAI

# Set page configuration
st.set_page_config(
    page_title="Redmine Assistant",
    page_icon="💻",
    layout="centered"
)

# Add custom CSS for chat styling
st.markdown("""
<style>
.chat-message {
    padding: 1.5rem; border-radius: 0.5rem; margin-bottom: 1rem;
}
.chat-message.user {
    background-color: #e6f7ff;
    color: #333;
}
.chat-message.bot {
    background-color: #f0f2f6;
    color: #333;
}
.chat-message .message {
    width: 100%;
}
.main-header {
    text-align: center;
    margin-bottom: 2rem;
}
.footer {
    text-align: center;
    margin-top: 2rem;
    font-size: 0.8rem;
    color: #888;
}
</style>
""", unsafe_allow_html=True)

# Header
st.markdown('<h1 class="main-header">Redmine Assistant</h1>', unsafe_allow_html=True)


# Function to get response from model
def get_assistant_response(query, conversation_history=None):
    """Get response from the OpenAI model"""
    openai_client = OpenAI()
    try:
        return openai_client.get_assistant_response(query, conversation_history)
    except Exception as e:
        raise Exception(f"Error getting response from model: {str(e)}")

# Initialize chat history and session ID
import uuid

if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "¡Hola! Soy tu asistente de Redmine. ¿En qué puedo ayudarte hoy?"}
    ]
    
# Clear chat history button
if st.sidebar.button("Clear Chat History"):
    st.session_state.messages = [
        {"role": "assistant", "content": "¡Hola! Soy tu asistente de Redmine. ¿En qué puedo ayudarte hoy?"}
    ]
    st.rerun()

# UI Components
# ------------

# Create a container for the chat messages
chat_container = st.container()

# Display chat messages from history in the container
with chat_container:
    for message in st.session_state.messages:
        if message["role"] == "user":
            st.markdown(f"""
            <div class="chat-message user">
                <div class="message">{message['content']}</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="chat-message bot">
                <div class="message">{message['content']}</div>
            </div>
            """, unsafe_allow_html=True)


# Chat Interface
# -------------

# Helper function to format conversation history for the model
def prepare_conversation_history():
    """Convert session state messages to the format expected by OpenAI"""
    conversation_history = []
    for msg in st.session_state.messages:
        if msg["role"] != "system":  # Skip system messages
            conversation_history.append({
                "role": msg["role"],
                "content": msg["content"]
            })
    return conversation_history

# Helper function to display bot response
def display_bot_response(response_content):
    """Add the bot's response to chat history"""
    # Check if the response is a dict with tool calls
    if isinstance(response_content, dict) and 'tool_calls' in response_content:
        # Add assistant message with tool calls
        st.session_state.messages.append({
            "role": "assistant", 
            "content": response_content.get('content', ''),
            "tool_calls": response_content['tool_calls']
        })
        
        # If there are tool results, add them as tool messages
        if 'tool_results' in response_content:
            for tool_result in response_content['tool_results']:
                st.session_state.messages.append({
                    "role": "tool",
                    "content": tool_result['content'],
                    "tool_call_id": tool_result['tool_call_id']
                })
    else:
        # Simple text response
        st.session_state.messages.append({"role": "assistant", "content": response_content})
    # No rerun needed here

# Helper function to generate fallback responses
def get_fallback_response(user_input, demo_mode=False):
    """Generate a fallback response when the model fails"""
    mode_suffix = " (Demo mode)" if demo_mode else ""
    
    if "ticket" in user_input.lower() or "issue" in user_input.lower():
        return f"I can help you with Redmine tickets! You can ask me about ticket status, create new tickets, or search for specific issues.{mode_suffix}"
    elif "project" in user_input.lower() or "projects" in user_input.lower():
        return f"There are several active projects in Redmine: Web Development, Mobile App, Infrastructure, and Documentation. Which one would you like to know more about?{mode_suffix}"
    elif "status" in user_input.lower() or "progress" in user_input.lower():
        return f"The Web Development project is currently at 75% completion with 12 open tickets and 36 closed tickets. The next milestone is scheduled for August 15th.{mode_suffix}"
    elif "user" in user_input.lower() or "assign" in user_input.lower():
        return f"There are 15 active users in the system. The most active contributors this month are Alex, Maria, and John.{mode_suffix}"
    elif "help" in user_input.lower():
        return "I can help you with:\n- Checking ticket status\n- Creating new tickets\n- Finding information about projects\n- Generating reports\n- Assigning tasks to team members"
    else:
        if demo_mode:
            return f"I understand you're asking about '{user_input}'. I'm currently running in demo mode since I can't connect to my knowledge base."
        else:
            return f"I understand you're asking about '{user_input}'. I'm having trouble connecting to my knowledge base right now. Please try again later."

# User input area at the bottom
user_input = st.chat_input("Ask me about Redmine...")

if user_input:
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": user_input})
    
    # Process the query
    with st.spinner("Thinking..."):
        try:
            # Get conversation history
            conversation_history = prepare_conversation_history()
            
            # Get response from model
            # This is the Redmine username that will be used in the system message
            # and for automatically handling queries about "my tasks" or "my projects"
            user_str = 'sally'  # In a real app, this would come from authentication
            try:
                response_content = call_agent(user_input, st.session_state.session_id, user_str, conversation_history)
                if isinstance(response_content, dict) and 'message' in response_content:
                    message_response = response_content['message']
                    print('Response content:', message_response)
                    
                    # Add response to chat history and update UI
                    display_bot_response(message_response)
                else:
                    print('Unexpected response format:', response_content)
                    display_bot_response("I'm sorry, I encountered an error processing your request.")
            except Exception as e:
                print(f"Error in call_agent: {str(e)}")
                display_bot_response("I'm sorry, I encountered an error processing your request.")
            
        except Exception as e:
            # Log the error
            print('Error generating response:', str(e))
            st.error(f"Error generating response: {str(e)}", icon="🚨")
            
            # Get fallback response
            response_content = get_fallback_response(user_input)
            
            # Add fallback response to chat history and update UI
            display_bot_response(response_content)
            
    # Force a rerun to update the UI with all messages
    st.rerun()

# Footer
# ------
st.markdown("---")
st.caption(f"Redmine Assistant • Last updated: {datetime.now().strftime('%Y-%m-%d')}")
