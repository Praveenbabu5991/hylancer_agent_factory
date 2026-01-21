"""
Image Generation Tools using Gemini API.

Provides image generation, editing, and animation capabilities
with proper error handling and rate limiting.
"""

import os
import uuid
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from google import genai
from google.genai import types
from PIL import Image
from colorthief import ColorThief
from dotenv import load_dotenv

load_dotenv()


class ImageGenerationError(Exception):
    """Custom exception for image generation errors."""
    pass


def _get_client():
    """Get Gemini client with validation."""
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ImageGenerationError(
            "API key not configured. Please set GOOGLE_API_KEY in your environment."
        )
    return genai.Client(api_key=api_key)


def _retry_with_backoff(func, max_retries: int = 3, base_delay: float = 1.0):
    """Execute function with exponential backoff retry."""
    last_error = None
    for attempt in range(max_retries):
        try:
            return func()
        except Exception as e:
            last_error = e
            error_str = str(e).lower()
            # Don't retry on certain errors
            if "invalid" in error_str or "not found" in error_str:
                raise
            if attempt < max_retries - 1:
                delay = base_delay * (2 ** attempt)
                print(f"⚠️ Attempt {attempt + 1} failed, retrying in {delay}s...")
                time.sleep(delay)
    raise last_error


def _format_error(error: Exception, context: str = "") -> dict:
    """Format error into user-friendly response."""
    error_str = str(error).lower()
    
    if "quota" in error_str or "rate" in error_str:
        message = "The image generation service is busy. Please wait a moment and try again."
    elif "safety" in error_str or "blocked" in error_str:
        message = "The image couldn't be generated due to content guidelines. Try adjusting your prompt."
    elif "api" in error_str and "key" in error_str:
        message = "There's an issue with the API configuration. Please contact support."
    elif "timeout" in error_str:
        message = "The image generation took too long. Try a simpler design."
    elif "not found" in error_str:
        message = "The requested model or resource wasn't found. Please try again."
    else:
        message = f"Image generation failed. {context}" if context else "Image generation failed. Please try again."
    
    return {
        "status": "error",
        "message": message,
        "technical_details": str(error)
    }


def extract_brand_colors(image_path: str) -> dict:
    """
    Extract dominant colors from a logo/image using ColorThief.
    
    Args:
        image_path: Path to the image file
        
    Returns:
        Dictionary with dominant color and palette
    """
    try:
        if not os.path.exists(image_path):
            return {
                "status": "error",
                "message": f"Image not found: {image_path}",
                "dominant": "#3498db",
                "palette": ["#3498db", "#2ecc71", "#e74c3c", "#f39c12", "#9b59b6"]
            }
        
        color_thief = ColorThief(image_path)
        dominant = color_thief.get_color(quality=1)
        palette = color_thief.get_palette(color_count=6, quality=1)
        
        def rgb_to_hex(rgb):
            return '#{:02x}{:02x}{:02x}'.format(rgb[0], rgb[1], rgb[2])
        
        return {
            "status": "success",
            "dominant": rgb_to_hex(dominant),
            "palette": [rgb_to_hex(color) for color in palette]
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Could not extract colors: {str(e)}",
            "dominant": "#3498db",
            "palette": ["#3498db", "#2ecc71", "#e74c3c", "#f39c12", "#9b59b6"]
        }


