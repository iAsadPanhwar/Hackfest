import os
from typing import Dict, List, Any
from dotenv import load_dotenv
import base64
import requests
import tempfile

# LangChain and Groq imports
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain.agents import create_structured_chat_agent, AgentExecutor
from langchain.memory import ConversationBufferMemory
from langchain.tools import BaseTool
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.pydantic_v1 import BaseModel, Field
import langgraph.graph as lg
from langgraph.graph import END, StateGraph

# Load environment variables
load_dotenv()

# Initialize Groq LLM
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = "llama3-70b-8192"  # Using llama3 model

llm = ChatGroq(
    api_key=GROQ_API_KEY,
    model_name=GROQ_MODEL,
    temperature=0.2
)

# Define some custom tools for the agent

class FileAnalyzer(BaseTool):
    """Tool to list files in Supabase storage"""
    name = "file_analyzer"
    description = "Lists files in Supabase storage"

    def _run(self, supabase_client) -> List[Dict]:
        """Returns the list of files in storage"""
        return supabase_client.list_files()
        
class ImageAnalyzer(BaseTool):
    """Tool to analyze receipt images"""
    name = "image_analyzer"
    description = "Extracts amounts from receipt images"

    def _run(self, base64_image: str) -> float:
        """Extracts the amount from the receipt image using OpenAI Vision"""
        from openai import OpenAI
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY", ""))
        
        try:
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

class AudioTranscriber(BaseTool):
    """Tool to transcribe audio files"""
    name = "audio_transcriber"
    description = "Transcribes audio files to text"

    def _run(self, audio_path: str) -> str:
        """Transcribes the audio file using OpenAI Whisper"""
        from openai import OpenAI
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY", ""))
        
        try:
            with open(audio_path, "rb") as audio_file:
                response = client.audio.transcriptions.create(
                    model="whisper-1", 
                    file=audio_file
                )
            return response.text
        except Exception as e:
            print(f"Error during audio transcription: {e}")
            return None

class TextSummarizer(BaseTool):
    """Tool to summarize text"""
    name = "text_summarizer"
    description = "Summarizes text content"

    def _run(self, text: str) -> str:
        """Summarizes the text using Groq LLM"""
        prompt = ChatPromptTemplate.from_template(
            "Summarize the following text in a concise way while capturing the key points:\n\n{text}"
        )
        chain = prompt | llm | StrOutputParser()
        return chain.invoke({"text": text})

# Define our LangGraph state
class AgentState(BaseModel):
    """State for the Supabase agent."""
    task: str = Field(description="Current task being performed")
    query: str = Field(description="User query/request")
    result: Dict[str, Any] = Field(default_factory=dict, description="Results of operations")
    error: str = Field(default="", description="Error message if any")
    next_step: str = Field(default="", description="Next step to be taken")
    completed: bool = Field(default=False, description="Whether the task is completed")
    
# Build the LangGraph nodes
def task_classifier(state: AgentState) -> Dict:
    """Classify the task to determine the correct agent to use"""
    prompt = ChatPromptTemplate.from_template(
        """
        You are a task classifier for a AI system. Given the query, classify it into one of these categories:
        - employee_management: tasks related to employee data like fetching, adding, updating, or deleting
        - image_analysis: tasks related to analyzing receipt images
        - audio_analysis: tasks related to transcribing and summarizing audio files
        - general_query: any other general questions

        Query: {query}
        
        Respond with just the category name.
        """
    )
    chain = prompt | llm | StrOutputParser()
    
    category = chain.invoke({"query": state.query})
    state.task = category.strip()
    
    return {"state": state}

def employee_agent(state: AgentState) -> Dict:
    """Handle employee management tasks"""
    prompt = ChatPromptTemplate.from_template(
        """
        You are an employee management expert. Help with the following task:
        
        Task: {query}
        
        Provide detailed steps on how to handle this employee management task using Supabase.
        """
    )
    chain = prompt | llm | StrOutputParser()
    
    result = chain.invoke({"query": state.query})
    state.result["response"] = result
    state.completed = True
    
    return {"state": state}

