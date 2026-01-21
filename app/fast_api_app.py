"""
Content Studio Agent - FastAPI Server

Provides a secure web interface with:
- Split-screen UI (chat left, generations right)
- File upload with validation
- Streaming chat responses
- Session management with persistence
- Rate limiting
"""

import os
import uuid
import json
import asyncio
import time
from pathlib import Path
from typing import Optional
from datetime import datetime, timedelta
from collections import defaultdict
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.requests import Request
from starlette.middleware.base import BaseHTTPMiddleware
from pydantic import BaseModel, field_validator
from dotenv import load_dotenv
from PIL import Image
import io

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

# Load environment
load_dotenv()

# Import configuration
from config.settings import (
    HOST, PORT, DEBUG, ALLOWED_ORIGINS,
    UPLOAD_DIR, GENERATED_DIR, STATIC_DIR, TEMPLATES_DIR,
    MAX_UPLOAD_SIZE_BYTES, ALLOWED_IMAGE_TYPES, MAX_IMAGE_DIMENSION,
    RATE_LIMIT_REQUESTS, RATE_LIMIT_WINDOW,
    SESSION_TIMEOUT_HOURS,
)

# Import the root agent
from agents.root_agent import root_agent

# Import tools for direct use
from tools.image_gen import extract_brand_colors

# Import memory store
from memory.store import get_memory_store


# =============================================================================
# Rate Limiting Middleware
# =============================================================================

class RateLimitMiddleware(BaseHTTPMiddleware):
    """Simple in-memory rate limiting middleware."""
    
    # Paths to exclude from rate limiting (static files, images, etc.)
    EXCLUDED_PATHS = ['/static/', '/generated/', '/uploads/', '/favicon.ico', '/health']
    
    def __init__(self, app, requests_per_minute: int = 60):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.requests = defaultdict(list)
    
    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting for static files and health checks
        path = request.url.path
        if any(path.startswith(excluded) for excluded in self.EXCLUDED_PATHS):
            return await call_next(request)
        
        # Get client IP
        client_ip = request.client.host if request.client else "unknown"
        
        # Clean old requests
        current_time = time.time()
        window_start = current_time - 60
        self.requests[client_ip] = [t for t in self.requests[client_ip] if t > window_start]
        
        # Check rate limit
        if len(self.requests[client_ip]) >= self.requests_per_minute:
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={"detail": "Too many requests. Please wait a moment and try again."}
            )
        
        # Record request
        self.requests[client_ip].append(current_time)
        
        return await call_next(request)


# =============================================================================
# Initialize FastAPI
# =============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan handler for startup and shutdown events."""
    # Startup
    try:
        store = get_memory_store()
        deleted = store.cleanup_old_sessions(SESSION_TIMEOUT_HOURS)
        if deleted > 0:
            print(f"🧹 Cleaned up {deleted} old sessions")
    except Exception as e:
        print(f"⚠️ Session cleanup error: {e}")
    
    yield
    
    # Shutdown (cleanup if needed)
    print("👋 Content Studio Agent shutting down...")


app = FastAPI(
    title="Content Studio Agent",
    description="Multi-agent social media content creation platform",
    version="1.0.0",
    lifespan=lifespan
)

# Add rate limiting
app.add_middleware(RateLimitMiddleware, requests_per_minute=RATE_LIMIT_REQUESTS)

# CORS - Use configured origins instead of wildcard
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["Content-Type", "Authorization"],
)

# Static files and templates
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
app.mount("/generated", StaticFiles(directory=str(GENERATED_DIR)), name="generated")
app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

# ADK components
session_service = InMemorySessionService()
runner = Runner(
    agent=root_agent,
    app_name="content_studio",
    session_service=session_service,
)


# =============================================================================
# Request/Response Models with Validation
# =============================================================================

class ChatRequest(BaseModel):
    message: str
    user_id: Optional[str] = "default_user"
    session_id: Optional[str] = None
    attachments: Optional[list[dict]] = None
    last_generated_image: Optional[str] = None  # For edit context
    
    @field_validator('message')
    @classmethod
    def message_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError('Message cannot be empty')
        if len(v) > 10000:
            raise ValueError('Message too long (max 10000 characters)')
        return v.strip()