def generate_post_image(
    prompt: str,
    brand_name: str = "",
    brand_colors: str = "",
    style: str = "creative",
    logo_path: str = "",
    output_dir: str = "generated",
    industry: str = "",
    occasion: str = "",
    reference_images: str = "",
    company_overview: str = "",
    greeting_text: str = ""
) -> dict:
    """
    Generate a professional social media post image using Gemini.
    
    Args:
        prompt: Description of the image to generate
        brand_name: Name of the brand/company
        brand_colors: Comma-separated brand colors (hex codes)
        style: Visual style (creative, professional, playful, minimal, bold)
        logo_path: Path to logo image to incorporate
        output_dir: Directory to save generated images
        industry: Brand's industry/niche
        occasion: Special occasion/event theme
        reference_images: Comma-separated paths to reference images
        company_overview: Description of what the company does
        greeting_text: Event greeting text (e.g., "Happy Valentine's Day!")
        
    Returns:
        Dictionary with image path and generation details
    """
    print(f"🎨 Generating image for: {brand_name or 'brand'}")
    print(f"   Style: {style}, Occasion: {occasion or 'general'}")
    
    try:
        client = _get_client()
        
        # Build color instructions - STRONGLY emphasize brand colors
        color_scheme = ""
        colors_list = []
        if brand_colors:
            colors_list = [c.strip() for c in brand_colors.split(",") if c.strip()]
            if colors_list:
                primary = colors_list[0]
                color_scheme = f"""
COLOR PALETTE (MUST USE THESE COLORS PROMINENTLY):
- PRIMARY COLOR: {primary} - Use this as the DOMINANT color in the image
- This color should be visible in backgrounds, overlays, accents, or lighting
"""
                if len(colors_list) > 1:
                    color_scheme += f"- SECONDARY COLORS: {', '.join(colors_list[1:4])} - Use as accents\n"
                color_scheme += f"- The overall color mood of the image should reflect {primary}\n"
        
        # Style descriptions
        style_map = {
            'creative': 'Artistic, imaginative, visually striking',
            'professional': 'Clean, corporate, polished',
            'playful': 'Fun, vibrant, energetic',
            'minimal': 'Simple, clean, focused',
            'bold': 'Strong, impactful, attention-grabbing'
        }
        style_desc = style_map.get(style, style_map['creative'])
        
        # Extract colors from reference images if provided
        ref_colors = []
        ref_context = ""
        has_refs = False
        
        if reference_images:
            ref_paths = [p.strip() for p in reference_images.split(",") if p.strip() and os.path.exists(p.strip())]
            if ref_paths:
                has_refs = True
                print(f"   📸 Using {len(ref_paths)} reference images")
                for rp in ref_paths[:3]:
                    try:
                        colors = extract_brand_colors(rp)
                        if colors.get("status") == "success":
                            ref_colors.append(colors.get("dominant"))
                            ref_colors.extend(colors.get("palette", [])[:2])
                    except:
                        pass
                
                ref_colors = list(dict.fromkeys(ref_colors))[:6]
                ref_context = f"""
REFERENCE IMAGES PROVIDED - Match this visual style:
- Extracted colors: {', '.join(ref_colors) if ref_colors else 'Match reference style'}
- Match the design style, composition, and mood from references
- Create an image that looks like it belongs in the same campaign"""
        
        # Build the generation prompt with strong color emphasis
        primary_color = colors_list[0] if colors_list else "#000000"
        
        full_prompt = f"""Create a premium Instagram post image for {brand_name or 'a brand'}.

CONTENT DESCRIPTION: {prompt}

BRAND IDENTITY:
- Brand: {brand_name or 'Brand'}
- Industry: {industry or 'General'}
{f"- About: {company_overview}" if company_overview else ""}

{color_scheme}

VISUAL STYLE: {style_desc}
{f"OCCASION/THEME: {occasion}" if occasion else ""}

CRITICAL COLOR REQUIREMENT:
The image MUST prominently feature the brand's primary color ({primary_color}).
This means: 
- Use {primary_color} in the background gradient/overlay OR
- Use {primary_color} in prominent visual elements OR
- Ensure the overall color mood reflects {primary_color}
- The brand colors should be immediately recognizable

TEXT ON IMAGE (MUST appear clearly and be readable):
{f'MAIN TEXT AT TOP: {greeting_text}' if greeting_text else ''}
Extract any headline, tagline, subtext, and CTA text from the content description above.

CRITICAL - TEXT FORMATTING RULES:
- NEVER put labels like "HEADLINE:", "GREETING:", "SUBTEXT:", "CTA:" on the image
- Only put the ACTUAL text content that should be read by viewers
- For example, if the brief says 'HEADLINE: "Innovate Today"' → put "Innovate Today" on the image, NOT the word "HEADLINE"
- All text should be legible, well-placed, and contrast with the background

{ref_context if has_refs else '''
VISUAL APPROACH: Professional photography with real, diverse people.
Natural lighting, authentic expressions, premium magazine quality.'''}

TECHNICAL SPECIFICATIONS:
- Aspect ratio: 4:5 (Instagram optimal)
- Ultra high resolution and quality
- All text must be sharp and readable
- Brand colors must be prominently visible
{f"- Include {brand_name} logo: Bottom-right corner, subtle but clear" if logo_path else ""}

Create a scroll-stopping, on-brand, magazine-quality image that immediately evokes the brand's identity through its color palette."""

        # Prepare content with images
        contents = [full_prompt]
        
        if logo_path and os.path.exists(logo_path):
            try:
                logo_image = Image.open(logo_path)
                contents.append(logo_image)
                print(f"   📷 Added logo: {logo_path}")
            except Exception as e:
                print(f"   ⚠️ Could not load logo: {e}")
        
        if reference_images:
            ref_paths = [p.strip() for p in reference_images.split(",") if p.strip()]
            for ref_path in ref_paths[:3]:  # Limit to 3 references
                if os.path.exists(ref_path):
                    try:
                        ref_image = Image.open(ref_path)
                        contents.append(ref_image)
                        print(f"   📷 Added reference: {ref_path}")
                    except Exception as e:
                        print(f"   ⚠️ Could not load reference {ref_path}: {e}")
        
        # Generate image with retry
        model = os.getenv("IMAGE_MODEL", "gemini-2.0-flash-exp")
        
        def make_request():
            return client.models.generate_content(
                model=model,
                contents=contents,
                config=types.GenerateContentConfig(
                    response_modalities=["image", "text"],
                )
            )
        
        response = _retry_with_backoff(make_request)
        
        # Save the generated image
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        for part in response.candidates[0].content.parts:
            if part.inline_data is not None:
                image_id = str(uuid.uuid4())[:8]
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"post_{timestamp}_{image_id}.png"
                image_path = output_path / filename
                
                with open(image_path, "wb") as f:
                    f.write(part.inline_data.data)
                
                print(f"   ✅ Image saved: {image_path}")
                
                return {
                    "status": "success",
                    "image_path": str(image_path),
                    "filename": filename,
                    "url": f"/generated/{filename}",
                    "prompt_used": prompt,
                    "style": style,
                    "model": model
                }
        
        return {
            "status": "error",
            "message": "No image was generated. Try adjusting your prompt."
        }
            
    except Exception as e:
        return _format_error(e, "Try simplifying your design request.")


