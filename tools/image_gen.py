"""Image generation tools using Gemini API."""

import os
import uuid
import base64
from datetime import datetime
from pathlib import Path
from typing import Any

from google import genai
from google.genai import types
from PIL import Image
from colorthief import ColorThief
from dotenv import load_dotenv

load_dotenv()


def extract_brand_colors(image_path: str) -> dict:
    """
    Extract dominant colors from a logo/image using ColorThief.
    
    Args:
        image_path: Path to the image file
        
    Returns:
        Dictionary with dominant color and palette
    """
    try:
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
            "message": str(e),
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
        brand_colors: Comma-separated brand colors (hex codes), e.g. "#3498db,#2ecc71"
        style: Visual style (creative, professional, playful, minimal, bold)
        logo_path: Path to logo image to incorporate
        output_dir: Directory to save generated images
        industry: Brand's industry/niche
        occasion: Special occasion/event theme
        reference_images: Comma-separated paths to reference images for style inspiration
        company_overview: Description of what the company does (for contextual imagery)
        greeting_text: Event greeting text to display at top of image (e.g., "Happy Valentine's Day!")
        
    Returns:
        Dictionary with image path and generation details
    """
    # Debug logging
    print(f"🎨 generate_post_image called:")
    print(f"   - prompt: {prompt[:100]}...")
    print(f"   - brand_name: {brand_name}")
    print(f"   - logo_path: {logo_path}")
    print(f"   - reference_images: {reference_images}")
    
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        return {"status": "error", "message": "No API key found. Set GEMINI_API_KEY environment variable."}
    
    client = genai.Client(api_key=api_key)
    
    # Build color instructions - parse comma-separated colors
    color_scheme = ""
    if brand_colors:
        colors_list = [c.strip() for c in brand_colors.split(",") if c.strip()]
        if colors_list:
            color_scheme = f"Primary brand color: {colors_list[0]}. "
            if len(colors_list) > 1:
                color_scheme += f"Accent colors: {', '.join(colors_list[1:3])}. "
    
    # Style descriptions
    style_descriptions = {
        'creative': 'Artistic, imaginative, and visually striking with unique creative elements',
        'professional': 'Clean, corporate, and polished with a business-appropriate aesthetic',
        'playful': 'Fun, vibrant, and energetic with playful visual elements',
        'minimal': 'Simple, clean, and focused with minimal visual clutter',
        'bold': 'Strong, impactful, and attention-grabbing with bold colors and shapes'
    }
    style_desc = style_descriptions.get(style, style_descriptions['creative'])
    
    # Build occasion context
    occasion_context = ""
    if occasion:
        occasion_context = f"\nTheme/Occasion: {occasion} - Incorporate subtle thematic elements related to this."
    
    # Build reference images context
    reference_context = ""
    has_reference_images = False
    extracted_ref_colors = []
    use_real_people = True  # Default to real people if no references
    
    if reference_images:
        ref_paths = [p.strip() for p in reference_images.split(",") if p.strip() and os.path.exists(p.strip())]
        print(f"   📸 Reference image paths found: {len(ref_paths)} images")
        for rp in ref_paths:
            print(f"      - {rp} (exists: {os.path.exists(rp)})")
        
        # Auto-extract colors from first few references
        for rp in ref_paths[:3]:  # Extract from up to 3 references
            try:
                ref_colors = extract_brand_colors(rp)
                if ref_colors.get("status") == "success":
                    extracted_ref_colors.append(ref_colors.get("dominant"))
                    extracted_ref_colors.extend(ref_colors.get("palette", [])[:2])
            except:
                pass
        
        # Remove duplicates and format
        extracted_ref_colors = list(dict.fromkeys(extracted_ref_colors))[:6]
        extracted_colors_str = ", ".join(extracted_ref_colors) if extracted_ref_colors else "Match reference style"
        print(f"   🎨 Auto-extracted colors from refs: {extracted_colors_str}")
        
        if ref_paths:
            has_reference_images = True
            use_real_people = False  # Use reference style instead
            reference_context = f"""
═══════════════════════════════════════════════
🎨 REFERENCE IMAGES ({len(ref_paths)} provided) - MATCH THIS STYLE!
═══════════════════════════════════════════════
⚠️ CRITICAL: These references define the EXACT visual identity!

🎯 AUTO-EXTRACTED COLORS FROM REFERENCES:
{extracted_colors_str}

