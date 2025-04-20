import streamlit as st
import os
import tempfile
import requests
import base64
from PIL import Image
from io import BytesIO

def download_file(url, local_filename=None):
    """
    Download a file from a URL to a local file
    
    Args:
        url (str): The URL to download from
        local_filename (str, optional): The local filename to save to
            
    Returns:
        str: Path to the downloaded file
    """
    if not local_filename:
        # Extract filename from URL
        local_filename = url.split('/')[-1]
    
    # Create temporary file if no specific path provided
    if '/' not in local_filename:
        temp_dir = tempfile.gettempdir()
        local_filename = os.path.join(temp_dir, local_filename)
    
    # Download the file
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        with open(local_filename, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
    
    return local_filename

def get_image_as_base64(image_file):
    """
    Convert an image file to base64
    
    Args:
        image_file: The image file (can be a path or file-like object)
            
    Returns:
        str: Base64-encoded image data
    """
    if isinstance(image_file, str):
        # If it's a path, open the file
        with open(image_file, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")
    else:
        # If it's already a file-like object
        return base64.b64encode(image_file.read()).decode("utf-8")

def resize_image(image_bytes, max_width=800):
    """
    Resize an image to a maximum width while maintaining aspect ratio
    
    Args:
        image_bytes (bytes): The image data
        max_width (int): Maximum width for the resized image
            
    Returns:
        bytes: The resized image data
    """
    try:
        # Open the image
        image = Image.open(BytesIO(image_bytes))
        
        # Calculate new dimensions
        width, height = image.size
        if width > max_width:
            ratio = max_width / width
            new_width = max_width
            new_height = int(height * ratio)
            
            # Resize the image
            image = image.resize((new_width, new_height), Image.LANCZOS)
        
        # Save to bytes
        output = BytesIO()
        image_format = image.format if image.format else 'JPEG'
        image.save(output, format=image_format)
        
        return output.getvalue()
    except Exception as e:
        st.error(f"Error resizing image: {e}")
        return image_bytes

def format_currency(amount):
    """
    Format a number as currency
    
    Args:
        amount (float or int): The amount to format
            
    Returns:
        str: Formatted currency string
    """
    if amount is None:
        return "N/A"
    
    try:
        return f"${amount:,.2f}"
    except (ValueError, TypeError):
        return f"${amount}"

def truncate_text(text, max_length=100):
    """
    Truncate text to a maximum length and add ellipsis
    
    Args:
        text (str): The text to truncate
        max_length (int): Maximum length before truncation
            
    Returns:
        str: Truncated text
    """
    if not text:
        return ""
    
    if len(text) <= max_length:
        return text
    
    return text[:max_length] + "..."

def display_error_message(error_text):
    """
    Display a formatted error message
    
    Args:
        error_text (str): The error message to display
    """
    st.error(f"Error: {error_text}")

def display_success_message(success_text):
    """
    Display a formatted success message
    
    Args:
        success_text (str): The success message to display
    """
    st.success(success_text)
