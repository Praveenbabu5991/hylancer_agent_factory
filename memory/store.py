"""Session memory store for maintaining context across conversations."""

from datetime import datetime
from typing import Any, Optional
import json


class MemoryStore:
    """In-memory store for session context and project data."""
    
    def __init__(self):
        self.projects: dict[str, dict] = {}
        self.profiles: dict[str, dict] = {}
        self.generated_content: list[dict] = []
        self.session_context: dict[str, Any] = {}
    
    def save_project(
        self,
        project_id: str,
        name: str,
        brand_info: dict[str, Any]
    ) -> dict:
        """Save or update a project."""
        self.projects[project_id] = {
            "id": project_id,
            "name": name,
            "brand_info": brand_info,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "content_history": []
        }
        return {"status": "success", "project_id": project_id}
    
    def get_project(self, project_id: str) -> Optional[dict]:
        """Get a project by ID."""
        return self.projects.get(project_id)
    
    def list_projects(self) -> list[dict]:
        """List all projects."""
        return list(self.projects.values())
    
    def save_profile(
        self,
        username: str,
        profile_data: dict[str, Any]
    ) -> dict:
        """Save analyzed profile data."""
        self.profiles[username] = {
            "username": username,
            "data": profile_data,
            "analyzed_at": datetime.now().isoformat()
        }
        return {"status": "success", "username": username}
    
    def get_profile(self, username: str) -> Optional[dict]:
        """Get saved profile data."""
        return self.profiles.get(username)
    
    def save_generated_content(
        self,
        content_type: str,
        content: dict[str, Any],
        project_id: str = None
    ) -> dict:
        """Save generated content (images, captions, etc.)."""
        entry = {
            "type": content_type,
            "content": content,
            "project_id": project_id,
            "created_at": datetime.now().isoformat()
        }
        self.generated_content.append(entry)
        
        # Also add to project history if project_id provided
        if project_id and project_id in self.projects:
            self.projects[project_id]["content_history"].append(entry)
            self.projects[project_id]["updated_at"] = datetime.now().isoformat()
        
        return {"status": "success", "content_id": len(self.generated_content) - 1}
    
    def get_recent_content(self, limit: int = 10) -> list[dict]:
        """Get recently generated content."""
        return self.generated_content[-limit:][::-1]
    
    def set_context(self, key: str, value: Any) -> None:
        """Set a context value for the current session."""
        self.session_context[key] = value
    
    def get_context(self, key: str, default: Any = None) -> Any:
        """Get a context value."""
        return self.session_context.get(key, default)
    
    def get_context_summary(self) -> str:
        """Get a summary of current context for the agent."""
        summary_parts = []
        
        if self.projects:
            summary_parts.append(f"Active projects: {len(self.projects)}")
            recent_project = list(self.projects.values())[-1]
            summary_parts.append(f"Last project: {recent_project['name']}")
        
        if self.profiles:
            summary_parts.append(f"Analyzed profiles: {len(self.profiles)}")
        
        if self.generated_content:
            summary_parts.append(f"Generated items: {len(self.generated_content)}")
            recent = self.generated_content[-1]
            summary_parts.append(f"Last generated: {recent['type']}")
        
        if self.session_context:
            if "current_brand" in self.session_context:
                summary_parts.append(f"Current brand: {self.session_context['current_brand']}")
            if "current_theme" in self.session_context:
                summary_parts.append(f"Working on: {self.session_context['current_theme']}")
        
        return " | ".join(summary_parts) if summary_parts else "No previous context."
    
    def clear(self) -> None:
        """Clear all stored data."""
        self.projects.clear()
        self.profiles.clear()
        self.generated_content.clear()
        self.session_context.clear()


# Global memory store instance
_memory_store: Optional[MemoryStore] = None


def get_memory_store() -> MemoryStore:
    """Get the global memory store instance."""
    global _memory_store
    if _memory_store is None:
        _memory_store = MemoryStore()
    return _memory_store


# Tool functions for agents
def save_to_memory(
    category: str,
    key: str,
    value: str
) -> dict:
    """
    Save data to memory for later recall.
    
    Args:
        category: Type of data (project, profile, content, context)
        key: Identifier for the data
        value: JSON string or simple text value to save
        
    Returns:
        Confirmation of save
    """
    store = get_memory_store()
    
    # Try to parse value as JSON
    try:
        data = json.loads(value) if value.startswith("{") or value.startswith("[") else {"value": value}
    except:
        data = {"value": value}
    
    if category == "project":
        return store.save_project(key, data.get("name", key), data)
    elif category == "profile":
        return store.save_profile(key, data)
    elif category == "content":
        return store.save_generated_content(data.get("type", "unknown"), data, key)
    elif category == "context":
        store.set_context(key, data)
        return {"status": "success", "key": key}
    else:
        return {"status": "error", "message": f"Unknown category: {category}"}


def recall_from_memory(
    category: str,
    key: str = None
) -> dict:
    """
    Recall data from memory.
    
    Args:
        category: Type of data to recall
        key: Specific identifier (optional)
        
    Returns:
        Retrieved data
    """
    store = get_memory_store()
    
    if category == "project":
        if key:
            project = store.get_project(key)
            return {"status": "success", "data": project} if project else {"status": "not_found"}
        return {"status": "success", "data": store.list_projects()}
    
    elif category == "profile":
        if key:
            profile = store.get_profile(key)
            return {"status": "success", "data": profile} if profile else {"status": "not_found"}
        return {"status": "success", "data": list(store.profiles.values())}
    
    elif category == "content":
        limit = int(key) if key and key.isdigit() else 10
        return {"status": "success", "data": store.get_recent_content(limit)}
    
    elif category == "context":
        if key:
            value = store.get_context(key)
            return {"status": "success", "data": value}
        return {"status": "success", "data": store.session_context}
    
    elif category == "summary":
        return {"status": "success", "summary": store.get_context_summary()}
    
    return {"status": "error", "message": f"Unknown category: {category}"}


def get_or_create_project(
    project_name: str,
    brand_name: str = "",
    niche: str = "",
    tone: str = "professional"
) -> dict:
    """
    Get existing project or create a new one.
    
    Args:
        project_name: Name of the project
        brand_name: Brand name (for new projects)
        niche: Brand industry/niche
        tone: Brand voice/tone
        
    Returns:
        Project data
    """
    store = get_memory_store()
    
    # Check if project exists
    for project_id, project in store.projects.items():
        if project["name"].lower() == project_name.lower():
            return {"status": "success", "project": project, "is_new": False}
    
    # Create new project
    import uuid
    project_id = str(uuid.uuid4())[:8]
    brand_info = {
        "name": brand_name or project_name,
        "niche": niche,
        "tone": tone
    }
    store.save_project(project_id, project_name, brand_info)
    
    return {
        "status": "success",
        "project": store.get_project(project_id),
        "is_new": True
    }
