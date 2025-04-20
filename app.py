import streamlit as st
import os
from supabase_client import SupabaseClient
from employee_management import EmployeeManagement
from refund_processing import RefundProcessing
from dotenv import load_dotenv
from ai_agent import ask_groq, run_agent

# Load environment variables
load_dotenv()

# Set page configuration
st.set_page_config(
    page_title="EmerGen AI - Supabase Dashboard",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# App title and description
st.title("🤖 EmerGen AI - Supabase Dashboard")
st.markdown("""
This application connects to Supabase to manage employee data and process refund requests 
with AI-powered image and audio analysis using Groq LLM with LangChain and LangGraph.
""")

# Initialize session state for chat messages
if 'messages' not in st.session_state:
    st.session_state.messages = []

# Initialize session state for Supabase client
if 'supabase_client' not in st.session_state:
    # Get Supabase credentials from environment variables or secrets
    supabase_url = os.getenv("SUPABASE_URL", "")
    supabase_key = os.getenv("SUPABASE_KEY", "")
    
    # Debug info - temporary
    st.write(f"Supabase URL: {supabase_url}")
    st.write(f"Supabase Key: {'*' * (len(supabase_key) - 4) + supabase_key[-4:] if supabase_key else 'Not set'}")
    
    # Initialize Supabase client
    if supabase_url and supabase_key:
        try:
            st.session_state.supabase_client = SupabaseClient(supabase_url, supabase_key)
            st.session_state.connection_status = "Connected"
            st.success("Successfully connected to Supabase!")
        except Exception as e:
            st.error(f"Failed to connect to Supabase: {str(e)}")
            st.session_state.connection_status = "Error"
    else:
        st.session_state.connection_status = "Not Connected"
        st.error("Supabase credentials not found. Please set SUPABASE_URL and SUPABASE_KEY environment variables.")

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
        employee_mgmt = EmployeeManagement(st.session_state.supabase_client)
        employee_mgmt.display()
    else:
        st.error("Please connect to Supabase first.")

elif page == "Refund Requests":
    if st.session_state.get('connection_status') == "Connected":
        refund_proc = RefundProcessing(st.session_state.supabase_client)
        refund_proc.display_refund_requests()
    else:
        st.error("Please connect to Supabase first.")

elif page == "Image Analysis":
    if st.session_state.get('connection_status') == "Connected":
        refund_proc = RefundProcessing(st.session_state.supabase_client)
        refund_proc.display_image_analysis()
    else:
        st.error("Please connect to Supabase first.")

elif page == "Audio Analysis":
    if st.session_state.get('connection_status') == "Connected":
        refund_proc = RefundProcessing(st.session_state.supabase_client)
        refund_proc.display_audio_analysis()
    else:
        st.error("Please connect to Supabase first.")

# Footer
st.sidebar.markdown("---")
st.sidebar.markdown("© 2024 EmerGen AI")