class ChatResponse(BaseModel):
    response: str
    session_id: str
    user_id: str
    generated_images: Optional[list[dict]] = None


# =============================================================================
# File Validation Helpers
# =============================================================================

def validate_image_file(file: UploadFile) -> None:
    """Validate uploaded image file."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")
    
    # Check content type
    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid file type. Allowed: PNG, JPEG, GIF, WebP"
        )
    
    # Check file extension
    ext = Path(file.filename).suffix.lower()
    if ext not in {'.png', '.jpg', '.jpeg', '.gif', '.webp'}:
        raise HTTPException(status_code=400, detail="Invalid file extension")


async def validate_image_content(content: bytes) -> None:
    """Validate image content and dimensions."""
    if len(content) > MAX_UPLOAD_SIZE_BYTES:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size: {MAX_UPLOAD_SIZE_BYTES // (1024*1024)}MB"
        )
    
    # Validate it's actually an image and check dimensions
    try:
        image = Image.open(io.BytesIO(content))
        width, height = image.size
        if width > MAX_IMAGE_DIMENSION or height > MAX_IMAGE_DIMENSION:
            raise HTTPException(
                status_code=400,
                detail=f"Image too large. Maximum dimension: {MAX_IMAGE_DIMENSION}px"
            )
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid or corrupted image file")


def sanitize_filename(filename: str) -> str:
    """Sanitize filename to prevent path traversal."""
    # Remove any path components
    filename = Path(filename).name
    # Remove any special characters except . and -
    import re
    filename = re.sub(r'[^\w\-.]', '_', filename)
    return filename


# =============================================================================
# Routes
# =============================================================================

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Serve the main UI."""
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "ok",
        "agent": "Content Studio Manager",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    }


@app.post("/upload-logo")
async def upload_logo(file: UploadFile = File(...)):
    """
    Upload a logo file and extract brand colors.
    
    Validates file type, size, and dimensions.
    """
    validate_image_file(file)
    
    content = await file.read()
    await validate_image_content(content)
    
    # Generate unique filename
    ext = Path(file.filename).suffix.lower()
    unique_filename = f"{uuid.uuid4()}{ext}"
    filepath = UPLOAD_DIR / unique_filename
    
    # Save file
    with open(filepath, "wb") as f:
        f.write(content)
    
    # Extract colors
    colors = extract_brand_colors(str(filepath))
    
    return {
        "success": True,
        "filename": unique_filename,
        "path": f"/uploads/{unique_filename}",
        "full_path": str(filepath),
        "colors": colors
    }


