"""
Workflow State Management for Content Studio Agent.
Provides explicit state tracking instead of implicit pattern matching.
"""

from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Any
import json


class WorkflowState(Enum):
    """Explicit workflow states."""
    START = "start"
    BRAND_SETUP = "brand_setup"
    BRAND_COMPLETE = "brand_complete"
    MODE_SELECTION = "mode_selection"

    # General Image Flow (Quick path - no workflow)
    GENERAL_IMAGE_PROMPT = "general_image_prompt"
    GENERAL_IMAGE_GENERATING = "general_image_gen"

    # Single post flow
    POST_IDEA_SOURCE = "post_idea_source"  # Ask: user idea or suggestions?
    IDEA_REQUEST = "idea_request"
    IDEAS_SHOWN = "ideas_shown"
    IDEA_SELECTED = "idea_selected"
    POST_BRIEF_GENERATION = "post_brief_gen"
    BRIEF_SHOWN = "brief_shown"
    BRIEF_APPROVED = "brief_approved"
    POST_GENERATING = "post_generating"
    IMAGE_GENERATED = "image_generated"
    POST_EDIT_REQUESTED = "post_edit_req"
    POST_EDITING = "post_editing"
    ANIMATION_CHOICE = "animation_choice"
    ANIMATION_GENERATED = "animation_generated"
    CAPTION_REQUEST = "caption_request"
    CAPTION_GENERATED = "caption_generated"

    # Campaign flow
    CAMPAIGN_SETUP = "campaign_setup"
    CAMPAIGN_DETAILS_SET = "campaign_details_set"
    CAMPAIGN_IDEA_SOURCE = "campaign_idea_src"
    CAMPAIGN_IDEAS_GENERATED = "campaign_ideas"
    WEEK_PLANNING = "week_planning"
    WEEK_PRESENTED = "week_presented"
    WEEK_APPROVED = "week_approved"
    WEEK_GENERATING = "week_generating"
    WEEK_COMPLETE = "week_complete"
    CAMPAIGN_NEXT_WEEK = "campaign_next_week"
    CAMPAIGN_COMPLETE = "campaign_complete"

    # Carousel flow
    CAROUSEL_SETUP = "carousel_setup"
    CAROUSEL_GENERATING = "carousel_gen"
    CAROUSEL_COMPLETE = "carousel_complete"

    # Common
    COMPLETE = "complete"
    ERROR = "error"


@dataclass
class UserUploadedImage:
    """
    Single user-uploaded image for posts.

    Usage intent options (dropdown per image in UI):
    - "background" - Use as background image
    - "product_focus" - Show product prominently in foreground
    - "team_people" - Include people/team in composition
    - "style_reference" - Use for style inspiration only (not in final image)
    - "logo_badge" - Include as logo/badge overlay
    - "auto" - Let AI decide best placement
    """
    id: str = ""
    filename: str = ""
    path: str = ""
    url: str = ""
    uploaded_at: str = ""
    usage_intent: str = "auto"  # default: let AI decide
    extracted_colors: list = field(default_factory=list)
    dimensions: tuple = field(default_factory=tuple)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "filename": self.filename,
            "path": self.path,
            "url": self.url,
            "uploaded_at": self.uploaded_at,
            "usage_intent": self.usage_intent,
            "extracted_colors": self.extracted_colors,
            "dimensions": self.dimensions,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "UserUploadedImage":
        return cls(
            id=data.get("id", ""),
            filename=data.get("filename", ""),
            path=data.get("path", ""),
            url=data.get("url", ""),
            uploaded_at=data.get("uploaded_at", ""),
            usage_intent=data.get("usage_intent", "auto"),
            extracted_colors=data.get("extracted_colors", []),
            dimensions=tuple(data.get("dimensions", ())),
        )


# Valid usage intents for user images
USER_IMAGE_INTENTS = [
    "background",      # Use as background image
    "product_focus",   # Show product prominently
    "team_people",     # Include people/team in composition
    "style_reference", # Style inspiration only (not in final)
    "logo_badge",      # Include as logo/badge overlay
    "auto",            # Let AI decide
]


