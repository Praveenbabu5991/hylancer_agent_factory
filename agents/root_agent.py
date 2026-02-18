"""
Root Agent (Content Studio Manager) - Orchestrates the multi-agent workflow.
"""

print("📦 Loading root_agent.py...")

from google.adk.agents import LlmAgent
from google.genai import types
from config.models import get_orchestrator_model
from prompts.root_agent import get_root_agent_prompt
from memory.store import get_memory_store, get_or_create_project, save_to_memory, recall_from_memory
from tools.instagram import scrape_instagram_profile, get_profile_summary
from tools.web_search import search_web
from tools.calendar import get_upcoming_events
from tools.response_formatter import format_response_for_user

print("✅ Imports completed in root_agent.py")

# Import sub-agents
print("📦 Importing sub-agents...")
from agents.idea_agent import idea_suggestion_agent
from agents.image_agent import image_post_agent
from agents.caption_agent import caption_agent
from agents.edit_agent import edit_agent
from agents.animation_agent import animation_agent
from agents.campaign_agent import campaign_agent
from agents.writer_agent import writer_agent
print("✅ Sub-agents imported")


def get_memory_context() -> str:
    """Get current memory context for the orchestrator."""
    print("🧠 get_memory_context() called")
    try:
        store = get_memory_store()
        # Get recent activity summary
        recent = store.get_recent_content(5)
        if recent:
            return f"Recent generations: {len(recent)} items"
        return "No previous context."
    except Exception:
        return "No previous context."


# Create the root agent with dynamic prompt
print(f"🤖 Creating ContentStudioManager agent...")
print(f"   Model: {get_orchestrator_model()}")

root_agent = LlmAgent(
    name="ContentStudioManager",
    model=get_orchestrator_model(),
    instruction=get_root_agent_prompt(get_memory_context()),
    sub_agents=[
        idea_suggestion_agent,
        writer_agent,
        image_post_agent,
        caption_agent,
        edit_agent,
        animation_agent,
        campaign_agent,
    ],
    tools=[
        get_or_create_project,
        save_to_memory,
        recall_from_memory,
        scrape_instagram_profile,
        get_profile_summary,
        search_web,
        get_upcoming_events,
        format_response_for_user,  # MUST call this before returning any response to user
    ],
    generate_content_config=types.GenerateContentConfig(
        safety_settings=[
            types.SafetySetting(
                category="HARM_CATEGORY_DANGEROUS_CONTENT",
                threshold="BLOCK_ONLY_HIGH"
            ),
        ]
    )
)

print(f"✅ ContentStudioManager agent created successfully!")
