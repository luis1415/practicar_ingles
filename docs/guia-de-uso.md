# Guía de uso

## Requisitos

| Requisito | Para qué | Cómo comprobarlo |
|---|---|---|
| macOS con micrófono | Grabar la respuesta | — |
| [uv](https://docs.astral.sh/uv/) | Gestionar Python y dependencias | `uv --version` |
| [Claude Code](https://claude.com/claude-code) con sesión iniciada | Generar las correcciones | `claude --version` |
| ~1 GB libre | Modelo de Whisper y entorno virtual | — |

No hace falta una API key de Anthropic. Las correcciones se piden a través de Claude Code
y consumen el límite de uso de tu suscripción de Claude.

## Instalación

```bash
cd entrevistas_en_ingles_py
uv sync
```

`uv sync` crea `.venv/` con Python 3.11 y las dependencias de `uv.lock`.

La primera ejecución:
- descarga el modelo de Whisper `small.en` (~500 MB) a `~/.cache/huggingface/`;
- hace que macOS pida permiso de micrófono para la app desde la que lo ejecutas
  (Terminal, iTerm o VS Code). Acéptalo, o actívalo en
  **Ajustes del Sistema → Privacidad y seguridad → Micrófono**.

## Practicar una respuesta

```bash
uv run practicar.py --pregunta "Tell me about yourself"
```

1. Presiona **Enter** para empezar a grabar.
2. Responde en inglés como lo harías en la entrevista.
3. Presiona **Enter** otra vez para terminar.
4. Espera la transcripción (unos segundos) y las correcciones (entre 20 segundos y 1 minuto).

`--pregunta` (o `-p`) es opcional, pero conviene usarlo: con la pregunta, Claude puede
opinar también sobre si tu respuesta la contesta bien. Sin ella, solo revisa el idioma.

## El resultado

Se muestra en la terminal y se guarda en `resultados/ultima_practica.md`. Ese archivo se
**reemplaza en cada práctica**, así que no se acumulan archivos. Si quieres conservar
una práctica, cópiala antes de la siguiente.

Contiene:

- **Lo que dije**: la transcripción de tu respuesta.
- **Errores gramaticales**: fragmento original → corregido, con una explicación corta.
- **Vocabulario y naturalidad**: frases correctas que suenan traducidas del español, y
  cómo las diría un nativo en una entrevista.
- **Versión mejorada**: tu respuesta reescrita en inglés profesional, con tus mismas ideas.
- **Consejo para la entrevista**: sugerencias sobre el contenido o la estructura (por
  ejemplo, el método STAR).

## Skills de Claude Code

Si abres Claude Code dentro de esta carpeta, tienes dos comandos extra:

| Comando | Qué hace |
|---|---|
| `/pregunta-entrevista [tipo o tema]` | Te da una pregunta (`behavioral`, `technical`, `system design` o un tema como `kubernetes`), qué evalúa el entrevistador, una estructura sugerida, vocabulario útil y el comando para practicarla. |
| `/repasar-practica` | Lee `resultados/ultima_practica.md`, resume tus 3 errores principales y te pone 5 frases para corregir. |

Una sesión típica:

```text
/pregunta-entrevista behavioral        → en Claude Code
uv run practicar.py --pregunta "..."   → en tu terminal
/repasar-practica                      → en Claude Code
```

`practicar.py` se ejecuta siempre en tu terminal: necesita el micrófono y que presiones
Enter, así que Claude Code no puede correrlo por ti.

## Ajustes

Las constantes están al principio de `practicar.py`:

| Constante | Valor por defecto | Cuándo cambiarla |
|---|---|---|
| `WHISPER_MODEL` | `small.en` | `base.en` si la transcripción es lenta; `medium.en` si se pierden palabras o errores (más lento, ~1.5 GB). |
| `RESULT_FILE` | `resultados/ultima_practica.md` | Si quieres guardar el resultado en otra carpeta. |
| `SYSTEM_PROMPT` | Instrucciones del coach | Para cambiar el idioma de las explicaciones, las secciones o el nivel de exigencia. |
