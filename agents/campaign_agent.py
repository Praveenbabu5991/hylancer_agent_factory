"""
Campaign Agent - Creates multi-week content campaigns with week-by-week approval workflow.

Key features:
- Week-by-week planning with user approval at each stage
- Single post generation (no carousels within campaigns)
- Uses generate_complete_post for streamlined image + caption + hashtag creation
- Calendar and trend integration for timely content
"""

print("📦 Loading campaign_agent.py...")

from google.adk.agents import LlmAgent
from config.models import get_campaign_model
from prompts.campaign_agent import CAMPAIGN_AGENT_PROMPT
from tools.calendar import (
    get_content_calendar_suggestions,
    get_upcoming_events,
    get_festivals_and_events,
    suggest_best_posting_times,
)
from tools.web_search import search_trending_topics, search_web
from tools.image_gen import generate_complete_post, generate_post_image, extract_brand_colors
from tools.content import write_caption, generate_hashtags
from memory.store import save_to_memory, recall_from_memory

print(f"📅 Creating CampaignPlannerAgent with model: {get_campaign_model()}")

campaign_agent = LlmAgent(
    name="CampaignPlannerAgent",
    model=get_campaign_model(),
    instruction=CAMPAIGN_AGENT_PROMPT,
    tools=[
        # Planning tools
        get_content_calendar_suggestions,
        get_upcoming_events,
        get_festivals_and_events,
        suggest_best_posting_times,
        search_trending_topics,
        search_web,
        # Generation tools
        generate_complete_post,   # Primary - creates image + caption + hashtags in one call
        generate_post_image,      # For image-only generation
        write_caption,
        generate_hashtags,
        extract_brand_colors,
        # Memory tools
        save_to_memory,
        recall_from_memory,
    ],
    description="Creates multi-week content campaigns with week-by-week approval. Generates single posts only."
)