def image_analyzer_agent(state: AgentState) -> Dict:
    """Handle image analysis tasks"""
    prompt = ChatPromptTemplate.from_template(
        """
        You are an image analysis expert. Help with the following task:
        
        Task: {query}
        
        Provide detailed steps on how to analyze receipt images and extract amounts.
        """
    )
    chain = prompt | llm | StrOutputParser()
    
    result = chain.invoke({"query": state.query})
    state.result["response"] = result
    state.completed = True
    
    return {"state": state}

def audio_analyzer_agent(state: AgentState) -> Dict:
    """Handle audio analysis tasks"""
    prompt = ChatPromptTemplate.from_template(
        """
        You are an audio analysis expert. Help with the following task:
        
        Task: {query}
        
        Provide detailed steps on how to transcribe and summarize audio files.
        """
    )
    chain = prompt | llm | StrOutputParser()
    
    result = chain.invoke({"query": state.query})
    state.result["response"] = result
    state.completed = True
    
    return {"state": state}

def general_agent(state: AgentState) -> Dict:
    """Handle general queries"""
    prompt = ChatPromptTemplate.from_template(
        """
        You are a helpful assistant. Answer the following query:
        
        Query: {query}
        """
    )
    chain = prompt | llm | StrOutputParser()
    
    result = chain.invoke({"query": state.query})
    state.result["response"] = result
    state.completed = True
    
    return {"state": state}

# Setup LangGraph
workflow = StateGraph(AgentState)

# Add nodes
workflow.add_node("task_classifier", task_classifier)
workflow.add_node("employee_agent", employee_agent)
workflow.add_node("image_analyzer_agent", image_analyzer_agent)
workflow.add_node("audio_analyzer_agent", audio_analyzer_agent)
workflow.add_node("general_agent", general_agent)

# Add edges
workflow.add_edge("task_classifier", "employee_agent", condition=lambda state: state.task == "employee_management")
workflow.add_edge("task_classifier", "image_analyzer_agent", condition=lambda state: state.task == "image_analysis")
workflow.add_edge("task_classifier", "audio_analyzer_agent", condition=lambda state: state.task == "audio_analysis")
workflow.add_edge("task_classifier", "general_agent", condition=lambda state: state.task == "general_query")

# Add edge to END for completed nodes
workflow.add_edge("employee_agent", END)
workflow.add_edge("image_analyzer_agent", END)
workflow.add_edge("audio_analyzer_agent", END)
workflow.add_edge("general_agent", END)

# Compile the graph
agent_executor = workflow.compile()

# Function to run the agent
def run_agent(query: str) -> dict:
    """Run the agent with the given query"""
    state = AgentState(query=query, task="", result={}, error="", completed=False)
    result = agent_executor.invoke({"state": state})
    return result["state"].result

# AI functions for different tasks

def extract_amount_from_receipt(base64_image):
    """
    Extract the total amount from a receipt image using Groq or OpenAI
    
    Args:
        base64_image (str): Base64-encoded image data
        
    Returns:
        float or None: The extracted amount or None if extraction failed
    """
    # For image analysis, we'll use OpenAI since Groq doesn't support vision yet
    image_tool = ImageAnalyzer()
    return image_tool._run(base64_image)

def transcribe_audio(audio_path):
    """
    Transcribe audio file using OpenAI Whisper
    
    Args:
        audio_path (str): Path to the audio file
        
    Returns:
        str: The transcribed text
    """
    audio_tool = AudioTranscriber()
    return audio_tool._run(audio_path)

def summarize_transcript(transcript):
    """
    Summarize transcript using Groq
    
    Args:
        transcript (str): The text to summarize
        
    Returns:
        str: The summary of the transcript
    """
    text_tool = TextSummarizer()
    return text_tool._run(transcript)