import os
from typing import Annotated, Literal, TypedDict
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage, BaseMessage, AIMessage
from langchain_core.tools import Tool
from langgraph.graph import StateGraph, MessagesState
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import MemorySaver
from src.agents.tools import get_user_name, get_projects_for_user, get_issues_for_project, get_my_assigned_issues, get_all_projects
from langchain.callbacks.tracers import LangChainTracer
from src.agents.states import StatusMessagesState
from langchain.schema import HumanMessage, SystemMessage, AIMessage

# For LangChain Community (newer versions):
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage

# For OpenAI-style messages:
from openai.types.chat import ChatCompletionMessage
from src.agents.database import MOCK_DB
from src.agents.prompts import SYSTEM_MESSAGE

# Set your OpenAI API key
os.environ["OPENAI_API_KEY"] = ""
os.environ["LANGCHAIN_API_KEY"] = ""
## add langsmith
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_PROJECT"] = "redmine"


def chatbot(state: StatusMessagesState):
    """Main chatbot node that processes user input and decides whether to use tools."""
    print("🤖 Chatbot node: Processing messages...")

    # Initialize the LLM
    llm = ChatOpenAI(
        model="gpt-4.1",  # Using a more stable model
        temperature=0,
        max_tokens=1000
    )

    # Get user string from state or use default
    user_str = "default_user"
    try:
        if "user" in state:
            user_str = state["user"]
    except Exception as e:
        print(f"Error accessing user from state: {e}")
        
    # Clean up the messages to ensure proper structure
    # We need to make sure tool messages are always preceded by messages with tool_calls
    messages = state["messages"]

    # Create tools
    tools = [
        Tool(
            name="get_user_name", 
            func=get_user_name, 
            description="Finds the Redmine user ID for a given username. Use this when you need to look up a user. The result is the user ID."
        ),
        Tool(
            name="get_projects_for_user", 
            func=get_projects_for_user, 
            description="Gets a list of project names for a given user ID. Use this to see what projects a user is involved in."
        ),
        Tool(
            name="get_issues_for_project", 
            func=get_issues_for_project, 
            description="Fetches issues from a specific project. Can optionally filter by status (Open, In Progress, Closed) and/or priority (Low, Normal, High, Critical)."
        ),
        Tool(
            name="get_all_projects", 
            func=get_all_projects, 
            description="Gets a list of project names. Use this to see what projects are available."
        ),
        Tool(
            name="get_my_assigned_issues", 
            func=get_my_assigned_issues, 
            description="Gets all issues assigned to a specific user. Can optionally filter by status."
        )
    ]

    # Bind tools to the LLM
    llm_with_tools = llm.bind_tools(tools)

    # Define the system message with user name
    system_message_content = SYSTEM_MESSAGE.replace("USER_NAME", user_str)

    print(f"System message content: {system_message_content}")
    # Add system message if not present
    messages = state["messages"]
    if not any(isinstance(msg, SystemMessage) for msg in messages):
        messages = [SystemMessage(content=system_message_content)] + messages
    
    # Get response from LLM
    print(f"Messages: {messages}")
    response = llm_with_tools.invoke(messages)
    return {"messages": messages + [response]}


def should_continue(state: StatusMessagesState) -> Literal["tools", "__end__"]:
    """Determine whether to continue with tool calls or end."""
    messages = state["messages"]
    last_message = messages[-1]

    # If the LLM makes a tool call, continue to tools node
    if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
        return "node_tools"
    # Otherwise, end the conversation turn
    print("✅ Conversation complete")
    return "__end__"

def node_tools(state: StatusMessagesState):
    """Calls the tool based on the last message's tool call."""
    
    messages = state["messages"]
    last_message = messages[-1]
    
    # Keep track of all previous messages
    previous_messages = messages[:-1]  # All messages except the last one with tool calls
    
    print(f"Processing {len(last_message.tool_calls)} tool calls")
    
    # Create a list to store all tool messages
    tool_messages = []
    
    # Process all tool calls
    for tool in last_message.tool_calls:
        tool_call_id = tool['id']  # Get the tool call ID
        print(f"Processing tool call: {tool['name']}")
        
        if tool['name'] == "get_user_name":
            username = tool['args']['__arg1']
            user_id = get_user_name(username)
            tool_messages.append(ToolMessage(content=str(user_id), tool_call_id=tool_call_id))
            
        elif tool['name'] == "get_projects_for_user":
            user_id = tool['args']['__arg1']
            result = get_projects_for_user(user_id)
            tool_messages.append(ToolMessage(content=str(result), tool_call_id=tool_call_id))
            
        elif tool['name'] == "get_issues_for_project":
            project_name = tool['args']['__arg1']
            status = tool['args'].get("status")
            priority = tool['args'].get("priority")
            result = get_issues_for_project(project_name, status, priority)
            tool_messages.append(ToolMessage(content=str(result), tool_call_id=tool_call_id))
            
        elif tool['name'] == "get_my_assigned_issues":
            username = tool['args']['__arg1']
            user_id = get_user_name(username)
            status = tool['args'].get("status")
            result = get_my_assigned_issues(user_id, status)
            tool_messages.append(ToolMessage(content=str(result), tool_call_id=tool_call_id))
            
        elif tool['name'] == "get_all_projects":
            result = get_all_projects()
            tool_messages.append(ToolMessage(content=str(result), tool_call_id=tool_call_id))
    
    # Return all messages: previous messages + last message with tool calls + all tool messages
    return {
        "messages": previous_messages + [last_message] + tool_messages,
        "user": state.get("user", "default_user")
    }

