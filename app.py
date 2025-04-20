import streamlit as st
import json
from crewai_agent import run_crew

# Set page title and configure layout
st.set_page_config(page_title="AI Database Assistant", layout="wide")

# Add title
st.title("AI Database Assistant")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if "data" in message and message["data"]:
            st.dataframe(message["data"])

# Chat input
if prompt := st.chat_input("How can I help you with the employee database?"):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Display user message
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Display assistant response
    with st.chat_message("assistant"):
        try:
            result = run_crew(prompt)
            response_text = result.get("response", "No response available")
            data = result.get("data")
            
            # Display the response text
            st.markdown(response_text)
            
            # If there's structured data, display it in a table
            if data:
                st.dataframe(data)
            
            # Add assistant response to chat history
            st.session_state.messages.append({
                "role": "assistant",
                "content": response_text,
                "data": data
            })
            
        except Exception as e:
            error_message = f"Error: {str(e)}"
            st.error(error_message)
            st.session_state.messages.append({
                "role": "assistant",
                "content": error_message,
                "data": None
            })