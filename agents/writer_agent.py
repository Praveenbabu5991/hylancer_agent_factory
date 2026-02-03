"""
Writer Agent - Creates detailed post briefs with brand validation.

Takes selected ideas and brand context to create comprehensive
visual briefs for image generation.
"""

from google.adk.agents import LlmAgent
from config.models import get_writer_model
from prompts.writer_agent import WRITER_AGENT_PROMPT
from memory.store import recall_from_memory


def create_post_brief(
    idea: str,
    brand_name: str = "",
    brand_colors: str = "",
    industry: str = "",
    tone: str = "creative",
    company_overview: str = "",
    user_images_info: str = ""
) -> dict:
    """
    Create a detailed visual brief from an idea.

    Args:
        idea: The selected post idea/concept
        brand_name: Name of the brand
        brand_colors: Comma-separated brand colors
        industry: Brand's industry
        tone: Brand's communication tone
        company_overview: Description of the company
        user_images_info: Info about user-uploaded images and their intents

    Returns:
        Dictionary with structured brief sections
    """
    brief = {
        "idea": idea,
        "brand_context": {
            "name": brand_name,
            "colors": brand_colors.split(",") if brand_colors else [],
            "industry": industry,
            "tone": tone,
            "overview": company_overview,
        },
        "visual_concept": "",
        "color_usage": "",
        "text_elements": {
            "greeting": "",
            "headline": "",
            "subtext": "",
            "cta": "",
        },
        "layout": "",
        "user_images": user_images_info,
        "status": "pending_generation"
    }

    return {
        "status": "success",
        "brief": brief,
        "message": "Brief structure created. The agent will fill in the details."
    }


def validate_brief_alignment(
    brief: str,
    brand_name: str = "",
    industry: str = "",
    company_overview: str = ""
) -> dict:
    """
    Validate that a brief aligns with brand guidelines.

    Args:
        brief: The generated visual brief
        brand_name: Name of the brand
        industry: Brand's industry
        company_overview: Description of the company

    Returns:
        Dictionary with validation results
    """
    # Simple validation checks
    validation_results = {
        "brand_name_mentioned": brand_name.lower() in brief.lower() if brand_name else True,
        "industry_relevant": industry.lower() in brief.lower() if industry else True,
        "has_text_elements": any(keyword in brief.lower() for keyword in ["headline", "subtext", "cta"]),
        "has_color_guidance": "color" in brief.lower(),
        "has_visual_concept": "visual" in brief.lower() or "concept" in brief.lower(),
    }

    passed = all(validation_results.values())

    return {
        "status": "success" if passed else "needs_revision",
        "passed": passed,
        "checks": validation_results,
        "message": "Brief validated successfully" if passed else "Brief needs some adjustments"
    }


# Create the Writer Agent
writer_agent = LlmAgent(
    name="WriterAgent",
    model=get_writer_model(),
    instruction=WRITER_AGENT_PROMPT,
    tools=[
        create_post_brief,
        validate_brief_alignment,
        recall_from_memory,
    ],
    description="Creates detailed visual briefs from post ideas, ensuring brand alignment."
)
