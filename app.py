import streamlit as st
import os
from database_client import DatabaseClient
from employee_management import EmployeeManagement
from refund_processing import RefundProcessing
from dotenv import load_dotenv
from ai_agent import ask_groq, run_agent

# Load environment variables
load_dotenv()

# Set page configuration
st.set_page_config(
    page_title="EmerGen AI - Database Dashboard",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# App title and description
st.title("🤖 EmerGen AI - Database Dashboard")
st.markdown("""
This application connects to PostgreSQL to manage employee data and process refund requests 
with AI-powered image and audio analysis using Groq LLM with LangChain and LangGraph.
""")

# Initialize session state for chat messages
if 'messages' not in st.session_state:
    st.session_state.messages = []

# Initialize session state for Database client
if 'db_client' not in st.session_state:
    # Get Database URL from environment variables or secrets
    database_url = os.getenv("DATABASE_URL", "")
    
    # Debug info - temporary
    if database_url:
        masked_url = database_url.split('@')[0].split(':')[0] + ':****@' + database_url.split('@')[1]
        st.write(f"Database URL: {masked_url}")
    else:
        st.write("Database URL: Not set")
    
    # Initialize Database client
    if database_url:
        try:
            st.session_state.db_client = DatabaseClient()
            st.session_state.connection_status = "Connected"
            st.success("Successfully connected to the database!")
        except Exception as e:
            st.error(f"Failed to connect to the database: {str(e)}")
            st.session_state.connection_status = "Error"
    else:
        st.session_state.connection_status = "Not Connected"
        st.error("Database URL not found. Please set DATABASE_URL environment variable.")

# Connection status indicator
connection_status = st.sidebar.container()
connection_status.markdown(f"**Status:** {st.session_state.get('connection_status', 'Not Connected')}")

# Check if GROQ API key is available
groq_api_key = os.getenv("GROQ_API_KEY", "")
if not groq_api_key:
    st.sidebar.warning("GROQ API key not found. AI chatbot features may not work properly.")

# Check if OpenAI API key is available
openai_api_key = os.getenv("OPENAI_API_KEY", "")
if not openai_api_key:
    st.sidebar.warning("OpenAI API key not found. Image and audio analysis features may not work properly.")

# Main navigation sidebar
st.sidebar.title("Navigation")
page = st.sidebar.radio(
    "Select a page",
    ["AI Assistant", "Employee Management", "Refund Requests", "Image Analysis", "Audio Analysis"]
)

# Display appropriate page based on selection
if page == "AI Assistant":
    st.header("Groq AI Assistant")
    st.markdown("""
    This AI assistant is powered by Groq's LLM model. You can ask it questions about employee management,
    refund processing, or any other general query.
    """)
    
    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])
    
    # Chat input
    if prompt := st.chat_input("How can I help you today?"):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Display user message in chat
        with st.chat_message("user"):
            st.write(prompt)
        
        # Generate response using the agent
        with st.spinner("Thinking..."):
            if groq_api_key:
                response = run_agent(prompt)
                assistant_response = response.get("response", "I'm sorry, I couldn't generate a response.")
            else:
                assistant_response = "GROQ API key not found. Please add it to the environment variables to enable this feature."
        
        # Add assistant response to chat history
        st.session_state.messages.append({"role": "assistant", "content": assistant_response})
        
        # Display assistant response in chat
        with st.chat_message("assistant"):
            st.write(assistant_response)

elif page == "Employee Management":
    if st.session_state.get('connection_status') == "Connected":
        employee_mgmt = EmployeeManagement(st.session_state.db_client)
        employee_mgmt.display()
    else:
        st.error("Please connect to the database first.")

elif page == "Refund Requests":
    if st.session_state.get('connection_status') == "Connected":
        refund_proc = RefundProcessing(st.session_state.db_client)
        refund_proc.display_refund_requests()
    else:
        st.error("Please connect to the database first.")

elif page == "Image Analysis":
    if st.session_state.get('connection_status') == "Connected":
        refund_proc = RefundProcessing(st.session_state.db_client)
        refund_proc.display_image_analysis()
    else:
        st.error("Please connect to the database first.")

elif page == "Audio Analysis":
    if st.session_state.get('connection_status') == "Connected":
        refund_proc = RefundProcessing(st.session_state.db_client)
        refund_proc.display_audio_analysis()
    else:
        st.error("Please connect to the database first.")

# Footer
st.sidebar.markdown("---")
st.sidebar.markdown("© 2024 EmerGen AI")
