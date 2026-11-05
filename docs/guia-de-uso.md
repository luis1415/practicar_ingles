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
uv run practice --question "Tell me about yourself"
```

1. Presiona **Enter** para empezar a grabar.
2. Responde en inglés como lo harías en la entrevista.
3. Presiona **Enter** otra vez para terminar.
4. Espera la transcripción (unos segundos) y las correcciones (entre 20 segundos y 1 minuto).

`--question` (o `-q`) es opcional, pero conviene usarlo: con la pregunta, Claude puede
opinar también sobre si tu respuesta la contesta bien. Sin ella, solo revisa el idioma.

## Conversar con el tutor en una ventana

```bash
uv run tutor
```

La ventana está en inglés y se adapta al modo claro u oscuro de tu Mac.

1. En el panel izquierdo, escribe un tema o una pregunta si quieres, en **Topic or question**.
2. Elige la cantidad de respuestas con **−** y **+** en **Turns**: de 1 a 10, con 3 por defecto.
   No se puede cambiar una vez que empieza la entrevista.
3. Presiona **Start interview**. El tutor lee su pregunta en voz alta.
4. Responde con **Record** y **Stop and send**, o escribe y presiona **Send** o Enter (Shift+Enter
   agrega una línea). Puedes elegir en cada turno.
5. Las correcciones de cada respuesta aparecen a la derecha, en español, mientras la entrevista sigue.
6. Al terminar los turnos, el tutor lee un consejo final y se guarda el resultado. Ábrelo con
   **Open report**.

Si una pregunta del tutor falla, tu respuesta vuelve al cuadro de texto para que la envíes otra vez.

El resultado usa el mismo archivo que `uv run practice`, así que también reemplaza la práctica
anterior y `/repasar-practica` funciona igual.

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

Al final, después de guardar, un tutor lee en voz alta y en inglés una recomendación breve.
Esa recomendación se muestra en la terminal, pero no se guarda en el archivo.

## Skills de Claude Code

Si abres Claude Code dentro de esta carpeta, tienes dos comandos extra:

| Comando | Qué hace |
|---|---|
| `/pregunta-entrevista [tipo o tema]` | Te da una pregunta (`behavioral`, `technical`, `system design` o un tema como `kubernetes`), qué evalúa el entrevistador, una estructura sugerida, vocabulario útil y el comando para practicarla. |
| `/repasar-practica` | Lee `resultados/ultima_practica.md`, resume tus 3 errores principales y te pone 5 frases para corregir. |

Una sesión típica:

```text
/pregunta-entrevista behavioral        → en Claude Code
uv run practice --question "..."       → en tu terminal
/repasar-practica                      → en Claude Code
```

`uv run practice` y `uv run tutor` se ejecutan siempre fuera de Claude Code: usan el micrófono y
necesitan que interactúes con ellos.

## Ajustes

Los ajustes están en `src/interview_coach/config.py`:

| Constante | Valor por defecto | Cuándo cambiarla |
|---|---|---|
| `WHISPER_MODEL` | `small.en` | `base.en` si la transcripción es lenta; `medium.en` si se pierden palabras o errores (más lento, ~1.5 GB). |
| `REPORT_FILE` | `resultados/ultima_practica.md` | Si quieres guardar el resultado en otra carpeta. |
| `TUTOR_VOICE` | `Samantha (Mejorada)` | Para usar otra voz en inglés. Puedes ver las disponibles con `say -v '?'`. |
| `DEFAULT_TURNS`, `MIN_TURNS`, `MAX_TURNS` | `3`, `1`, `10` | Para cambiar los turnos por defecto o el rango del selector. |

Los prompts están en `src/interview_coach/prompts.py`:

| Constante | Cuándo cambiarla |
|---|---|
| `FEEDBACK_PROMPT` | Para cambiar el idioma de las explicaciones, las secciones o el nivel de exigencia del Markdown. |
| `SPOKEN_ADVICE_PROMPT` | Para cambiar el tono o la duración de la recomendación hablada. |
| `INTERVIEWER_PROMPT` | Para cambiar cómo pregunta el tutor. |
| `TURN_CORRECTION_PROMPT` | Para cambiar las correcciones de cada turno. |

Los colores y tamaños de la ventana están en `src/interview_coach/gui/theme.py`.
