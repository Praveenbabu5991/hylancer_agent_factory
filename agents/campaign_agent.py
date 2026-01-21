"""
Campaign Agent - Creates multi-week content campaigns with approval workflow.
"""

from google.adk.agents import LlmAgent
from config.settings import DEFAULT_MODEL
from prompts.campaign_agent import CAMPAIGN_AGENT_PROMPT
from tools.calendar import (
    get_content_calendar_suggestions,
    get_upcoming_events,
    get_festivals_and_events,
    suggest_best_posting_times,
)
from tools.web_search import search_trending_topics, search_web
from tools.image_gen import generate_post_image, extract_brand_colors
from tools.content import write_caption, generate_hashtags
from memory.store import save_to_memory, recall_from_memory


campaign_agent = LlmAgent(
    name="CampaignPlannerAgent",
    model=DEFAULT_MODEL,
    instruction=CAMPAIGN_AGENT_PROMPT,
    tools=[
        get_content_calendar_suggestions,
        get_upcoming_events,
        get_festivals_and_events,
        suggest_best_posting_times,
        search_trending_topics,
        search_web,
        generate_post_image,
        write_caption,
        generate_hashtags,
        extract_brand_colors,
        save_to_memory,
        recall_from_memory,
    ],
    description="Creates multi-week content campaigns with week-by-week approval."
)
