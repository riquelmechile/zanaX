"""Verificador v1: compila todo el código y chequea estructura/config."""
import ast, pathlib, sys

root = pathlib.Path(__file__).resolve().parent.parent.parent
errors = []

required = ["src/main.py", "src/agent/graph.py", "src/agent/tools.py",
            "src/agent/style.py", "src/approval.py", "src/x_client.py",
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
for key in ["OPENAI_API_KEY", "X_API_KEY", "TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID", "DRY_RUN"]:
    if key not in env:
        errors.append(f"ENV falta {key}")

readme = (root / "README.md").read_text()
for word in ["Railway", "Telegram", "LangGraph", "DRY_RUN"]:
    if word not in readme:
        errors.append(f"README no menciona {word}")

if errors:
    print("FAIL"); [print(" -", e) for e in errors]; sys.exit(1)
print("OK: estructura, sintaxis y configuración válidas")
