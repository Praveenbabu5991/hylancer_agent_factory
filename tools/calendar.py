"""Calendar and event planning tools for campaign planning."""

import os
from datetime import datetime, timedelta
from typing import Any

from google import genai
from dotenv import load_dotenv

load_dotenv()


# Festival and event database
FESTIVALS_DB = {
    "january": [
        {"date": "01", "name": "New Year's Day", "type": "holiday", "themes": ["new beginnings", "goals", "fresh start"]},
        {"date": "14", "name": "Makar Sankranti", "type": "festival", "region": "India", "themes": ["harvest", "kites", "celebration"]},
        {"date": "26", "name": "Republic Day", "type": "national", "region": "India", "themes": ["patriotism", "pride", "unity"]},
    ],
    "february": [
        {"date": "14", "name": "Valentine's Day", "type": "observance", "themes": ["love", "relationships", "gifts"]},
    ],
    "march": [
        {"date": "08", "name": "International Women's Day", "type": "awareness", "themes": ["empowerment", "equality", "women"]},
        {"date": "variable", "name": "Holi", "type": "festival", "region": "India", "themes": ["colors", "celebration", "spring"]},
    ],
    "april": [
        {"date": "22", "name": "Earth Day", "type": "awareness", "themes": ["environment", "sustainability", "nature"]},
    ],
    "may": [
        {"date": "second_sunday", "name": "Mother's Day", "type": "observance", "themes": ["mothers", "gratitude", "family"]},
    ],
    "june": [
        {"date": "third_sunday", "name": "Father's Day", "type": "observance", "themes": ["fathers", "gratitude", "family"]},
        {"date": "21", "name": "International Yoga Day", "type": "awareness", "themes": ["wellness", "health", "mindfulness"]},
    ],
    "july": [
        {"date": "04", "name": "Independence Day", "type": "national", "region": "US", "themes": ["freedom", "patriotism", "celebration"]},
    ],
    "august": [
        {"date": "15", "name": "Independence Day", "type": "national", "region": "India", "themes": ["freedom", "patriotism", "pride"]},
        {"date": "variable", "name": "Raksha Bandhan", "type": "festival", "region": "India", "themes": ["siblings", "bond", "love"]},
    ],
    "september": [
        {"date": "05", "name": "Teachers' Day", "type": "observance", "region": "India", "themes": ["education", "gratitude", "teachers"]},
    ],
    "october": [
        {"date": "02", "name": "Gandhi Jayanti", "type": "national", "region": "India", "themes": ["peace", "non-violence", "inspiration"]},
        {"date": "variable", "name": "Dussehra/Navratri", "type": "festival", "region": "India", "themes": ["victory", "celebration", "tradition"]},
        {"date": "31", "name": "Halloween", "type": "observance", "themes": ["costumes", "fun", "spooky"]},
    ],
    "november": [
        {"date": "variable", "name": "Diwali", "type": "festival", "region": "India", "themes": ["lights", "prosperity", "celebration"]},
        {"date": "fourth_thursday", "name": "Thanksgiving", "type": "holiday", "region": "US", "themes": ["gratitude", "family", "feast"]},
        {"date": "last_friday", "name": "Black Friday", "type": "commercial", "themes": ["sales", "shopping", "deals"]},
    ],
    "december": [
        {"date": "25", "name": "Christmas", "type": "holiday", "themes": ["gifts", "joy", "celebration", "family"]},
        {"date": "31", "name": "New Year's Eve", "type": "holiday", "themes": ["celebration", "reflection", "party"]},
    ]
}


def get_festivals_and_events(
    month: str = "",
    region: str = "global",
    include_themes: bool = True
) -> dict:
    """
    Get festivals and events for content planning.
    
    Args:
        month: Month name (empty for current month)
        region: Geographic region filter
        include_themes: Include content theme suggestions
        
    Returns:
        Dictionary with events and themes
    """
    if not month:
        month = datetime.now().strftime("%B").lower()
    else:
        month = month.lower()
    
    events = FESTIVALS_DB.get(month, [])
    
    # Filter by region if specified
    if region != "global":
        events = [e for e in events if e.get("region", "global") in [region, "global"] or "region" not in e]
    
    result = {
        "status": "success",
        "month": month.title(),
        "region": region,
        "events": events,
        "count": len(events)
    }
    
    if include_themes and events:
        all_themes = []
        for event in events:
            all_themes.extend(event.get("themes", []))
        result["content_themes"] = list(set(all_themes))
    
    return result