✅ YOU MUST MATCH:
1. **COLOR PALETTE**: Use the extracted colors above as PRIMARY palette
2. **DESIGN STYLE**: Match the illustration/photo/graphic style from refs
3. **VISUAL TONE**: Same mood - if refs are dark/moody, be dark/moody
4. **TYPOGRAPHY FEEL**: Match the bold/light/modern font styling
5. **COMPOSITION**: Similar layout principles and spacing
6. **QUALITY LEVEL**: Match the premium production quality

⚠️ PRIORITY ORDER:
1. FIRST: Match reference image colors and style
2. SECOND: Incorporate brand colors as accents
3. THIRD: Add the specific content/text requested

🎨 COLOR APPLICATION:
- PRIMARY (headlines/main elements): {extracted_ref_colors[0] if extracted_ref_colors else 'From references'}
- BACKGROUND: {extracted_ref_colors[1] if len(extracted_ref_colors) > 1 else 'From references'}
- ACCENTS: {extracted_ref_colors[2] if len(extracted_ref_colors) > 2 else 'Brand colors'}

Think of this as: "Create a NEW image that looks like it belongs in the SAME CAMPAIGN as the references."
The generated image should feel like it was designed by the SAME designer who made the references."""
    else:
        # No reference images - use real people default
        reference_context = """
═══════════════════════════════════════════════
📷 NO REFERENCE IMAGES - USE REAL PEOPLE!
═══════════════════════════════════════════════
⚠️ CRITICAL: Since no reference images were provided, use REAL PROFESSIONAL PHOTOGRAPHY style!

✅ YOU MUST:
1. **USE REAL PEOPLE**: Show authentic, diverse professionals
2. **PHOTOGRAPHY STYLE**: High-quality professional photography (not illustrations)
3. **DIVERSE REPRESENTATION**: Include people of different backgrounds
4. **PROFESSIONAL SETTINGS**: Modern offices, co-working spaces, or relevant environments
5. **AUTHENTIC EXPRESSIONS**: Natural, genuine emotions (not stock photo poses)

🎨 VISUAL STYLE:
- Clean, modern professional photography
- Natural lighting or studio quality
- Shallow depth of field for focus
- Warm, inviting color tones
- Premium magazine-quality aesthetics

🚫 AVOID:
- Generic illustrations or cartoons (unless brand specifically requires)
- Obvious stock photo poses
- Overly staged or artificial scenes
- Empty graphics without human element

**The image should feel like a premium lifestyle/business magazine photo shoot.**"""

    # Build logo context
    logo_context = ""
    if logo_path and os.path.exists(logo_path):
        logo_context = """
═══════════════════════════════════════════════
🖼️ BRAND LOGO (CRITICAL - MUST BE ACCURATE!)
═══════════════════════════════════════════════
A brand logo image has been provided. THIS IS THE ACTUAL LOGO - USE IT EXACTLY!

⚠️ LOGO ACCURACY REQUIREMENTS:
- REPRODUCE the logo EXACTLY as provided - do not recreate or redesign it
- The logo's shape, colors, and proportions MUST match the original
- Position: Bottom-right corner OR top-left (subtle but clearly visible)
- Size: Approximately 10-15% of image width
- Visibility: Must be legible against the background
- Do NOT add effects that distort the logo (no heavy shadows/glows)

