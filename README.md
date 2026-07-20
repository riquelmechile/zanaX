# zanaX 🤖🍌

> Agente autónomo de X que investiga tendencias de AI/dev cada día, escribe posts con tu propia voz, genera imágenes con nano banana (Gemini) y te pide aprobación por Telegram antes de publicar. Construido con LangGraph.

## Arquitectura (grafo LangGraph)

```
research ──► select ──► draft ──► image ──► [aprobación Telegram] ──► publish (X API)
   │            │          │         │              │                       │
HN+GitHub   LLM elige   LLM con   nano banana   Botones ✅/❌/✏️        tweepy v2
+Reddit     lo mejor    tu estilo  (opcional)    en tu chat          (o DRY_RUN)
```

- `src/agent/tools.py` — fuentes: Hacker News API, GitHub Trending RSS, Reddit JSON, DuckDuckGo News.
- `src/agent/style.py` — **tu voz**: guía de estilo + few-shot con tuits tuyos. Edítalo primero.
- `src/agent/images.py` — generación de imágenes con **nano banana** (`gemini-2.5-flash-image`). Opcional, se activa con `ENABLE_IMAGES=true`.
- `src/agent/graph.py` — grafo LangGraph (research → select → draft → image).
- `src/approval.py` — bot de Telegram: envía el borrador (con imagen si la hay); ✅ publica, ❌ descarta, o responde citando el mensaje con tu versión editada.
- `src/x_client.py` — publicación con X API v2 (sube imagen vía media upload). `DRY_RUN=true` = modo prueba.
- `src/main.py` — scheduler (9:30 y 18:00 por defecto) + polling de Telegram en un solo proceso.

## Setup (15 min)

1. **Telegram**: crea bot con [@BotFather](https://t.me/BotFather) (token) y obtén tu `chat_id` con [@userinfobot](https://t.me/userinfobot).
2. **X API**: cuenta en [developer.x.com](https://developer.x.com), plan **Basic** (necesario para postear). App con permisos Read & Write y copia las 4 claves.
3. **OpenAI**: API key (o cambia `ChatOpenAI` por otro provider en `graph.py`).
4. **Imágenes (opcional)**: API key gratis en [Google AI Studio](https://aistudio.google.com/apikey) y pon `ENABLE_IMAGES=true`.
5. **Tu estilo**: edita `src/agent/style.py` → pon 3-5 tuits reales tuyos en `MY_TWEETS`.

```bash
cp .env.example .env   # rellena las claves
pip install -r requirements.txt
python -m src.main     # arranca; ejecuta un ciclo de prueba al iniciar
```

Con `DRY_RUN=true` recibirás los borradores en Telegram sin publicar nada.
Cuando te gusten, pon `DRY_RUN=false`.

## Deploy en Railway (24/7)

1. En Railway: **New Project → Deploy from GitHub repo** (detecta el `Dockerfile` solo).
2. En **Variables**, pega todas las de `.env`.
3. Listo: el scheduler corre en la nube y te llegan borradores al móvil.

Alternativa VPS: `docker build -t zanax . && docker run --env-file .env zanax`

## Consejos para crecer (lo que el agente no hace solo)

- El agente te da munición; el crecimiento real viene de **responder y conectar** con cuentas grandes del nicho AI/dev.
- Revisa los borradores y edítalos a menudo al principio: cada edición tuya es un ejemplo más para `MY_TWEETS`.
- Los posts con imagen suelen tener más alcance: activa `ENABLE_IMAGES` cuando tengas la key de Google.
- Constancia > viralidad: 1-2 posts diarios con opinión propia durante meses.
