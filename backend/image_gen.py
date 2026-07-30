"""
image_gen.py
============
Image generation integration for BRAND STUDIO AI.

Generates:
  • 3 logo PNGs  — abstract Islamic geometric marks (no product imagery)
  • 3 social media visual PNGs (1080×1080) — abstract brand identity art

Design notes:
  • Images are generated using pure PIL geometric art.
    No external image-generation API is required.
  • Images are ABSTRACT / GEOMETRIC ONLY — never photorealistic product shots.
    This is intentional: the platform gives visual identity ideas, not
    ready-made product advertisements that could be misused.
  • Each image write is atomic: bytes → tmp → rename to final path.

Environment variables:
  None required for image generation — all images are generated locally via PIL.
"""

from __future__ import annotations

import io
import logging
import math
import os
from pathlib import Path
from typing import NamedTuple

from PIL import Image, ImageDraw

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# RESULT TYPE
# ---------------------------------------------------------------------------

class ImageResult(NamedTuple):
    path:   Path    # absolute path to saved PNG
    model:  str     # model that produced the image


# ---------------------------------------------------------------------------
# INTERNAL HELPERS
# ---------------------------------------------------------------------------

def _save_png(img: Image.Image, dest: Path) -> None:
    """Atomically write a PIL Image as PNG to *dest*."""
    tmp = dest.with_suffix(".tmp.png")
    img.save(str(tmp), format="PNG", optimize=False)
    tmp.rename(dest)


def _hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    """Convert a hex colour string (#RRGGBB) to an RGB tuple."""
    h = hex_color.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


# Brand-type → colour palette mapping used when no explicit palette is provided
_BRAND_PALETTE: dict[str, list[str]] = {
    "bakery":      ["#C9A96E", "#F5EFE6", "#2C2C2C"],
    "restaurant":  ["#B5451B", "#F9F1E7", "#2C2C2C"],
    "fashion":     ["#8B5E83", "#F7F3F0", "#1A1A1A"],
    "jewelry":     ["#C9A96E", "#1A1A2E", "#FFFFFF"],
    "beauty":      ["#E8A598", "#FFF5F5", "#3D2B1F"],
    "health":      ["#4CAF82", "#F0FFF4", "#1A2E2A"],
    "education":   ["#2563EB", "#EFF6FF", "#1E3A5F"],
    "technology":  ["#3B82F6", "#0F172A", "#E2E8F0"],
    "real estate": ["#8B6914", "#F5F5DC", "#1A1A1A"],
    "consulting":  ["#1E3A5F", "#F7F9FC", "#C9A96E"],
    "default":     ["#3B5CD8", "#F7F8FA", "#1F2328"],
}


def _get_palette(business_type: str) -> list[tuple[int, int, int]]:
    """Return 3 RGB tuples for the given business type."""
    bt = business_type.lower()
    for key, hexes in _BRAND_PALETTE.items():
        if key in bt:
            return [_hex_to_rgb(h) for h in hexes]
    return [_hex_to_rgb(h) for h in _BRAND_PALETTE["default"]]


def _draw_star_polygon(
    draw: ImageDraw.ImageDraw,
    cx: int, cy: int,
    outer_r: int, inner_r: int,
    points: int,
    fill: tuple,
    outline: tuple,
) -> None:
    """Draw a star polygon (Islamic geometric motif)."""
    coords = []
    for i in range(points * 2):
        angle = math.pi / points * i - math.pi / 2
        r = outer_r if i % 2 == 0 else inner_r
        coords.append((cx + r * math.cos(angle), cy + r * math.sin(angle)))
    draw.polygon(coords, fill=fill, outline=outline)


