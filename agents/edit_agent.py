"""
Edit Agent - Modifies and improves existing images based on feedback.
"""

from google.adk.agents import LlmAgent
from config.settings import DEFAULT_MODEL
from prompts.edit_agent import EDIT_AGENT_PROMPT
from tools.image_gen import edit_post_image
from memory.store import save_to_memory, recall_from_memory


edit_agent = LlmAgent(
    name="EditPostAgent",
    model=DEFAULT_MODEL,
    instruction=EDIT_AGENT_PROMPT,
    tools=[
        edit_post_image,
        save_to_memory,
        recall_from_memory,
    ],
    description="Modifies and improves existing images based on feedback."
)
