"""
Image Post Agent - Creates visual briefs and generates premium Instagram visuals.
"""

from google.adk.agents import LlmAgent
from config.settings import DEFAULT_MODEL
from prompts.image_agent import IMAGE_AGENT_PROMPT
from tools.image_gen import generate_post_image, extract_brand_colors
from tools.instagram import scrape_instagram_profile
from memory.store import save_to_memory, recall_from_memory


image_post_agent = LlmAgent(
    name="ImagePostAgent",
    model=DEFAULT_MODEL,
    instruction=IMAGE_AGENT_PROMPT,
    tools=[
        generate_post_image,
        extract_brand_colors,
        scrape_instagram_profile,
        save_to_memory,
        recall_from_memory,
    ],
    description="Creates visual briefs and generates premium Instagram visuals with brand integration."
)
