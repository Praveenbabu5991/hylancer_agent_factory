"""
Animation Agent - Transforms static images into animated videos/cinemagraphs.
"""

from google.adk.agents import LlmAgent
from config.models import get_video_model
from prompts.animation_agent import ANIMATION_AGENT_PROMPT
from tools.image_gen import animate_image
from memory.store import save_to_memory, recall_from_memory


animation_agent = LlmAgent(
    name="AnimationAgent",
    model=get_video_model(),
    instruction=ANIMATION_AGENT_PROMPT,
    tools=[
        animate_image,
        save_to_memory,
        recall_from_memory,
    ],
    description="Transforms static images into animated videos/cinemagraphs for social media."
)