@dataclass
class BrandContext:
    """Brand information for the session."""
    name: str = ""
    industry: str = ""
    overview: str = ""
    tone: str = "creative"
    logo_path: Optional[str] = None
    colors: list = field(default_factory=list)
    reference_images: list = field(default_factory=list)
    user_images: list = field(default_factory=list)  # List of UserUploadedImage dicts

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "industry": self.industry,
            "overview": self.overview,
            "tone": self.tone,
            "logo_path": self.logo_path,
            "colors": self.colors,
            "reference_images": self.reference_images,
            "user_images": [
                img.to_dict() if isinstance(img, UserUploadedImage) else img
                for img in self.user_images
            ],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "BrandContext":
        user_images_data = data.get("user_images", [])
        user_images = [
            UserUploadedImage.from_dict(img) if isinstance(img, dict) else img
            for img in user_images_data
        ]
        return cls(
            name=data.get("name", ""),
            industry=data.get("industry", ""),
            overview=data.get("overview", ""),
            tone=data.get("tone", "creative"),
            logo_path=data.get("logo_path"),
            colors=data.get("colors", []),
            reference_images=data.get("reference_images", []),
            user_images=user_images,
        )

    def is_complete(self) -> bool:
        """Check if basic brand info is set."""
        return bool(self.name)

    def get_images_for_generation(self) -> list:
        """Get images intended for use in post generation (not style reference)."""
        return [
            img for img in self.user_images
            if isinstance(img, UserUploadedImage) and img.usage_intent != "style_reference"
        ]

    def get_style_reference_images(self) -> list:
        """Get images for style reference only."""
        style_refs = [
            img for img in self.user_images
            if isinstance(img, UserUploadedImage) and img.usage_intent == "style_reference"
        ]
        # Also include the standard reference_images
        return style_refs + [{"path": p} for p in self.reference_images]

    def get_user_images_by_intent(self, intent: str) -> list:
        """Get user images filtered by usage intent."""
        return [
            img for img in self.user_images
            if isinstance(img, UserUploadedImage) and img.usage_intent == intent
        ]


