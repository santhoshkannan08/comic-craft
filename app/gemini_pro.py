from __future__ import annotations

import json
import os
import re
from typing import Any

from google import genai


def _extract_json_payload(raw_text: str) -> Any:
    cleaned = raw_text.strip()
    if not cleaned:
        raise ValueError("Gemini Pro returned an empty response.")

    match = re.search(r"```(?:json)?\s*(.*?)\s*```", cleaned, flags=re.DOTALL | re.IGNORECASE)
    if match:
        cleaned = match.group(1).strip()

    if cleaned.lower().startswith("json"):
        cleaned = cleaned[4:].strip()

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    first_bracket = cleaned.find("[")
    first_brace = cleaned.find("{")

    if first_bracket != -1 and (first_brace == -1 or first_bracket < first_brace):
        last_bracket = cleaned.rfind("]")
        if last_bracket != -1 and last_bracket > first_bracket:
            try:
                return json.loads(cleaned[first_bracket : last_bracket + 1])
            except json.JSONDecodeError:
                pass
    elif first_brace != -1:
        last_brace = cleaned.rfind("}")
        if last_brace != -1 and last_brace > first_brace:
            try:
                return json.loads(cleaned[first_brace : last_brace + 1])
            except json.JSONDecodeError:
                pass

    raise ValueError("Invalid JSON from Gemini Pro response.")


def _mock_story(outline: list[dict[str, Any]]) -> list[dict[str, Any]]:
    mock_story = []
    for panel in outline:
        panel_number = int(panel.get("panel_number", 1))
        title = str(panel.get("title", f"Panel {panel_number}"))
        desc = str(panel.get("scene_description", ""))
        
        dialogues = [
            "We have walked right into something far bigger than we imagined.",
            "Look at the symbols... they're reacting to our presence!",
            "Brace yourselves, this is where our real test begins!",
            "I won't back down now. Stand firm!",
            "We did it. A new chapter starts today.",
        ]
        d_idx = (panel_number - 1) % len(dialogues)
        dialogue = dialogues[d_idx]

        mock_story.append(
            {
                "panel_number": panel_number,
                "title": title,
                "narration": f"{desc} Every heartbeat counts as the story unfolds.",
                "character_dialogue": dialogue,
                "caption": f"CHAPTER #{panel_number}: {title.upper()}",
            }
        )
    return mock_story


def generate_story(outline: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Expand the panel outline into narration, dialogue, and captions."""
    api_key = os.getenv("GEMINI_API_KEY")
    if os.getenv("MOCK_MODE", "false").lower() == "true" or not api_key:
        return _mock_story(outline)

    prompt = """
    You are writing a coherent five-panel comic story. Use the provided panel outlines and expand them:
    For each panel provide:
    - panel_number
    - narration
    - character_dialogue
    - caption

    Requirements:
    - Keep chronology from panel 1 to panel 5.
    - Ensure the narrative feels connected and emotionally consistent.
    - The output must be valid JSON, with a top-level array of 5 story objects.
    - Do not include markdown fences.
    Panel data:
    """ + json.dumps(outline, ensure_ascii=False)

    try:
        client = genai.Client(api_key=api_key)
        model_name = os.getenv("GEMINI_PRO_MODEL") or "gemini-1.5-pro"
        response = client.models.generate_content(model=model_name, contents=prompt)
        text = getattr(response, "text", None) or str(response)
        payload = _extract_json_payload(text)

        if not isinstance(payload, list) or len(payload) != len(outline):
            raise ValueError("Gemini Pro output did not return the expected 5-panel story array.")

        stories: list[dict[str, Any]] = []
        for index, item in enumerate(payload, start=1):
            if not isinstance(item, dict):
                raise ValueError("Each story entry must be a JSON object.")

            panel_number = int(item.get("panel_number", index))
            narration = str(item.get("narration", "")).strip()
            character_dialogue = str(item.get("character_dialogue", "")).strip()
            caption = str(item.get("caption", "")).strip()

            if not narration or not character_dialogue or not caption:
                raise ValueError(f"Story panel {panel_number} is missing narration, dialogue, or caption.")

            stories.append(
                {
                    "panel_number": panel_number,
                    "narration": narration,
                    "character_dialogue": character_dialogue,
                    "caption": caption,
                }
            )

        return sorted(stories, key=lambda item: int(item["panel_number"]))
    except Exception as exc:
        raise RuntimeError("Failed to generate coherent comic narration and dialogue with Gemini Pro.") from exc
