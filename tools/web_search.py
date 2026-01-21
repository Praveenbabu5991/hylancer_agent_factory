"""Web search tools using Gemini for trend research."""

import os
from datetime import datetime
from typing import Any

from google import genai
from dotenv import load_dotenv

load_dotenv()


def search_web(query: str, context: str = "") -> dict:
    """
    Search the web for information using Gemini's knowledge.
    
    Args:
        query: Search query
        context: Additional context for the search
        
    Returns:
        Dictionary with search results
    """
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        return {"status": "error", "message": "No API key found"}
    
    client = genai.Client(api_key=api_key)
    
    prompt = f"""As a research assistant, provide comprehensive information about:

Query: {query}
{f"Context: {context}" if context else ""}
Current Date: {datetime.now().strftime("%B %d, %Y")}

Provide accurate, up-to-date information that would be useful for social media content creation.
Include relevant facts, trends, and insights."""

    try:
        response = client.models.generate_content(
            model=os.getenv("DEFAULT_MODEL", "gemini-2.5-flash"),
            contents=prompt
        )
        return {
            "status": "success",
            "query": query,
            "results": response.text.strip(),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


def search_trending_topics(
    niche: str,
    region: str = "global",
    platform: str = "instagram"
) -> dict:
    """
    Search for trending topics relevant to a niche.
    
    Args:
        niche: Industry or topic niche
        region: Geographic region (global, US, India, etc.)
        platform: Social media platform (instagram, twitter, etc.)
        
    Returns:
        Dictionary with trending topics analysis
    """
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        return {"status": "error", "message": "No API key found"}
    
    client = genai.Client(api_key=api_key)
    
    prompt = f"""As a social media trend analyst, identify current trending topics for {platform} in the {niche} niche.

Region: {region}
Current Date: {datetime.now().strftime("%B %Y")}

Provide:
1. **Top 5 Trending Topics** - What's hot right now
2. **Emerging Trends** - 3 trends gaining momentum
3. **Popular Content Formats** - What type of content performs best
4. **Hashtag Trends** - Relevant trending hashtags (10-15)
5. **Content Opportunities** - Specific post ideas that could go viral

Be specific, actionable, and focused on what would work for content creators."""

    try:
        response = client.models.generate_content(
            model=os.getenv("DEFAULT_MODEL", "gemini-2.5-flash"),
            contents=prompt
        )
        return {
            "status": "success",
            "niche": niche,
            "region": region,
            "platform": platform,
            "trends_analysis": response.text.strip(),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


def get_competitor_insights(
    competitor_handles: str,
    platform: str = "instagram"
) -> dict:
    """
    Get insights about competitor accounts.
    
    Args:
        competitor_handles: Comma-separated list of competitor usernames
        platform: Social media platform
        
    Returns:
        Dictionary with competitor analysis
    """
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        return {"status": "error", "message": "No API key found"}
    
    client = genai.Client(api_key=api_key)
    
    handles_str = competitor_handles
    
    prompt = f"""As a social media strategist, provide insights about these {platform} accounts: {handles_str}

For each competitor, analyze (based on typical patterns for such accounts):
1. Content strategy patterns
2. Posting frequency recommendations
3. Engagement tactics they likely use
4. Content themes that work in their space
5. Gaps/opportunities for differentiation

Provide actionable insights for someone competing in the same space."""

    try:
        response = client.models.generate_content(
            model=os.getenv("DEFAULT_MODEL", "gemini-2.5-flash"),
            contents=prompt
        )
        return {
            "status": "success",
            "competitors": competitor_handles,
            "platform": platform,
            "insights": response.text.strip()
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}
