import os
from dotenv import load_dotenv
import google.generativeai as genai
from PIL import Image
import requests
from io import BytesIO
from typing import Optional
import re

# Load environment variables
load_dotenv()

# Configure Gemini
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
model = genai.GenerativeModel('gemini-1.5-flash')

def extract_amount_from_receipt(image_url: str) -> Optional[float]:
    """
    Extract the total amount from a receipt image using Gemini Vision
    
    Args:
        image_url (str): Public URL of the receipt image
        
    Returns:
        Optional[float]: The total amount from the receipt, or None if extraction fails
    """
    try:
        # Download the image from URL
        response = requests.get(image_url)
        img = Image.open(BytesIO(response.content))
        
        # Prepare the prompt for Gemini
        prompt = """
        Analyze this receipt image and find the total amount.
        Look for terms like 'Total', 'Total Amount', 'Grand Total', 'Amount Due', etc.
        Return ONLY the numerical value (e.g., if total is $123.45, return just 123.45).
        If there are multiple amounts, return the largest one or the final total.
        Do not include any currency symbols, text, or explanations.
        """
        
        # Generate response from Gemini
        response = model.generate_content([prompt, img])
        
        # Extract the amount from response
        if response.text:
            # Clean up the response
            text = response.text.strip().lower()
            
            # Try to find a number in the text
            # Look for patterns like "123.45" or "123"
            amount_match = re.search(r'\d+\.?\d*', text)
            if amount_match:
                try:
                    return float(amount_match.group())
                except ValueError:
                    print(f"Could not convert {amount_match.group()} to float")
                    return None
            
            # If no match found with regex, try cleaning up the text
            amount_str = ''.join(filter(lambda x: x.isdigit() or x == '.', text))
            if amount_str:
                try:
                    return float(amount_str)
                except ValueError:
                    print(f"Could not convert {amount_str} to float")
                    return None
        
        print(f"No valid amount found in response: {response.text}")
        return None
        
    except Exception as e:
        print(f"Error processing receipt: {e}")
        return None 