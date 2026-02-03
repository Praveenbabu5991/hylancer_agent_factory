"""
Regenerate Agent - Edits and regenerates posts based on user feedback.

This agent handles:
- Image edits (color changes, element modifications, style adjustments)
- Caption regeneration with new tone/message
- Hashtag refresh
- Full post regeneration combining all elements
"""

from google.adk.agents import LlmAgent
from config.models import get_edit_model
from prompts.edit_agent import EDIT_AGENT_PROMPT
from tools.image_gen import edit_post_image, regenerate_post
from tools.content import improve_caption, generate_hashtags
from memory.store import save_to_memory, recall_from_memory


edit_agent = LlmAgent(
    name="EditPostAgent",
    model=get_edit_model(),
    instruction=EDIT_AGENT_PROMPT,
    tools=[
        regenerate_post,     # Primary tool - regenerates image + caption + hashtags
        edit_post_image,     # For image-only edits
        improve_caption,     # For caption improvements
        generate_hashtags,   # For hashtag refresh
        save_to_memory,
        recall_from_memory,
    ],
    description="Edits and regenerates posts based on user feedback - handles image edits, caption improvements, and hashtag refresh."
)