def get_upcoming_events(
    days_ahead: int = 30,
    region: str = "global"
) -> dict:
    """
    Get upcoming events within a specified number of days.
    
    Args:
        days_ahead: Number of days to look ahead
        region: Geographic region filter
        
    Returns:
        Dictionary with upcoming events
    """
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        return {"status": "error", "message": "No API key found"}
    
    client = genai.Client(api_key=api_key)
    
    start_date = datetime.now()
    end_date = start_date + timedelta(days=days_ahead)
    
    prompt = f"""List important events, holidays, and observances from {start_date.strftime('%B %d, %Y')} to {end_date.strftime('%B %d, %Y')}.

Region Focus: {region}

For each event, provide:
- Date
- Event Name
- Type (holiday/festival/awareness day/commercial)
- Content Opportunity (how brands can leverage it)

Include: Major holidays, awareness days, cultural events, seasonal themes, and commercial events.
Format as a structured list."""

    try:
        response = client.models.generate_content(
            model=os.getenv("DEFAULT_MODEL", "gemini-2.5-flash"),
            contents=prompt
        )
        return {
            "status": "success",
            "start_date": start_date.strftime('%Y-%m-%d'),
            "end_date": end_date.strftime('%Y-%m-%d'),
            "region": region,
            "events": response.text.strip()
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


def get_content_calendar_suggestions(
    brand_name: str,
    niche: str = "general",
    tone: str = "professional",
    target_audience: str = "general audience",
    planning_period: str = "month",
    posts_per_week: int = 5
) -> dict:
    """
    Generate a content calendar with post suggestions.
    
    Args:
        brand_name: Name of the brand
        niche: Industry or niche
        tone: Brand tone of voice
        target_audience: Target audience description
        planning_period: week, month, or quarter
        posts_per_week: Target number of posts per week
        
    Returns:
        Dictionary with content calendar
    """
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        return {"status": "error", "message": "No API key found"}
    
    client = genai.Client(api_key=api_key)
    
    days_map = {"week": 7, "month": 30, "quarter": 90}
    days = days_map.get(planning_period, 30)
    
    start_date = datetime.now()
    end_date = start_date + timedelta(days=days)
    
    # Get events for context
    current_month = start_date.strftime("%B").lower()
    events = FESTIVALS_DB.get(current_month, [])
    events_str = ", ".join([e["name"] for e in events]) if events else "No major events"
    
    audience = target_audience
    
    prompt = f"""Create a detailed Instagram content calendar for {brand_name}.

**Brand Details:**
- Industry/Niche: {niche}
- Tone: {tone}
- Target Audience: {audience}

**Planning Period:** {start_date.strftime('%B %d')} to {end_date.strftime('%B %d, %Y')}
**Target:** {posts_per_week} posts per week

**Relevant Events This Period:** {events_str}

**Create a calendar with:**
1. Specific posting dates
2. Content type for each post (Feed post, Reel idea, Story series, Carousel)
3. Topic/Theme for each post
4. Best posting time recommendation
5. Caption hook idea
6. Hashtag category to use

**Content Mix Should Include:**
- Educational content (how-to, tips)
- Behind-the-scenes
- User engagement posts (questions, polls)
- Product/service highlights
- Event-based content
- Trending topic tie-ins

Format as a structured weekly calendar."""

    try:
        response = client.models.generate_content(
            model=os.getenv("DEFAULT_MODEL", "gemini-2.5-flash"),
            contents=prompt
        )
        return {
            "status": "success",
            "brand": brand_name,
            "period": planning_period,
            "start_date": start_date.strftime('%Y-%m-%d'),
            "end_date": end_date.strftime('%Y-%m-%d'),
            "posts_per_week": posts_per_week,
            "calendar": response.text.strip()
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


def suggest_best_posting_times(
    niche: str,
    target_audience: str = "",
    timezone: str = "IST"
) -> dict:
    """
    Suggest optimal posting times for Instagram.
    
    Args:
        niche: Industry/niche
        target_audience: Target audience description
        timezone: Timezone for recommendations
        
    Returns:
        Dictionary with posting time recommendations
    """
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        return {"status": "error", "message": "No API key found"}
    
    client = genai.Client(api_key=api_key)
    
    prompt = f"""Recommend optimal Instagram posting times for:

**Niche:** {niche}
**Target Audience:** {target_audience or "General audience"}
**Timezone:** {timezone}

Provide:
1. Best days of the week to post
2. Optimal times for each recommended day
3. Times to avoid
4. Reasoning behind recommendations
5. Tips for testing and optimizing

Base recommendations on typical social media engagement patterns."""

    try:
        response = client.models.generate_content(
            model=os.getenv("DEFAULT_MODEL", "gemini-2.5-flash"),
            contents=prompt
        )
        return {
            "status": "success",
            "niche": niche,
            "timezone": timezone,
            "recommendations": response.text.strip()
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}