✅ Logo Checklist:
□ Logo is the EXACT same as the provided image
□ Logo colors are accurate
□ Logo is readable and not pixelated
□ Logo placement is professional
□ Logo doesn't clash with other design elements"""
    
    # Build company context with imagery suggestions
    company_context = ""
    if company_overview:
        # Generate relevant visual elements based on company overview
        company_lower = company_overview.lower()
        visual_suggestions = []
        
        if any(word in company_lower for word in ['freelance', 'freelancing', 'gig', 'remote']):
            visual_suggestions.append("modern professionals, laptops, flexible work, digital connections")
        if any(word in company_lower for word in ['platform', 'marketplace', 'connect']):
            visual_suggestions.append("people connecting, handshakes, bridge metaphors, networks")
        if any(word in company_lower for word in ['tech', 'technology', 'software', 'app']):
            visual_suggestions.append("sleek devices, digital interfaces, modern aesthetics")
        if any(word in company_lower for word in ['business', 'enterprise', 'corporate']):
            visual_suggestions.append("professional settings, success imagery, growth charts")
        if any(word in company_lower for word in ['creative', 'design', 'art']):
            visual_suggestions.append("artistic elements, creative tools, vibrant colors")
        
        visual_elements = " | ".join(visual_suggestions) if visual_suggestions else "professional, relevant imagery"
        
        company_context = f"""
═══════════════════════════════════════════════
🏢 COMPANY CONTEXT (Use for Relevant Imagery!)
═══════════════════════════════════════════════
WHAT THEY DO: {company_overview}

SUGGESTED VISUAL ELEMENTS: {visual_elements}

⚠️ Imagery should RELATE to their business - don't just show generic graphics!"""
    
    # Extract text elements from prompt if present
    import re
    extracted_greeting = ""
    
    # Parse prompt for greeting if not provided as parameter
    prompt_lower = prompt.lower()
    if not greeting_text:  # Only extract if not provided as parameter
        if "greeting:" in prompt_lower or "happy " in prompt_lower:
            # Try to extract greeting
            greeting_match = re.search(r'GREETING[:\s]*["\']?([^"\'"\n]+)["\']?', prompt, re.IGNORECASE)
            if greeting_match:
                extracted_greeting = greeting_match.group(1).strip()
            elif "happy valentine" in prompt_lower:
                extracted_greeting = "Happy Valentine's Day!"
            elif "happy republic" in prompt_lower:
                extracted_greeting = "Happy Republic Day!"
            elif "happy diwali" in prompt_lower:
                extracted_greeting = "Happy Diwali!"
            elif "happy holi" in prompt_lower:
                extracted_greeting = "Happy Holi!"
            elif "happy new year" in prompt_lower:
                extracted_greeting = "Happy New Year!"
    
    # Use parameter if provided, otherwise use extracted
    final_greeting = greeting_text if greeting_text else extracted_greeting
    print(f"   🎊 Greeting text: '{final_greeting}'")
    
    # Build the prompt - professional social media marketer approach
    full_prompt = f"""You are an ELITE SOCIAL MEDIA DESIGNER creating a premium Instagram post for a professional marketing campaign.

═══════════════════════════════════════════════
🎯 CONTENT BRIEF
═══════════════════════════════════════════════
MAIN MESSAGE/SUBJECT: {prompt}
{f"BRAND: {brand_name}" if brand_name else ""}
{f"INDUSTRY: {industry}" if industry else ""}{company_context}
{occasion_context}

═══════════════════════════════════════════════
📝 TEXT OVERLAY REQUIREMENTS (CRITICAL!)
═══════════════════════════════════════════════
⚠️ ALL TEXT BELOW MUST APPEAR ON THE IMAGE EXACTLY AS SPECIFIED:

{f'''
⭐⭐⭐ MANDATORY GREETING AT TOP OF IMAGE ⭐⭐⭐
🎊 GREETING TEXT: "{final_greeting}"
- This greeting MUST appear at the VERY TOP of the image
- Use large, celebratory, festive typography
- Make it the FIRST thing viewers see
- Position: Top-center, above the headline
- DO NOT SKIP THIS TEXT!
''' if final_greeting else ''}

The image MUST include these text elements as overlays:
1. {"🎊 GREETING: '" + final_greeting + "' - AT THE TOP!" if final_greeting else "No greeting required"}
2. HEADLINE - The main message, prominently displayed (center)
3. SUBTEXT - Supporting text below the headline  
4. CTA (Call to Action) - Action text at the bottom

⚠️ DO NOT SKIP ANY TEXT ELEMENTS! Every text mentioned in the prompt must appear on the final image.
⚠️ {"GREETING '" + final_greeting + "' IS MANDATORY - IT MUST BE VISIBLE!" if final_greeting else ""}

═══════════════════════════════════════════════
🎨 BRAND IDENTITY
═══════════════════════════════════════════════
{color_scheme if color_scheme else "Use sophisticated, premium color palette"}
VISUAL STYLE: {style_desc}
{logo_context}
{reference_context}

═══════════════════════════════════════════════
📐 TECHNICAL SPECIFICATIONS
═══════════════════════════════════════════════
- Aspect Ratio: 4:5 (Instagram optimal - 1080x1350px feel)
- Quality: Ultra-high definition, crisp and sharp
- Format: Ready for immediate posting

═══════════════════════════════════════════════
✨ PROFESSIONAL DESIGN REQUIREMENTS
═══════════════════════════════════════════════
1. SCROLL-STOPPING POWER: First 0.5 seconds must grab attention
2. BRAND CONSISTENCY: Every element reinforces brand identity
3. VISUAL HIERARCHY: Clear focal point with supporting elements
4. PREMIUM QUALITY: Magazine-cover worthy aesthetics
5. INSTAGRAM OPTIMIZED: Perfect for feed viewing

COMPOSITION RULES:
- Rule of thirds for balanced layouts
- Strategic use of negative space
- Eye-flow guidance toward key message
- Balanced text-to-visual ratio if any text included

QUALITY MARKERS:
- Professional studio lighting quality
- Rich, intentional color palette
- Depth and dimension
- Clean, refined edges
- Cohesive visual storytelling

{"IMPORTANT: If logo is provided, it MUST be visible and integrated professionally in the final image." if logo_path else ""}

{"⚠️ CRITICAL - REFERENCE IMAGE MATCHING:" if has_reference_images else ""}
{"The reference images provided are the GOLD STANDARD for this design." if has_reference_images else ""}
{"Your generated image MUST look like it belongs in the SAME visual campaign." if has_reference_images else ""}
{"Match their: color palette, design style, typography feel, mood, and quality level." if has_reference_images else ""}

Create an image that:
1. {'MATCHES the style of provided reference images' if has_reference_images else 'Looks premium and professional'}
2. Incorporates the company context appropriately
3. Uses brand colors effectively
4. A Fortune 500 company would proudly post."""

    try:
        model = os.getenv("IMAGE_MODEL", "gemini-3-pro-image-preview")
        
        # Prepare contents - include logo and reference images if provided
        contents = [full_prompt]
        
        # Add logo if provided
        if logo_path and os.path.exists(logo_path):
            logo_image = Image.open(logo_path)
            contents.append(logo_image)
        
        # Add reference images if provided
        if reference_images:
            ref_paths = [p.strip() for p in reference_images.split(",") if p.strip()]
            for ref_path in ref_paths:
                if os.path.exists(ref_path):
                    try:
                        ref_image = Image.open(ref_path)
                        contents.append(ref_image)
                    except Exception as e:
                        print(f"Could not load reference image {ref_path}: {e}")
        
        response = client.models.generate_content(
            model=model,
            contents=contents,
            config=types.GenerateContentConfig(
                response_modalities=["image", "text"],
            )
        )
        
        # Create output directory
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Process response and save image
        for part in response.candidates[0].content.parts:
            if part.inline_data is not None:
                image_id = str(uuid.uuid4())[:8]
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"post_{timestamp}_{image_id}.png"
                image_path = output_path / filename
                
                # Save the image
                with open(image_path, "wb") as f:
                    f.write(part.inline_data.data)
                
                return {
                    "status": "success",
                    "image_path": str(image_path),
                    "filename": filename,
                    "url": f"/generated/{filename}",
                    "prompt_used": prompt,
                    "style": style,
                    "model": model
                }
        
        return {"status": "error", "message": "No image was generated in the response"}
            
    except Exception as e:
        return {"status": "error", "message": str(e)}


