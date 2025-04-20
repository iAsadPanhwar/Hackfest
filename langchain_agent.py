import os
import json
import traceback
from dotenv import load_dotenv
from typing import Dict, List, Any, Union
from langchain_core.tools import tool
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_groq import ChatGroq
from langchain.agents import AgentExecutor, create_openai_tools_agent
from supabase import create_client
import streamlit as st

# Load environment variables
load_dotenv()

# Set up Supabase client with better error handling
supabase_url = os.getenv('SUPABASE_URL')
supabase_key = os.getenv('SUPABASE_KEY')

# Debug output for connection parameters
print(f"Connecting to Supabase: URL={supabase_url}, Key exists: {bool(supabase_key)}")

try:
    supabase = create_client(supabase_url, supabase_key)
    # Test connection by listing tables
    print("Supabase client created successfully")
except Exception as e:
    print(f"Error initializing Supabase client: {e}")
    traceback.print_exc()
    supabase = None

# Create a single tool for database interactions
@tool
def query_database(operation: str, params: Dict[str, Any] = None) -> Any:
    """
    Execute operations against the employee database.
    
    Args:
        operation (str): The operation to perform. Options are:
            - "get_all": Get all employees
            - "get_by_id": Get employee by ID
            - "get_by_salary": Get employees with specific salary
            - "get_by_age_gt": Get employees with age greater than value
            - "get_highest_salary": Get employee with highest salary
            - "get_by_name_starts": Get employees whose name starts with letter
            - "insert": Insert a new employee
            - "update": Update an existing employee
            - "delete": Delete an employee
        params (dict, optional): Parameters for the operation. 
            Required parameters depend on the operation:
            - "get_by_id": {"id": int}
            - "get_by_salary": {"salary": int}
            - "get_by_age_gt": {"age": int}
            - "get_by_name_starts": {"letter": str}
            - "insert": {"name": str, "age": int, "salary": int}
            - "update": {"id": int}, plus any of {"name": str, "age": int, "salary": int}
            - "delete": {"id": int}
    
    Returns:
        List or dict: The result of the operation, typically employee records
    """
    # Ensure params is a dictionary
    if params is None:
        params = {}
    
    try:
        print(f"Executing database operation: {operation} with params: {params}")
        
        # Handle different operations
        if operation == "get_all":
            response = supabase.table('employeees').select('*').execute()
            return response.data
            
        elif operation == "get_by_id":
            if not params or "id" not in params:
                return {"error": "ID parameter is required"}
            
            id_value = params["id"]
            response = supabase.table('employeees').select('*').eq('id', id_value).execute()
            if response.data and len(response.data) > 0:
                return response.data[0]
            return {"error": "No employee found with that ID"}
                
        elif operation == "get_by_salary":
            if not params or "salary" not in params:
                return {"error": "Salary parameter is required"}
                
            salary_value = params["salary"]
            response = supabase.table('employeees').select('*').eq('salary', salary_value).execute()
            return response.data
            
        elif operation == "get_by_age_gt":
            if not params or "age" not in params:
                return {"error": "Age parameter is required"}
                
            age_value = params["age"]
            response = supabase.table('employeees').select('*').gt('age', age_value).execute()
            return response.data
            
        elif operation == "get_highest_salary":
            response = supabase.table('employeees').select('*').order('salary', desc=True).limit(1).execute()
            if response.data and len(response.data) > 0:
                return response.data[0]
            return {"error": "No employees found"}
            
        elif operation == "get_by_name_starts":
            if not params or "letter" not in params:
                return {"error": "Letter parameter is required"}
                
            letter_value = params["letter"]
            response = supabase.table('employeees').select('*').ilike('name', f'{letter_value}%').execute()
            return response.data
            
        elif operation == "insert":
            if not params or not all(k in params for k in ["name", "age", "salary"]):
                return {"error": "Name, age, and salary parameters are required"}
                
            employee_data = {
                "name": params["name"],
                "age": params["age"],
                "salary": params["salary"]
            }
            response = supabase.table('employeees').insert(employee_data).execute()
            if response.data and len(response.data) > 0:
                return response.data[0]
            return {"error": "Failed to insert employee"}
            
        elif operation == "update":
            if not params or "id" not in params:
                return {"error": "ID parameter is required"}
                
            update_data = {}
            if "name" in params:
                update_data["name"] = params["name"]
            if "age" in params:
                update_data["age"] = params["age"]
            if "salary" in params:
                update_data["salary"] = params["salary"]
                
            if not update_data:
                return {"error": "At least one of name, age, or salary must be provided"}
                
            response = supabase.table('employeees').update(update_data).eq('id', params["id"]).execute()
            if response.data and len(response.data) > 0:
                return response.data[0]
            return {"error": "Failed to update employee or employee not found"}
            
        elif operation == "delete":
            if not params or "id" not in params:
                return {"error": "ID parameter is required"}
                
            response = supabase.table('employeees').delete().eq('id', params["id"]).execute()
            if response.data:
                return {"success": True, "message": f"Employee with ID {params['id']} deleted successfully"}
            return {"success": False, "message": f"Failed to delete employee with ID {params['id']}"}
            
        else:
            return {"error": f"Unknown operation: {operation}"}
            
    except Exception as e:
        print(f"Error executing database operation: {e}")
        traceback.print_exc()
        return {"error": str(e)}