@dataclass
class PostContext:
    """Context for current post being created."""
    theme: Optional[str] = None
    selected_idea: Optional[dict] = None
    visual_brief: Optional[dict] = None
    image_path: Optional[str] = None
    animation_style: Optional[str] = None
    video_path: Optional[str] = None
    caption: Optional[str] = None
    hashtags: list = field(default_factory=list)
    
    def to_dict(self) -> dict:
        return {
            "theme": self.theme,
            "selected_idea": self.selected_idea,
            "visual_brief": self.visual_brief,
            "image_path": self.image_path,
            "animation_style": self.animation_style,
            "video_path": self.video_path,
            "caption": self.caption,
            "hashtags": self.hashtags,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "PostContext":
        return cls(**data)
    
    def reset(self):
        """Reset for new post."""
        self.theme = None
        self.selected_idea = None
        self.visual_brief = None
        self.image_path = None
        self.animation_style = None
        self.video_path = None
        self.caption = None
        self.hashtags = []


@dataclass
class CampaignContext:
    """Context for campaign planning."""
    month: Optional[str] = None
    posts_per_week: int = 2
    total_weeks: int = 4
    current_week: int = 1
    completed_weeks: list = field(default_factory=list)
    posts_generated: list = field(default_factory=list)
    
    def to_dict(self) -> dict:
        return {
            "month": self.month,
            "posts_per_week": self.posts_per_week,
            "total_weeks": self.total_weeks,
            "current_week": self.current_week,
            "completed_weeks": self.completed_weeks,
            "posts_generated": self.posts_generated,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "CampaignContext":
        return cls(**data)
    
    def reset(self):
        """Reset for new campaign."""
        self.month = None
        self.posts_per_week = 2
        self.total_weeks = 4
        self.current_week = 1
        self.completed_weeks = []
        self.posts_generated = []


@dataclass
class SessionState:
    """Complete session state."""
    session_id: str
    user_id: str
    workflow_state: WorkflowState = WorkflowState.START
    mode: Optional[str] = None  # "single" or "campaign"
    brand: BrandContext = field(default_factory=BrandContext)
    post: PostContext = field(default_factory=PostContext)
    campaign: CampaignContext = field(default_factory=CampaignContext)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> dict:
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "workflow_state": self.workflow_state.value,
            "mode": self.mode,
            "brand": self.brand.to_dict(),
            "post": self.post.to_dict(),
            "campaign": self.campaign.to_dict(),
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "SessionState":
        return cls(
            session_id=data["session_id"],
            user_id=data["user_id"],
            workflow_state=WorkflowState(data["workflow_state"]),
            mode=data.get("mode"),
            brand=BrandContext.from_dict(data.get("brand", {})),
            post=PostContext.from_dict(data.get("post", {})),
            campaign=CampaignContext.from_dict(data.get("campaign", {})),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
        )
    
    def transition(self, new_state: WorkflowState) -> None:
        """Transition to a new workflow state."""
        self.workflow_state = new_state
        self.updated_at = datetime.now()
    
    def get_context_summary(self) -> str:
        """Get a summary for the agent."""
        parts = [f"State: {self.workflow_state.value}"]
        
        if self.brand.name:
            parts.append(f"Brand: {self.brand.name}")
        if self.mode:
            parts.append(f"Mode: {self.mode}")
        if self.post.theme:
            parts.append(f"Theme: {self.post.theme}")
        if self.post.image_path:
            parts.append(f"Image: {self.post.image_path}")
        if self.campaign.month:
            parts.append(f"Campaign: {self.campaign.month}, Week {self.campaign.current_week}/{self.campaign.total_weeks}")
        
        return " | ".join(parts)


class StateTransitions:
    """Valid state transitions for the workflow."""

    VALID_TRANSITIONS = {
        WorkflowState.START: [WorkflowState.BRAND_SETUP],
        WorkflowState.BRAND_SETUP: [WorkflowState.BRAND_COMPLETE, WorkflowState.MODE_SELECTION],
        WorkflowState.BRAND_COMPLETE: [WorkflowState.MODE_SELECTION],
        WorkflowState.MODE_SELECTION: [
            WorkflowState.POST_IDEA_SOURCE,       # Single Post
            WorkflowState.GENERAL_IMAGE_PROMPT,   # General Image (quick path)
            WorkflowState.CAMPAIGN_SETUP,         # Campaign
            WorkflowState.CAROUSEL_SETUP,         # Carousel
            WorkflowState.IDEA_REQUEST,           # Legacy support
        ],

        # General Image Flow (Quick path)
        WorkflowState.GENERAL_IMAGE_PROMPT: [WorkflowState.GENERAL_IMAGE_GENERATING],
        WorkflowState.GENERAL_IMAGE_GENERATING: [WorkflowState.IMAGE_GENERATED],

        # Single post flow - new states
        WorkflowState.POST_IDEA_SOURCE: [
            WorkflowState.IDEA_REQUEST,           # User wants suggestions
            WorkflowState.POST_BRIEF_GENERATION,  # User has own idea
        ],
        WorkflowState.IDEA_REQUEST: [WorkflowState.IDEAS_SHOWN],
        WorkflowState.IDEAS_SHOWN: [WorkflowState.IDEA_SELECTED, WorkflowState.IDEA_REQUEST],
        WorkflowState.IDEA_SELECTED: [WorkflowState.POST_BRIEF_GENERATION, WorkflowState.BRIEF_SHOWN],
        WorkflowState.POST_BRIEF_GENERATION: [WorkflowState.BRIEF_SHOWN],
        WorkflowState.BRIEF_SHOWN: [WorkflowState.BRIEF_APPROVED, WorkflowState.IDEA_SELECTED],
        WorkflowState.BRIEF_APPROVED: [WorkflowState.POST_GENERATING, WorkflowState.IMAGE_GENERATED],
        WorkflowState.POST_GENERATING: [WorkflowState.IMAGE_GENERATED],
        WorkflowState.IMAGE_GENERATED: [
            WorkflowState.POST_EDIT_REQUESTED,
            WorkflowState.ANIMATION_CHOICE,
            WorkflowState.CAPTION_REQUEST,
            WorkflowState.COMPLETE,
            WorkflowState.MODE_SELECTION,
        ],
        WorkflowState.POST_EDIT_REQUESTED: [WorkflowState.POST_EDITING],
        WorkflowState.POST_EDITING: [WorkflowState.IMAGE_GENERATED],
        WorkflowState.ANIMATION_CHOICE: [
            WorkflowState.ANIMATION_GENERATED,
            WorkflowState.CAPTION_REQUEST,
        ],
        WorkflowState.ANIMATION_GENERATED: [WorkflowState.CAPTION_REQUEST],
        WorkflowState.CAPTION_REQUEST: [WorkflowState.CAPTION_GENERATED],
        WorkflowState.CAPTION_GENERATED: [
            WorkflowState.COMPLETE,
            WorkflowState.MODE_SELECTION,
        ],

        # Campaign flow - extended
        WorkflowState.CAMPAIGN_SETUP: [WorkflowState.CAMPAIGN_DETAILS_SET],
        WorkflowState.CAMPAIGN_DETAILS_SET: [WorkflowState.CAMPAIGN_IDEA_SOURCE, WorkflowState.WEEK_PLANNING],
        WorkflowState.CAMPAIGN_IDEA_SOURCE: [WorkflowState.CAMPAIGN_IDEAS_GENERATED, WorkflowState.WEEK_PLANNING],
        WorkflowState.CAMPAIGN_IDEAS_GENERATED: [WorkflowState.WEEK_PLANNING],
        WorkflowState.WEEK_PLANNING: [WorkflowState.WEEK_PRESENTED, WorkflowState.WEEK_APPROVED],
        WorkflowState.WEEK_PRESENTED: [WorkflowState.WEEK_APPROVED, WorkflowState.WEEK_PLANNING],
        WorkflowState.WEEK_APPROVED: [WorkflowState.WEEK_GENERATING, WorkflowState.POST_GENERATING],
        WorkflowState.WEEK_GENERATING: [WorkflowState.WEEK_COMPLETE],
        WorkflowState.WEEK_COMPLETE: [
            WorkflowState.CAMPAIGN_NEXT_WEEK,
            WorkflowState.CAMPAIGN_COMPLETE,
            WorkflowState.WEEK_PLANNING,
            WorkflowState.COMPLETE,
        ],
        WorkflowState.CAMPAIGN_NEXT_WEEK: [WorkflowState.WEEK_PLANNING],
        WorkflowState.CAMPAIGN_COMPLETE: [WorkflowState.COMPLETE, WorkflowState.MODE_SELECTION],

        # Carousel flow
        WorkflowState.CAROUSEL_SETUP: [WorkflowState.CAROUSEL_GENERATING],
        WorkflowState.CAROUSEL_GENERATING: [WorkflowState.CAROUSEL_COMPLETE],
        WorkflowState.CAROUSEL_COMPLETE: [WorkflowState.COMPLETE, WorkflowState.MODE_SELECTION],

        WorkflowState.COMPLETE: [WorkflowState.MODE_SELECTION],
        WorkflowState.ERROR: [WorkflowState.MODE_SELECTION, WorkflowState.START],
    }
    
    @classmethod
    def is_valid_transition(cls, from_state: WorkflowState, to_state: WorkflowState) -> bool:
        """Check if a state transition is valid."""
        valid_next = cls.VALID_TRANSITIONS.get(from_state, [])
        return to_state in valid_next
    
    @classmethod
    def get_valid_next_states(cls, current_state: WorkflowState) -> list:
        """Get valid next states from current state."""
        return cls.VALID_TRANSITIONS.get(current_state, [])
