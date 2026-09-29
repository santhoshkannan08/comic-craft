from __future__ import annotations

import json
import os
import re
from typing import Any

from google import genai


def _extract_json_payload(raw_text: str) -> Any:
    cleaned = raw_text.strip()
    if not cleaned:
        raise ValueError("Gemini returned an empty response.")

    match = re.search(r"```(?:json)?\s*(.*?)\s*```", cleaned, flags=re.DOTALL | re.IGNORECASE)
    if match:
        cleaned = match.group(1).strip()

    if cleaned.lower().startswith("json"):
        cleaned = cleaned[4:].strip()

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    first_brace = cleaned.find("{")
    first_bracket = cleaned.find("[")

    if first_brace != -1 and (first_bracket == -1 or first_brace < first_bracket):
        last_brace = cleaned.rfind("}")
        if last_brace != -1 and last_brace > first_brace:
            try:
                return json.loads(cleaned[first_brace : last_brace + 1])
            except json.JSONDecodeError:
                pass
    elif first_bracket != -1:
        last_bracket = cleaned.rfind("]")
        if last_bracket != -1 and last_bracket > first_bracket:
            try:
                return json.loads(cleaned[first_bracket : last_bracket + 1])
            except json.JSONDecodeError:
                pass

    raise ValueError("Invalid JSON from Gemini Flash response.")


def _mock_outline(
    story_prompt: str = "",
    character_name: str = "Hero",
    setting: str = "World",
    tone: str = "Dramatic",
    art_style: str = "Comic Book",
) -> list[dict[str, Any]]:
    char = character_name.strip() or "The protagonist"
    place = setting.strip() or "the unknown realm"
    theme = story_prompt.strip() or f"A grand quest begins for {char}"
    
    return [
        {
            "panel_number": 1,
            "title": f"The Awakening at {place.title()[:24]}",
            "scene_description": f"{char} stands at the threshold of {place}, facing an unexpected disturbance: {theme[:120]}.",
            "image_prompt": f"cinematic comic illustration of {char} in {place}, vibrant {art_style} style, dramatic lighting, opening scene",
        },
        {
            "panel_number": 2,
            "title": "A Sign in the Shadows",
            "scene_description": f"{char} uncovers an ancient relic that pulses with glowing energy, echoing the true purpose of their journey.",
            "image_prompt": f"{char} examining a glowing mysterious artifact in {place}, high contrast {art_style} comic style, action focus",
        },
        {
            "panel_number": 3,
            "title": "The Trial Begins",
            "scene_description": f"The environment shifts violently as hidden mechanisms and unseen guardians challenge {char}'s resolve in {place}.",
            "image_prompt": f"dramatic action scene with {char} overcoming trials in {place}, dynamic angles, {art_style} comic artwork",
        },
        {
            "panel_number": 4,
            "title": "Clash of Destinies",
            "scene_description": f"Reaching the core of {place}, {char} makes a decisive stand, unleashing courage against overwhelming odds.",
            "image_prompt": f"epic climax confrontation featuring {char}, intense powers glowing in {place}, bold {art_style} graphic novel style",
        },
        {
            "panel_number": 5,
            "title": "A Legend Forged",
            "scene_description": f"With peace restored, {char} looks toward a transformed horizon in {place}, ready for whatever the universe brings next.",
            "image_prompt": f"triumphant and inspiring final panel of {char} standing proudly under vibrant skies in {place}, majestic {art_style}",
        },
    ]


def generate_outline(story_prompt: str, character_name: str, setting: str, tone: str, art_style: str) -> list[dict[str, Any]]:
    """Generate a validated 5-panel comic outline from Gemini Flash or mock mode."""
    api_key = os.getenv("GEMINI_API_KEY")
    if os.getenv("MOCK_MODE", "false").lower() == "true" or not api_key:
        return _mock_outline(story_prompt, character_name, setting, tone, art_style)

    prompt = f"""
    You are creating a five-panel comic outline.
    Return ONLY valid JSON with a top-level "panels" array.
    Each panel must include exactly these fields:
    - panel_number
    - title
    - scene_description
    - image_prompt

    Requirements:
    - Exactly 5 panels.
    - Story prompt: {story_prompt}
    - Main character: {character_name}
    - Setting: {setting}
    - Tone: {tone}
    - Art style: {art_style}
    - Keep the narrative coherent from panel 1 to panel 5.
    - Do not include markdown fences.
    - Ensure image_prompt is vivid and suitable for image generation.
    """

    try:
        client = genai.Client(api_key=api_key)
        model_name = os.getenv("GEMINI_FLASH_MODEL") or "gemini-2.0-flash"
        response = client.models.generate_content(model=model_name, contents=prompt)
        text = getattr(response, "text", None) or str(response)
        payload = _extract_json_payload(text)

        panels = payload.get("panels") if isinstance(payload, dict) else payload
        if not isinstance(panels, list) or len(panels) != 5:
            raise ValueError("Gemini Flash output did not contain exactly 5 panels.")

        validated: list[dict[str, Any]] = []
        for index, raw_panel in enumerate(panels, start=1):
            if not isinstance(raw_panel, dict):
                raise ValueError("Each panel must be a JSON object.")

            panel_number = int(raw_panel.get("panel_number", index))
            title = str(raw_panel.get("title", f"Panel {panel_number}")).strip()
            scene_description = str(raw_panel.get("scene_description", "")).strip()
            image_prompt = str(raw_panel.get("image_prompt", "")).strip()

            if not title or not scene_description or not image_prompt:
                raise ValueError(f"Panel {panel_number} is missing required fields.")

            validated.append(
                {
                    "panel_number": panel_number,
                    "title": title,
                    "scene_description": scene_description,
                    "image_prompt": image_prompt,
                }
            )

        if len(validated) != 5:
            raise ValueError("The generated outline does not contain 5 valid panels.")

        return sorted(validated, key=lambda item: int(item["panel_number"]))
    except Exception as exc:
        raise RuntimeError("Failed to generate a valid 5-panel outline with Gemini Flash.") from exc
