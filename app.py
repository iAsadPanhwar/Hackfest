import streamlit as st
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
from groq import Groq

# Load environment variables
load_dotenv()

# Set up Groq client
groq_api_key = os.getenv("GROQ_API_KEY")
groq_client = Groq(api_key=groq_api_key)

# Page configuration
st.set_page_config(
    page_title="AI Database Assistant",
    page_icon="🤖",
    layout="wide"
)

# Database connection
def get_db_connection():
    try:
        conn = psycopg2.connect(os.getenv('DATABASE_URL'))
        conn.autocommit = False
        return conn
    except Exception as e:
        st.error(f"Error connecting to database: {e}")
        return None

# Database query function
def query_database(query, params=None):
    conn = get_db_connection()
    if not conn:
        return None
    
    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        
        result = cursor.fetchall()
        cursor.close()
        conn.close()
        return [dict(row) for row in result]
    except Exception as e:
        st.error(f"Error executing query: {e}")
        if conn:
            conn.close()
        return None

# Function to run AI agent
def run_agent(query):
    # Get employees table structure info
    table_info = """
    Table: employees
    Columns:
    - id (int): primary key
    - created_at (timestamp): creation timestamp
    - name (text): employee name
    - age (numeric): employee age
    - salary (numeric): employee salary in USD
    """
    
    # Try to run a simple query to get some sample data
    sample_data = query_database("SELECT * FROM employees LIMIT 3")
    sample_data_str = str(sample_data) if sample_data else "No sample data available"
    
    # Create prompt for Groq
    system_prompt = f"""You are an AI agent that helps query a PostgreSQL database.
    You have access to the following database structure:
    {table_info}
    
    Sample data:
    {sample_data_str}
    
    When asked to retrieve or query data, you should:
    1. Generate the appropriate SQL query
    2. Execute it via the Python code
    3. Return the results in a formatted way
    
    Do not make up data. Only return data that is actually retrieved from the database.
    If you cannot answer a question with the available data, say so clearly.
    """
    
    user_prompt = f"User question: {query}\n\nPlease help answer this by querying the employees database. If you need to run a SQL query, include it in your reasoning."
    
    try:
        # Call Groq AI
        response = groq_client.chat.completions.create(
            model="llama3-70b-8192",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.1,
            max_tokens=1024
        )
        
        # Extract AI's thinking
        ai_reasoning = response.choices[0].message.content
        
        # Look for SQL queries in the response
        import re
        sql_match = re.search(r'```sql\s*(.*?)\s*```', ai_reasoning, re.DOTALL)
        
        result_data = None
        if sql_match:
            sql_query = sql_match.group(1).strip()
            st.info(f"Executing SQL: {sql_query}")
            # Execute the query
            result_data = query_database(sql_query)
        
        # Prepare the final response
        if result_data is not None:
            # Call Groq again with the results to format the response nicely
            final_prompt = f"""
            User question: {query}
            
            SQL Query executed: {sql_match.group(1) if sql_match else "No SQL executed"}
            
            Query Results: {str(result_data)}
            
            Please provide a clear, concise answer to the user's question based on the data retrieved.
            """
            
            final_response = groq_client.chat.completions.create(
                model="llama3-70b-8192",
                messages=[
                    {"role": "system", "content": "You are a helpful database assistant."},
                    {"role": "user", "content": final_prompt}
                ],
                temperature=0.1,
                max_tokens=1024
            )
            
            return {
                "response": final_response.choices[0].message.content,
                "query": sql_match.group(1) if sql_match else "No SQL query was executed",
                "data": result_data
            }
        else:
            # If no SQL was executed or it failed, just return the AI's reasoning
            return {
                "response": ai_reasoning,
                "query": sql_match.group(1) if sql_match else "No SQL query was executed",
                "data": None
            }
    except Exception as e:
        return {
            "response": f"Sorry, I encountered an error: {str(e)}",
            "query": "",
            "data": None
        }

# Main app
st.title("🤖 AI Database Assistant")
st.markdown("""
Ask me questions about the employee database! I can help you:

- Get all employees
- Find employees by ID
- Find employees with specific salaries
- Get employees by age criteria
- Search for employees by name
- And more!
""")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])
        
        # If there's data, display it in a table
        if message.get("data"):
            st.dataframe(message["data"])

# Chat input
if prompt := st.chat_input("Ask me about the employee database..."):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Display user message
    with st.chat_message("user"):
        st.write(prompt)
    
    # Generate response
    with st.spinner("Thinking..."):
        response = run_agent(prompt)
    
    # Add assistant response to chat history with any data
    st.session_state.messages.append({
        "role": "assistant", 
        "content": response["response"],
        "data": response.get("data")
    })
    
    # Display assistant response
    with st.chat_message("assistant"):
        st.write(response["response"])
        
        # If there's data, display it in a table
        if response.get("data"):
            st.dataframe(response["data"])