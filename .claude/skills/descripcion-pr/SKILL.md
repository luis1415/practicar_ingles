---
name: descripcion-pr
description: Genera la descripción de un pull request a partir de los commits y el diff de la rama actual, después de verificar que ruff y mypy pasan. Usar antes de hacer push o abrir un PR, cuando el usuario diga "descripción del PR", "prepara el PR", "voy a hacer push" o "qué pongo en el PR".
argument-hint: "[rama base, por defecto main]"
allowed-tools: Bash(git status:*), Bash(git log:*), Bash(git diff:*), Bash(git branch:*), Bash(git rev-parse:*), Bash(git merge-base:*), Bash(uv run ruff:*), Bash(uv run mypy:*), Read, Write
---

# Descripción del PR

1. **Rama base:** usa `$ARGUMENTS` si viene; si no, `main`. Si la base no existe localmente (por ejemplo, el repo aún no tiene commits en `main`), compara contra el primer commit de la rama y avísalo.

2. **Revisa el estado:** corre `git status`. Si hay cambios sin commitear, avísale al usuario que no quedarán en el PR y pregunta si quiere commitearlos antes de seguir.

3. **Verifica la calidad:** corre `uv run ruff format --check .`, `uv run ruff check .` y `uv run mypy .`. Si alguno falla, muestra los errores y recomienda corregirlos antes del push. Aun así genera la descripción si el usuario lo pide.

4. **Reúne el contexto:**
   - `git log --oneline <base>..HEAD` para los commits.
   - `git diff --stat <base>...HEAD` y `git diff <base>...HEAD` para los cambios. Lee los archivos completos solo si el diff no basta para entender el porqué.

5. **Escribe la descripción en español** (los nombres de código, comandos y archivos quedan como están), con este formato:

   ```markdown
   ## Resumen
   1–3 líneas: qué cambia y por qué, desde el punto de vista de quien usa la herramienta.

   ## Cambios
   - Viñetas agrupadas por tema, no por archivo. Menciona decisiones no obvias
     (por ejemplo, un cambio de versión de Python o una dependencia nueva) y su motivo.

   ## Cómo probarlo
   - Comandos concretos (`uv sync`, `uv run practicar.py --pregunta "..."`, `uv run ruff check .`).
   - Si algo necesita micrófono o Claude Code con sesión iniciada, dilo.

   ## Notas
   Solo si hay riesgos, pasos manuales o trabajo pendiente. Si no, omite la sección.

   🤖 Generated with [Claude Code](https://claude.com/claude-code)
   ```

   Título sugerido aparte: corto (menos de 70 caracteres), en imperativo, sin punto final.

   Describe solo lo que está en el diff: no inventes pruebas que no se corrieron ni cambios que no existen.

6. **Guarda y muestra:** escribe la descripción en `.git/PR_DESCRIPTION.md` (dentro de `.git` nunca se commitea) y muéstrala al usuario junto con el título. Luego indícale cómo usarla:

   ```bash
   git push -u origin <rama>
   gh pr create --base <base> --title "<título>" --body-file .git/PR_DESCRIPTION.md
   ```

7. No hagas `git push` ni crees el PR tú mismo: solo si el usuario lo pide explícitamente después de revisar la descripción.
