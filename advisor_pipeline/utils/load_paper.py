# SPDX-FileCopyrightText: 2026 Chelsea Liekhus-Schmaltz and Johnathon Barhydt
#
# SPDX-License-Identifier: AGPL-3.0-only

from pathlib import Path
from typing import Any, Dict
from PIL import Image
import io
import base64
import re


def load_paper_from_file(paper_file: Path, figure_folder: Path, bib_file: Path) -> Dict[str, Any]:

    with open(paper_file) as f:
        paper_text = f.read()

    figures: Dict[str, Dict[str, str]] = {}
    if figure_folder.exists():
        for img_path in figure_folder.iterdir():
            if img_path.is_file():
                img_data, media_type = encode_image(img_path)
                figures[img_path.name] = {"data": img_data, "media_type": media_type}

    with open(bib_file) as f:
        bib_raw_text = f.read()

    bib_dict = parse_citations(bib_raw_text)

    return {
        "paper_text": paper_text,
        "figures": figures,
        "bib_text": bib_dict,
    }

def encode_image(image_path: Path, max_size: int = 800) -> tuple[str, str]:
    """Resize and base64-encode an image file."""
    img = Image.open(image_path)
    if max(img.size) > max_size:
        ratio = max_size / max(img.size)
        new_size = tuple(int(dim * ratio) for dim in img.size)
        img = img.resize(new_size, Image.Resampling.LANCZOS)

    suffix = image_path.suffix.lower()
    format_map = {
        ".png": ("PNG", "image/png"),
        ".jpg": ("JPEG", "image/jpeg"),
        ".jpeg": ("JPEG", "image/jpeg"),
        ".gif": ("GIF", "image/gif"),
        ".webp": ("WEBP", "image/webp"),
    }
    img_format, media_type = format_map.get(suffix, ("JPEG", "image/jpeg"))

    buffer = io.BytesIO()
    img.save(buffer, format=img_format)
    image_data = base64.standard_b64encode(buffer.getvalue()).decode("utf-8")
    return image_data, media_type


def parse_citations(text: str) -> dict[int, str]:
    pattern = r'\[(\d+)\]\s*(.*?)(?=\[\d+\]|$)'
    matches = re.findall(pattern, text, re.DOTALL)
    return {
        int(num): re.sub(r'\\+\[0pt\]', '', citation).strip()
        for num, citation in matches
    }