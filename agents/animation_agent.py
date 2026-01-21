"""
Animation Agent - Transforms static images into animated videos/cinemagraphs.
"""

from google.adk.agents import LlmAgent
from config.settings import DEFAULT_MODEL
from prompts.animation_agent import ANIMATION_AGENT_PROMPT
from tools.image_gen import animate_image
from memory.store import save_to_memory, recall_from_memory


animation_agent = LlmAgent(
    name="AnimationAgent",
    model=DEFAULT_MODEL,
    instruction=ANIMATION_AGENT_PROMPT,
    tools=[
        animate_image,
        save_to_memory,
        recall_from_memory,
    ],
    description="Transforms static images into animated videos/cinemagraphs for social media."
)