@app.post("/upload-reference")
async def upload_reference(file: UploadFile = File(...)):
    """
    Upload a reference image for style inspiration.
    
    Validates file type, size, and dimensions.
    """
    validate_image_file(file)
    
    content = await file.read()
    await validate_image_content(content)
    
    # Generate unique filename with 'ref_' prefix
    ext = Path(file.filename).suffix.lower()
    unique_filename = f"ref_{uuid.uuid4()}{ext}"
    filepath = UPLOAD_DIR / unique_filename
    
    # Save file
    with open(filepath, "wb") as f:
        f.write(content)
    
    return {
        "success": True,
        "filename": unique_filename,
        "path": f"/uploads/{unique_filename}",
        "full_path": str(filepath)
    }


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Send a message to the Content Studio Agent.
    
    Supports attachments like uploaded logos with extracted colors.
    """
    session_id = request.session_id or str(uuid.uuid4())
    
    # Get or create session
    session = await session_service.get_session(
        app_name="content_studio",
        user_id=request.user_id,
        session_id=session_id
    )
    
    if not session:
        session = await session_service.create_session(
            app_name="content_studio",
            user_id=request.user_id,
            session_id=session_id
        )
    
    # Build message with attachment context if provided
    message_text = request.message
    if request.attachments:
        attachment_context = "\n\n[Attachments provided by user:]"
        for att in request.attachments:
            if att.get("type") == "logo":
                attachment_context += f"\n- Logo uploaded: {att.get('path')}"
                if att.get("colors"):
                    colors = att["colors"]
                    attachment_context += f"\n  Brand colors extracted: Dominant={colors.get('dominant')}, Palette={colors.get('palette')}"
        message_text = message_text + attachment_context
    
    # Create user message
    user_message = types.Content(
        role="user",
        parts=[types.Part(text=message_text)]
    )
    
    # Run agent
    response_text = ""
    generated_images = []
    
    async for event in runner.run_async(
        user_id=request.user_id,
        session_id=session_id,
        new_message=user_message
    ):
        if event.is_final_response() and event.content and event.content.parts:
            for part in event.content.parts:
                if hasattr(part, 'text') and part.text:
                    response_text += part.text
    
    # Check for generated images in response
    import re
    image_pattern = r'/generated/[^\s\)\"\']+\.png'
    found_images = re.findall(image_pattern, response_text)
    for img_path in found_images:
        generated_images.append({
            "url": img_path,
            "filename": Path(img_path).name
        })
    
    return ChatResponse(
        response=response_text,
        session_id=session_id,
        user_id=request.user_id,
        generated_images=generated_images if generated_images else None
    )


@app.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    """
    Stream chat response using Server-Sent Events.
    
    Great for real-time chat UI showing response as it generates.
    """
    session_id = request.session_id or str(uuid.uuid4())
    
    session = await session_service.get_session(
        app_name="content_studio",
        user_id=request.user_id,
        session_id=session_id
    )
    
    if not session:
        session = await session_service.create_session(
            app_name="content_studio",
            user_id=request.user_id,
            session_id=session_id
        )
    
    # Build message with explicit paths for the agent
    message_text = request.message
    
    # Add last generated image context for editing operations
    if request.last_generated_image:
        message_text = f"{message_text}\n\n[LAST GENERATED IMAGE: {request.last_generated_image}]"
    
    if request.attachments:
        attachment_context = "\n\n[BRAND ASSETS PROVIDED - USE THESE FOR IMAGE GENERATION:]"
        for att in request.attachments:
            if att.get("type") == "logo":
                attachment_context += f"\n📷 LOGO_PATH: {att.get('full_path', att.get('path'))}"
                if att.get("colors"):
                    colors = att["colors"]
                    attachment_context += f"\n🎨 BRAND_COLORS: {colors.get('dominant')}"
                    if colors.get('palette'):
                        attachment_context += f", {','.join(colors.get('palette', []))}"
            elif att.get("type") == "reference_images":
                ref_paths = att.get("paths", [])
                if ref_paths:
                    attachment_context += f"\n🖼️ REFERENCE_IMAGES: {','.join(ref_paths)}"
            elif att.get("type") == "company_overview":
                attachment_context += f"\n📋 COMPANY_OVERVIEW: {att.get('content', '')}"
        message_text = message_text + attachment_context
    
    user_message = types.Content(
        role="user",
        parts=[types.Part(text=message_text)]
    )
    
    async def generate():
        # Send session ID first
        yield f"data: {json.dumps({'type': 'session', 'session_id': session_id})}\n\n"
        
        try:
            async for event in runner.run_async(
                user_id=request.user_id,
                session_id=session_id,
                new_message=user_message
            ):
                if event.content and event.content.parts:
                    for part in event.content.parts:
                        if hasattr(part, 'text') and part.text:
                            yield f"data: {json.dumps({'type': 'text', 'content': part.text})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': 'An error occurred. Please try again.'})}\n\n"
        
        yield f"data: {json.dumps({'type': 'done'})}\n\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        }
    )


@app.post("/sessions")
async def create_session(user_id: str = "default_user"):
    """Create a new chat session."""
    session_id = str(uuid.uuid4())
    await session_service.create_session(
        app_name="content_studio",
        user_id=user_id,
        session_id=session_id
    )
    return {"session_id": session_id, "user_id": user_id}


@app.get("/sessions/{session_id}")
async def check_session(session_id: str):
    """Check if a session exists and is valid."""
    try:
        session = await session_service.get_session(
            app_name="content_studio",
            user_id="default_user",
            session_id=session_id
        )
        if session:
            return {"valid": True, "session_id": session_id}
        return JSONResponse(status_code=404, content={"valid": False, "error": "Session not found"})
    except Exception:
        return JSONResponse(status_code=404, content={"valid": False, "error": "Session not found"})


@app.get("/sessions/user/{user_id}")
async def list_sessions(user_id: str):
    """List all sessions for a user."""
    sessions = await session_service.list_sessions(
        app_name="content_studio",
        user_id=user_id
    )
    return {"sessions": [s.id for s in sessions] if sessions else []}


@app.delete("/sessions/{user_id}/{session_id}")
async def delete_session(user_id: str, session_id: str):
    """Delete a specific session."""
    await session_service.delete_session(
        app_name="content_studio",
        user_id=user_id,
        session_id=session_id
    )
    return {"status": "deleted", "session_id": session_id}


@app.get("/generated-images")
async def list_generated_images(limit: int = 20, offset: int = 0):
    """List generated images with pagination to avoid loading too many at once."""
    images = []
    for pattern in ['*.png', '*.jpg', '*.jpeg', '*.mp4']:
        for img_path in GENERATED_DIR.glob(pattern):
            images.append({
                "filename": img_path.name,
                "url": f"/generated/{img_path.name}",
                "created": img_path.stat().st_mtime,
                "type": "video" if img_path.suffix == ".mp4" else "image"
            })
    
    # Sort by creation time, newest first
    images.sort(key=lambda x: x["created"], reverse=True)
    
    # Apply pagination - default to 20 most recent images
    total = len(images)
    images = images[offset:offset + limit]
    
    return {
        "images": images,
        "total": total,
        "limit": limit,
        "offset": offset,
        "hasMore": offset + limit < total
    }


class UrlScrapeRequest(BaseModel):
    username: str
    limit: int = 6
    url_type: str = "auto"
    
    @field_validator('limit')
    @classmethod
    def limit_range(cls, v: int) -> int:
        if v < 1 or v > 20:
            raise ValueError('Limit must be between 1 and 20')
        return v


@app.post("/scrape-instagram")
async def scrape_url_images(request: UrlScrapeRequest):
    """
    Scrape images and brand info from various sources for style reference.
    
    NOTE: Instagram scraping is limited due to API restrictions.
    For best results, upload reference images manually.
    """
    import httpx
    import re
    from urllib.parse import urlparse
    from tools.web_scraper import scrape_brand_from_url
    
    url_or_username = request.username.strip()
    
    # Extract brand info from URL
    brand_info = scrape_brand_from_url(url_or_username)
    
    # Detect URL type
    url_type = request.url_type
    if url_type == "auto":
        if "instagram.com" in url_or_username or url_or_username.startswith("@"):
            url_type = "instagram"
        elif "pinterest.com" in url_or_username:
            url_type = "pinterest"
        else:
            url_type = "website"
    
    # Create identifier for folder
    if url_type == "instagram":
        from tools.instagram import extract_username
        identifier = extract_username(url_or_username)
    else:
        try:
            parsed = urlparse(url_or_username if url_or_username.startswith("http") else f"https://{url_or_username}")
            identifier = parsed.netloc.replace(".", "_") or "website"
        except:
            identifier = "scraped"
    
    # Sanitize identifier
    identifier = re.sub(r'[^\w\-]', '_', identifier)
    
    # Create folder for scraped images
    scraped_dir = UPLOAD_DIR / "scraped" / identifier
    scraped_dir.mkdir(parents=True, exist_ok=True)
    
    images = []
    
    # For Instagram, return a helpful message since scraping is restricted
    # But still provide brand info extracted from the profile
    if url_type == "instagram":
        return {
            "success": True,  # Brand info was extracted
            "identifier": identifier,
            "url_type": "instagram",
            "images": [],
            "brand_info": brand_info,
            "message": f"Instagram images require manual upload, but we've noted @{identifier} as your brand reference. Upload images from their profile as Reference Images."
        }
    
    # For websites, try to scrape images
    async with httpx.AsyncClient(
        headers={
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        },
        follow_redirects=True,
        timeout=15.0
    ) as client:
        try:
            target_url = url_or_username if url_or_username.startswith("http") else f"https://{url_or_username}"
            response = await client.get(target_url)
            
            if response.status_code == 200:
                html = response.text
                
                # Extract image URLs
                img_patterns = [
                    r'<img[^>]+src=["\']([^"\']+)["\']',
                    r'<meta[^>]+property="og:image"[^>]+content=["\']([^"\']+)["\']',
                ]
                
                found_urls = set()
                for pattern in img_patterns:
                    matches = re.findall(pattern, html, re.IGNORECASE)
                    for match in matches:
                        if match.startswith("//"):
                            match = "https:" + match
                        elif match.startswith("/"):
                            parsed = urlparse(target_url)
                            match = f"{parsed.scheme}://{parsed.netloc}{match}"
                        elif not match.startswith("http"):
                            continue
                        
                        if any(ext in match.lower() for ext in ['.jpg', '.jpeg', '.png', '.webp']):
                            if not any(skip in match.lower() for skip in ['icon', 'favicon', '1x1', 'pixel']):
                                found_urls.add(match)
                
                # Download images
                for i, img_url in enumerate(list(found_urls)[:request.limit]):
                    try:
                        img_response = await client.get(img_url, timeout=10.0)
                        if img_response.status_code == 200 and len(img_response.content) > 10000:
                            ext = ".jpg"
                            for e in ['.png', '.webp']:
                                if e in img_url.lower():
                                    ext = e
                                    break
                            
                            filename = f"web_{identifier}_{i}{ext}"
                            filepath = scraped_dir / filename
                            
                            with open(filepath, "wb") as f:
                                f.write(img_response.content)
                            
                            images.append({
                                "url": f"/uploads/scraped/{identifier}/{filename}",
                                "full_path": str(filepath),
                                "source": url_type
                            })
                    except Exception:
                        continue
                        
        except Exception as e:
            return {
                "success": False,
                "identifier": identifier,
                "url_type": url_type,
                "images": [],
                "message": "Could not fetch images from this URL. Please upload reference images manually."
            }
    
    if images:
        return {
            "success": True,
            "identifier": identifier,
            "url_type": url_type,
            "images": images,
            "brand_info": brand_info,
            "message": f"Successfully scraped {len(images)} images and brand info for style reference"
        }
    
    return {
        "success": True if brand_info.get("status") == "success" else False,
        "identifier": identifier,
        "url_type": url_type,
        "images": [],
        "brand_info": brand_info,
        "message": "Extracted brand info. No images found - please upload reference images manually."
    }


@app.get("/preset-paths")
async def get_preset_paths():
    """Get full filesystem paths for preset logos and reference images."""
    presets_dir = STATIC_DIR / "presets"
    presets = {}
    
    preset_config = {
        "socialbunkr": {
            "logo": "socialbunkr-logo.jpeg",
            "refs_folder": "socialbunkr-refs"
        },
        "hylancer": {
            "logo": "hylancer-logo.jpeg",
            "refs_folder": "hylancer-refs"
        },
        "technova": {
            "logo": None,
            "refs_folder": "technova-refs"
        }
    }
    
    for preset_id, config in preset_config.items():
        preset_data = {}
        
        if config["logo"]:
            logo_path = presets_dir / config["logo"]
            if logo_path.exists():
                preset_data["logo_url"] = f"/static/presets/{config['logo']}"
                preset_data["logo_full_path"] = str(logo_path)
        
        refs_folder = presets_dir / config["refs_folder"]
        if refs_folder.exists() and refs_folder.is_dir():
            ref_files = []
            for ext in ['*.png', '*.jpg', '*.jpeg', '*.webp']:
                ref_files.extend(refs_folder.glob(ext))
            
            if ref_files:
                preset_data["reference_images"] = []
                for ref_file in sorted(ref_files)[:8]:
                    preset_data["reference_images"].append({
                        "url": f"/static/presets/{config['refs_folder']}/{ref_file.name}",
                        "full_path": str(ref_file)
                    })
        
        if preset_data:
            presets[preset_id] = preset_data
    
    return {"presets": presets}




# =============================================================================
# Run Server
# =============================================================================

if __name__ == "__main__":
    import uvicorn
    
    print(f"\n🎨 Content Studio Agent starting...")
    print(f"📍 Custom UI: http://localhost:{PORT}")
    print(f"📍 API Docs: http://localhost:{PORT}/docs")
    print(f"\n💡 Tip: Run 'adk web' for ADK's built-in UI\n")
    
    uvicorn.run(
        "app.fast_api_app:app",
        host=HOST,
        port=PORT,
        reload=DEBUG
    )
