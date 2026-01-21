"""Content creation tools for captions and hashtags."""

import os
from typing import Any

from google import genai
from dotenv import load_dotenv

load_dotenv()


def write_caption(
    topic: str,
    brand_voice: str = "professional yet friendly",
    target_audience: str = "general",
    key_message: str = "",
    occasion: str = "",
    tone: str = "engaging",
    max_length: int = 2200,
    include_cta: bool = True,
    emoji_level: str = "moderate",
    company_overview: str = "",
    brand_name: str = "",
    image_description: str = ""
) -> dict:
    """
    Write an engaging Instagram caption.
    
    Args:
        topic: Main topic/theme of the post
        brand_voice: Brand's tone of voice
        target_audience: Who the content is for
        key_message: Main message to convey
        occasion: Special occasion/event
        tone: Desired tone (engaging, professional, playful, inspirational)
        max_length: Maximum character length
        include_cta: Include call-to-action
        emoji_level: none, minimal, moderate, heavy
        company_overview: Description of what the company does (for context)
        brand_name: Name of the brand
        image_description: Description of the image this caption is for
        
    Returns:
        Dictionary with generated caption
    """
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        return {"status": "error", "message": "No API key found"}
    
    client = genai.Client(api_key=api_key)
    
    emoji_instruction = {
        "none": "Do not use any emojis.",
        "minimal": "Use 1-2 emojis strategically.",
        "moderate": "Use 3-5 emojis to enhance the message.",
        "heavy": "Use emojis liberally throughout."
    }.get(emoji_level, "Use emojis moderately.")
    
    # Build company context
    company_context = ""
    if company_overview:
        company_context = f"\n**About the Company:** {company_overview}"
    if brand_name:
        company_context = f"\n**Brand Name:** {brand_name}" + company_context
    
    # Add image context if provided
    image_context = ""
    if image_description:
        image_context = f"\n**This caption is for an image showing:** {image_description}"
    
    prompt = f"""Write a SHORT, CRISP Instagram caption for the following:

**Topic:** {topic}
**Brand Voice:** {brand_voice}
**Target Audience:** {target_audience}
**Key Message:** {key_message or "Engage and connect with the audience"}
**Occasion:** {occasion or "Regular post"}
**Tone:** {tone}{company_context}{image_context}

**CRITICAL REQUIREMENTS - KEEP IT SHORT:**
- Total length: 50-150 words MAXIMUM (around 3-5 sentences)
- First line = attention-grabbing HOOK
- 1-2 sentences of core message
- End with ONE clear call-to-action
- {emoji_instruction}
- Easy to copy-paste to Instagram

**FORMAT:**
[Hook line]

[1-2 sentences of value]

[Simple CTA] 👇

**DON'T:**
- Write long paragraphs
- Exceed 150 words
- Be overly promotional
- Use too many emojis

Write ONLY the caption text, nothing else:"""

    try:
        response = client.models.generate_content(
            model=os.getenv("DEFAULT_MODEL", "gemini-2.5-flash"),
            contents=prompt
        )
        caption = response.text.strip()
        return {
            "status": "success",
            "caption": caption,
            "character_count": len(caption),
            "topic": topic,
            "tone": tone
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


def generate_hashtags(
    topic: str,
    niche: str = "",
    brand_name: str = "",
    trending_context: str = "",
    max_hashtags: int = 30
) -> dict:
    """
    Generate relevant hashtags for an Instagram post.
    
    Args:
        topic: Main topic of the post
        niche: Industry/niche for targeted hashtags
        brand_name: Brand name for branded hashtag
        trending_context: Any trending topics to incorporate
        max_hashtags: Maximum number of hashtags
        
    Returns:
        Dictionary with hashtags
    """
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        return {"status": "error", "message": "No API key found"}
    
    client = genai.Client(api_key=api_key)
    
    prompt = f"""Generate {max_hashtags} strategic Instagram hashtags for a post about:

**Topic:** {topic}
**Niche/Industry:** {niche or "general"}
**Brand Name:** {brand_name or "N/A"}
**Trending Context:** {trending_context or "None specified"}

**Hashtag Strategy:**
- Mix of high-volume (1M+ posts) and niche-specific tags
- Include 2-3 branded hashtags if brand name provided
- Add relevant trending hashtags
- Include community hashtags
- Mix different reach levels for optimal discovery

Return ONLY hashtags, one per line, each starting with #:"""

    try:
        response = client.models.generate_content(
            model=os.getenv("DEFAULT_MODEL", "gemini-2.5-flash"),
            contents=prompt
        )
        
        # Parse hashtags from response
        hashtags = []
        for line in response.text.strip().split("\n"):
            line = line.strip()
            if line.startswith("#"):
                # Clean up the hashtag
                tag = ''.join(c for c in line.split()[0] if c.isalnum() or c == '#')
                if tag and tag != "#":
                    hashtags.append(tag)
        
        # Remove duplicates while preserving order
        hashtags = list(dict.fromkeys(hashtags))[:max_hashtags]
        
        return {
            "status": "success",
            "hashtags": hashtags,
            "hashtag_string": " ".join(hashtags),
            "count": len(hashtags),
            "topic": topic
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


def improve_caption(
    original_caption: str,
    feedback: str,
    preserve_tone: bool = True
) -> dict:
    """
    Improve an existing caption based on feedback.
    
    Args:
        original_caption: The current caption
        feedback: What changes to make
        preserve_tone: Keep the same overall tone
        
    Returns:
        Dictionary with improved caption
    """
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        return {"status": "error", "message": "No API key found"}
    
    client = genai.Client(api_key=api_key)
    
    prompt = f"""Improve this Instagram caption based on the feedback:

**Original Caption:**
{original_caption}

**Feedback/Changes Requested:**
{feedback}

**Instructions:**
- {"Maintain the same overall tone and voice" if preserve_tone else "Adjust tone as needed"}
- Keep it engaging and authentic
- Ensure it's still suitable for Instagram
- Apply the requested changes thoughtfully

Write ONLY the improved caption, nothing else:"""

    try:
        response = client.models.generate_content(
            model=os.getenv("DEFAULT_MODEL", "gemini-2.5-flash"),
            contents=prompt
        )
        improved = response.text.strip()
        return {
            "status": "success",
            "improved_caption": improved,
            "character_count": len(improved),
            "changes_applied": feedback
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


def create_complete_post(
    topic: str,
    brand_name: str = "",
    brand_voice: str = "professional",
    niche: str = "",
    occasion: str = "",
    include_hashtags: bool = True
) -> dict:
    """
    Create a complete post with caption and hashtags.
    
    Args:
        topic: Main topic/theme
        brand_name: Brand name
        brand_voice: Brand's tone
        niche: Industry/niche
        occasion: Special occasion
        include_hashtags: Whether to include hashtags
        
    Returns:
        Dictionary with complete post content
    """
    # Generate caption
    caption_result = write_caption(
        topic=topic,
        brand_voice=brand_voice,
        occasion=occasion,
        include_cta=True
    )
    
    if caption_result["status"] != "success":
        return caption_result
    
    result = {
        "status": "success",
        "caption": caption_result["caption"],
        "caption_length": caption_result["character_count"]
    }
    
    # Generate hashtags if requested
    if include_hashtags:
        hashtag_result = generate_hashtags(
            topic=topic,
            niche=niche,
            brand_name=brand_name
        )
        
        if hashtag_result["status"] == "success":
            result["hashtags"] = hashtag_result["hashtags"]
            result["hashtag_string"] = hashtag_result["hashtag_string"]
            result["full_post"] = f"{caption_result['caption']}\n\n.\n.\n.\n\n{hashtag_result['hashtag_string']}"
        else:
            result["full_post"] = caption_result["caption"]
    else:
        result["full_post"] = caption_result["caption"]
    
    return result
