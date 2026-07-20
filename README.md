<div align="center">

# 🤖🍌 zanaX

**Tu cuenta de X creciendo sola en el mundo AI/dev: investiga, escribe con tu voz, genera imágenes y publica en el mejor momento — tú solo apruebas desde Telegram.**

[![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)](https://python.org)
[![LangGraph](https://img.shields.io/badge/Orchestration-LangGraph-1C3C3C)](https://langchain-ai.github.io/langgraph/)
[![LLM](https://img.shields.io/badge/LLM-Gemini%202.5-8E75B2?logo=google&logoColor=white)](https://ai.google.dev)
[![Deploy](https://img.shields.io/badge/Deploy-Railway-0B0D0E?logo=railway&logoColor=white)](https://railway.app)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

</div>

---

## 🧠 Cómo funciona

```mermaid
flowchart LR
    subgraph Research
        A[HN · GitHub · Reddit] --> R
        B[Cuentas clave de X] --> R
        M2[Servidores MCP<br/>arXiv · Product Hunt] --> R
    end
    R[research] --> S[select<br/>Gemini Flash<br/>+ memoria anti-repetición]
    S --> I[image<br/>🍌 nano banana]
    I --> D[draft<br/>Gemini Pro + tu voz<br/>+ learnings reales]
    D --> C[critic<br/>rúbrica + top posts<br/>reescribe si < 0.8]
    C --> T{Telegram<br/>✅ / ❌ / ✏️}
    T -->|aprobado| P[publish<br/>X API]
    T -->|descartado| X[🗑️]
    P --> M[(métricas + memoria)]
    M -->|cada lunes| LLM[LLM re-aprende<br/>horarios y lecciones]
    LLM -.reprograma.-> S

    subgraph Growth
        G1[descubre cuentas afines] --> G2[sigue 25/día<br/>en 4 tandas]
        G3[prune sin follow-back<br/>50/semana]
        G4[💬 respuestas con tu voz<br/>siempre con tu ✅]
    end
```

## ✨ Módulos

| Módulo | Qué hace | Archivo |
|---|---|---|
| **Research** | Tendencias de HN, GitHub Trending, Reddit y DuckDuckGo News | `src/agent/tools.py` |
| **MCP Sources** | Fuentes extra vía **Model Context Protocol** (arXiv, Product Hunt…) configurables en `MCP_SERVERS` | `src/agent/mcp_sources.py` |
| **X Research** | Lee cuentas que publican a diario (`X_ACCOUNTS`), rankeadas por engagement | `src/agent/x_research.py` |
| **LLM multi-provider** | Gemini Flash (análisis) + Gemini Pro (redacción); conmutable a OpenAI/Claude | `src/agent/llm.py` |
| **Imágenes** | nano banana (`gemini-2.5-flash-image`), generadas antes de redactar | `src/agent/images.py` |
| **Tu voz** | Guía de estilo + few-shot con tus tuits reales | `src/agent/style.py` |
| **Grafo** | research → select → image → draft → **critic** | `src/agent/graph.py` |
| **Crítico** | Puntúa contra rúbrica + tus posts top históricos (modelo distinto al redactor); reescribe si < `CRITIC_THRESHOLD` | `src/agent/critic.py` |
| **Memoria** | Temas cubiertos (anti-repetición) + lecciones semanales de tu engagement real | `src/agent/memory.py` |
| **Timing** | Aprende tus mejores horas con tu engagement real; reprograma el scheduler | `src/agent/timing.py` |
| **Growth** | Descubre/afines, follow/unfollow con límites seguros, respuestas con aprobación | `src/agent/growth.py` |
| **Aprobación** | Bot de Telegram: ✅ publica · ❌ descarta · cita el mensaje para editar | `src/approval.py` |
| **Publisher** | Posts, respuestas e imágenes vía X API v2; `DRY_RUN` = modo prueba | `src/x_client.py` |

## 🚀 Quickstart (15 min)

1. **Telegram** → bot con [@BotFather](https://t.me/BotFather) + tu `chat_id` con [@userinfobot](https://t.me/userinfobot)
2. **X API** → [developer.x.com](https://developer.x.com) plan Basic: 4 claves OAuth + Bearer Token
3. **Google** → key gratis en [AI Studio](https://aistudio.google.com/apikey) (LLM + nano banana con la misma key)
4. **Tu voz** → pon 3-5 tuits tuyos en `src/agent/style.py`
5. **Arranca**:

```bash
cp .env.example .env   # rellena las claves
pip install -r requirements.txt
python -m src.main     # ciclo de prueba al iniciar
```

> [!WARNING]
> Arranca siempre con `DRY_RUN=true`: recibirás los borradores en Telegram sin publicar nada. Cuando la voz te convenza, pon `DRY_RUN=false`.

## ⚙️ Configuración

| Variable | Default | Para qué |
|---|---|---|
| `LLM_PROVIDER` | `google` | `google` · `openai` · `anthropic` |
| `LLM_MODEL` | `gemini-2.5-flash` | Tareas baratas: selección, prompts, timing |
| `LLM_MODEL_DRAFT` | `gemini-2.5-pro` | Redacción de posts y comentarios |
| `X_BEARER_TOKEN` | — | Leer cuentas, tendencias y métricas |
| `X_ACCOUNTS` | OpenAI, DeepMind… | Cuentas a vigilar (sin `@`, por comas) |
| `ENABLE_IMAGES` | `false` | Activa nano banana 🍌 |
| `POSTS_PER_DAY` | `2` | Borradores por ciclo |
| `FOLLOW_PER_DAY` | `25` | Máx. follows/día (cada uno cuesta $0.015) |
| `FOLLOW_BATCH` | `7` | Por tanda — 4 tandas: 8h, 12h, 16h, 20h |
| `UNFOLLOW_PER_WEEK` | `50` | Máx. 50/semana, en dosis de `UNFOLLOW_BATCH=7` |
| `X_NEVER_UNFOLLOW` | — | Cuentas protegidas para siempre |
| `MEMORY_ENABLED` | `true` | Memoria de contenido (anti-repetición + learnings) |
| `CRITIC_THRESHOLD` | `0.8` | Nota mínima del crítico para mandarte el post |
| `CRITIC_MAX_RETRIES` | `2` | Reescrituras máximas por borrador |
| `MCP_SERVERS` | `[]` | JSON con servidores MCP extra (arXiv, Product Hunt…) |
| `DRY_RUN` | `true` | `true` = no publica nada |

## ⏰ Cómo aprende (horarios + contenido)

1. Cada post aprobado se registra (hora, texto, tema, imagen) en `DATA_DIR/`
2. Un job diario refresca likes/RTs vía X API
3. Cada lunes, un LLM decide tus 2 mejores horas **y** extrae 3-5 lecciones de qué temas/ganchos rinden más en tu audiencia
4. El scheduler se reprograma solo y las lecciones se inyectan en la redacción; la memoria evita repetir temas ya cubiertos

## 📈 Crecimiento (máximo seguro)

- **Seguir**: hasta **25/día** en 4 tandas, con pausas aleatorias de **30-60s** entre follows; filtra bots (mín. 500 followers) y busca engagement real en el nicho
- **Dejar de seguir**: limpieza diaria en dosis de 7, máx. **50/semana**, solo sin follow-back tras 7 días
- **Comentar**: respuestas redactadas con tu voz a posts con tracción → llegan como "💬 Respuesta propuesta" y solo se publican con tu ✅

> [!WARNING]
> **Coste pay-per-use (2026):** cada follow cuesta $0.015 en la API de X (25/día ≈ $12/mes) y cada post **con link** cuesta $0.20 — por eso el agente nunca pone links en los posts. Subir `FOLLOW_PER_DAY` aumenta coste linealmente y las ráfagas >30-50/hora disparan el anti-spam de X.

## ☁️ Deploy en Railway (24/7)

1. **New Project → Deploy from GitHub repo** (detecta el `Dockerfile` solo)
2. En **Variables**, pega todo tu `.env`
3. Listo: corre 24/7 y te llegan los borradores al móvil

VPS alternativo: `docker build -t zanax . && docker run --env-file .env zanax`

## 🗺️ Roadmap

- [x] Grafo research → select → image → draft → critic
- [x] Imágenes nano banana 🍌
- [x] Timing aprendido con LLM
- [x] Growth: follow/unfollow/comentarios con límites seguros
- [x] Memoria de temas ya cubiertos (anti-repetición) + learnings de engagement
- [x] Crítico grounded que reescribe borradores antes de pedir aprobación
- [x] Fuentes extra vía MCP (arXiv, Product Hunt…)
- [ ] Hilos (threads) automáticos para tendencias grandes
- [ ] Dashboard de métricas en Telegram (`/stats`)

## ⚖️ Disclaimer

Automatización responsable: respeta las [reglas de la plataforma X](https://help.x.com/rules-and-policies/platform-rules). Los límites de este repo existen para proteger tu cuenta — no los subas de golpe. El contenido siempre se reformula con voz propia; nunca copies posts de terceros.

---

<div align="center">
Hecho con 🧠 + 🍌 · ¿Dudas? Abre un issue
</div>
