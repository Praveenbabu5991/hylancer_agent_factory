"""
Caption Agent - Creates scroll-stopping captions and strategic hashtags.
"""

from google.adk.agents import LlmAgent
from config.settings import DEFAULT_MODEL
from prompts.caption_agent import CAPTION_AGENT_PROMPT
from tools.content import write_caption, generate_hashtags, improve_caption, create_complete_post
from tools.web_search import search_trending_topics
from tools.calendar import get_festivals_and_events
from memory.store import save_to_memory, recall_from_memory


caption_agent = LlmAgent(
    name="CaptionAgent",
    model=DEFAULT_MODEL,
    instruction=CAPTION_AGENT_PROMPT,
    tools=[
        write_caption,
        generate_hashtags,
        improve_caption,
        create_complete_post,
        search_trending_topics,
        get_festivals_and_events,
        save_to_memory,
        recall_from_memory,
    ],
    description="Creates scroll-stopping captions and strategic hashtag sets."
)
