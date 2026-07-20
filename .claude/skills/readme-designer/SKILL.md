---
name: readme-designer
description: Diseña y mantiene READMEs de GitHub de nivel profesional para este repo (zanaX). Úsala al crear o editar README.md, la descripción del repo o documentación visible en GitHub.
---

# README Designer

Estándar de diseño y documentación para el README de zanaX (y repos similares de agentes de IA).

## Estructura obligatoria (en este orden)

1. **Hero centrado**: logo/emoji, título, tagline de una línea orientada a resultado ("qué consigue", no "qué contiene").
2. **Badges** (shields.io): lenguaje, framework clave, LLM, licencia, deploy. Máximo 5.
3. **Demo visual**: diagrama de arquitectura en **Mermaid** (GitHub lo renderiza nativo) — nunca ASCII art.
4. **Features en tabla**: módulo | qué hace | archivo. Una fila por módulo.
5. **Quickstart**: 5 pasos numerados máximo, cada uno de una línea, con bloque de código copiable.
6. **Configuración en tabla**: variable | default | para qué. Todas las de `.env.example`.
7. **Secciones de comportamiento** (cómo aprende horarios, límites de crecimiento) con bullets cortos.
8. **Roadmap** con checkboxes y **Disclaimer** de automatización responsable.

## Reglas de estilo

- Español, tono directo de dev; emojis funcionales (🤖🍌📈⚠️) solo en encabezados y alertas.
- Todo número configurable debe aparecer también en `.env.example` con comentario.
- Nada de párrafos largos: bullets de una línea.
- Las advertencias de riesgo (límites de X, DRY_RUN) van en bloque `> [!WARNING]`.
- Links verificables: docs oficiales de X, Google AI Studio, Railway, BotFather.

## Descripción corta del repo (GitHub About)

Máx. 160 caracteres, orientada a resultado, con 2-3 keywords buscables y 1-2 emojis. Formato:
`<qué hace> con <stack>: <3 capacidades clave>. <emoji>`
