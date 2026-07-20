"""Generación de imágenes con 'nano banana' (Gemini image, gemini-2.5-flash-image).

Se activa con ENABLE_IMAGES=true y requiere GOOGLE_API_KEY (Google AI Studio).
Docs: https://ai.google.dev/gemini-api/docs/image-generation
"""
from __future__ import annotations

import os
import pathlib
import uuid

OUT_DIR = pathlib.Path("/tmp/x-ai-agent-images")


def enabled() -> bool:
    return (
        os.getenv("ENABLE_IMAGES", "false").lower() == "true"
        and bool(os.getenv("GOOGLE_API_KEY"))
    )


def generate_image(prompt: str) -> str | None:
    """Genera una imagen y devuelve la ruta local, o None si falla/está off."""
    if not enabled():
        return None
    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=os.environ["GOOGLE_API_KEY"])
        resp = client.models.generate_content(
            model=os.getenv("IMAGE_MODEL", "gemini-2.5-flash-image"),
            contents=prompt,
            config=types.GenerateContentConfig(response_modalities=["IMAGE"]),
        )
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        for part in resp.candidates[0].content.parts:
            if part.inline_data is not None:
                path = OUT_DIR / f"{uuid.uuid4().hex}.png"
                path.write_bytes(part.inline_data.data)
                return str(path)
    except Exception:
        return None
    return None