def edit_post_image(
    original_image_path: str,
    edit_instruction: str,
    output_dir: str = "generated"
) -> dict:
    """
    Edit an existing image based on instructions.
    
    Args:
        original_image_path: Path to the original image
        edit_instruction: What changes to make
        output_dir: Directory to save edited images
        
    Returns:
        Dictionary with new image path and edit details
    """
    print(f"✏️ Editing image: {original_image_path}")
    print(f"   Instruction: {edit_instruction[:50]}...")
    
    try:
        client = _get_client()
        
        if not os.path.exists(original_image_path):
            return {
                "status": "error",
                "message": f"Original image not found: {original_image_path}"
            }
        
        edit_prompt = f"""Edit this image with the following changes:
{edit_instruction}

Keep the overall quality and brand feel while making the requested modifications.
Maintain professional, high-quality output suitable for Instagram."""

        original_image = Image.open(original_image_path)
        model = os.getenv("IMAGE_MODEL", "gemini-2.0-flash-exp")
        
        def make_request():
            return client.models.generate_content(
                model=model,
                contents=[edit_prompt, original_image],
                config=types.GenerateContentConfig(
                    response_modalities=["image", "text"],
                )
            )
        
        response = _retry_with_backoff(make_request)
        
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        for part in response.candidates[0].content.parts:
            if part.inline_data is not None:
                image_id = str(uuid.uuid4())[:8]
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"edited_{timestamp}_{image_id}.png"
                image_path = output_path / filename
                
                with open(image_path, "wb") as f:
                    f.write(part.inline_data.data)
                
                print(f"   ✅ Edited image saved: {image_path}")
                
                return {
                    "status": "success",
                    "image_path": str(image_path),
                    "filename": filename,
                    "url": f"/generated/{filename}",
                    "edit_instruction": edit_instruction,
                    "original_image": original_image_path
                }
        
        return {
            "status": "error",
            "message": "Could not generate edited image. Try different edit instructions."
        }
            
    except Exception as e:
        return _format_error(e, "Try simpler edit instructions.")


