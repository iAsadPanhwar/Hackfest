import os
from supabase import create_client
import streamlit as st

class SupabaseClient:
    def __init__(self, url, key):
        """
        Initialize the Supabase client
        
        Args:
            url (str): Supabase project URL
            key (str): Supabase project API key
        """
        self.supabase = create_client(url, key)
        self.bucket_name = "receipts"  # Default bucket name for receipts
        
        # Ensure the bucket exists
        try:
            self.supabase.storage.get_bucket(self.bucket_name)
        except Exception:
            # Bucket doesn't exist, create it
            try:
                self.supabase.storage.create_bucket(
                    self.bucket_name, 
                    {"public": True}  # Make bucket public
                )
            except Exception as e:
                print(f"Error creating bucket: {e}")
    
    def get_employees(self):
        """Fetch all employees from the database"""
        try:
            response = self.supabase.table('employees').select('*').execute()
            return response.data
        except Exception as e:
            st.error(f"Error fetching employees: {e}")
            return []
    
    def get_employee_by_id(self, employee_id):
        """
        Fetch an employee by ID
        
        Args:
            employee_id (int): The ID of the employee to fetch
            
        Returns:
            dict: Employee data or None if not found
        """
        try:
            response = self.supabase.table('employees').select('*').eq('id', employee_id).execute()
            if response.data and len(response.data) > 0:
                return response.data[0]
            return None
        except Exception as e:
            st.error(f"Error fetching employee by ID: {e}")
            return None
    
    def get_employees_by_condition(self, column, operator, value):
        """
        Fetch employees based on a condition
        
        Args:
            column (str): The column to filter on
            operator (str): The operator to use ('eq', 'gt', 'lt', 'lte', 'gte', 'like')
            value: The value to compare against
            
        Returns:
            list: List of matching employees
        """
        try:
            query = self.supabase.table('employees').select('*')
            
            if operator == 'eq':
                query = query.eq(column, value)
            elif operator == 'gt':
                query = query.gt(column, value)
            elif operator == 'lt':
                query = query.lt(column, value)
            elif operator == 'lte':
                query = query.lte(column, value)
            elif operator == 'gte':
                query = query.gte(column, value)
            elif operator == 'like':
                query = query.like(column, f'%{value}%')
            
            response = query.execute()
            return response.data
        except Exception as e:
            st.error(f"Error fetching employees by condition: {e}")
            return []
    
    def insert_employee(self, employee_data):
        """
        Insert a new employee into the database
        
        Args:
            employee_data (dict): The employee data to insert
            
        Returns:
            dict: The inserted employee data or None if failed
        """
        try:
            response = self.supabase.table('employees').insert(employee_data).execute()
            if response.data and len(response.data) > 0:
                return response.data[0]
            return None
        except Exception as e:
            st.error(f"Error inserting employee: {e}")
            return None
    
    def update_employee(self, employee_id, employee_data):
        """
        Update an existing employee in the database
        
        Args:
            employee_id (int): The ID of the employee to update
            employee_data (dict): The updated employee data
            
        Returns:
            dict: The updated employee data or None if failed
        """
        try:
            response = self.supabase.table('employees').update(employee_data).eq('id', employee_id).execute()
            if response.data and len(response.data) > 0:
                return response.data[0]
            return None
        except Exception as e:
            st.error(f"Error updating employee: {e}")
            return None
    
    def delete_employee(self, employee_id):
        """
        Delete an employee from the database
        
        Args:
            employee_id (int): The ID of the employee to delete
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            response = self.supabase.table('employees').delete().eq('id', employee_id).execute()
            return True if response.data else False
        except Exception as e:
            st.error(f"Error deleting employee: {e}")
            return False
    
    def get_refund_requests(self):
        """Fetch all refund requests from the database"""
        try:
            response = self.supabase.table('refund_requests').select('*').execute()
            return response.data
        except Exception as e:
            st.error(f"Error fetching refund requests: {e}")
            return []
    
    def get_refund_request_by_id(self, request_id):
        """
        Fetch a refund request by ID
        
        Args:
            request_id (int): The ID of the refund request to fetch
            
        Returns:
            dict: Refund request data or None if not found
        """
        try:
            response = self.supabase.table('refund_requests').select('*').eq('id', request_id).execute()
            if response.data and len(response.data) > 0:
                return response.data[0]
            return None
        except Exception as e:
            st.error(f"Error fetching refund request by ID: {e}")
            return None
    
    def update_refund_request(self, request_id, request_data):
        """
        Update an existing refund request in the database
        
        Args:
            request_id (int): The ID of the refund request to update
            request_data (dict): The updated refund request data
            
        Returns:
            dict: The updated refund request data or None if failed
        """
        try:
            response = self.supabase.table('refund_requests').update(request_data).eq('id', request_id).execute()
            if response.data and len(response.data) > 0:
                return response.data[0]
            return None
        except Exception as e:
            st.error(f"Error updating refund request: {e}")
            return None
    
    def get_storage_url(self, file_name):
        """
        Get the public URL for a file in Supabase storage
        
        Args:
            file_name (str): The name of the file
            
        Returns:
            str: The public URL of the file or None if not found
        """
        try:
            return self.supabase.storage.from_(self.bucket_name).get_public_url(file_name)
        except Exception as e:
            st.error(f"Error getting file URL: {e}")
            return None
    
    def upload_file(self, file_name, file_bytes):
        """
        Upload a file to Supabase storage
        
        Args:
            file_name (str): The name to give the file
            file_bytes (bytes): The file data
            
        Returns:
            str: The public URL of the uploaded file or None if failed
        """
        try:
            self.supabase.storage.from_(self.bucket_name).upload(file_name, file_bytes, {'content-type': 'auto'})
            return self.get_storage_url(file_name)
        except Exception as e:
            st.error(f"Error uploading file: {e}")
            return None
    
    def list_files(self):
        """
        List all files in the storage bucket
        
        Returns:
            list: List of file information dictionaries
        """
        try:
            return self.supabase.storage.from_(self.bucket_name).list()
        except Exception as e:
            st.error(f"Error listing files: {e}")
            return []
