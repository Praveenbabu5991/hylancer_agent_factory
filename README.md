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

## Prerequisites

- Python 3.10+
- Google API Key (for Gemini)

## Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/Praveenbabu5991/hylancer_agent_factory.git
   cd hylancer_agent_factory
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
GOOGLE_API_KEY=your_google_api_key_here
DEFAULT_MODEL=gemini-2.5-flash
```

## Running the Application

```bash
# Using Python directly
PORT=8080 python -m app.fast_api_app

# Or using Make
make run
```

Then open http://localhost:8080 in your browser.

## Usage

1. **Brand Setup** - Configure your brand (name, logo, colors, reference images)
2. **Choose Mode** - Single Post or Campaign
3. **Get Ideas** - AI suggests relevant content ideas
4. **Generate** - Create professional visuals with your brand identity
5. **Animate** - Optionally convert to video/Reels
6. **Caption** - Get engaging captions and hashtags

## Project Structure

```
content-studio-agent/
├── app/
│   ├── agent.py          # Multi-agent definitions & orchestrator
│   └── fast_api_app.py   # FastAPI server
├── tools/
│   ├── calendar.py       # Calendar & events tools
│   ├── content.py        # Caption & hashtag tools
│   ├── image_gen.py      # Image generation & animation
│   ├── instagram.py      # Profile scraping tools
│   └── web_search.py     # Web search & trends
├── memory/
│   └── store.py          # Session memory management
├── static/
│   ├── css/style.css     # UI styles
│   ├── js/app.js         # Frontend JavaScript
│   └── presets/          # Brand presets & assets
├── templates/
│   └── index.html        # Main UI template
├── requirements.txt
├── pyproject.toml
└── README.md
```

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                 ContentStudioManager                         │
│                    (Orchestrator)                            │
│  • Collects brand info                                       │
│  • Routes to appropriate agent                               │
│  • Passes context during handoffs                            │
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

## License

MIT

## Contributing

Pull requests are welcome! For major changes, please open an issue first.
