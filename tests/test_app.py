from __future__ import annotations

import os

from fastapi.testclient import TestClient

os.environ.setdefault("MOCK_MODE", "true")

from app.main import app

client = TestClient(app)


def test_homepage_loads() -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert "ComicCraft" in response.text


def test_invalid_form_returns_error() -> None:
    response = client.post(
        "/generate",
        data={
            "story_prompt": "",
            "character_name": "Nova",
            "setting": "Forest",
            "tone": "Funny",
            "art_style": "Anime",
        },
    )
    assert response.status_code == 400


def test_mock_json_generation_returns_five_panels() -> None:
    response = client.post(
        "/generate-comic/json",
        json={
            "story_prompt": "A brave fox discovers a moonlit portal in a magical forest.",
            "character_name": "Nova",
            "setting": "Moonlit forest",
            "tone": "Dramatic",
            "art_style": "Comic Book",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert len(data["panels"]) == 5
    assert data["pdf_path"].startswith("/static/exports/")


def test_test_image_route_returns_info() -> None:
    response = client.get("/test-image")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True


def test_health_endpoint() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_valid_form_submission_renders_preview() -> None:
    response = client.post(
        "/generate",
        data={
            "story_prompt": "A brave astronaut discovers a hidden alien oasis.",
            "character_name": "Astra",
            "setting": "Mars Crater",
            "tone": "Dramatic",
            "art_style": "Comic Book",
        },
    )
    assert response.status_code == 200
    assert "Comic Preview" in response.text
    assert "Panel 1" in response.text
    assert "Download Your Comic as PDF" in response.text


def test_export_success_page() -> None:
    response = client.get("/export-success?pdf_path=/static/exports/comic_test.pdf")
    assert response.status_code == 200
    assert "Your Comic Has Been Successfully Created!" in response.text


def test_outline_and_story_generation_unit() -> None:
    from app.gemini_flash import generate_outline
    from app.gemini_pro import generate_story

    outline = generate_outline(
        story_prompt="Detective Raven searches for clues in Neo-Tokyo",
        character_name="Raven",
        setting="Neo-Tokyo",
        tone="Dramatic",
        art_style="Anime",
    )
    assert len(outline) == 5
    assert "Raven" in outline[0]["scene_description"] or "Raven" in outline[0]["title"] or "Raven" in outline[0]["image_prompt"]

    stories = generate_story(outline)
    assert len(stories) == 5
    assert stories[0]["panel_number"] == 1
    assert "narration" in stories[0]
    assert "character_dialogue" in stories[0]


def test_pdf_exporter_generates_file() -> None:
    from app.exporters import save_pdf
    from app.image_generator import generate_image

    img_path = generate_image("test image prompt", 1, image_id="test_unit")
    sample_layout = [
        {
            "panel_number": 1,
            "title": "The First Clue",
            "image_path": img_path,
            "scene_description": "Detective investigates the crime scene",
            "caption": "Chapter 1: The Beginning",
            "narration": "Rain falls continuously on the city streets.",
            "dialogue": "There is something unnatural here.",
            "image_prompt": "cyberpunk detective in rain",
        }
    ]
    pdf_path = save_pdf(sample_layout)
    assert pdf_path.startswith("/static/exports/")
    assert pdf_path.endswith(".pdf")

