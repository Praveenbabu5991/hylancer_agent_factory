# Content Studio Agent

A multi-agent social media content creation platform powered by Google ADK with a custom chat-driven UI.

## Features

- **Image Post Generation**: Create stunning Instagram posts with AI-generated images
- **Caption & Hashtag Creation**: Generate engaging captions with trending hashtags
- **Campaign Planning**: Plan content calendars for weeks/months ahead
- **Image Editing**: Modify generated images based on feedback
- **Human-in-the-Loop**: Conversational workflow with approval steps

## Architecture

The platform uses an orchestrator agent that coordinates four specialized sub-agents:

1. **ImagePostAgent**: Generates Instagram images using logo, palette, and theme
2. **CaptionAgent**: Creates captions with hashtags using web search + calendar context
3. **EditPostAgent**: Modifies existing images based on user feedback
4. **CampaignPlannerAgent**: Plans content calendars for weeks/months

## Quick Start

### Prerequisites

- Python 3.10+
- Google/Gemini API Key

### Installation

1. Clone and enter the directory:
```bash
cd content-studio-agent
```

2. Create virtual environment and install:
```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

3. Set up environment variables:
```bash
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY
```

### Running the Application

**Option 1: Custom UI (Recommended)**
```bash
make dev
# or
python -m app.fast_api_app
```
Open http://localhost:5000 in your browser.

**Option 2: ADK Web UI (Development)**
```bash
make adk-web
# or
adk web
```
Open http://localhost:8000 in your browser.

## Usage

1. Start a conversation: "Create a post for my company"
2. Upload your logo and select brand colors
3. Describe the content theme
4. Review generated images
5. Request captions and hashtags
6. Make modifications as needed
7. Download your final posts

## Project Structure

```
content-studio-agent/
├── app/
│   ├── agent.py              # Orchestrator + sub-agents
│   └── fast_api_app.py       # Custom FastAPI server
├── tools/
│   ├── image_gen.py          # Image generation tool
│   ├── web_search.py         # Web search tool
│   ├── content.py            # Caption & hashtag tools
│   ├── calendar.py           # Festival/calendar tool
│   └── instagram.py          # Instagram scraper tool
├── memory/
│   └── store.py              # Session memory
├── static/                   # Frontend assets
├── templates/                # HTML templates
├── generated/                # Output images
└── uploads/                  # User uploads
```

## License

MIT License
# hylancer_agent_factory
