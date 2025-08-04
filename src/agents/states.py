import os
from typing import Annotated, Literal, TypedDict
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage, BaseMessage
from langchain_core.tools import Tool
from langgraph.graph import StateGraph, MessagesState
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import MemorySaver
from src.agents.tools import get_user_name, get_projects_for_user, get_issues_for_project, get_my_assigned_issues
from langchain.callbacks.tracers import LangChainTracer
from typing import Annotated, List, TypedDict, Literal
from pydantic import BaseModel, Field
import operator

class StatusMessagesState(TypedDict):
    messages: list[BaseMessage] # List of messages
    user: str # User name
