"""
Idea Suggestion Agent - Suggests creative post ideas based on events and trends.
"""

from google.adk.agents import LlmAgent
from config.settings import DEFAULT_MODEL
from prompts.idea_agent import IDEA_AGENT_PROMPT
from tools.calendar import get_upcoming_events, get_festivals_and_events
from tools.web_search import search_trending_topics, search_web
from memory.store import recall_from_memory


idea_suggestion_agent = LlmAgent(
    name="IdeaSuggestionAgent",
    model=DEFAULT_MODEL,
    instruction=IDEA_AGENT_PROMPT,
    tools=[
        get_upcoming_events,
        get_festivals_and_events,
        search_trending_topics,
        search_web,
        recall_from_memory,
    ],
    description="Suggests creative post ideas based on events, trends, and brand context."
)
