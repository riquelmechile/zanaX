# zanaX 🤖🍌

> Agente autónomo de X que investiga tendencias de AI/dev cada día (incluidas cuentas clave dentro de X), escribe posts con tu propia voz, genera imágenes con nano banana (Gemini), aprende tus mejores horarios de publicación con un LLM, hace crecer tu red (seguir/dejar de seguir/comentar con límites seguros) y te pide aprobación por Telegram antes de publicar. Construido con LangGraph.

## Arquitectura (grafo LangGraph)

```
research ──► select ──► image ──► draft ──► [aprobación Telegram] ──► publish (X API)
   │            │          │         │              │                       │
HN+GitHub   LLM elige  nano banana  LLM con   Botones ✅/❌/✏️        tweepy v2
+Reddit+X   lo mejor   (opcional)  tu estilo   en tu chat          (o DRY_RUN)
```

- `src/agent/tools.py` — fuentes: Hacker News API, GitHub Trending RSS, Reddit JSON, DuckDuckGo News.
- `src/agent/x_research.py` — lee las cuentas de X que publican a diario (configurables en `X_ACCOUNTS`) y las convierte en tendencias rankeadas por engagement.
- `src/agent/timing.py` — **timing inteligente**: registra cada post publicado, refresca sus métricas a diario y un LLM re-analiza cada lunes cuáles son tus mejores horas; el scheduler se reprograma solo.
- `src/agent/style.py` — **tu voz**: guía de estilo + few-shot con tuits tuyos. Edítalo primero.
- `src/agent/images.py` — generación de imágenes con **nano banana** (`gemini-2.5-flash-image`). Opcional, se activa con `ENABLE_IMAGES=true`.
- `src/agent/graph.py` — grafo LangGraph (research → select → image → draft).
- `src/agent/llm.py` — LLM multi-provider con dos roles: **barato** (`LLM_MODEL`, def. `gemini-2.5-flash`) para selección/análisis y **draft** (`LLM_MODEL_DRAFT`, def. `gemini-2.5-pro`) para redactar posts y comentarios. Provider: `google` (def.), `openai` o `anthropic`.
- `src/agent/growth.py` — **crecimiento**: descubre cuentas afines al nicho, las sigue (tope `FOLLOW_PER_DAY`, def. 10/día), deja de seguir las que no devuelven el follow en 7 días (tope semanal + whitelist `X_NEVER_UNFOLLOW`) y redacta respuestas a posts con tracción que **siempre requieren tu ✅ en Telegram**.
- `src/approval.py` — bot de Telegram: envía borradores y respuestas propuestas (con imagen si la hay); ✅ publica, ❌ descarta, o responde citando el mensaje con tu versión editada. Cada publicación queda registrada para el análisis de timing.
- `src/x_client.py` — publicación con X API v2 (posts, respuestas e imagen vía media upload). `DRY_RUN=true` = modo prueba.
- `src/main.py` — scheduler **dinámico** (horas aprendidas por el LLM) + jobs de crecimiento + polling de Telegram en un solo proceso.

## Cómo aprende los horarios

1. Cada vez que apruebas un post se guarda en `DATA_DIR/published.json` (hora, texto, si llevaba imagen).
2. Un job diario consulta likes/RTs de esos posts vía X API (`X_BEARER_TOKEN`).
3. Cada lunes un LLM cruza ese historial con heurísticas del nicho AI/dev y decide las 2 mejores horas; el scheduler se reconfigura solo.
4. Sin datos todavía → usa heurísticas (9:30 y 18:00).

## Crecimiento automático (con límites seguros)

- **Seguir**: cada mañana descubre cuentas del nicho con engagement real (filtra bots: mín. 500 seguidores) y sigue hasta `FOLLOW_PER_DAY`. Te avisa por Telegram.
- **Dejar de seguir**: cada domingo limpia cuentas que no devolvieron el follow en 7 días (máx. `UNFOLLOW_PER_WEEK`; las de `X_NEVER_UNFOLLOW` jamás se tocan).
- **Comentar**: en cada ciclo redacta respuestas con tu voz a posts con tracción de las cuentas vigiladas — llegan a Telegram como "💬 Respuesta propuesta" y solo se publican si las apruebas.
- ⚠️ Los topes existen porque X suspende cuentas por follow churn y comentarios masivos automatizados. No los subas de golpe.

## Setup (15 min)

1. **Telegram**: crea bot con [@BotFather](https://t.me/BotFather) (token) y obtén tu `chat_id` con [@userinfobot](https://t.me/userinfobot).
2. **X API**: cuenta en [developer.x.com](https://developer.x.com), plan **Basic** (necesario para postear). App con permisos Read & Write y copia las 4 claves + el **Bearer Token** (para investigar cuentas y métricas).
3. **LLM**: por defecto **Gemini** — usa la misma `GOOGLE_API_KEY` del paso 4 y no necesitas nada más. Para OpenAI o Claude cambia `LLM_PROVIDER` y añade su key.
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
