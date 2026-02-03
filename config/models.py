"""
Multi-provider model registry with environment-based configuration.

Supports per-agent model configuration via environment variables.
This allows different agents to use different models based on their
capabilities and requirements.

Environment Variables:
    DEFAULT_MODEL: Default model for agents without specific config
    ORCHESTRATOR_MODEL: Model for root orchestrator
    IDEA_MODEL: Model for idea recommendation agent
    WRITER_MODEL: Model for writer/brief agent
    IMAGE_MODEL: Model for image generation
    EDIT_MODEL: Model for edit/regeneration
    CAMPAIGN_MODEL: Model for campaign planning
    CAPTION_MODEL: Model for caption writing
    VIDEO_MODEL: Model for video generation
"""

import os
from enum import Enum
from dataclasses import dataclass
from typing import Optional, Dict, List
from dotenv import load_dotenv

load_dotenv()


class ModelProvider(Enum):
    """Supported LLM providers."""
    GOOGLE = "google"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    VERTEXAI = "vertexai"


class ModelCapability(Enum):
    """Model capabilities for matching agents to models."""
    TEXT = "text"
    IMAGE_GENERATION = "image_generation"
    IMAGE_UNDERSTANDING = "image_understanding"
    VIDEO_GENERATION = "video_generation"
    CODE = "code"
    REASONING = "reasoning"


@dataclass
class ModelConfig:
    """Configuration for a specific model."""
    model_id: str
    provider: ModelProvider
    capabilities: List[ModelCapability]
    max_tokens: int = 8192
    supports_streaming: bool = True
    cost_tier: str = "standard"  # "free" | "standard" | "premium"
    description: str = ""


# Model definitions registry
MODELS: Dict[str, ModelConfig] = {
    # Google Gemini models
    "gemini-2.5-flash": ModelConfig(
        model_id="gemini-2.5-flash",
        provider=ModelProvider.GOOGLE,
        capabilities=[ModelCapability.TEXT, ModelCapability.IMAGE_UNDERSTANDING, ModelCapability.REASONING],
        cost_tier="standard",
        description="Fast, versatile model for general tasks",
    ),
    "gemini-2.5-pro": ModelConfig(
        model_id="gemini-2.5-pro",
        provider=ModelProvider.GOOGLE,
        capabilities=[ModelCapability.TEXT, ModelCapability.IMAGE_UNDERSTANDING, ModelCapability.REASONING, ModelCapability.CODE],
        cost_tier="premium",
        description="Advanced model for complex reasoning",
    ),
    "gemini-2.0-flash-exp": ModelConfig(
        model_id="gemini-2.0-flash-exp",
        provider=ModelProvider.GOOGLE,
        capabilities=[ModelCapability.TEXT, ModelCapability.IMAGE_GENERATION, ModelCapability.IMAGE_UNDERSTANDING],
        cost_tier="standard",
        description="Experimental model with image generation",
    ),
    "gemini-3-pro-image-preview": ModelConfig(
        model_id="gemini-3-pro-image-preview",
        provider=ModelProvider.GOOGLE,
        capabilities=[ModelCapability.TEXT, ModelCapability.IMAGE_GENERATION, ModelCapability.IMAGE_UNDERSTANDING],
        cost_tier="premium",
        description="Latest image generation model",
    ),
    "veo-2.0-generate-001": ModelConfig(
        model_id="veo-2.0-generate-001",
        provider=ModelProvider.GOOGLE,
        capabilities=[ModelCapability.VIDEO_GENERATION],
        cost_tier="premium",
        description="Video generation model",
    ),

    # OpenAI models (for future multi-provider support)
    "gpt-4o": ModelConfig(
        model_id="gpt-4o",
        provider=ModelProvider.OPENAI,
        capabilities=[ModelCapability.TEXT, ModelCapability.IMAGE_UNDERSTANDING, ModelCapability.REASONING, ModelCapability.CODE],
        cost_tier="premium",
        description="OpenAI's most capable model",
    ),
    "gpt-4o-mini": ModelConfig(
        model_id="gpt-4o-mini",
        provider=ModelProvider.OPENAI,
        capabilities=[ModelCapability.TEXT, ModelCapability.IMAGE_UNDERSTANDING],
        cost_tier="standard",
        description="Fast, cost-effective OpenAI model",
    ),
    "dall-e-3": ModelConfig(
        model_id="dall-e-3",
        provider=ModelProvider.OPENAI,
        capabilities=[ModelCapability.IMAGE_GENERATION],
        cost_tier="premium",
        description="OpenAI image generation",
    ),

    # Anthropic models (for future multi-provider support)
    "claude-sonnet-4-20250514": ModelConfig(
        model_id="claude-sonnet-4-20250514",
        provider=ModelProvider.ANTHROPIC,
        capabilities=[ModelCapability.TEXT, ModelCapability.IMAGE_UNDERSTANDING, ModelCapability.REASONING, ModelCapability.CODE],
        cost_tier="premium",
        description="Anthropic Claude Sonnet",
    ),
}


