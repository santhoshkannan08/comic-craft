from __future__ import annotations

import math
import os
import uuid
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont


def _ensure_panel_directory() -> Path:
    root = Path(__file__).resolve().parent.parent
    panel_dir = root / "static" / "panels"
    panel_dir.mkdir(parents=True, exist_ok=True)
    return panel_dir


def _mock_image(panel_number: int, prompt: str, image_id: str | None = None) -> str:
    panel_dir = _ensure_panel_directory()
    filename = f"panel_{image_id}_{panel_number}.png" if image_id else f"panel_{panel_number}.png"
    save_path = panel_dir / filename

    width, height = 1200, 900
    
    # Palette themes based on panel sequence
    palettes = [
        {"sky": (20, 24, 48), "grad": (67, 34, 114), "accent": (255, 107, 107), "glow": (255, 209, 102), "theme": "PROLOGUE"},
        {"sky": (15, 42, 74), "grad": (14, 116, 144), "accent": (56, 189, 248), "glow": (254, 240, 138), "theme": "JOURNEY"},
        {"sky": (49, 16, 68), "grad": (162, 28, 175), "accent": (236, 72, 153), "glow": (253, 224, 71), "theme": "DISCOVERY"},
        {"sky": (67, 20, 7), "grad": (194, 65, 12), "accent": (249, 115, 22), "glow": (254, 215, 170), "theme": "CLIMAX"},
        {"sky": (6, 78, 59), "grad": (16, 185, 129), "accent": (52, 211, 153), "glow": (250, 204, 21), "theme": "RESOLUTION"},
    ]
    p_idx = (panel_number - 1) % len(palettes)
    pal = palettes[p_idx]

    image = Image.new("RGB", (width, height), color=pal["sky"])
    draw = ImageDraw.Draw(image)

    # 1. Background gradient stripes
    for y in range(0, height, 4):
        ratio = y / height
        r = int(pal["sky"][0] * (1 - ratio) + pal["grad"][0] * ratio)
        g = int(pal["sky"][1] * (1 - ratio) + pal["grad"][1] * ratio)
        b = int(pal["sky"][2] * (1 - ratio) + pal["grad"][2] * ratio)
        draw.line([(0, y), (width, y)], fill=(r, g, b), width=4)

    # 2. Comic burst / speed lines from center
    cx, cy = width // 2, height // 2 - 40
    num_rays = 36
    for i in range(num_rays):
        angle = (2 * math.pi / num_rays) * i
        length = max(width, height)
        ex = cx + int(length * math.cos(angle))
        ey = cy + int(length * math.sin(angle))
        ray_alpha_color = (
            min(255, pal["grad"][0] + 30),
            min(255, pal["grad"][1] + 30),
            min(255, pal["grad"][2] + 30),
        )
        if i % 2 == 0:
            draw.polygon([(cx, cy), (ex - 30, ey), (ex + 30, ey)], fill=ray_alpha_color)

    # 3. Comic Halftone / Dot effect in corners
    for dot_x in range(40, width - 40, 28):
        for dot_y in range(40, 180, 28):
            rad = 3
            draw.ellipse([dot_x - rad, dot_y - rad, dot_x + rad, dot_y + rad], fill=pal["glow"])

    # 4. Central Hero Action Frame
    margin = 50
    draw.rounded_rectangle(
        [margin, margin, width - margin, height - margin],
        radius=24,
        outline=(255, 255, 255),
        width=6,
    )
    # Inner accent border
    draw.rounded_rectangle(
        [margin + 8, margin + 8, width - margin - 8, height - margin - 8],
        radius=18,
        outline=pal["accent"],
        width=3,
    )

    # 5. Central glowing artifact / character silhouette silhouette
    draw.ellipse([cx - 240, cy - 200, cx + 240, cy + 280], fill=pal["glow"], outline=pal["accent"], width=8)
    draw.ellipse([cx - 190, cy - 150, cx + 190, cy + 230], fill=(255, 255, 255), outline=None)

    # Dynamic action silhouette / crest
    draw.polygon(
        [
            (cx, cy - 120),
            (cx + 120, cy + 60),
            (cx + 40, cy + 50),
            (cx + 80, cy + 180),
            (cx - 30, cy + 70),
            (cx - 100, cy + 140),
            (cx - 40, cy + 20),
            (cx - 120, cy + 50),
        ],
        fill=pal["sky"],
    )

    # 6. Comic Sound Effect / Badge top-left
    badge_x, badge_y = 90, 80
    draw.rounded_rectangle([badge_x, badge_y, badge_x + 220, badge_y + 54], radius=14, fill=pal["accent"], outline=(255, 255, 255), width=3)
    draw.text((badge_x + 24, badge_y + 16), f"PANEL #{panel_number} • {pal['theme']}", fill=(20, 24, 48), font=None)

    # 7. Lower prompt caption ribbon
    ribbon_y = height - 150
    draw.rectangle([margin + 12, ribbon_y, width - margin - 12, height - margin - 12], fill=(15, 23, 42))
    draw.line([(margin + 12, ribbon_y), (width - margin - 12, ribbon_y)], fill=pal["accent"], width=4)
    
    # Prompt text display
    clean_prompt = (prompt[:105] + "...") if len(prompt) > 105 else prompt
    draw.text((margin + 30, ribbon_y + 18), "SCENE BEAT:", fill=pal["glow"], font=None)
    draw.text((margin + 30, ribbon_y + 45), clean_prompt, fill=(241, 245, 249), font=None)

    image.save(save_path, format="PNG")
    return f"/static/panels/{filename}"


def generate_image(image_prompt: str, panel_number: int, image_id: str | None = None) -> str:
    """Generate a panel image using Stable Diffusion or a rich deterministic mock fallback."""
    if os.getenv("MOCK_MODE", "false").lower() == "true":
        return _mock_image(panel_number, image_prompt, image_id=image_id)

    api_key = os.getenv("HF_API_KEY")
    if not api_key:
        # Graceful fallback to rich mock illustration if API key is not configured
        return _mock_image(panel_number, image_prompt, image_id=image_id)

    try:
        from diffusers import StableDiffusionPipeline
        import torch
    except Exception:
        # Fallback if diffusers/torch aren't available locally
        return _mock_image(panel_number, image_prompt, image_id=image_id)

    model_id = os.getenv("HF_MODEL_ID") or "runwayml/stable-diffusion-v1-5"
    panel_dir = _ensure_panel_directory()
    filename = f"panel_{image_id}_{panel_number}.png" if image_id else f"panel_{panel_number}.png"
    save_path = panel_dir / filename

    try:
        pipe = StableDiffusionPipeline.from_pretrained(
            model_id,
            token=api_key,
            torch_dtype=torch.float32,
        )
        pipe = pipe.to("cpu")
        image = pipe(image_prompt, num_inference_steps=20, guidance_scale=7.5).images[0]
        image.save(save_path)
        return f"/static/panels/{filename}"
    except Exception:
        # Fallback to rich mock illustration on diffusion runtime error
        return _mock_image(panel_number, image_prompt, image_id=image_id)

