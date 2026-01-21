"""Agent prompts package."""
from prompts.idea_agent import IDEA_AGENT_PROMPT
from prompts.image_agent import IMAGE_AGENT_PROMPT
from prompts.caption_agent import CAPTION_AGENT_PROMPT
from prompts.edit_agent import EDIT_AGENT_PROMPT
from prompts.animation_agent import ANIMATION_AGENT_PROMPT
from prompts.campaign_agent import CAMPAIGN_AGENT_PROMPT
from prompts.root_agent import ROOT_AGENT_PROMPT

__all__ = [
    "IDEA_AGENT_PROMPT",
    "IMAGE_AGENT_PROMPT", 
    "CAPTION_AGENT_PROMPT",
    "EDIT_AGENT_PROMPT",
    "ANIMATION_AGENT_PROMPT",
    "CAMPAIGN_AGENT_PROMPT",
    "ROOT_AGENT_PROMPT",
]
