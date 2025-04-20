import os
import requests
from typing import List, Dict, Any
from supabase import create_client
from dotenv import load_dotenv
import gdown
import tempfile

# Load environment variables
load_dotenv()

# Initialize Supabase client
supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)

def download_from_drive(folder_url: str) -> List[str]:
    """
    Download all receipt images from a Google Drive folder
    
    Args:
        folder_url (str): URL of the Google Drive folder
        
    Returns:
        List[str]: List of paths to downloaded files
    """
    try:
        # Create a temporary directory to store downloads
        temp_dir = tempfile.mkdtemp()
        
        # Extract folder ID from URL
        folder_id = folder_url.split('folders/')[-1].split('?')[0]
        
        # List files in the folder
        files_url = f"https://drive.google.com/drive/folders/{folder_id}"
        file_list = gdown.download_folder(url=files_url, output=temp_dir, quiet=False)
        
        return file_list if file_list else []
        
    except Exception as e:
        print(f"Error downloading from Google Drive: {e}")
        return []

def upload_to_supabase(file_paths: List[str]) -> List[Dict[str, Any]]:
    """
    Upload files to Supabase storage
    
    Args:
        file_paths (List[str]): List of paths to files to upload
        
    Returns:
        List[Dict[str, Any]]: List of upload results with file names and URLs
    """
    results = []
    
    try:
        for file_path in file_paths:
            try:
                # Get the file name
                file_name = os.path.basename(file_path)
                
                # Read the file
                with open(file_path, 'rb') as f:
                    file_data = f.read()
                
                # Upload to Supabase storage
                response = supabase.storage.from_('receipts').upload(
                    path=file_name,
                    file=file_data,
                    file_options={"content-type": "image/jpeg"}
                )
                
                # Get the public URL
                url = supabase.storage.from_('receipts').get_public_url(file_name)
                
                results.append({
                    "file_name": file_name,
                    "url": url,
                    "status": "success"
                })
                
            except Exception as e:
                print(f"Error uploading {file_path}: {e}")
                results.append({
                    "file_name": os.path.basename(file_path),
                    "error": str(e),
                    "status": "failed"
                })
                
    except Exception as e:
        print(f"Error in upload process: {e}")
        
    return results

def process_drive_folder(folder_url: str) -> Dict[str, Any]:
    """
    Download files from Google Drive and upload them to Supabase
    
    Args:
        folder_url (str): URL of the Google Drive folder
        
    Returns:
        Dict[str, Any]: Results of the process
    """
    try:
        # Download files from Google Drive
        downloaded_files = download_from_drive(folder_url)
        if not downloaded_files:
            return {
                "success": False,
                "message": "No files downloaded from Google Drive",
                "uploaded_files": []
            }
        
        # Upload files to Supabase
        upload_results = upload_to_supabase(downloaded_files)
        
        # Clean up temporary files
        for file_path in downloaded_files:
            try:
                os.remove(file_path)
            except:
                pass
        
        # Count successes and failures
        successes = sum(1 for r in upload_results if r["status"] == "success")
        failures = sum(1 for r in upload_results if r["status"] == "failed")
        
        return {
            "success": True,
            "message": f"Processed {len(downloaded_files)} files. {successes} uploaded successfully, {failures} failed.",
            "uploaded_files": upload_results
        }
        
    except Exception as e:
        return {
            "success": False,
            "message": f"Error processing drive folder: {str(e)}",
            "uploaded_files": []
        } 