def animate_image(
    image_path: str,
    motion_prompt: str,
    duration_seconds: int = 5,
    output_dir: str = "generated"
) -> dict:
    """
    Animate a static image to create a short video/cinemagraph.
    
    NOTE: Video generation model availability varies by region/account.
    Falls back to helpful guidance if unavailable.
    
    Args:
        image_path: Path to the static image to animate
        motion_prompt: Description of desired motion
        duration_seconds: Length of video (3-8 seconds recommended)
        output_dir: Directory to save the generated video
        
    Returns:
        Dictionary with video path or guidance for alternatives
    """
    print(f"🎬 Animating image: {image_path}")
    print(f"   Motion: {motion_prompt[:50]}...")
    
    try:
        client = _get_client()
        
        if not os.path.exists(image_path):
            return {
                "status": "error",
                "message": f"Image not found: {image_path}"
            }
        
        animation_prompt = f"""Create a short, looping video animation from this image.

MOTION: {motion_prompt}

GUIDELINES:
- Duration: {duration_seconds} seconds
- Smooth, seamless loop
- Keep brand elements (logo, text) stable
- Subtle, professional motion
- Perfect for Instagram Reels/Stories"""

        video_model = os.getenv("VIDEO_MODEL", "veo-2.0-generate-001")
        source_image = Image.open(image_path)
        
        def make_request():
            return client.models.generate_content(
                model=video_model,
                contents=[animation_prompt, source_image],
                config=types.GenerateContentConfig(
                    response_modalities=["video"],
                )
            )
        
        try:
            response = _retry_with_backoff(make_request, max_retries=2)
            
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
            
            for part in response.candidates[0].content.parts:
                if part.inline_data is not None and "video" in part.inline_data.mime_type:
                    video_id = str(uuid.uuid4())[:8]
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    filename = f"animated_{timestamp}_{video_id}.mp4"
                    video_path = output_path / filename
                    
                    with open(video_path, "wb") as f:
                        f.write(part.inline_data.data)
                    
                    print(f"   ✅ Video saved: {video_path}")
                    
                    return {
                        "status": "success",
                        "video_path": str(video_path),
                        "filename": filename,
                        "url": f"/generated/{filename}",
                        "motion_prompt": motion_prompt,
                        "duration_seconds": duration_seconds,
                        "source_image": image_path,
                        "type": "video"
                    }
        
        except Exception as model_error:
            error_str = str(model_error).lower()
            if "not found" in error_str or "invalid" in error_str or "unavailable" in error_str:
                # Model not available - provide helpful alternatives
                return {
                    "status": "model_unavailable",
                    "message": "Video generation is not available in your region/account.",
                    "source_image": image_path,
                    "motion_prompt": motion_prompt,
                    "alternatives": [
                        "Runway ML (runwayml.com) - Image to Video",
                        "Pika Labs (pika.art) - Motion generation",
                        "Kaiber AI - Image animation",
                        "LeiaPix - 3D depth animation"
                    ],
                    "export_data": {
                        "image_path": image_path,
                        "motion_instructions": motion_prompt,
                        "duration": f"{duration_seconds} seconds"
                    }
                }
            raise
        
        return {
            "status": "partial",
            "message": "Animation processing. The result will be available shortly.",
            "source_image": image_path,
            "motion_prompt": motion_prompt
        }
            
    except Exception as e:
        return _format_error(e, "Video generation may not be available in your region.")
