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
    MODE_SELECTION = "mode_selection"
    
    # Single post flow
    IDEA_REQUEST = "idea_request"
    IDEAS_SHOWN = "ideas_shown"
    IDEA_SELECTED = "idea_selected"
    BRIEF_SHOWN = "brief_shown"
    BRIEF_APPROVED = "brief_approved"
    IMAGE_GENERATED = "image_generated"
    ANIMATION_CHOICE = "animation_choice"
    ANIMATION_GENERATED = "animation_generated"
    CAPTION_REQUEST = "caption_request"
    CAPTION_GENERATED = "caption_generated"
    
    # Campaign flow
    CAMPAIGN_SETUP = "campaign_setup"
    CAMPAIGN_DETAILS_SET = "campaign_details_set"
    WEEK_PLANNING = "week_planning"
    WEEK_APPROVED = "week_approved"
    POST_GENERATING = "post_generating"
    WEEK_COMPLETE = "week_complete"
    
    # Common
    COMPLETE = "complete"
    ERROR = "error"


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
    
    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "industry": self.industry,
            "overview": self.overview,
            "tone": self.tone,
            "logo_path": self.logo_path,
            "colors": self.colors,
            "reference_images": self.reference_images,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "BrandContext":
        return cls(**data)
    
    def is_complete(self) -> bool:
        """Check if basic brand info is set."""
        return bool(self.name)


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
        WorkflowState.BRAND_SETUP: [WorkflowState.MODE_SELECTION],
        WorkflowState.MODE_SELECTION: [
            WorkflowState.IDEA_REQUEST,
            WorkflowState.CAMPAIGN_SETUP,
        ],
        
        # Single post flow
        WorkflowState.IDEA_REQUEST: [WorkflowState.IDEAS_SHOWN],
        WorkflowState.IDEAS_SHOWN: [WorkflowState.IDEA_SELECTED, WorkflowState.IDEA_REQUEST],
        WorkflowState.IDEA_SELECTED: [WorkflowState.BRIEF_SHOWN],
        WorkflowState.BRIEF_SHOWN: [WorkflowState.BRIEF_APPROVED, WorkflowState.IDEA_SELECTED],
        WorkflowState.BRIEF_APPROVED: [WorkflowState.IMAGE_GENERATED],
        WorkflowState.IMAGE_GENERATED: [
            WorkflowState.ANIMATION_CHOICE,
            WorkflowState.CAPTION_REQUEST,
        ],
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
        
        # Campaign flow
        WorkflowState.CAMPAIGN_SETUP: [WorkflowState.CAMPAIGN_DETAILS_SET],
        WorkflowState.CAMPAIGN_DETAILS_SET: [WorkflowState.WEEK_PLANNING],
        WorkflowState.WEEK_PLANNING: [WorkflowState.WEEK_APPROVED],
        WorkflowState.WEEK_APPROVED: [WorkflowState.POST_GENERATING],
        WorkflowState.POST_GENERATING: [WorkflowState.WEEK_COMPLETE],
        WorkflowState.WEEK_COMPLETE: [
            WorkflowState.WEEK_PLANNING,
            WorkflowState.COMPLETE,
        ],
        
        WorkflowState.COMPLETE: [WorkflowState.MODE_SELECTION],
        WorkflowState.ERROR: [WorkflowState.MODE_SELECTION],
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
