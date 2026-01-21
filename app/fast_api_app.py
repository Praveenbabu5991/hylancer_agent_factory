"""
Content Studio Agent - Custom FastAPI Server

Provides a custom web interface with:
- Split-screen UI (chat left, generations right)
- File upload for logos
- Streaming chat responses
- Image serving for generated content
"""

import os
import uuid
import json
import asyncio
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, UploadFile, File, Form, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.requests import Request
from pydantic import BaseModel
from dotenv import load_dotenv

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

# Load environment
load_dotenv()

# Import our agent
from app.agent import root_agent

# Import tools for direct use
from tools.image_gen import extract_brand_colors

# Base paths
BASE_DIR = Path(__file__).parent.parent
UPLOAD_DIR = BASE_DIR / "uploads"
GENERATED_DIR = BASE_DIR / "generated"
STATIC_DIR = BASE_DIR / "static"
TEMPLATES_DIR = BASE_DIR / "templates"

# Ensure directories exist
UPLOAD_DIR.mkdir(exist_ok=True)
GENERATED_DIR.mkdir(exist_ok=True)

# Initialize FastAPI
app = FastAPI(
    title="Content Studio Agent",
    description="Multi-agent social media content creation platform",
    version="0.1.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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


# Request/Response models
class ChatRequest(BaseModel):
    message: str
    user_id: Optional[str] = "default_user"
    session_id: Optional[str] = None
    attachments: Optional[list[dict]] = None  # [{type: "logo", path: "...", colors: {...}}]


class ChatResponse(BaseModel):
    response: str
    session_id: str
    user_id: str
    generated_images: Optional[list[dict]] = None


# Active WebSocket connections
class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, session_id: str):
        await websocket.accept()
        self.active_connections[session_id] = websocket

    def disconnect(self, session_id: str):
        if session_id in self.active_connections:
            del self.active_connections[session_id]

    async def send_message(self, session_id: str, message: dict):
        if session_id in self.active_connections:
            await self.active_connections[session_id].send_json(message)


manager = ConnectionManager()


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
    return {"status": "ok", "agent": "Content Studio Manager"}


