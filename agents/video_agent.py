"""
Video Agent - Creates video content using Veo 3.1 and external services.

Handles three types of video generation:
1. Animated Product Videos - Transform product images into showcase videos
2. Motion Graphics - Create branded motion graphics from text
3. AI Talking Head - Guide users to external AI presenter services
"""

print("📦 Loading video_agent.py...")

from google.adk.agents import LlmAgent
from config.models import get_orchestrator_model
from prompts.video_agent import VIDEO_AGENT_PROMPT
from tools.video_gen import (
    generate_animated_product_video,
    generate_motion_graphics_video,
    generate_talking_head_video,
    get_video_type_options,
    suggest_video_ideas,
)
from tools.response_formatter import format_response_for_user
from tools.content import write_caption, generate_hashtags
from memory.store import save_to_memory, recall_from_memory

print(f"🎬 Creating VideoAgent with model: {get_orchestrator_model()}")

video_agent = LlmAgent(
    name="VideoAgent",
    model=get_orchestrator_model(),
    instruction=VIDEO_AGENT_PROMPT,
    tools=[
        suggest_video_ideas,               # Step 1: Get video ideas
        generate_animated_product_video,   # Step 2: Generate product video
        generate_motion_graphics_video,    # Step 2: Generate motion graphics
        generate_talking_head_video,       # Step 2: Generate talking head guidance
        get_video_type_options,            # Helper: Get video type options
        write_caption,                     # Step 3: Generate caption for video
        generate_hashtags,                 # Step 3: Generate hashtags for video
        format_response_for_user,
        save_to_memory,
        recall_from_memory,
    ],
    description="Creates Reels/TikTok videos: suggests ideas, generates 8-second videos, provides captions and hashtags."
)

print("✅ VideoAgent created successfully!")
