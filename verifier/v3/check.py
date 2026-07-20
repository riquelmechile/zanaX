"""Verificador v3: v2 + investigación en X, timing LLM y orden del grafo."""
import ast, pathlib, sys

root = pathlib.Path(__file__).resolve().parent.parent.parent
errors = []

required = ["src/main.py", "src/agent/graph.py", "src/agent/tools.py",
            "src/agent/style.py", "src/agent/images.py",
            "src/agent/x_research.py", "src/agent/timing.py",
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
for key in ["OPENAI_API_KEY", "X_API_KEY", "X_BEARER_TOKEN", "X_ACCOUNTS",
            "TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID", "DRY_RUN",
            "ENABLE_IMAGES", "GOOGLE_API_KEY", "IMAGE_MODEL", "DATA_DIR"]:
    if key not in env:
        errors.append(f"ENV falta {key}")

graph = (root / "src/agent/graph.py").read_text()
for node in ["research_node", "select_node", "image_node", "draft_node"]:
    if node not in graph:
        errors.append(f"graph.py sin nodo {node}")
# Orden requerido: research -> select -> image -> draft
for edge in ['"research", "select"', '"select", "image"', '"image", "draft"']:
    if edge not in graph:
        errors.append(f"graph.py sin arista {edge}")
if "fetch_account_posts" not in graph:
    errors.append("graph.py no usa x_research")

timing = (root / "src/agent/timing.py").read_text()
for fn in ["record_publish", "refresh_metrics", "analyze_best_hours", "current_hours"]:
    if f"def {fn}" not in timing:
        errors.append(f"timing.py sin {fn}")

main = (root / "src/main.py").read_text()
for feat in ["schedule_posts", "refresh_metrics", "analyze_best_hours", "day_of_week"]:
    if feat not in main:
        errors.append(f"main.py sin scheduler dinámico ({feat})")

approval = (root / "src/approval.py").read_text()
if "record_publish" not in approval:
    errors.append("approval.py no registra publicaciones")

xc = (root / "src/x_client.py").read_text()
if "media_upload" not in xc:
    errors.append("x_client.py no sube imágenes")

readme = (root / "README.md").read_text()
for word in ["Railway", "Telegram", "LangGraph", "nano banana", "X_ACCOUNTS",
             "timing", "Bearer Token"]:
    if word not in readme:
        errors.append(f"README no menciona {word}")

if errors:
    print("FAIL"); [print(" -", e) for e in errors]; sys.exit(1)
print("OK v3: X-research, timing LLM, grafo reordenado y scheduler dinámico válidos")