@app.post("/upload-logo")
async def upload_logo(file: UploadFile = File(...)):
    """
    Upload a logo file and extract brand colors.
    
    Returns:
        - filename: Saved filename
        - colors: Extracted brand colors
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")
    
    # Validate file type
    allowed_types = {"image/png", "image/jpeg", "image/jpg", "image/gif", "image/webp"}
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="Invalid file type. Use PNG, JPEG, GIF, or WebP.")
    
    # Generate unique filename
    ext = Path(file.filename).suffix
    unique_filename = f"{uuid.uuid4()}{ext}"
    filepath = UPLOAD_DIR / unique_filename
    
    # Save file
    content = await file.read()
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
    
    Returns:
        - filename: Saved filename
        - path: URL path to access the image
        - full_path: Full filesystem path for the agent to use
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")
    
    # Validate file type
    allowed_types = {"image/png", "image/jpeg", "image/jpg", "image/gif", "image/webp"}
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="Invalid file type. Use PNG, JPEG, GIF, or WebP.")
    
    # Generate unique filename with 'ref_' prefix
    ext = Path(file.filename).suffix
    unique_filename = f"ref_{uuid.uuid4()}{ext}"
    filepath = UPLOAD_DIR / unique_filename
    
    # Save file
    content = await file.read()
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
    # Parse response for image paths
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
    logo_full_path = None
    reference_image_paths = []
    
    if request.attachments:
        attachment_context = "\n\n[BRAND ASSETS PROVIDED - USE THESE FOR IMAGE GENERATION:]"
        for att in request.attachments:
            if att.get("type") == "logo":
                attachment_context += f"\n📷 LOGO_PATH: {att.get('full_path', att.get('path'))}"
                logo_full_path = att.get('full_path')
                if att.get("colors"):
                    colors = att["colors"]
                    attachment_context += f"\n🎨 BRAND_COLORS: {colors.get('dominant')}"
                    if colors.get('palette'):
                        attachment_context += f", {','.join(colors.get('palette', []))}"
            elif att.get("type") == "reference_images":
                ref_paths = att.get("paths", [])
                if ref_paths:
                    reference_image_paths = ref_paths
                    attachment_context += f"\n🖼️ REFERENCE_IMAGES: {','.join(ref_paths)}"
                    attachment_context += f"\n   (IMPORTANT: Pass these exact paths to reference_images parameter in generate_post_image)"
                    print(f"📸 Reference images being sent to agent: {ref_paths}")
        message_text = message_text + attachment_context
        print(f"📝 Full message to agent:\n{message_text[:500]}...")
    
    user_message = types.Content(
        role="user",
        parts=[types.Part(text=message_text)]
    )
    
    async def generate():
        # Send session ID first
        yield f"data: {json.dumps({'type': 'session', 'session_id': session_id})}\n\n"
        
        async for event in runner.run_async(
            user_id=request.user_id,
            session_id=session_id,
            new_message=user_message
        ):
            if event.content and event.content.parts:
                for part in event.content.parts:
                    if hasattr(part, 'text') and part.text:
                        yield f"data: {json.dumps({'type': 'text', 'content': part.text})}\n\n"
        
        yield f"data: {json.dumps({'type': 'done'})}\n\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )


@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """
    WebSocket endpoint for real-time bidirectional chat.
    """
    await manager.connect(websocket, session_id)
    user_id = "default_user"
    
    # Ensure session exists
    session = await session_service.get_session(
        app_name="content_studio",
        user_id=user_id,
        session_id=session_id
    )
    if not session:
        await session_service.create_session(
            app_name="content_studio",
            user_id=user_id,
            session_id=session_id
        )
    
    try:
        while True:
            data = await websocket.receive_json()
            message = data.get("message", "")
            attachments = data.get("attachments", [])
            
            # Build message with attachments
            message_text = message
            if attachments:
                attachment_context = "\n\n[Attachments:]"
                for att in attachments:
                    if att.get("type") == "logo":
                        attachment_context += f"\n- Logo: {att.get('path')}"
                        if att.get("colors"):
                            attachment_context += f" (Colors: {att['colors'].get('dominant')})"
                message_text += attachment_context
            
            user_message = types.Content(
                role="user",
                parts=[types.Part(text=message_text)]
            )
            
            # Stream response
            async for event in runner.run_async(
                user_id=user_id,
                session_id=session_id,
                new_message=user_message
            ):
                if event.content and event.content.parts:
                    for part in event.content.parts:
                        if hasattr(part, 'text') and part.text:
                            await manager.send_message(session_id, {
                                "type": "text",
                                "content": part.text
                            })
            
            # Signal completion
            await manager.send_message(session_id, {"type": "done"})
            
    except WebSocketDisconnect:
        manager.disconnect(session_id)


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


@app.get("/sessions/{user_id}")
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
async def list_generated_images():
    """List all generated images."""
    images = []
    for img_path in GENERATED_DIR.glob("*.png"):
        images.append({
            "filename": img_path.name,
            "url": f"/generated/{img_path.name}",
            "created": img_path.stat().st_mtime
        })
    # Sort by creation time, newest first
    images.sort(key=lambda x: x["created"], reverse=True)
    return {"images": images}


class UrlScrapeRequest(BaseModel):
    username: str  # Can be Instagram username or any URL
    limit: int = 6
    url_type: str = "auto"  # auto, instagram, pinterest, website


@app.post("/scrape-instagram")
async def scrape_url_images(request: UrlScrapeRequest):
    """
    Scrape images from various sources for style reference.
    
    Supports:
    - Instagram profiles (requires manual upload due to API restrictions)
    - Pinterest boards
    - General websites
    
    Returns:
        - images: List of image URLs and paths
    """
    import httpx
    import re
    from urllib.parse import urlparse
    
    url_or_username = request.username.strip()
    
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
        # Use domain as identifier
        try:
            parsed = urlparse(url_or_username if url_or_username.startswith("http") else f"https://{url_or_username}")
            identifier = parsed.netloc.replace(".", "_") or "website"
        except:
            identifier = "scraped"
    
    # Create a folder for scraped images
    scraped_dir = UPLOAD_DIR / "scraped" / identifier
    scraped_dir.mkdir(parents=True, exist_ok=True)
    
    images = []
    
    async with httpx.AsyncClient(
        headers={
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Upgrade-Insecure-Requests": "1",
        },
        follow_redirects=True,
        timeout=20.0
    ) as client:
        
        if url_type == "instagram":
            # Instagram has strict anti-scraping measures
            # Return a helpful message instead of failing silently
            print(f"Instagram URL detected: {identifier}")
            
            # Try multiple approaches
            scraped = False
            
            # Approach 1: Try the web API (usually blocked)
            try:
                response = await client.get(
                    f"https://www.instagram.com/{identifier}/?__a=1&__d=dis",
                    headers={"X-IG-App-ID": "936619743392459"}
                )
                if response.status_code == 200:
                    try:
                        data = response.json()
                        if "graphql" in data:
                            user = data.get("graphql", {}).get("user", {})
                            media = user.get("edge_owner_to_timeline_media", {}).get("edges", [])
                            for i, edge in enumerate(media[:request.limit]):
                                node = edge.get("node", {})
                                display_url = node.get("display_url")
                                if display_url:
                                    try:
                                        img_response = await client.get(display_url)
                                        if img_response.status_code == 200:
                                            filename = f"ig_{identifier}_{i}.jpg"
                                            filepath = scraped_dir / filename
                                            with open(filepath, "wb") as f:
                                                f.write(img_response.content)
                                            images.append({
                                                "url": f"/uploads/scraped/{identifier}/{filename}",
                                                "full_path": str(filepath),
                                                "source": "instagram"
                                            })
                                            scraped = True
                                    except:
                                        continue
                    except:
                        pass
            except Exception as e:
                print(f"Instagram API approach failed: {e}")
            
            # Approach 2: Try scraping the HTML page for og:image
            if not scraped:
                try:
                    response = await client.get(f"https://www.instagram.com/{identifier}/")
                    if response.status_code == 200:
                        html = response.text
                        # Extract og:image meta tags
                        og_images = re.findall(r'<meta[^>]+property="og:image"[^>]+content="([^"]+)"', html)
                        for i, img_url in enumerate(og_images[:request.limit]):
                            try:
                                img_response = await client.get(img_url)
                                if img_response.status_code == 200 and len(img_response.content) > 5000:
                                    filename = f"ig_{identifier}_{i}.jpg"
                                    filepath = scraped_dir / filename
                                    with open(filepath, "wb") as f:
                                        f.write(img_response.content)
                                    images.append({
                                        "url": f"/uploads/scraped/{identifier}/{filename}",
                                        "full_path": str(filepath),
                                        "source": "instagram"
                                    })
                                    scraped = True
                            except:
                                continue
                except Exception as e:
                    print(f"Instagram HTML scraping failed: {e}")
            
            # If still no images, return helpful message
            if not images:
                return {
                    "success": False,
                    "identifier": identifier,
                    "url_type": "instagram",
                    "images": [],
                    "message": f"Instagram requires authentication to access @{identifier}'s posts. Please download images from their profile manually and upload them as Reference Images below."
                }
        
        elif url_type in ["pinterest", "website"]:
            # Generic website/Pinterest scraping - extract images from page
            try:
                target_url = url_or_username if url_or_username.startswith("http") else f"https://{url_or_username}"
                response = await client.get(target_url)
                
                if response.status_code == 200:
                    html = response.text
                    
                    # Extract image URLs from HTML
                    img_patterns = [
                        r'<img[^>]+src=["\']([^"\']+)["\']',
                        r'<meta[^>]+property="og:image"[^>]+content=["\']([^"\']+)["\']',
                        r'<meta[^>]+name="twitter:image"[^>]+content=["\']([^"\']+)["\']',
                        r'background-image:\s*url\(["\']?([^"\')\s]+)["\']?\)',
                        r'srcset=["\']([^\s"\']+)',
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
                            
                            # Filter for actual image URLs
                            if any(ext in match.lower() for ext in ['.jpg', '.jpeg', '.png', '.webp', '.gif']):
                                # Skip tiny images (usually icons)
                                if not any(skip in match.lower() for skip in ['icon', 'favicon', '16x16', '32x32', '1x1', 'pixel', 'tracking']):
                                    found_urls.add(match)
                    
                    # Download images
                    for i, img_url in enumerate(list(found_urls)[:request.limit]):
                        try:
                            img_response = await client.get(img_url, timeout=10.0)
                            if img_response.status_code == 200 and len(img_response.content) > 10000:  # Skip tiny images
                                ext = ".jpg"
                                for e in ['.png', '.webp', '.gif']:
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
                        except Exception as e:
                            print(f"Error downloading image from {img_url}: {e}")
                            continue
                            
            except Exception as e:
                print(f"Website scraping error: {e}")
    
    if images:
        return {
            "success": True,
            "identifier": identifier,
            "url_type": url_type,
            "images": images,
            "message": f"Successfully scraped {len(images)} images for style reference"
        }
    
    return {
        "success": False,
        "identifier": identifier,
        "url_type": url_type,
        "images": [],
        "message": f"Could not scrape images from this URL. Please upload reference images manually using the 'Reference Images' section below."
    }


@app.get("/preset-paths")
async def get_preset_paths():
    """Get full filesystem paths for preset logos and reference images."""
    presets_dir = STATIC_DIR / "presets"
    presets = {}
    
    # Define preset mappings - logo and reference images folder
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
        
        # Logo path
        if config["logo"]:
            logo_path = presets_dir / config["logo"]
            if logo_path.exists():
                preset_data["logo_url"] = f"/static/presets/{config['logo']}"
                preset_data["logo_full_path"] = str(logo_path)
        
        # Reference images
        refs_folder = presets_dir / config["refs_folder"]
        if refs_folder.exists() and refs_folder.is_dir():
            ref_files = []
            for ext in ['*.png', '*.jpg', '*.jpeg', '*.webp']:
                ref_files.extend(refs_folder.glob(ext))
            
            if ref_files:
                preset_data["reference_images"] = []
                for ref_file in sorted(ref_files)[:8]:  # Max 8 reference images
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
    
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 5000))
    debug = os.getenv("DEBUG", "true").lower() == "true"
    
    print(f"\n🎨 Content Studio Agent starting...")
    print(f"📍 Custom UI: http://localhost:{port}")
    print(f"📍 API Docs: http://localhost:{port}/docs")
    print(f"\n💡 Tip: Run 'adk web' for ADK's built-in UI\n")
    
    uvicorn.run(
        "app.fast_api_app:app",
        host=host,
        port=port,
        reload=debug
    )