def build_graph():
    
    # Define the graph
    workflow = StateGraph(StatusMessagesState)

    # Add nodes
    workflow.add_node("chatbot", chatbot)
    workflow.add_node("node_tools", node_tools)

    # Set entry point
    workflow.set_entry_point("chatbot")

    # Add conditional edges
    workflow.add_conditional_edges(
        "chatbot",
        should_continue,
        {"node_tools": "node_tools", "__end__": "__end__"}
    )

    # After tools, always go back to chatbot
    workflow.add_edge("node_tools", "chatbot")

    # Add memory for conversation history
    memory = MemorySaver()

    # Compile the graph
    app = workflow.compile(checkpointer=memory)
    return app

def call_agent(
    message: str,
    session_id: str,
    user_str: str,
    chat_history: list[BaseMessage] = []
):
    app = build_graph()
    tracer = LangChainTracer()
    thread = {
        "configurable": {
            "thread_id": session_id,
        }
    }
    
    thread["callbacks"] = [tracer]
    thread["tracing_v2_enabled"] = True
    
    # Process the chat history to ensure proper structure
    messages = []
    tool_call_message = None  # Track the last message with tool_calls
    
    for msg in chat_history:
        if msg["role"] == "system":
            messages.append(SystemMessage(content=msg["content"]))
        elif msg['role'] == 'user':
            messages.append(HumanMessage(content=msg['content']))
        elif msg['role'] == 'assistant':
            # Convert to AIMessage and check if it has tool_calls
            ai_msg = AIMessage(content=msg['content'])
            if 'tool_calls' in msg:
                # If there are tool_calls, add them to the message
                ai_msg.tool_calls = msg['tool_calls']
                tool_call_message = ai_msg
            messages.append(ai_msg)
        elif msg['role'] == 'tool':
            # Only add tool messages if they follow a message with tool_calls
            if tool_call_message is not None:
                tool_msg = ToolMessage(
                    content=msg['content'],
                    tool_call_id=msg.get('tool_call_id', '')
                )
                messages.append(tool_msg)
                tool_call_message = None  # Reset after adding tool message
    
    # Add the current user message
    messages.append(HumanMessage(content=message))
    
    # Create initial state with messages and user
    initial_state = StatusMessagesState(
        messages=messages,
        user=user_str
    )
    
    try:
        print(f"🚀 Starting conversation with {len(messages)} messages")
        result = app.invoke(initial_state, config=thread)
        print(f"📋 Final result has {len(result['messages'])} messages")
        
        # Find the last AI message and check if it has tool calls
        for msg in reversed(result["messages"]):
            if isinstance(msg, AIMessage):
                if hasattr(msg, 'tool_calls') and msg.tool_calls:
                    # Return both the message content and tool calls
                    tool_results = []
                    
                    # Look for any tool messages that followed this message
                    tool_call_ids = [tc['id'] for tc in msg.tool_calls]
                    for potential_tool_msg in result["messages"]:
                        if isinstance(potential_tool_msg, ToolMessage) and hasattr(potential_tool_msg, 'tool_call_id'):
                            if potential_tool_msg.tool_call_id in tool_call_ids:
                                tool_results.append({
                                    'content': potential_tool_msg.content,
                                    'tool_call_id': potential_tool_msg.tool_call_id
                                })
                    
                    return {
                        'message': msg.content,
                        'tool_calls': msg.tool_calls,
                        'tool_results': tool_results
                    }
                else:
                    # Simple message without tool calls
                    return {'message': msg.content}
        
        # If no suitable AI message found, return the last message content
        if result["messages"]:
            last_message = result["messages"][-1]
            if hasattr(last_message, 'content') and last_message.content:
                return {'message': last_message.content}
                
    except Exception as e:
        print(f"❌ Error invoking app: {e}")
        return {"message": f"Error: {str(e)}"}
    
    return {'message': 'No hay respuesta disponible'}
    

    