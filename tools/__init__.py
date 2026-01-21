"""Shared tools for Content Studio Agent."""

from .image_gen import generate_post_image, extract_brand_colors, edit_post_image, animate_image
from .web_search import search_trending_topics, search_web
from .content import write_caption, generate_hashtags, improve_caption
from .calendar import get_festivals_and_events, get_content_calendar_suggestions
from .instagram import scrape_instagram_profile, get_profile_summary

__all__ = [
    "generate_post_image",
    "extract_brand_colors",
    "edit_post_image",
    "animate_image",
    "search_trending_topics",
    "search_web",
    "write_caption",
    "generate_hashtags",
    "improve_caption",
    "get_festivals_and_events",
    "get_content_calendar_suggestions",
    "scrape_instagram_profile",
    "get_profile_summary",
]
