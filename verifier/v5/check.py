"""Verificador v5: v4 + topes al máximo seguro con pacing anti-ráfaga."""
import ast, pathlib, sys

root = pathlib.Path(__file__).resolve().parent.parent.parent
errors = []

# Hereda la esencia de v4: archivos, sintaxis, módulos clave
required = ["src/main.py", "src/agent/graph.py", "src/agent/llm.py",
            "src/agent/growth.py", "src/agent/timing.py", "src/agent/x_research.py",
            "src/agent/images.py", "src/approval.py", "src/x_client.py",
            "requirements.txt", ".env.example", "README.md"]
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

growth = (root / "src/agent/growth.py").read_text()
if 'FOLLOW_PER_DAY", "100"' not in growth:
    errors.append("growth.py FOLLOW_PER_DAY default != 100")
if 'UNFOLLOW_PER_WEEK", "50"' not in growth:
    errors.append("growth.py UNFOLLOW_PER_WEEK default != 50")
if "random.uniform(30, 60)" not in growth:
    errors.append("growth.py sin pacing anti-ráfaga (30-60s)")
if "FOLLOW_BATCH" not in growth:
    errors.append("growth.py sin FOLLOW_BATCH")

env = (root / ".env.example").read_text()
for key in ["FOLLOW_PER_DAY=100", "FOLLOW_BATCH=25", "UNFOLLOW_PER_WEEK=50",
            "X_NEVER_UNFOLLOW"]:
    if key not in env:
        errors.append(f"ENV falta {key}")

main = (root / "src/main.py").read_text()
for h in ["8, 12, 16, 20"]:
    if h not in main:
        errors.append("main.py sin 4 tandas de follow")
if "growth_prune" not in main:
    errors.append("main.py sin job de prune")

readme = (root / "README.md").read_text()
for word in ["100/día", "50/semana", "30-60s", "FOLLOW_BATCH"]:
    if word not in readme:
        errors.append(f"README no menciona {word}")

if errors:
    print("FAIL"); [print(" -", e) for e in errors]; sys.exit(1)
print("OK v5: topes al máximo seguro (100/día en 4 tandas con pacing) válidos")
