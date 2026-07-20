"""Verificador v6: v5 + estándar de diseño del README (skill readme-designer)."""
import pathlib, sys

root = pathlib.Path(__file__).resolve().parent.parent.parent
errors = []

readme = (root / "README.md").read_text()

# Estándar de diseño según .claude/skills/readme-designer
if '<div align="center">' not in readme:
    errors.append("README sin hero centrado")
if readme.count("img.shields.io") < 4:
    errors.append("README con menos de 4 badges")
if "```mermaid" not in readme:
    errors.append("README sin diagrama Mermaid")
if "| Módulo | Qué hace | Archivo |" not in readme:
    errors.append("README sin tabla de features")
if "| Variable | Default | Para qué |" not in readme:
    errors.append("README sin tabla de configuración")
if readme.count("> [!WARNING]") < 2:
    errors.append("README sin bloques WARNING")
for section in ["Quickstart", "Cómo aprende tus horarios", "Roadmap", "Disclaimer"]:
    if section not in readme:
        errors.append(f"README sin sección {section}")
# Conserva los números clave de v5
for word in ["100/día", "50/semana", "30-60s", "FOLLOW_BATCH", "DRY_RUN"]:
    if word not in readme:
        errors.append(f"README no menciona {word}")
# Mermaid válido básico
if "flowchart" not in readme:
    errors.append("Mermaid sin flowchart")

skill = root / ".claude/skills/readme-designer/SKILL.md"
if not skill.exists():
    errors.append("FALTA la skill .claude/skills/readme-designer/SKILL.md")
elif "readme-designer" not in skill.read_text():
    errors.append("SKILL.md sin frontmatter name")

# Coherencia: variables documentadas existen en .env.example
env = (root / ".env.example").read_text()
for var in ["LLM_PROVIDER", "LLM_MODEL", "LLM_MODEL_DRAFT", "X_BEARER_TOKEN",
            "X_ACCOUNTS", "ENABLE_IMAGES", "POSTS_PER_DAY", "FOLLOW_PER_DAY",
            "FOLLOW_BATCH", "UNFOLLOW_PER_WEEK", "UNFOLLOW_BATCH",
            "X_NEVER_UNFOLLOW", "DRY_RUN"]:
    if var not in env:
        errors.append(f"Variable {var} documentada pero no está en .env.example")

if errors:
    print("FAIL"); [print(" -", e) for e in errors]; sys.exit(1)
print("OK v6: README con diseño profesional (hero, badges, mermaid, tablas) y coherente con .env")