# Create a Groq-based LLM
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
    
# List all the available tools
tools = [query_database]

# Create a basic agent prompt without any formatted variables other than input and agent_scratchpad
system_msg = """You are an AI assistant that helps manage an employee database. You can query the database to find employees, add new employees, update employee information, or delete employees.

The employee database has fields for id, name, age, and salary.

IMPORTANT: When using the query_database tool, always provide a valid dictionary for the 'params' argument. Even if no parameters are needed, provide an empty dictionary {}.

For example, to get all employees:
query_database(operation="get_all", params={})

To get the employee with the highest salary:
query_database(operation="get_highest_salary", params={})

For operations that require parameters, always include them in the params dictionary:
query_database(operation="get_by_id", params={"id": 1})
"""

# Create agent using only the required standard format
prompt = ChatPromptTemplate.from_template(
    """
{system_message}

USER: {input}
ASSISTANT: {agent_scratchpad}
"""
)

# Create the agent
try:
    print("Creating agent...")
    agent = create_openai_tools_agent(
        llm=llm,
        tools=tools,
        prompt=prompt.partial(system_message=system_msg)
    )
    print("Agent created successfully")
except Exception as e:
    print(f"Error creating agent: {e}")
    traceback.print_exc()

# Create the agent executor
try:
    print("Creating agent executor...")
    agent_executor = AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True,
        handle_parsing_errors=True,
        max_iterations=5,
        return_intermediate_steps=True
    )
    print("Agent executor created successfully")
except Exception as e:
    print(f"Error creating agent executor: {e}")
    traceback.print_exc()

def format_employee(employee):
    """Format an employee record for better readability"""
    if not employee:
        return "No employee found"
    
    if "error" in employee:
        return f"Error: {employee['error']}"
        
    return f"ID: {employee.get('id')}\nName: {employee.get('name')}\nAge: {employee.get('age')}\nSalary: ${employee.get('salary')}"

def format_employees(employees):
    """Format a list of employee records for better readability"""
    if not employees:
        return "No employees found"
    
    result = []
    for emp in employees:
        result.append(format_employee(emp))
    
    return "\n\n".join(result)

def run_agent(query):
    """
    Run the agent with the given query
    
    Args:
        query (str): The user's query
        
    Returns:
        dict: The agent's response, including the answer and any intermediate steps
    """
    print(f"Running agent with query: {query}")
    
    try:
        print("Invoking agent executor...")
        result = agent_executor.invoke({"input": query})
        print(f"Agent result: {result}")
        
        # If the agent somehow returns an empty output, provide a generic response
        if not result.get("output") or result.get("output").strip() == "":
            print("Agent returned empty output, providing generic response")
            return {
                "response": "I understood your request but couldn't generate a proper response. Could you please rephrase your question?",
                "data": None
            }
        
        response = {
            "response": result["output"],
            "steps": [step for step in result.get("intermediate_steps", [])],
            "data": None
        }
        
        # Try to extract data from the steps
        for step in result.get("intermediate_steps", []):
            if isinstance(step[1], list) and len(step[1]) > 0:
                response["data"] = step[1]
                print(f"Extracted list data: {len(step[1])} items")
                break
            elif isinstance(step[1], dict) and len(step[1]) > 0:
                if "error" not in step[1]:
                    response["data"] = [step[1]]
                    print(f"Extracted dict data: {step[1]}")
                    break
        
        print(f"Final response: {response['response']}")
        return response
    except Exception as e:
        print(f"Error running agent: {e}")
        traceback.print_exc()
        return {
            "response": f"Sorry, I encountered an error: {str(e)}. Please try again.",
            "steps": [],
            "data": None
        } 