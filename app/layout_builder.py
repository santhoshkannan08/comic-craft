from __future__ import annotations

from typing import Any

from app.models import ComicLayout, ComicPanel, ComicStory


def build_comic_layout(panels: list[ComicPanel], stories: list[ComicStory], image_paths: list[str]) -> list[ComicLayout]:
    """Merge panel, story, and image data into final preview layout objects."""
    panel_map = {panel.panel_number: panel for panel in panels}
    story_map = {story.panel_number: story for story in stories}

    layout: list[ComicLayout] = []
    for index, panel_number in enumerate(sorted(panel_map.keys())):
        panel = panel_map[panel_number]
        story = story_map.get(panel_number, ComicStory(panel_number=panel_number, narration="", character_dialogue="", caption=""))
        image_path = image_paths[index] if index < len(image_paths) else panel.image_path

        layout.append(
            ComicLayout(
                panel_number=panel_number,
                title=panel.title,
                image_path=image_path,
                scene_description=panel.scene_description,
                caption=story.caption,
                narration=story.narration,
                dialogue=story.character_dialogue,
                image_prompt=panel.image_prompt,
            )
        )

    return layout
