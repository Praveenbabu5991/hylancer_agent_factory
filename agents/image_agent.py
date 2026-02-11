"""
Post Generation Agent - Creates complete social media posts with images, captions, and hashtags.

This agent combines image generation with caption and hashtag creation for a streamlined
one-stop post creation experience.
"""

print("📦 Loading image_agent.py...")

from google.adk.agents import LlmAgent
from config.models import get_image_model
from prompts.image_agent import IMAGE_AGENT_PROMPT
from tools.image_gen import (
    generate_post_image,
    generate_complete_post,
    generate_product_showcase,
    extract_brand_colors
)
from tools.content import write_caption, generate_hashtags
from tools.instagram import scrape_instagram_profile
from tools.response_formatter import format_response_for_user
from memory.store import save_to_memory, recall_from_memory

print(f"🖼️ Creating ImagePostAgent with model: {get_image_model()}")

image_post_agent = LlmAgent(
    name="ImagePostAgent",
    model=get_image_model(),
    instruction=IMAGE_AGENT_PROMPT,
    tools=[
        generate_complete_post,    # Primary tool - creates image + caption + hashtags
        generate_product_showcase, # Product-focused posts with uploaded product images
        generate_post_image,       # For image-only generation
        write_caption,             # For caption-only generation
        generate_hashtags,         # For hashtag-only generation
        extract_brand_colors,
        scrape_instagram_profile,
        format_response_for_user,
        save_to_memory,
        recall_from_memory,
    ],
    description="Creates complete social media posts with images, captions, and hashtags in one workflow."
)
