"""
Animation Agent - Transforms static images into animated videos/cinemagraphs.

Uses Veo 3.1 for high-quality video generation with optional audio.
The agent uses Gemini for reasoning and orchestrates the Veo video tools.
"""

print("📦 Loading animation_agent.py...")

from google.adk.agents import LlmAgent
from config.models import get_orchestrator_model  # Use a text model for agent reasoning
from prompts.animation_agent import ANIMATION_AGENT_PROMPT
from tools.image_gen import animate_image, generate_video_from_text
from memory.store import save_to_memory, recall_from_memory

# The agent uses a text model (Gemini) for reasoning
# Video generation is done via the tools which use Veo internally
print(f"🎬 Creating AnimationAgent with model: {get_orchestrator_model()}")

animation_agent = LlmAgent(
    name="AnimationAgent",
    model=get_orchestrator_model(),  # Text model for reasoning, not video model
    instruction=ANIMATION_AGENT_PROMPT,
    tools=[
        animate_image,              # Image-to-video animation (uses Veo 3.1 internally)
        generate_video_from_text,   # Text-to-video generation (uses Veo 3.1 internally)
        save_to_memory,
        recall_from_memory,
    ],
    description="Transforms static images into animated videos/cinemagraphs using Veo 3.1 with audio support."
)
