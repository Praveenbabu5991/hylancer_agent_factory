"""Tools package for Content Studio Agent."""

from tools.image_gen import (
    generate_post_image,
    edit_post_image,
    animate_image,
    extract_brand_colors,
)
from tools.content import (
    write_caption,
    generate_hashtags,
    improve_caption,
    create_complete_post,
)
from tools.calendar import (
    get_festivals_and_events,
    get_upcoming_events,
    get_content_calendar_suggestions,
    suggest_best_posting_times,
)
from tools.web_search import (
    get_ai_knowledge,
    search_trending_topics,
    get_competitor_insights,
    search_web,  # backward compatibility alias
)
from tools.instagram import (
    scrape_instagram_profile,
    get_profile_summary,
    extract_username,
)
from tools.web_scraper import (
    scrape_brand_from_url,
    get_brand_context_from_url,
)

__all__ = [
    # Image generation
    "generate_post_image",
    "edit_post_image",
    "animate_image",
    "extract_brand_colors",
    # Content creation
    "write_caption",
    "generate_hashtags",
    "improve_caption",
    "create_complete_post",
    # Calendar
    "get_festivals_and_events",
    "get_upcoming_events",
    "get_content_calendar_suggestions",
    "suggest_best_posting_times",
    # Research
    "get_ai_knowledge",
    "search_trending_topics",
    "get_competitor_insights",
    "search_web",
    # Instagram
    "scrape_instagram_profile",
    "get_profile_summary",
    "extract_username",
    # Web scraping (any URL)
    "scrape_brand_from_url",
    "get_brand_context_from_url",
]
