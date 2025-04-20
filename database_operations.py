from supabase import create_client
import os
from dotenv import load_dotenv
from typing import List, Dict, Any, Optional

# Load environment variables
load_dotenv()

# Initialize Supabase client
supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)

# Constants
STORAGE_BUCKET = 'reciept'  # Name of the storage bucket

def get_all_employees() -> List[Dict[str, Any]]:
    """Fetch all employees from the database"""
    try:
        response = supabase.table('employeees').select("*").execute()
        return response.data
    except Exception as e:
        print(f"Error fetching all employees: {e}")
        return []

def get_employee_by_id(employee_id: int) -> Optional[Dict[str, Any]]:
    """Fetch an employee by their ID"""
    try:
        response = supabase.table('employeees').select("*").eq('id', employee_id).execute()
        return response.data[0] if response.data else None
    except Exception as e:
        print(f"Error fetching employee by ID: {e}")
        return None

def get_employees_by_salary(salary: float) -> List[Dict[str, Any]]:
    """Get employees with exact salary match"""
    try:
        response = supabase.table('employeees').select("*").eq('salary', salary).execute()
        return response.data
    except Exception as e:
        print(f"Error fetching employees by salary: {e}")
        return []

def get_employee_highest_salary() -> Optional[Dict[str, Any]]:
    """Get the employee with the highest salary"""
    try:
        response = supabase.table('employeees').select("*").order('salary', desc=True).limit(1).execute()
        return response.data[0] if response.data else None
    except Exception as e:
        print(f"Error fetching employee with highest salary: {e}")
        return None

def get_employees_by_age_greater_than(age: int) -> List[Dict[str, Any]]:
    """Get all employees older than specified age"""
    try:
        response = supabase.table('employeees').select("*").gt('age', age).execute()
        return response.data
    except Exception as e:
        print(f"Error fetching employees by age: {e}")
        return []

def get_employees_by_name_start(letter: str) -> List[Dict[str, Any]]:
    """Get employees whose names start with specified letter"""
    try:
        response = supabase.table('employeees').select("*").ilike('name', f'{letter}%').execute()
        return response.data
    except Exception as e:
        print(f"Error fetching employees by name start: {e}")
        return []

def get_storage_file_url(file_path: str) -> str:
    """
    Get public URL for a file in Supabase storage bucket
    
    Args:
        file_path (str): Name of the file in the bucket
        
    Returns:
        str: Public URL of the file
    """
    try:
        # Get the public URL directly without checking existence
        # since we can see the files exist in the bucket
        url = supabase.storage.from_(STORAGE_BUCKET).get_public_url(file_path)
        print(f"Generated public URL for {file_path}: {url}")
        return url
        
    except Exception as e:
        print(f"Error getting file URL: {e}")
        return ""

def list_bucket_files() -> List[str]:
    """
    List all files in the storage bucket
    
    Returns:
        List[str]: List of file names in the bucket
    """
    try:
        files = supabase.storage.from_(STORAGE_BUCKET).list()
        return [file['name'] for file in files]
    except Exception as e:
        print(f"Error listing bucket files: {e}")
        return []

def create_refund_request(image_url: str, amount: float) -> Dict[str, Any]:
    """
    Create a new refund request entry
    
    Args:
        image_url (str): Public URL of the receipt image
        amount (float): Amount extracted from the receipt
        
    Returns:
        Dict[str, Any]: Created refund request record
    """
    try:
        data = {
            'image_url': image_url,
            'amount': amount,
            'status': 'pending'  # Default status
        }
        response = supabase.table('refund_requests').insert(data).execute()
        return response.data[0] if response.data else {}
    except Exception as e:
        print(f"Error creating refund request: {e}")
        return {}

def update_refund_row(row_id: int, image_url: str, amount: float) -> bool:
    """
    Update a specific row in the refund_requests table with image URL and amount
    
    Args:
        row_id (int): The row ID to update (1-10)
        image_url (str): Public URL of the receipt image
        amount (float): Amount extracted from the receipt
        
    Returns:
        bool: True if update was successful, False otherwise
    """
    try:
        data = {
            'image_url': image_url,
            'amount': amount
        }
        response = supabase.table('refund_requests').update(data).eq('id', row_id).execute()
        return bool(response.data)
    except Exception as e:
        print(f"Error updating refund row {row_id}: {e}")
        return False

def get_all_audio_urls() -> List[Dict[str, Any]]:
    """
    Get all audio URLs from the refund_requests table
    
    Returns:
        List[Dict[str, Any]]: List of dictionaries containing row ID and audio URL
    """
    try:
        response = supabase.table('refund_requests').select('id, audio_url').execute()
        return [
            {"id": row["id"], "audio_url": row["audio_url"]} 
            for row in response.data 
            if row.get("audio_url")
        ]
    except Exception as e:
        print(f"Error fetching audio URLs: {e}")
        return [] 