# Content Studio Agent 🎨

A **multi-agent social media content creation platform** powered by Google ADK (Agent Development Kit) and Gemini.

## Features

- 🤖 **6 Specialized AI Agents** working together:
  - **Content Agent** - Suggests post ideas based on calendar events & company context
  - **Poster Agent** - Creates stunning visual posts with brand integration
  - **Caption Agent** - Writes engaging captions & hashtags
  - **Edit Agent** - Modifies and improves existing images
  - **Animation Agent** - Transforms static images into Reels/videos
  - **Campaign Agent** - Plans multi-week content campaigns

- 🎯 **Smart Orchestration** - Root agent coordinates workflow with proper context handoffs
- 🎨 **Brand Integration** - Logo, colors, reference images, and tone consistency
- 📅 **Calendar-Aware** - Suggests content based on upcoming events and festivals
- 🖼️ **AI Image Generation** - Creates professional Instagram-ready visuals
- ✍️ **Caption Generation** - Short, crisp captions optimized for engagement
- 💾 **Persistent Storage** - SQLite-based session and memory management

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                 ContentStudioManager                         │
│                    (Orchestrator)                            │
│  • Manages workflow state                                    │
│  • Routes to appropriate agent                               │
│  • Maintains session context                                 │
└─────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
┌───────────────┐   ┌───────────────┐   ┌───────────────┐
│   Idea        │   │   Image       │   │   Campaign    │
│   Suggestion  │   │   Post        │   │   Planner     │
│   Agent       │   │   Agent       │   │   Agent       │
└───────────────┘   └───────────────┘   └───────────────┘
        │                     │                     │
        ▼                     ▼                     ▼
┌───────────────┐   ┌───────────────┐   ┌───────────────┐
│   Caption     │   │   Animation   │   │   Edit        │
│   Agent       │   │   Agent       │   │   Agent       │
└───────────────┘   └───────────────┘   └───────────────┘
```

## Project Structure

```
content-studio-agent/
├── agents/                    # Modular agent definitions
│   ├── root_agent.py         # Orchestrator agent
│   ├── idea_agent.py         # Content ideas
│   ├── image_agent.py        # Image generation
│   ├── caption_agent.py      # Caption writing
│   ├── edit_agent.py         # Image editing
│   ├── animation_agent.py    # Video creation
│   └── campaign_agent.py     # Campaign planning
├── prompts/                   # Agent prompts (concise & focused)
│   ├── root_agent.py
│   ├── idea_agent.py
│   ├── image_agent.py
│   └── ...
├── config/                    # Configuration management
│   └── settings.py           # Environment-based settings
├── memory/                    # Persistence layer
│   ├── store.py              # SQLite-backed memory store
│   └── state.py              # Workflow state management
├── tools/                     # Agent tools
│   ├── calendar.py           # Calendar & events (dynamic dates)
│   ├── content.py            # Caption & hashtag tools
│   ├── image_gen.py          # Image generation & animation
│   ├── instagram.py          # Profile tools (simulated for MVP)
│   └── web_search.py         # AI knowledge retrieval
├── app/
│   ├── agent.py              # Backward compatibility re-exports
│   └── fast_api_app.py       # FastAPI server (with security)
├── static/
│   ├── css/style.css         # UI styles
│   ├── js/app.js             # Frontend JavaScript
│   └── presets/              # Brand presets & assets
├── templates/
│   └── index.html            # Main UI template
├── data/                      # SQLite database storage
├── uploads/                   # User uploads
├── generated/                 # Generated content
├── requirements.txt
└── README.md
```

## Prerequisites

- Python 3.10+
- Google API Key (for Gemini)

## Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourrepo/content-studio-agent.git
   cd content-studio-agent
   ```

2. **Create virtual environment:**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables:**
   ```bash
   cp env.example .env
   # Edit .env and add your GOOGLE_API_KEY
   ```

## Environment Variables

Create a `.env` file with:

```env
# Required
GOOGLE_API_KEY=your_google_api_key_here

# Optional - Model Configuration
DEFAULT_MODEL=gemini-2.5-flash
IMAGE_MODEL=gemini-2.0-flash-exp
VIDEO_MODEL=veo-2.0-generate-001

# Optional - Server Configuration
PORT=5000
DEBUG=true
ALLOWED_ORIGINS=http://localhost:5000,http://127.0.0.1:5000

# Optional - File Upload Limits
MAX_UPLOAD_SIZE_MB=10
MAX_IMAGE_DIMENSION=4096

# Optional - Rate Limiting
RATE_LIMIT_REQUESTS=60
RATE_LIMIT_WINDOW=60

# Optional - Session Configuration
SESSION_TIMEOUT_HOURS=24
```

## Running the Application

```bash
# Using Python directly
PORT=5000 python -m app.fast_api_app

# Or using Make
make run
```

Then open http://localhost:5000 in your browser.

## Usage

1. **Brand Setup** - Configure your brand (name, logo, colors, reference images)
2. **Choose Mode** - Single Post or Campaign
3. **Get Ideas** - AI suggests relevant content ideas
4. **Generate** - Create professional visuals with your brand identity
5. **Animate** - Optionally convert to video/Reels
6. **Caption** - Get engaging captions and hashtags

## Key Improvements (v1.0)

### Prompt Engineering
- Reduced prompt sizes by ~70% (from 1500 to ~100 lines)
- Removed redundant instructions and conflicting guidance
- Clear, actionable instructions focused on specific tasks

### State Management
- Explicit workflow states instead of pattern matching
- SessionState tracking with proper transitions
- Persistent state across server restarts

### Reliability
- Retry with exponential backoff for API calls
- User-friendly error messages
- Rate limiting to prevent abuse

### Security
- CORS properly configured (no more wildcards)
- File upload validation (type, size, dimensions)
- Input sanitization

### Tools
- Renamed misleading "search_web" to "get_ai_knowledge"
- Clear documentation of simulated data (Instagram)
- Dynamic calendar dates (Easter, Thanksgiving, etc.)

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Main UI |
| `/health` | GET | Health check |
| `/chat` | POST | Send message (blocking) |
| `/chat/stream` | POST | Send message (SSE streaming) |
| `/upload-logo` | POST | Upload logo file |
| `/upload-reference` | POST | Upload reference image |
| `/sessions` | POST | Create new session |
| `/generated-images` | GET | List generated content |
| `/preset-paths` | GET | Get preset asset paths |

## License

MIT

## Contributing

Pull requests are welcome! For major changes, please open an issue first.

### Development Notes

- Agent prompts are in `prompts/` - keep them concise
- New tools should include error handling and retry logic
- State transitions are defined in `memory/state.py`
- All file uploads are validated in `app/fast_api_app.py`
