import streamlit as st
import pandas as pd
import os
import requests
import io
import base64
from openai import OpenAI
import tempfile
from dotenv import load_dotenv
from ai_agent import extract_amount_from_receipt, transcribe_audio, summarize_transcript

# Load environment variables
load_dotenv()

class RefundProcessing:
    def __init__(self, db_client):
        """
        Initialize the Refund Processing component
        
        Args:
            db_client (DatabaseClient): The initialized Database client
        """
        self.db_client = db_client
        self.openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY", ""))
    
    def display_refund_requests(self):
        """Display all refund requests"""
        st.header("Refund Requests")
        
        # Add refresh button
        if st.button("Refresh Refund Data", key="refresh_refunds"):
            st.session_state.pop('refund_requests', None)
        
        # Fetch refund requests if not already in session state
        if 'refund_requests' not in st.session_state:
            with st.spinner("Fetching refund requests..."):
                st.session_state.refund_requests = self.db_client.get_refund_requests()
        
        # Display refund requests in a table
        if st.session_state.refund_requests:
            df = pd.DataFrame(st.session_state.refund_requests)
            
            # Format columns for better display
            for col in ['image_url', 'audio_url']:
                if col in df.columns:
                    # Create clickable links for URLs
                    df[col] = df[col].apply(lambda x: f'<a href="{x}" target="_blank">View</a>' if x else '')
            
            st.write("Refund Requests:")
            st.dataframe(df, use_container_width=True, unsafe_allow_html=True)
            
            # Allow user to select a refund to view details
            if len(st.session_state.refund_requests) > 0:
                refund_options = {f"{req['name']} (ID: {req['id']})": req['id'] for req in st.session_state.refund_requests}
                selected_refund_label = st.selectbox("Select Refund to View Details", options=list(refund_options.keys()))
                selected_refund_id = refund_options[selected_refund_label]
                
                # Get the selected refund
                selected_refund = next((req for req in st.session_state.refund_requests if req['id'] == selected_refund_id), None)
                
                if selected_refund:
                    st.subheader("Refund Details")
                    
                    # Display refund details
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"**Customer Name:** {selected_refund['name']}")
                        st.write(f"**Refund Amount:** ${selected_refund['amount'] if selected_refund['amount'] else 'Not specified'}")
                    
                    # Display image if available
                    if selected_refund.get('image_url'):
                        with col2:
                            st.write("**Receipt Image:**")
                            st.image(selected_refund['image_url'], use_column_width=True)
                    
                    # Display audio player if available
                    if selected_refund.get('audio_url'):
                        st.write("**Audio Description:**")
                        st.audio(selected_refund['audio_url'])
        else:
            st.info("No refund requests found in the database.")
    
    def display_image_analysis(self):
        """Display interface for analyzing receipt images and updating refund requests"""
        st.header("Receipt Image Analysis")
        
        # Fetch refund requests
        if 'refund_requests' not in st.session_state:
            with st.spinner("Fetching refund requests..."):
                st.session_state.refund_requests = self.db_client.get_refund_requests()
        
        # Check if OpenAI API key is available
        if not os.getenv("OPENAI_API_KEY"):
            st.error("OpenAI API Key is required for image analysis. Please set the OPENAI_API_KEY environment variable.")
            return
        
        st.subheader("1. Manual Image Upload & Analysis")
        
        # Option 1: Manually upload an image for analysis
        uploaded_file = st.file_uploader("Upload a receipt image", type=["jpg", "jpeg", "png"])
        
        if uploaded_file:
            # Display the uploaded image
            st.image(uploaded_file, caption="Uploaded Receipt", use_column_width=True)
            
            # Analyze button
            if st.button("Analyze Receipt", key="analyze_single_receipt"):
                with st.spinner("Analyzing receipt..."):
                    # Convert the file to base64
                    bytes_data = uploaded_file.getvalue()
                    base64_image = base64.b64encode(bytes_data).decode("utf-8")
                    
                    # Extract amount from receipt using OpenAI Vision
                    amount = self.extract_amount_from_receipt(base64_image)
                    
                    if amount:
                        st.success(f"Analysis complete! Detected amount: ${amount}")
                    else:
                        st.error("Failed to extract amount from the receipt.")
        
        st.subheader("2. Batch Process Storage Images")
        
        # Option 2: Process multiple files from Supabase storage
        st.write("This will analyze all receipt images in storage and update the corresponding refund requests.")
        
        if st.button("Process All Images", key="process_all_receipts"):
            with st.spinner("Fetching image list..."):
                files = self.db_client.list_files()
                
                if not files:
                    st.warning("No files found in storage.")
                    return
                
                # Filter for image files
                image_files = [f for f in files if f.get('name', '').lower().endswith(('.png', '.jpg', '.jpeg'))]
                
                if not image_files:
                    st.warning("No image files found in storage.")
                    return
                
                st.write(f"Found {len(image_files)} images in storage.")
                
                # Process each image
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                for idx, file in enumerate(image_files):
                    file_name = file.get('name')
                    status_text.write(f"Processing {file_name}...")
                    
                    # Get file URL
                    file_url = self.db_client.get_storage_url(file_name)
                    
                    if not file_url:
                        status_text.write(f"Skipping {file_name}: Unable to get URL")
                        continue
                    
                    try:
                        # Download the image
                        response = requests.get(file_url)
                        if response.status_code != 200:
                            status_text.write(f"Skipping {file_name}: Failed to download image")
                            continue
                        
                        # Convert to base64
                        base64_image = base64.b64encode(response.content).decode("utf-8")
                        
                        # Extract amount
                        amount = self.extract_amount_from_receipt(base64_image)
                        
                        if not amount:
                            status_text.write(f"Skipping {file_name}: Failed to extract amount")
                            continue
                        
                        # Determine which refund request to update
                        # Assuming filename format is refund_req{id}.png
                        import re
                        match = re.search(r'refund_req(\d+)', file_name)
                        
                        if match:
                            row_id = int(match.group(1))
                            
                            # Find the corresponding refund request
                            refund_request = next((req for req in st.session_state.refund_requests if req['id'] == row_id), None)
                            
                            if refund_request:
                                # Update the refund request
                                updated_data = {
                                    "image_url": file_url,
                                    "amount": float(amount)
                                }
                                
                                result = self.db_client.update_refund_request(row_id, updated_data)
                                
                                if result:
                                    status_text.write(f"Updated refund request {row_id} with amount ${amount}")
                                else:
                                    status_text.write(f"Failed to update refund request {row_id}")
                            else:
                                status_text.write(f"No matching refund request found for {file_name}")
                        else:
                            status_text.write(f"Could not determine refund ID from filename {file_name}")
                    
                    except Exception as e:
                        status_text.write(f"Error processing {file_name}: {e}")
                    
                    # Update progress
                    progress_bar.progress((idx + 1) / len(image_files))
                
                # Reset session state to refresh data
                st.session_state.pop('refund_requests', None)
                status_text.write("Processing complete!")
                st.success("All receipts processed. The refund requests have been updated.")
    
    def extract_amount_from_receipt(self, base64_image):
        """
        Extract the total amount from a receipt image using AI
        
        Args:
            base64_image (str): Base64-encoded image data
            
        Returns:
            float or None: The extracted amount or None if extraction failed
        """
        try:
            # Use the AI agent implementation from ai_agent.py
            amount = extract_amount_from_receipt(base64_image)
            
            if amount:
                return float(amount)
            else:
                st.error("Failed to extract amount from receipt. Falling back to OpenAI.")
                # Fallback to OpenAI if Groq AI fails
                response = self.openai_client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {
                            "role": "system",
                            "content": "You are a receipt analyzer. Extract the total amount from the receipt image. Return just the numeric value without any currency symbols or additional text."
                        },
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": "What is the total amount on this receipt?"},
                                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                            ]
                        }
                    ],
                    max_tokens=50
                )
                
                # Extract amount from response
                result = response.choices[0].message.content.strip()
                
                # Clean up result - remove any non-numeric characters except decimal point
                import re
                cleaned_result = re.sub(r'[^\d.]', '', result)
                
                try:
                    # Convert to float
                    return float(cleaned_result)
                except ValueError:
                    st.error(f"Failed to convert extracted amount to a number: {result}")
                    return None
            
        except Exception as e:
            st.error(f"Error during image analysis: {e}")
            return None
    
    def display_audio_analysis(self):
        """Display interface for analyzing audio files and generating summaries"""
        st.header("Audio Analysis & Summarization")
        
        # Fetch refund requests
        if 'refund_requests' not in st.session_state:
            with st.spinner("Fetching refund requests..."):
                st.session_state.refund_requests = self.db_client.get_refund_requests()
        
        # Check if OpenAI API key is available
        if not os.getenv("OPENAI_API_KEY"):
            st.error("OpenAI API Key is required for audio analysis. Please set the OPENAI_API_KEY environment variable.")
            return
        
        st.subheader("1. Manual Audio Upload & Analysis")
        
        # Option 1: Manually upload an audio file for analysis
        uploaded_file = st.file_uploader("Upload an audio file", type=["mp3", "wav", "m4a", "ogg"])
        
        if uploaded_file:
            # Display audio player
            st.audio(uploaded_file)
            
            # Transcribe button
            if st.button("Transcribe & Summarize", key="analyze_single_audio"):
                with st.spinner("Processing audio..."):
                    # Save the uploaded file to a temporary file
                    with tempfile.NamedTemporaryFile(delete=False, suffix=f".{uploaded_file.name.split('.')[-1]}") as tmp_file:
                        tmp_file.write(uploaded_file.getvalue())
                        audio_path = tmp_file.name
                    
                    try:
                        # Transcribe the audio
                        transcript = self.transcribe_audio(audio_path)
                        
                        if transcript:
                            st.success("Transcription complete!")
                            st.write("**Transcript:**")
                            st.write(transcript)
                            
                            # Generate summary
                            summary = self.summarize_transcript(transcript)
                            
                            if summary:
                                st.write("**Summary:**")
                                st.write(summary)
                            else:
                                st.error("Failed to generate summary.")
                        else:
                            st.error("Failed to transcribe audio.")
                    except Exception as e:
                        st.error(f"Error processing audio: {e}")
                    finally:
                        # Clean up the temporary file
                        if os.path.exists(audio_path):
                            os.unlink(audio_path)
        
        st.subheader("2. Batch Process Audio URLs")
        
        # Option 2: Process audio URLs from the refund_requests table
        st.write("This will process all audio files referenced in the refund_requests table and generate summaries.")
        
        if st.button("Process All Audio Files", key="process_all_audio"):
            # Get refund requests with audio URLs
            refund_requests = st.session_state.refund_requests
            refund_requests_with_audio = [req for req in refund_requests if req.get('audio_url')]
            
            if not refund_requests_with_audio:
                st.warning("No refund requests with audio URLs found.")
                return
            
            st.write(f"Found {len(refund_requests_with_audio)} refund requests with audio URLs.")
            
            # Process each audio file
            results = []
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            for idx, req in enumerate(refund_requests_with_audio):
                audio_url = req.get('audio_url')
                req_id = req.get('id')
                customer_name = req.get('name')
                
                status_text.write(f"Processing audio for request {req_id} ({customer_name})...")
                
                try:
                    # Download the audio file
                    response = requests.get(audio_url)
                    if response.status_code != 200:
                        status_text.write(f"Skipping request {req_id}: Failed to download audio")
                        continue
                    
                    # Save to temporary file
                    audio_format = audio_url.split('.')[-1].lower()
                    if audio_format not in ['mp3', 'wav', 'ogg', 'm4a']:
                        audio_format = 'mp3'  # Default to mp3 if format is unknown
                    
                    with tempfile.NamedTemporaryFile(delete=False, suffix=f".{audio_format}") as tmp_file:
                        tmp_file.write(response.content)
                        audio_path = tmp_file.name
                    
                    # Transcribe and summarize
                    transcript = self.transcribe_audio(audio_path)
                    
                    if not transcript:
                        status_text.write(f"Skipping request {req_id}: Failed to transcribe audio")
                        continue
                    
                    summary = self.summarize_transcript(transcript)
                    
                    if not summary:
                        status_text.write(f"Skipping request {req_id}: Failed to generate summary")
                        continue
                    
                    # Add to results
                    results.append({
                        "id": req_id,
                        "name": customer_name,
                        "transcript": transcript,
                        "summary": summary
                    })
                    
                    status_text.write(f"Processed audio for request {req_id}")
                
                except Exception as e:
                    status_text.write(f"Error processing request {req_id}: {e}")
                finally:
                    # Clean up the temporary file
                    if 'audio_path' in locals() and os.path.exists(audio_path):
                        os.unlink(audio_path)
                
                # Update progress
                progress_bar.progress((idx + 1) / len(refund_requests_with_audio))
            
            # Display results
            if results:
                status_text.write("Processing complete!")
                st.success(f"Processed {len(results)} audio files.")
                
                # Convert to DataFrame for display
                df = pd.DataFrame(results)
                
                # Display summaries
                st.subheader("Audio Summaries")
                for idx, row in df.iterrows():
                    with st.expander(f"{row['name']} (ID: {row['id']})"):
                        st.write("**Summary:**")
                        st.write(row['summary'])
                        st.write("**Full Transcript:**")
                        st.write(row['transcript'])
            else:
                st.warning("No audio files were successfully processed.")
    
    def transcribe_audio(self, audio_path):
        """
        Transcribe an audio file using Groq or OpenAI Whisper
        
        Args:
            audio_path (str): Path to the audio file
            
        Returns:
            str or None: The transcribed text or None if transcription failed
        """
        try:
            # First try using our Groq AI agent implementation
            result = transcribe_audio(audio_path)
            
            if result:
                return result
            else:
                st.warning("Groq transcription failed, falling back to OpenAI Whisper")
                # Fallback to OpenAI if Groq fails
                with open(audio_path, "rb") as audio_file:
                    response = self.openai_client.audio.transcriptions.create(
                        model="whisper-1",
                        file=audio_file
                    )
                return response.text
        except Exception as e:
            st.error(f"Error during audio transcription: {e}")
            return None
    
    def summarize_transcript(self, transcript):
        """
        Generate a summary of a transcript using Groq or OpenAI
        
        Args:
            transcript (str): The transcript to summarize
            
        Returns:
            str or None: The summary or None if summarization failed
        """
        try:
            # First try using our Groq AI agent implementation
            result = summarize_transcript(transcript)
            
            if result:
                return result
            else:
                st.warning("Groq summarization failed, falling back to OpenAI")
                # Fallback to OpenAI if Groq fails
                response = self.openai_client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {
                            "role": "system",
                            "content": "You are an assistant that summarizes audio transcripts of refund requests. Create a concise summary that includes the reason for the refund, any relevant details, and the customer's tone or sentiment."
                        },
                        {
                            "role": "user",
                            "content": f"Summarize this transcript of a refund request:\n\n{transcript}"
                        }
                    ],
                    max_tokens=150
                )
                
                return response.choices[0].message.content
        except Exception as e:
            st.error(f"Error during transcript summarization: {e}")
            return None
