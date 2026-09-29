from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from fpdf import FPDF


def _as_ascii_safe(value: str) -> str:
    cleaned = (
        (value or "")
        .replace("—", "-")
        .replace("–", "-")
        .replace("“", '"')
        .replace("”", '"')
        .replace("’", "'")
        .replace("‘", "'")
        .replace("…", "...")
        .replace("\n", " ")
    )
    return cleaned.encode("latin-1", errors="replace").decode("latin-1")


def _as_absolute_image_path(image_path: str) -> str:
    if not image_path:
        return ""

    if image_path.startswith("/"):
        root = Path(__file__).resolve().parent.parent
        relative = image_path.lstrip("/")
        return str(root / relative)
    return str(Path(image_path).resolve())


def save_pdf(layout: list[dict[str, Any]], title_prefix: str = "ComicCraft Issue") -> str:
    """Render a multi-panel PDF containing the final comic layout."""
    export_dir = Path(__file__).resolve().parent.parent / "static" / "exports"
    export_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_name = f"comic_{timestamp}.pdf"
    output_path = export_dir / output_name

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=12)

    total_panels = len(layout)
    for index, panel in enumerate(layout, start=1):
        pdf.add_page()

        panel_num = panel.get("panel_number", index)
        title = _as_ascii_safe(str(panel.get("title", f"Panel {panel_num}")))
        caption = _as_ascii_safe(str(panel.get("caption", "")))
        narration = _as_ascii_safe(str(panel.get("narration", "")))
        dialogue = _as_ascii_safe(str(panel.get("dialogue", "")))

        # Header bar background
        pdf.set_fill_color(27, 27, 47)
        pdf.rect(10, 10, 190, 14, "F")

        # Header Title
        pdf.set_xy(14, 12)
        pdf.set_font("Helvetica", "B", 13)
        pdf.set_text_color(255, 209, 102)
        pdf.cell(50, 10, f"COMICCRAFT  |  PANEL {panel_num} OF {total_panels}", ln=0)
        
        pdf.set_xy(100, 12)
        pdf.set_font("Helvetica", "B", 12)
        pdf.set_text_color(255, 255, 255)
        pdf.cell(96, 10, title[:38], align="R", ln=1)

        # Panel artwork frame
        image_path = _as_absolute_image_path(panel.get("image_path", ""))
        art_y = 28
        if image_path and Path(image_path).exists():
            # Border behind image
            pdf.set_fill_color(240, 240, 245)
            pdf.rect(14, art_y - 1, 182, 117, "F")
            pdf.image(image_path, x=15, y=art_y, w=180, h=115)
            next_y = art_y + 120
        else:
            pdf.set_xy(15, art_y)
            pdf.set_font("Helvetica", "I", 12)
            pdf.set_text_color(120, 120, 120)
            pdf.cell(180, 20, "[Illustration Panel]", align="C", ln=1)
            next_y = art_y + 25

        # Narration Box (Yellowish comic box)
        pdf.set_xy(15, next_y)
        if narration:
            pdf.set_fill_color(255, 250, 230)
            pdf.set_draw_color(255, 209, 102)
            pdf.set_line_width(0.8)
            pdf.rect(15, next_y, 180, 22, "DF")

            pdf.set_xy(18, next_y + 2)
            pdf.set_font("Helvetica", "B", 9)
            pdf.set_text_color(180, 83, 9)
            pdf.cell(0, 4, "NARRATION", ln=1)

            pdf.set_xy(18, next_y + 7)
            pdf.set_font("Helvetica", "", 9)
            pdf.set_text_color(30, 41, 59)
            pdf.multi_cell(174, 4.5, narration[:220])
            next_y += 26

        # Dialogue Bubble (Sleek light bubble)
        if dialogue:
            pdf.set_fill_color(243, 244, 246)
            pdf.set_draw_color(203, 213, 225)
            pdf.set_line_width(0.6)
            pdf.rect(15, next_y, 180, 22, "DF")

            pdf.set_xy(18, next_y + 2)
            pdf.set_font("Helvetica", "B", 9)
            pdf.set_text_color(217, 75, 75)
            pdf.cell(0, 4, "CHARACTER DIALOGUE", ln=1)

            pdf.set_xy(18, next_y + 7)
            pdf.set_font("Helvetica", "I", 10)
            pdf.set_text_color(15, 23, 42)
            clean_dialogue = f'"{dialogue}"' if not dialogue.startswith('"') else dialogue
            pdf.multi_cell(174, 4.5, clean_dialogue[:200])
            next_y += 25

        # Caption Bar (Bottom)
        if caption:
            pdf.set_xy(15, next_y + 1)
            pdf.set_font("Helvetica", "B", 9)
            pdf.set_text_color(100, 116, 139)
            pdf.cell(180, 6, f">> {caption[:120]}", ln=1)

    pdf.output(str(output_path))
    return f"/static/exports/{output_name}"
