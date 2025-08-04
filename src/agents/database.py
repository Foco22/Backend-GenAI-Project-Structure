import os
from typing import Annotated, Literal, TypedDict
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from langchain_core.tools import Tool
from langgraph.graph import StateGraph, MessagesState
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import MemorySaver


MOCK_DB = {
    "users": [{"id": 101, "username": "dave"}, {"id": 102, "username": "sally"}],
    "projects": [
        {"id": 201, "name": "Project Phoenix", "members": [101, 102]},
        {"id": 202, "name": "Internal Tools", "members": [101]},
        {"id": 203, "name": "Mobile App Q3", "members": [101, 102]},
    ],
    "issues": [
        {"id": 1, "project_id": 201, "subject": "Fix login button", "status": "Open", "priority": "High", "assigned_to": 101},
        {"id": 2, "project_id": 201, "subject": "Update documentation", "status": "In Progress", "priority": "Normal", "assigned_to": 102},
        {"id": 3, "project_id": 203, "subject": "Deploy to TestFlight", "status": "Open", "priority": "High", "assigned_to": 101},
        {"id": 4, "project_id": 202, "subject": "Setup CI/CD pipeline", "status": "Closed", "priority": "Normal", "assigned_to": 101},
        {"id": 5, "project_id": 203, "subject": "Fix crash on iOS 17", "status": "Open", "priority": "Critical", "assigned_to": 102},
    ],
}

test = ''