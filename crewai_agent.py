import os
import json
import traceback
from dotenv import load_dotenv
from typing import Dict, List, Any, Union
from crewai import Agent, Task, Crew, Process
from langchain.tools import Tool
from langchain_groq import ChatGroq
from supabase import create_client, Client
import streamlit as st
from database_operations import *
from receipt_processor import extract_amount_from_receipt
from audio_processor import transcribe_and_summarize_audio
import re

# Load environment variables
load_dotenv()

# Set up Supabase client
supabase_url = os.getenv('SUPABASE_URL')
supabase_key = os.getenv('SUPABASE_KEY')

try:
    supabase = create_client(supabase_url, supabase_key)
    print("Supabase client created successfully")
except Exception as e:
    print(f"Error initializing Supabase client: {e}")
    traceback.print_exc()
    supabase = None

# Initialize Groq LLM for our agents
try:
    groq_api_key = os.getenv("GROQ_API_KEY")
    print(f"Initializing Groq LLM. API key exists: {bool(groq_api_key)}")
    llm = ChatGroq(
        api_key=groq_api_key,
        model="deepseek-r1-distill-llama-70b",
        temperature=0.1,
        max_tokens=2048,
    )
    print("Groq LLM initialized successfully")
except Exception as e:
    print(f"Error initializing Groq LLM: {e}")
    traceback.print_exc()

def process_all_receipts() -> Dict[str, Any]:
    """
    Process all receipts (refund_req1.png through refund_req10.png) and update refunds table
    
    Returns:
        Dict[str, Any]: Results of processing all receipts
    """
    results = []
    processed = 0
    failed = 0
    
    try:
        # Process receipts from 1 to 10
        for i in range(1, 11):
            file_name = f"refund_req{i}.png"
            try:
                # Get public URL for the receipt
                image_url = get_storage_file_url(file_name)
                if not image_url:
                    print(f"Could not get URL for {file_name}")
                    failed += 1
                    continue
                
                # Extract amount from receipt
                amount = extract_amount_from_receipt(image_url)
                if amount is None:
                    print(f"Could not extract amount from {file_name}")
                    failed += 1
                    continue
                
                # Update refunds table for this row
                success = update_refund_row(i, image_url, amount)
                if success:
                    results.append({
                        "row": i,
                        "file_name": file_name,
                        "amount": amount,
                        "url": image_url,
                        "status": "processed"
                    })
                    processed += 1
                else:
                    failed += 1
                    
            except Exception as e:
                print(f"Error processing {file_name}: {e}")
                failed += 1
                continue
        
        return {
            "response": f"Successfully processed {processed} receipts and updated refunds table. {failed} failed.",
            "data": results
        }
            
    except Exception as e:
        return {
            "response": f"Error processing receipts: {str(e)}",
            "data": []
        }

def process_all_audio_files() -> Dict[str, Any]:
    """
    Process all audio files from the refund_requests table
    
    Returns:
        Dict[str, Any]: Results of processing all audio files
    """
    results = []
    processed = 0
    failed = 0
    
    try:
        # Get all audio URLs
        audio_files = get_all_audio_urls()
        
        for audio_file in audio_files:
            try:
                # Process each audio file
                result = transcribe_and_summarize_audio(audio_file["audio_url"])
                
                if result["success"]:
                    results.append({
                        "id": audio_file["id"],
                        "audio_url": audio_file["audio_url"],
                        "summary": result["summary"],
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

def execute_database_operation(query_description: str) -> Dict[str, Any]:
    """
    Execute database operations based on natural language description
    
    Args:
        query_description (str): Natural language description of what to do
        
    Returns:
        Dict[str, Any]: Results and response message
    """
    query_description = query_description.lower()
    
    try:
        # Check if this is a request to process audio files
        if "audio" in query_description and "summary" in query_description:
            return process_all_audio_files()
            
        # Check if this is a request to process all receipts
        if "get all the urls" in query_description and "refund_req" in query_description:
            return process_all_receipts()
            
        # Handle other database queries
        if "all employees" in query_description or "list all" in query_description:
            data = get_all_employees()
            return {
                "response": "Here are all employees:",
                "data": data
            }
            
        elif "highest salary" in query_description:
            data = get_employee_highest_salary()
            return {
                "response": "Here is the employee with the highest salary:",
                "data": [data] if data else []
            }
            
        elif "salary" in query_description and any(x in query_description for x in ["is", "equals", "="]):
            # Extract salary value
            salary_match = re.search(r'\d+', query_description)
            if salary_match:
                salary = float(salary_match.group())
                data = get_employees_by_salary(salary)
                return {
                    "response": f"Here are employees with salary {salary}:",
                    "data": data
                }
                
        elif "age greater than" in query_description or "older than" in query_description:
            # Extract age value
            age_match = re.search(r'\d+', query_description)
            if age_match:
                age = int(age_match.group())
                data = get_employees_by_age_greater_than(age)
                return {
                    "response": f"Here are employees older than {age}:",
                    "data": data
                }
                
        elif "starts with" in query_description or "beginning with" in query_description:
            # Extract starting letter
            letter_match = re.search(r'with\s+["\']?([a-zA-Z])["\']?', query_description)
            if letter_match:
                letter = letter_match.group(1)
                data = get_employees_by_name_start(letter)
                return {
                    "response": f"Here are employees whose names start with '{letter}':",
                    "data": data
                }
                
        elif "id" in query_description:
            # Extract ID value
            id_match = re.search(r'\d+', query_description)
            if id_match:
                employee_id = int(id_match.group())
                data = get_employee_by_id(employee_id)
                return {
                    "response": f"Here is the employee with ID {employee_id}:",
                    "data": [data] if data else []
                }
                
        return {
            "response": "I couldn't understand the query. Please try rephrasing it.",
            "data": None
        }
        
    except Exception as e:
        return {
            "response": f"Error executing operation: {str(e)}",
            "data": None
        }

# Create agents
query_analyzer_agent = Agent(
    role='Query Analyzer',
    goal='Analyze user queries and determine the required database operation',
    backstory='I am an expert at understanding natural language queries and converting them into structured database operations.'
)

database_agent = Agent(
    role='Database Operator',
    goal='Execute database operations accurately and return results',
    backstory='I am a database expert who knows how to perform various operations on the employee database.'
)

response_formatter_agent = Agent(
    role='Response Formatter',
    goal='Format database results into clear, user-friendly responses',
    backstory='I am skilled at presenting data in a way that is easy for users to understand.'
)

def run_crew(query: str) -> Dict[str, Any]:
    """
    Process the user's query
    
    Args:
        query (str): The user's query
        
    Returns:
        Dict[str, Any]: The response and any data
    """
    return execute_database_operation(query) 