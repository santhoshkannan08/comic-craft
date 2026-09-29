from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field, field_validator


class PromptRequest(BaseModel):
    """User input for a comic story generation request."""

    story_prompt: str = Field(..., min_length=10, max_length=2000)
    character_name: str = Field(..., min_length=1, max_length=100)
    setting: str = Field(..., min_length=1, max_length=200)
    tone: str = Field(..., min_length=1, max_length=50)
    art_style: str = Field(..., min_length=1, max_length=50)

    @field_validator("story_prompt", "character_name", "setting", "tone", "art_style")
    @classmethod
    def clean_text(cls, value: str) -> str:
        trimmed = value.strip()
        if not trimmed:
            raise ValueError("Field cannot be empty.")
        return trimmed


class ComicPanel(BaseModel):
    """Single panel metadata before layout assembly."""

    panel_number: int
    title: str
    scene_description: str
    image_prompt: str
    narration: str = ""
    character_dialogue: str = ""
    caption: str = ""
    image_path: str = ""
    image_url: Optional[str] = None


class ComicStory(BaseModel):
    """Narrative text generated for a panel."""

    panel_number: int
    narration: str
    character_dialogue: str
    caption: str


class ComicLayout(BaseModel):
    """Final structured comic panel for preview and PDF output."""

    panel_number: int
    title: str
    image_path: str
    scene_description: str
    caption: str
    narration: str
    dialogue: str
    image_prompt: str
