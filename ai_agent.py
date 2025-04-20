import os
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv
import base64
import requests
import tempfile
from openai import OpenAI

# Load environment variables
load_dotenv()

# Initialize Groq client
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = "llama3-70b-8192"  # Using llama3 model

# Simplified implementation for a direct integration with Groq
# without complex LangChain tools to avoid dependency issues
import groq

# Initialize Groq client
groq_client = groq.Client(api_key=GROQ_API_KEY)

def ask_groq(prompt: str) -> str:
    """Send a prompt to Groq and get a response"""
    try:
        completion = groq_client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {"role": "system", "content": "You are a helpful AI assistant."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2,
            max_tokens=1000,
        )
        return completion.choices[0].message.content
    except Exception as e:
        print(f"Error querying Groq: {e}")
        return ""

# Simple implementation of AI functions for integration with the application
def extract_amount_from_receipt(base64_image: str) -> Optional[float]:
    """
    Extract the total amount from a receipt image using OpenAI Vision
    
    Args:
        base64_image (str): Base64-encoded image data
        
    Returns:
        float or None: The extracted amount or None if extraction failed
    """
    try:
        # Using OpenAI for image analysis since Groq doesn't support vision
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY", ""))
        
        # Call OpenAI API to analyze the image
        response = client.chat.completions.create(
            model="gpt-4o",  # Using Vision model
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
        
        # Convert to float
        return float(cleaned_result)
    except Exception as e:
        print(f"Error during image analysis: {e}")
        return None

def transcribe_audio(audio_path: str) -> Optional[str]:
    """
    Transcribe an audio file using OpenAI Whisper
    
    Args:
        audio_path (str): Path to the audio file
        
    Returns:
        str or None: The transcribed text or None if transcription failed
    """
    try:
        # OpenAI is used for audio transcription as Groq doesn't support this yet
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY", ""))
        
        with open(audio_path, "rb") as audio_file:
            response = client.audio.transcriptions.create(
                model="whisper-1", 
                file=audio_file
            )
        return response.text
    except Exception as e:
        print(f"Error during audio transcription: {e}")
        return None

def summarize_transcript(transcript: str) -> Optional[str]:
    """
    Summarize transcript using Groq
    
    Args:
        transcript (str): The text to summarize
        
    Returns:
        str or None: The summary of the transcript
    """
    try:
        prompt = f"Summarize the following transcript in a concise way while capturing the key points. Include the reason for the refund request, any relevant details, and the customer's tone or sentiment:\n\n{transcript}"
        return ask_groq(prompt)
    except Exception as e:
        print(f"Error during transcript summarization: {e}")
        return None
        
def run_agent(query: str) -> Dict[str, Any]:
    """
    Run a simple agent with the user query
    
    Args:
        query (str): The user query
        
    Returns:
        dict: The agent response
    """
    try:
        # Classify the task
        task_prompt = f"""
        You are a task classifier for an AI system. Given the query, classify it into one of these categories:
        - employee_management: tasks related to employee data like fetching, adding, updating, or deleting
        - image_analysis: tasks related to analyzing receipt images
        - audio_analysis: tasks related to transcribing and summarizing audio files
        - general_query: any other general questions

        Query: {query}
        
        Respond with just the category name.
        """
        
        task_category = ask_groq(task_prompt).strip()
        
        # Based on the task category, generate a response
        if task_category == "employee_management":
            prompt = f"""
            You are an employee management expert. Help with the following task:
            
            Task: {query}
            
            Provide detailed steps on how to handle this employee management task using Supabase.
            """
        elif task_category == "image_analysis":
            prompt = f"""
            You are an image analysis expert. Help with the following task:
            
            Task: {query}
            
            Provide detailed steps on how to analyze receipt images and extract amounts.
            """
        elif task_category == "audio_analysis":
            prompt = f"""
            You are an audio analysis expert. Help with the following task:
            
            Task: {query}
            
            Provide detailed steps on how to transcribe and summarize audio files.
            """
        else:
            prompt = f"""
            You are a helpful assistant. Answer the following query:
            
            Query: {query}
            """
        
        # Get response from Groq
        response = ask_groq(prompt)
        
        # Return result
        return {
            "response": response,
            "task": task_category
        }
    except Exception as e:
        print(f"Error running agent: {e}")
        return {"response": f"Error: {str(e)}", "task": "error"}

