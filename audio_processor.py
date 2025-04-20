import os
import tempfile
import requests
from typing import Dict, Any, List
from langchain_groq import ChatGroq
from database_operations import supabase

def ensure_bucket_exists(bucket_name: str) -> bool:
    """
    Check if bucket exists, create if it doesn't
    
    Args:
        bucket_name (str): Name of the bucket
        
    Returns:
        bool: True if bucket exists or was created, False otherwise
    """
    try:
        # List all buckets
        buckets = supabase.storage.list_buckets()
        bucket_exists = any(bucket.name == bucket_name for bucket in buckets)
        
        if not bucket_exists:
            # Try to create the bucket
            supabase.storage.create_bucket(bucket_name)
            print(f"Created new bucket: {bucket_name}")
        return True
        
    except Exception as e:
        print(f"Error managing bucket {bucket_name}: {e}")
        return False

def download_audio_file(url: str) -> str:
    """
    Download audio file from URL to temporary location
    
    Args:
        url (str): URL of the audio file
        
    Returns:
        str: Path to downloaded file, or empty string if failed
    """
    try:
        # Create temp directory if it doesn't exist
        temp_dir = os.path.join(tempfile.gettempdir(), 'audio_processing')
        os.makedirs(temp_dir, exist_ok=True)
        
        # Generate a safe filename from the URL
        filename = url.split('/')[-1].split('?')[0]
        temp_file = os.path.join(temp_dir, f"temp_audio_{filename}")
        
        # Download file using requests
        response = requests.get(url)
        response.raise_for_status()  # Raise exception for bad status codes
        
        # Save the file
        with open(temp_file, 'wb') as f:
            f.write(response.content)
            
        print(f"Successfully downloaded file to: {temp_file}")
        return temp_file
        
    except Exception as e:
        print(f"Error downloading audio file: {str(e)}")
        return ""

def transcribe_and_summarize_audio(audio_url: str) -> Dict[str, Any]:
    """
    Download, transcribe and summarize audio file using Groq's whisper-large-v3-turbo
    
    Args:
        audio_url (str): URL of the audio file
        
    Returns:
        Dict[str, Any]: Results containing success status, transcription, summary, and any errors
    """
    try:
        # Download the file
        local_path = download_audio_file(audio_url)
        if not local_path:
            return {
                "success": False,
                "error": "Failed to download audio file"
            }

        # Initialize Groq client
        llm = ChatGroq(
            groq_api_key=os.getenv("GROQ_API_KEY"),
            model_name="whisper-large-v3-turbo"
        )
            
        # Transcribe audio using Whisper
        with open(local_path, 'rb') as audio_file:
            transcription_response = llm.invoke([{
                "role": "user",
                "content": "Please transcribe this audio file",
                "audio": audio_file
            }])
            transcription = transcription_response.content

        # Generate summary using Groq
        summary_response = llm.invoke([{
            "role": "system",
            "content": "You are a helpful assistant that provides concise summaries."
        }, {
            "role": "user",
            "content": f"Please provide a concise summary of this transcription: {transcription}"
        }])
        
        # Clean up temporary file
        try:
            os.remove(local_path)
        except:
            pass
            
        return {
            "success": True,
            "transcription": transcription,
            "summary": summary_response.content
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

def process_all_audio_files(audio_urls: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Process a list of audio files
    
    Args:
        audio_urls: List of dictionaries containing id and audio_url
        
    Returns:
        Dict[str, Any]: Results of processing all audio files
    """
    results = []
    processed = 0
    failed = 0
    
    try:
        for audio_file in audio_urls:
            try:
                # Process each audio file
                result = transcribe_and_summarize_audio(audio_file["audio_url"])
                
                if result["success"]:
                    results.append({
                        "id": audio_file["id"],
                        "audio_url": audio_file["audio_url"],
                        "transcription": result.get("transcription", ""),
                        "summary": result.get("summary", ""),
                        "status": "processed"
                    })
                    processed += 1
                else:
                    results.append({
                        "id": audio_file["id"],
                        "audio_url": audio_file["audio_url"],
                        "error": result["error"],
                        "status": "failed"
                    })
                    failed += 1
                    
            except Exception as e:
                print(f"Error processing audio file {audio_file['id']}: {e}")
                failed += 1
                continue
        
        return {
            "response": f"Successfully processed {processed} audio files. {failed} failed.",
            "data": results
        }
            
    except Exception as e:
        return {
            "response": f"Error processing audio files: {str(e)}",
            "data": []
        } 