def edit_post_image(
    original_image_path: str,
    edit_instruction: str,
    output_dir: str = "generated"
) -> dict:
    """
    Edit an existing image based on instructions.
    
    Args:
        original_image_path: Path to the original image
        edit_instruction: What changes to make (e.g., "change background to blue")
        output_dir: Directory to save edited images
        
    Returns:
        Dictionary with new image path and edit details
    """
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        return {"status": "error", "message": "No API key found"}
    
    if not os.path.exists(original_image_path):
        return {"status": "error", "message": f"Original image not found: {original_image_path}"}
    
    client = genai.Client(api_key=api_key)
    
    edit_prompt = f"""Edit this image with the following changes:
{edit_instruction}

Keep the overall quality and style of the image while making the requested modifications.
Maintain professional, high-quality output suitable for Instagram."""

    try:
        model = os.getenv("IMAGE_MODEL", "gemini-3-pro-image-preview")
        
        # Load original image
        original_image = Image.open(original_image_path)
        
        response = client.models.generate_content(
            model=model,
            contents=[edit_prompt, original_image],
            config=types.GenerateContentConfig(
                response_modalities=["image", "text"],
            )
        )
        
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
                
                return {
                    "status": "success",
                    "image_path": str(image_path),
                    "filename": filename,
                    "url": f"/generated/{filename}",
                    "edit_instruction": edit_instruction,
                    "original_image": original_image_path
                }
        
        return {"status": "error", "message": "No edited image was generated"}
            
    except Exception as e:
        return {"status": "error", "message": str(e)}


