# Verifier index

- **v1** (2026-07-21): `v1/check.py` — verifica existencia de archivos requeridos, sintaxis AST de todo el código Python, variables clave en `.env.example` y secciones mínimas del README. Primer verificador del proyecto.
- **v2** (2026-07-21): `v2/check.py` — todo lo de v1 + existencia de `src/agent/images.py` (nano banana / Gemini image), nodo `image_node` en el grafo, `media_upload` en el cliente de X, `google-genai` en requirements y variables `ENABLE_IMAGES`/`GOOGLE_API_KEY`/`IMAGE_MODEL` en `.env.example`. Añadido tras integrar la generación de imágenes.
