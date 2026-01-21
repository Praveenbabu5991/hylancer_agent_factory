"""
Content Studio Agent - Multi-Agent Social Media Content Creation Platform

This module provides backward compatibility.
The agents have been refactored into the `agents` package.
"""

# Re-export from the new modular structure
from agents.root_agent import root_agent
from agents.idea_agent import idea_suggestion_agent
from agents.image_agent import image_post_agent
from agents.caption_agent import caption_agent
from agents.edit_agent import edit_agent
from agents.animation_agent import animation_agent
from agents.campaign_agent import campaign_agent

# Re-export memory functions
from memory.store import (
    save_to_memory,
    recall_from_memory,
    get_or_create_project,
    get_memory_store,
)

__all__ = [
    "root_agent",
    "idea_suggestion_agent",
    "image_post_agent",
    "caption_agent",
    "edit_agent",
    "animation_agent",
    "campaign_agent",
    "save_to_memory",
    "recall_from_memory",
    "get_or_create_project",
    "get_memory_store",
]