def _make_geometric_logo(
    width: int,
    height: int,
    primary: tuple[int, int, int],
    secondary: tuple[int, int, int],
    accent: tuple[int, int, int],
    variant: int = 0,
) -> Image.Image:
    """
    Generate an abstract Islamic geometric logo mark using PIL.
    variant (0, 1, 2) gives three different compositions.
    """
    img  = Image.new("RGBA", (width, height), (*secondary, 255))
    draw = ImageDraw.Draw(img)

    cx, cy = width // 2, height // 2

    # Outer decorative ring
    margin = width // 8
    draw.ellipse(
        [margin, margin, width - margin, height - margin],
        outline=(*primary, 180), width=3,
    )

    # Inner geometric fill ring
    inner_m = width // 4
    draw.ellipse(
        [inner_m, inner_m, width - inner_m, height - inner_m],
        outline=(*accent, 120), width=2,
    )

    # Star polygon composition based on variant
    star_configs = [
        (8, 5, width // 3, width // 6),   # 8-point star
        (6, 5, width // 3, width // 7),   # 6-point star
        (12, 5, width // 3, width // 5),  # 12-point star
    ]
    pts, _, outer_r, inner_r = star_configs[variant % 3]
    _draw_star_polygon(draw, cx, cy, outer_r, inner_r, pts,
                       fill=(*primary, 200), outline=(*accent, 255))

    # Small centre diamond
    d = width // 12
    draw.polygon(
        [(cx, cy - d), (cx + d, cy), (cx, cy + d), (cx - d, cy)],
        fill=(*accent, 255),
    )

    return img


def _make_social_post(
    width: int,
    height: int,
    primary: tuple[int, int, int],
    secondary: tuple[int, int, int],
    accent: tuple[int, int, int],
    variant: int = 0,
) -> Image.Image:
    """Generate a 1080×1080 abstract brand identity background using PIL."""
    img  = Image.new("RGBA", (width, height), (*secondary, 255))
    draw = ImageDraw.Draw(img)

    # Arabesque-inspired tiled star pattern
    tile = width // 5
    for row in range(7):
        for col in range(7):
            x = col * tile - tile // 2
            y = row * tile - tile // 2
            if (row + col) % 2 == 0:
                _draw_star_polygon(
                    draw, x, y,
                    tile // 2 - 4, tile // 4 - 2,
                    8 if variant != 1 else 6,
                    fill=(*primary, 60),
                    outline=(*accent, 90),
                )
            else:
                draw.rectangle(
                    [x - tile // 4, y - tile // 4,
                     x + tile // 4, y + tile // 4],
                    outline=(*primary, 50), width=1,
                )

    # Central focal element
    cx, cy = width // 2, height // 2
    for i in range(3, 0, -1):
        r = (width // 3) * i // 3
        draw.ellipse(
            [cx - r, cy - r, cx + r, cy + r],
            outline=(*accent, 40 + i * 30), width=2,
        )
    _draw_star_polygon(
        draw, cx, cy,
        width // 5, width // 10,
        8 + variant * 2,
        fill=(*primary, 140),
        outline=(*accent, 200),
    )

    # Decorative border
    b = 16
    draw.rectangle([b, b, width - b, height - b], outline=(*accent, 160), width=3)

    return img


# ---------------------------------------------------------------------------
# PUBLIC API
# ---------------------------------------------------------------------------

def generate_logos(
    prompts: list[str],
    business_name: str,
    output_dir: Path,
    business_type: str = "",
) -> list[ImageResult]:
    """
    Generate 3 abstract Islamic geometric logo PNGs via PIL.
    All images are purely geometric — no product imagery.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    palette = _get_palette(business_type)
    primary, secondary, accent = palette[0], palette[1], palette[2]
    results: list[ImageResult] = []

    for idx in range(1, 4):
        dest = output_dir / f"logo_{idx}.png"
        img  = _make_geometric_logo(512, 512, primary, secondary, accent, variant=idx - 1)
        _save_png(img, dest)
        logger.info("Logo %d saved → %s  (model=pil-geometric)", idx, dest)
        results.append(ImageResult(path=dest, model="pil-geometric"))

    return results


def generate_social_posts(
    prompts: list[str],
    brand_color_hint: str,
    output_dir: Path,
    business_type: str = "",
) -> list[ImageResult]:
    """
    Generate 3 abstract brand visual PNGs (1080×1080) via PIL.
    Purely geometric / abstract brand identity artworks — NOT product photos.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    palette = _get_palette(business_type)
    primary, secondary, accent = palette[0], palette[1], palette[2]
    results: list[ImageResult] = []

    for idx in range(1, 4):
        dest = output_dir / f"post_{idx}.png"
        img  = _make_social_post(1080, 1080, primary, secondary, accent, variant=idx - 1)
        _save_png(img, dest)
        logger.info("Social post %d saved → %s  (model=pil-geometric)", idx, dest)
        results.append(ImageResult(path=dest, model="pil-geometric"))

    return results


def generate_svg_from_png(png_path: Path) -> Path:
    """
    Produce a minimal SVG wrapper that embeds the PNG as a base64 data URI.
    """
    import base64

    svg_path = png_path.with_suffix(".svg")
    b64      = base64.b64encode(png_path.read_bytes()).decode()
    svg      = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<svg xmlns="http://www.w3.org/2000/svg" '
        'xmlns:xlink="http://www.w3.org/1999/xlink" '
        'width="512" height="512" viewBox="0 0 512 512">\n'
        f'  <image width="512" height="512" '
        f'xlink:href="data:image/png;base64,{b64}"/>\n'
        '</svg>\n'
    )
    svg_path.write_text(svg, encoding="utf-8")
    logger.info("SVG wrapper saved → %s", svg_path)
    return svg_path
