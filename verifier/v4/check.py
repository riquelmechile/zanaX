"""Verificador v4: v3 + LLM multi-provider y módulo de crecimiento."""
import ast, pathlib, sys

root = pathlib.Path(__file__).resolve().parent.parent.parent
errors = []

required = ["src/main.py", "src/agent/graph.py", "src/agent/tools.py",
            "src/agent/style.py", "src/agent/images.py", "src/agent/llm.py",
            "src/agent/x_research.py", "src/agent/timing.py", "src/agent/growth.py",
            "src/approval.py", "src/x_client.py",
            "requirements.txt", ".env.example", "Dockerfile", "railway.json", "README.md"]
for f in required:
    if not (root / f).exists():
        errors.append(f"FALTA {f}")

for py in root.rglob("*.py"):
    if "verifier" in py.parts:
        continue
    try:
        ast.parse(py.read_text())
    except SyntaxError as e:
        errors.append(f"SINTAXIS {py.name}: {e}")

env = (root / ".env.example").read_text()
for key in ["LLM_PROVIDER", "LLM_MODEL", "LLM_MODEL_DRAFT", "GOOGLE_API_KEY",
            "X_BEARER_TOKEN", "X_ACCOUNTS", "FOLLOW_PER_DAY", "UNFOLLOW_PER_WEEK",
            "X_NEVER_UNFOLLOW", "TELEGRAM_BOT_TOKEN", "DRY_RUN", "ENABLE_IMAGES",
            "DATA_DIR"]:
    if key not in env:
        errors.append(f"ENV falta {key}")

llmpy = (root / "src/agent/llm.py").read_text()
for prov in ["google", "openai", "anthropic"]:
    if prov not in llmpy:
        errors.append(f"llm.py sin provider {prov}")
if "gemini-2.5-flash" not in llmpy or "gemini-2.5-pro" not in llmpy:
    errors.append("llm.py sin defaults Gemini")

growth = (root / "src/agent/growth.py").read_text()
for fn in ["discover_accounts", "follow_top", "prune_following",
           "draft_replies", "mark_commented"]:
    if f"def {fn}" not in growth:
        errors.append(f"growth.py sin {fn}")
for guard in ["FOLLOW_PER_DAY", "UNFOLLOW_PER_WEEK", "X_NEVER_UNFOLLOW"]:
    if guard not in growth:
        errors.append(f"growth.py sin límite {guard}")

graph = (root / "src/agent/graph.py").read_text()
if 'llm("draft")' not in graph:
    errors.append("graph.py no usa rol draft")
if "fetch_account_posts" not in graph:
    errors.append("graph.py no usa x_research")

approval = (root / "src/approval.py").read_text()
if "x_client.reply" not in approval or "mark_commented" not in approval:
    errors.append("approval.py no maneja respuestas aprobadas")

xc = (root / "src/x_client.py").read_text()
if "def reply" not in xc or "in_reply_to_tweet_id" not in xc:
    errors.append("x_client.py sin reply")

main = (root / "src/main.py").read_text()
for job in ["growth_follow", "growth_prune", "draft_replies"]:
    if job not in main:
        errors.append(f"main.py sin job {job}")

req = (root / "requirements.txt").read_text()
for pkg in ["langchain-google-genai", "langchain-anthropic", "google-genai"]:
    if pkg not in req:
        errors.append(f"requirements.txt sin {pkg}")

readme = (root / "README.md").read_text()
for word in ["gemini-2.5-flash", "gemini-2.5-pro", "FOLLOW_PER_DAY",
             "X_NEVER_UNFOLLOW", "Crecimiento", "nano banana"]:
    if word not in readme:
        errors.append(f"README no menciona {word}")

if errors:
    print("FAIL"); [print(" -", e) for e in errors]; sys.exit(1)
print("OK v4: LLM multi-provider (Gemini), growth con topes y comentarios aprobados válidos")
