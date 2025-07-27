import os
import openai
from dotenv import load_dotenv
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class OpenAI:

    def __init__(self):
        self.client = openai.OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

    def get_assistant_response(self, user_query, conversation_history=None):
        """
        Get a response from the OpenAI model for Redmine-related queries.
        
        Args:
            user_query (str): The user's question or request
            conversation_history (list, optional): List of previous messages in the format 
                                                [{'role': 'user', 'content': '...'}, {'role': 'assistant', 'content': '...'}]
        
        Returns:
            str: The assistant's response
        """
        try:
            if not self.client:
                return "OpenAI API key not configured. Please set the OPENAI_API_KEY environment variable."
            
            # Prepare conversation history
            messages = []
            
            # Add system message to set context
            messages.append({
                "role": "system",
                "content": """You are a helpful Redmine project management assistant. 
                You can help with tickets, projects, users, and other Redmine-related queries. 
                Provide concise, accurate information about Redmine functionality and best practices.
                If you don't know something, admit it rather than making up information."""
            })
            
            # Add conversation history if provided
            if conversation_history:
                messages.extend(conversation_history)
            
            # Add the current user query
            messages.append({"role": "user", "content": user_query})
            
            # Call OpenAI API
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",  # You can change to a different model if needed
                messages=messages,
                max_tokens=500,
                temperature=0.7
            )
            
            # Extract and return the response text
            return response.choices[0].message.content
        
        except Exception as e:
            logger.error(f"Error calling OpenAI API: {str(e)}")
            return f"I'm sorry, but I encountered an error: {str(e)}"
