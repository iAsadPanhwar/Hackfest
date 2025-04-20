import streamlit as st
import os
from supabase_client import SupabaseClient
from employee_management import EmployeeManagement
from refund_processing import RefundProcessing

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
with AI-powered image and audio analysis.
""")

# Initialize session state for Supabase client
if 'supabase_client' not in st.session_state:
    # Get Supabase credentials from environment variables or secrets
    supabase_url = os.getenv("SUPABASE_URL", "")
    supabase_key = os.getenv("SUPABASE_KEY", "")
    
    # Initialize Supabase client
    if supabase_url and supabase_key:
        st.session_state.supabase_client = SupabaseClient(supabase_url, supabase_key)
        st.session_state.connection_status = "Connected"
    else:
        st.session_state.connection_status = "Not Connected"
        st.error("Supabase credentials not found. Please set SUPABASE_URL and SUPABASE_KEY environment variables.")

# Connection status indicator
connection_status = st.sidebar.container()
connection_status.markdown(f"**Status:** {st.session_state.get('connection_status', 'Not Connected')}")

# Check if OpenAI API key is available
openai_api_key = os.getenv("OPENAI_API_KEY", "")
if not openai_api_key:
    st.sidebar.warning("OpenAI API key not found. Some features may not work properly.")

# Main navigation sidebar
st.sidebar.title("Navigation")
page = st.sidebar.radio(
    "Select a page",
    ["Employee Management", "Refund Requests", "Image Analysis", "Audio Analysis"]
)

# Display appropriate page based on selection
if page == "Employee Management":
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
