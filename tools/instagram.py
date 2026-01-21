"""Instagram profile analysis tools (simulated for MVP)."""

import re
from typing import Any


def scrape_instagram_profile(profile_url: str) -> dict:
    """
    Analyze Instagram profile from URL.
    
    For MVP/POC, this simulates profile analysis. In production,
    use official Instagram Graph API or approved services.
    
    Args:
        profile_url: Instagram profile URL (e.g., https://instagram.com/username)
        
    Returns:
        Dictionary containing profile analysis
    """
    username = extract_username(profile_url)
    
    # Simulated profile data for MVP
    return {
        "status": "success",
        "username": username,
        "profile_url": profile_url,
        "note": "MVP mode - Profile data is simulated. Please provide actual brand details for accurate results.",
        "profile_data": {
            "username": username,
            "full_name": f"{username.replace('_', ' ').title()}",
            "bio": "Sample bio - Please provide actual profile details for better content creation",
            "followers_count": "10K+",
            "following_count": "500",
            "posts_count": "150",
            "is_business_account": True,
            "category": "Brand/Business",
        },
        "content_analysis": {
            "posting_frequency": "3-5 posts per week",
            "top_performing_content": ["Product showcases", "Behind-the-scenes", "User testimonials"],
            "average_engagement": "3-5%",
            "best_performing_times": ["9 AM", "12 PM", "7 PM"],
        },
        "brand_voice": {
            "tone": "professional yet approachable",
            "style": "visual-first, storytelling",
            "themes": ["quality", "community", "innovation"],
            "emoji_usage": "moderate",
            "hashtag_style": "branded + trending mix"
        },
        "recommendations": [
            "Increase video/Reels content for better reach",
            "Engage more with comments within first hour",
            "Use more carousel posts for higher engagement",
            "Add more user-generated content"
        ],
        "agent_instructions": (
            "Since this is MVP mode with simulated data, please ask the user for: "
            "1. Industry/niche, 2. Brand colors, 3. Tone of voice, 4. Target audience, "
            "5. Key products/services, 6. Competitors to reference"
        )
    }


def extract_username(profile_url: str) -> str:
    """Extract Instagram username from URL or handle."""
    patterns = [
        r"instagram\.com/([^/?\s]+)",
        r"instagr\.am/([^/?\s]+)",
        r"^@?([a-zA-Z0-9._]+)$"
    ]
    
    for pattern in patterns:
        match = re.search(pattern, profile_url)
        if match:
            username = match.group(1).lstrip("@").rstrip("/")
            # Filter out non-profile paths
            if username not in ["p", "reel", "reels", "stories", "explore", "tv"]:
                return username
    
    # Fallback: try to extract from the string
    return profile_url.strip().lstrip("@").split("/")[-1].split("?")[0]


def get_profile_summary(username: str) -> str:
    """
    Generate a formatted summary of the Instagram profile.
    
    Args:
        username: Instagram username or profile URL
        
    Returns:
        Formatted string summary
    """
    # Scrape the profile first
    profile_data = scrape_instagram_profile(username)
    
    if not profile_data or profile_data.get("status") != "success":
        return "No profile data available."
    
    data = profile_data.get("profile_data", {})
    voice = profile_data.get("brand_voice", {})
    content = profile_data.get("content_analysis", {})
    
    summary = f"""
📊 **Profile Summary for @{data.get('username', 'unknown')}**

**Account Overview:**
- Name: {data.get('full_name', 'N/A')}
- Followers: {data.get('followers_count', 'N/A')}
- Posts: {data.get('posts_count', 'N/A')}
- Account Type: {data.get('category', 'Personal')}

**Content Performance:**
- Posting Frequency: {content.get('posting_frequency', 'N/A')}
- Avg Engagement: {content.get('average_engagement', 'N/A')}
- Best Times: {', '.join(content.get('best_performing_times', ['N/A']))}

**Brand Voice:**
- Tone: {voice.get('tone', 'Not analyzed')}
- Style: {voice.get('style', 'Not analyzed')}
- Key Themes: {', '.join(voice.get('themes', ['general']))}
- Emoji Usage: {voice.get('emoji_usage', 'N/A')}

**Top Content Types:**
{chr(10).join(['- ' + c for c in content.get('top_performing_content', ['N/A'])])}
""".strip()
    
    return summary


def analyze_post_performance(post_url: str) -> dict:
    """
    Analyze a specific Instagram post (simulated).
    
    Args:
        post_url: URL of the Instagram post
        
    Returns:
        Dictionary with post analysis
    """
    return {
        "status": "success",
        "post_url": post_url,
        "note": "MVP mode - Post analysis is simulated",
        "analysis": {
            "content_type": "Image Post",
            "estimated_reach": "5K-10K",
            "engagement_rate": "4.2%",
            "top_hashtags_used": 15,
            "caption_length": 180,
            "has_cta": True,
            "posting_time": "12:30 PM",
        },
        "what_worked": [
            "Strong visual composition",
            "Engaging first line in caption",
            "Relevant hashtag mix",
            "Good posting time"
        ],
        "improvement_suggestions": [
            "Could add more storytelling in caption",
            "Consider using carousel format",
            "Add location tag for local discovery"
        ]
    }


def get_hashtag_research(hashtag: str) -> dict:
    """
    Research a hashtag's performance (simulated).
    
    Args:
        hashtag: Hashtag to research (with or without #)
        
    Returns:
        Dictionary with hashtag analysis
    """
    tag = hashtag.lstrip("#")
    
    return {
        "status": "success",
        "hashtag": f"#{tag}",
        "note": "MVP mode - Hashtag data is simulated",
        "metrics": {
            "total_posts": "100K-500K",
            "daily_posts": "500-1000",
            "competition_level": "Medium",
            "recommended_for": "Growing accounts"
        },
        "related_hashtags": [
            f"#{tag}life",
            f"#{tag}daily",
            f"#{tag}community",
            f"#{tag}lover",
            f"#{tag}vibes"
        ],
        "best_used_with": [
            "Product showcases",
            "Lifestyle content",
            "Community posts"
        ]
    }
