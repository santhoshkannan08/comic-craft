from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pydantic import ValidationError

from app.exporters import save_pdf
from app.gemini_flash import generate_outline
from app.gemini_pro import generate_story
from app.image_generator import generate_image
from app.layout_builder import build_comic_layout
from app.models import ComicLayout, ComicPanel, ComicStory, PromptRequest

router = APIRouter()
templates = Jinja2Templates(directory=str(Path(__file__).resolve().parent.parent / "templates"))
logger = logging.getLogger("comiccraft")


def _sanitize_prompt(value: str, max_length: int = 2000) -> str:
    cleaned = (value or "").strip()
    if len(cleaned) > max_length:
        raise HTTPException(status_code=400, detail=f"Input exceeds {max_length} characters.")
    return cleaned


def _build_comic_workflow(payload: PromptRequest) -> tuple[list[ComicPanel], list[ComicStory], list[dict[str, Any]], str]:
    import uuid
    run_id = uuid.uuid4().hex[:8]
    
    outline = generate_outline(
        payload.story_prompt,
        payload.character_name,
        payload.setting,
        payload.tone,
        payload.art_style,
    )
    stories_raw = generate_story(outline)

    panels: list[ComicPanel] = []
    for item in outline:
        panels.append(
            ComicPanel(
                panel_number=int(item["panel_number"]),
                title=str(item["title"]),
                scene_description=str(item["scene_description"]),
                image_prompt=str(item["image_prompt"]),
            )
        )

    story_objects = [
        ComicStory(
            panel_number=int(story["panel_number"]),
            narration=str(story.get("narration", "")),
            character_dialogue=str(story.get("character_dialogue", "")),
            caption=str(story.get("caption", "")),
        )
        for story in stories_raw
    ]

    image_paths: list[str] = []
    for panel in panels:
        image_paths.append(generate_image(panel.image_prompt, panel.panel_number, image_id=run_id))

    layout = build_comic_layout(panels, story_objects, image_paths)
    layout_dicts = [panel.model_dump() for panel in layout]
    pdf_path = save_pdf(layout_dicts)

    return panels, story_objects, layout_dicts, pdf_path


# Backwards compatibility alias
_build_mock_workflow = _build_comic_workflow


@router.get("/")
async def home(request: Request):
    html = templates.get_template("index.html").render(request=request)
    return HTMLResponse(content=html)


@router.post("/generate")
async def generate_comic_form(
    request: Request,
    story_prompt: str = Form(""),
    character_name: str = Form(""),
    setting: str = Form(""),
    tone: str = Form(""),
    art_style: str = Form(""),
):
    if not story_prompt or not story_prompt.strip():
        raise HTTPException(status_code=400, detail="Story prompt is required.")

    try:
        payload = PromptRequest(
            story_prompt=_sanitize_prompt(story_prompt),
            character_name=_sanitize_prompt(character_name, 100),
            setting=_sanitize_prompt(setting, 200),
            tone=_sanitize_prompt(tone, 50),
            art_style=_sanitize_prompt(art_style, 50),
        )
    except ValidationError as exc:
        raise HTTPException(status_code=400, detail=exc.errors()) from exc
    except HTTPException:
        raise

    try:
        _, _, layout, pdf_path = _build_comic_workflow(payload)
        html = templates.get_template("comic_preview.html").render(
            request=request,
            panels=layout,
            pdf_path=pdf_path,
            meta=payload.model_dump(),
        )
        return HTMLResponse(content=html)
    except Exception as exc:
        logger.exception("Comic generation failed")
        raise HTTPException(status_code=500, detail="Comic generation failed. Please check your inputs or API configuration.") from exc


@router.post("/generate-comic/json")
async def generate_comic_json(payload: PromptRequest):
    try:
        _, _, layout, pdf_path = _build_comic_workflow(payload)
        return {
            "success": True,
            "panels": layout,
            "pdf_path": pdf_path,
            "meta": payload.model_dump(),
        }
    except Exception as exc:
        logger.exception("JSON comic generation failed")
        raise HTTPException(status_code=500, detail="Comic generation failed. Please verify the request and environment settings.") from exc


@router.get("/export-success")
async def export_success(request: Request, pdf_path: str | None = None):
    html = templates.get_template("export_success.html").render(request=request, pdf_path=pdf_path)
    return HTMLResponse(content=html)


@router.get("/test-image")
async def test_image_generate():
    prompt = "A brave fox standing in an enchanted forest, cinematic comic book illustration"
    try:
        image_path = generate_image(prompt, 1)
        return {"success": True, "image_path": image_path, "prompt": prompt}
    except Exception as exc:
        logger.exception("Test image generation failed")
        raise HTTPException(status_code=500, detail="Image generation failed. Check the model and API keys.") from exc
