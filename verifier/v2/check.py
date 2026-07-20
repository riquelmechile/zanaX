"""Verificador v2: v1 + módulo de imágenes (nano banana) y su configuración."""
import ast, pathlib, sys

root = pathlib.Path(__file__).resolve().parent.parent.parent
errors = []

required = ["src/main.py", "src/agent/graph.py", "src/agent/tools.py",
            "src/agent/style.py", "src/agent/images.py",
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
for key in ["OPENAI_API_KEY", "X_API_KEY", "TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID",
            "DRY_RUN", "ENABLE_IMAGES", "GOOGLE_API_KEY", "IMAGE_MODEL"]:
    if key not in env:
        errors.append(f"ENV falta {key}")

graph = (root / "src/agent/graph.py").read_text()
for node in ["research_node", "select_node", "draft_node", "image_node"]:
    if node not in graph:
        errors.append(f"graph.py sin nodo {node}")

xc = (root / "src/x_client.py").read_text()
if "media_upload" not in xc:
    errors.append("x_client.py no sube imágenes")

req = (root / "requirements.txt").read_text()
if "google-genai" not in req:
    errors.append("requirements.txt sin google-genai")

readme = (root / "README.md").read_text()
for word in ["Railway", "Telegram", "LangGraph", "DRY_RUN", "nano banana", "ENABLE_IMAGES"]:
    if word not in readme:
        errors.append(f"README no menciona {word}")

if errors:
    print("FAIL"); [print(" -", e) for e in errors]; sys.exit(1)
print("OK v2: estructura, sintaxis, imágenes (nano banana) y configuración válidas")