# Default models per agent type
DEFAULT_AGENT_MODELS = {
    "orchestrator": "gemini-2.5-flash",
    "idea": "gemini-2.5-flash",
    "writer": "gemini-2.5-flash",
    "image": "gemini-2.0-flash-exp",
    "edit": "gemini-2.0-flash-exp",
    "campaign": "gemini-2.5-flash",
    "caption": "gemini-2.5-flash",
    "video": "veo-2.0-generate-001",
}


def get_agent_model(agent_name: str) -> str:
    """
    Get configured model for an agent.

    Checks for agent-specific environment variable first,
    then falls back to default for that agent type,
    then to global default.

    Args:
        agent_name: Name of the agent (e.g., "orchestrator", "idea", "writer")

    Returns:
        Model ID string
    """
    # Check for agent-specific environment variable
    env_key = f"{agent_name.upper()}_MODEL"
    env_model = os.getenv(env_key)
    if env_model:
        return env_model

    # Check for default for this agent type
    default_for_agent = DEFAULT_AGENT_MODELS.get(agent_name.lower())
    if default_for_agent:
        return default_for_agent

    # Fall back to global default
    return os.getenv("DEFAULT_MODEL", "gemini-2.5-flash")


def get_model_config(model_id: str) -> Optional[ModelConfig]:
    """Get configuration for a model."""
    return MODELS.get(model_id)


def get_models_with_capability(capability: ModelCapability) -> List[str]:
    """Get all models that have a specific capability."""
    return [
        model_id
        for model_id, config in MODELS.items()
        if capability in config.capabilities
    ]


def get_provider_api_key(provider: ModelProvider) -> Optional[str]:
    """Get API key for a provider."""
    key_map = {
        ModelProvider.GOOGLE: os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY"),
        ModelProvider.OPENAI: os.getenv("OPENAI_API_KEY"),
        ModelProvider.ANTHROPIC: os.getenv("ANTHROPIC_API_KEY"),
        ModelProvider.VERTEXAI: os.getenv("GOOGLE_API_KEY"),
    }
    return key_map.get(provider)


# =============================================================================
# Convenience Functions for Common Agent Types
# =============================================================================

def get_orchestrator_model() -> str:
    """Get model for orchestrator agent."""
    return get_agent_model("orchestrator")


def get_idea_model() -> str:
    """Get model for idea recommendation agent."""
    return get_agent_model("idea")


def get_writer_model() -> str:
    """Get model for writer/brief agent."""
    return get_agent_model("writer")


def get_image_model() -> str:
    """Get model for image generation."""
    return get_agent_model("image")


def get_edit_model() -> str:
    """Get model for edit/regeneration agent."""
    return get_agent_model("edit")


def get_campaign_model() -> str:
    """Get model for campaign planning agent."""
    return get_agent_model("campaign")


def get_caption_model() -> str:
    """Get model for caption writing."""
    return get_agent_model("caption")


def get_video_model() -> str:
    """Get model for video generation."""
    return get_agent_model("video")


# =============================================================================
# Validation
# =============================================================================

def validate_model_for_agent(agent_name: str, required_capabilities: List[ModelCapability]) -> bool:
    """
    Validate that the configured model for an agent has required capabilities.

    Args:
        agent_name: Name of the agent
        required_capabilities: List of required capabilities

    Returns:
        True if model has all required capabilities
    """
    model_id = get_agent_model(agent_name)
    config = get_model_config(model_id)

    if not config:
        # Unknown model, assume it works
        return True

    for cap in required_capabilities:
        if cap not in config.capabilities:
            return False

    return True


def print_model_configuration():
    """Print current model configuration for debugging."""
    print("\n=== Model Configuration ===")
    for agent_name in DEFAULT_AGENT_MODELS.keys():
        model = get_agent_model(agent_name)
        config = get_model_config(model)
        provider = config.provider.value if config else "unknown"
        print(f"  {agent_name.upper()}: {model} ({provider})")
    print("===========================\n")
