import os
from typing import Annotated, Literal, TypedDict
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from langchain_core.tools import Tool
from langgraph.graph import StateGraph, MessagesState
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import MemorySaver
from src.agents.database import MOCK_DB
## DATABASE

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


# --- 2. TOOL FUNCTIONS ---
def get_user_name(username: str) -> int:
    """Finds the Redmine username for a given username. The result is the user ID."""
    print(f"🔍 Calling Tool: get_user_name(username='{username}')")
    for user in MOCK_DB["users"]:
        if user["username"].lower() == username.lower():
            return user["id"]
    return None

def get_projects_for_user(user_id) -> list[str]:
    """Gets a list of project names for a given user ID."""
    print(f"📁 Calling Tool: get_projects_for_user(user_id={user_id})")
    
    # Convert to integer if it's a string
    try:
        user_id_int = int(user_id)
    except (ValueError, TypeError):
        print(f"❌ Cannot convert user_id to integer: {user_id}")
        return []
    
    project_names = []
    for project in MOCK_DB["projects"]:
        if user_id_int in project["members"]:
            project_names.append(project["name"])
    
    return project_names

def get_issues_for_project(project_name: str, status: str = None, priority: str = None) -> list[dict]:
    """Fetches issues from a specific project. Optionally filter by status and/or priority."""
    print(f"🎫 Calling Tool: get_issues_for_project(project_name='{project_name}', status='{status}', priority='{priority}')")
    
    project = next((p for p in MOCK_DB["projects"] if p["name"].lower() == project_name.lower()), None)
    if not project:
        return []
    
    issues = []
    for issue in MOCK_DB["issues"]:
        if issue["project_id"] == project["id"]:
            # Apply filters if provided
            if status and issue["status"].lower() != status.lower():
                continue
            if priority and issue["priority"].lower() != priority.lower():
                continue
            
            # Get assignee username
            assignee = next((u["username"] for u in MOCK_DB["users"] if u["id"] == issue["assigned_to"]), "Unassigned")
            
            issues.append({
                "id": issue["id"],
                "subject": issue["subject"],
                "status": issue["status"],
                "priority": issue["priority"],
                "assignee": assignee
            })
    
    return issues

def get_my_assigned_issues(user_id_intd: str, status: str = None) -> list[dict]:
    """Gets all issues assigned to a specific user, optionally filtered by status."""
    print(f"👤 Calling Tool: get_my_assigned_issues(user_id='{user_id_intd}', status='{status}')")
    
    if not user_id_intd:
        return []
    
    user_id_intd = int(user_id_intd)
    issues = []
    for issue in MOCK_DB["issues"]:
        if issue["assigned_to"] == user_id_intd:
            # Apply status filter if provided
            if status and issue["status"].lower() != status.lower():
                continue
                
            # Get project name
            project = next((p["name"] for p in MOCK_DB["projects"] if p["id"] == issue["project_id"]), "Unknown Project")
            
            issues.append({
                "id": issue["id"],
                "subject": issue["subject"],
                "status": issue["status"],
                "priority": issue["priority"],
                "project": project
            })
    
    return issues


def get_all_projects() -> list[str]:
    """Gets a list of project names."""
    print("📁 Calling Tool: get_all_projects()")
    return [p["name"] for p in MOCK_DB["projects"]]