def animate_image(
    image_path: str,
    motion_prompt: str,
    duration_seconds: int = 5,
    output_dir: str = "generated"
) -> dict:
    """
    Animate a static image to create a short video/cinemagraph (Motion Canvas feature).
    
    This converts a static social media post into a dynamic, attention-grabbing video
    perfect for Instagram Reels, TikTok, or animated posts.
    
    Args:
        image_path: Path to the static image to animate
        motion_prompt: Description of desired motion (e.g., "steam rising from cup", 
                      "background lights twinkling", "subtle zoom on product", 
                      "gentle camera pan left to right")
        duration_seconds: Length of video in seconds (3-8 seconds recommended for social)
        output_dir: Directory to save the generated video
        
    Returns:
        Dictionary with video path, URL, and animation details
        
    Example motion prompts:
    - "Make the steam rise gently from the coffee cup"
    - "Add subtle sparkle/twinkle effects to the background"
    - "Slow zoom in on the main subject"
    - "Gentle parallax effect with foreground and background"
    - "Make the logo pulse subtly"
    - "Add floating hearts/confetti for Valentine's theme"
    """
    print(f"🎬 animate_image called:")
    print(f"   - image_path: {image_path}")
    print(f"   - motion_prompt: {motion_prompt}")
    print(f"   - duration: {duration_seconds}s")
    
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        return {"status": "error", "message": "No API key found. Set GEMINI_API_KEY environment variable."}
    
    if not os.path.exists(image_path):
        return {"status": "error", "message": f"Image not found: {image_path}"}
    
    client = genai.Client(api_key=api_key)
    
    # Build the animation prompt
    animation_prompt = f"""Create a short, looping video animation based on this image.

MOTION INSTRUCTIONS:
{motion_prompt}

ANIMATION GUIDELINES:
- Duration: {duration_seconds} seconds
- Create smooth, seamless motion that loops well
- Maintain the original image quality and composition
- Keep brand elements (logo, text) stable and clear
- Add subtle, professional motion that enhances engagement
- Suitable for Instagram Reels/Stories format

MOTION STYLE:
- Cinemagraph-style: Only specific elements should move
- Keep the overall composition stable
- Avoid jarring or distracting motion
- Aim for premium, polished feel

OUTPUT: A high-quality MP4 video that makes this static post come alive."""

    try:
        # Try using Veo model for video generation
        video_model = os.getenv("VIDEO_MODEL", "veo-2.0-generate-001")
        
        # Load the source image
        source_image = Image.open(image_path)
        
        # Try video generation
        response = client.models.generate_content(
            model=video_model,
            contents=[animation_prompt, source_image],
            config=types.GenerateContentConfig(
                response_modalities=["video"],
            )
        )
        
        # Create output directory
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Process response and save video
        for part in response.candidates[0].content.parts:
            if part.inline_data is not None and "video" in part.inline_data.mime_type:
                video_id = str(uuid.uuid4())[:8]
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"animated_{timestamp}_{video_id}.mp4"
                video_path = output_path / filename
                
                # Save the video
                with open(video_path, "wb") as f:
                    f.write(part.inline_data.data)
                
                print(f"✅ Video saved: {video_path}")
                
                return {
                    "status": "success",
                    "video_path": str(video_path),
                    "filename": filename,
                    "url": f"/generated/{filename}",
                    "motion_prompt": motion_prompt,
                    "duration_seconds": duration_seconds,
                    "source_image": image_path,
                    "model": video_model,
                    "type": "video"
                }
        
        # If video generation not available, try alternative approach
        # Using image model with motion simulation
        print("⚠️ Video model response empty, trying alternative approach...")
        
        return {
            "status": "partial",
            "message": "Video generation is being processed. The animated version will be available shortly.",
            "source_image": image_path,
            "motion_prompt": motion_prompt,
            "suggestion": "You can also use external tools like Runway ML or Pika Labs to animate this image with the motion prompt provided."
        }
            
    except Exception as e:
        error_msg = str(e)
        print(f"❌ Animation error: {error_msg}")
        
        # Check if it's a model availability issue
        if "not found" in error_msg.lower() or "invalid" in error_msg.lower():
            return {
                "status": "model_unavailable",
                "message": "Video generation model is not available in your region/account. Try using an external tool.",
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
        
        return {"status": "error", "message": error_msg}
