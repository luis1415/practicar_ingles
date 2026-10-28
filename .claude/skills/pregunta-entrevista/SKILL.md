---
name: pregunta-entrevista
description: Genera una pregunta realista de entrevista en inglés para un ingeniero de sistemas (behavioral, técnica o de system design) y da el comando para practicarla con practicar.py. Usar cuando el usuario pida "dame una pregunta", "quiero practicar", "pregunta de entrevista" o un tema concreto (ej. "pregunta sobre microservicios").
argument-hint: "[tipo o tema, ej. behavioral | technical | system design | kubernetes]"
---

# Pregunta de entrevista

El usuario es un ingeniero de sistemas hispanohablante que practica entrevistas en inglés.

1. Elige **una** pregunta en inglés según `$ARGUMENTS`:
   - Sin argumentos: alterna entre behavioral, técnica y de system design.
   - `behavioral`: preguntas tipo "Tell me about a time…" (conflictos, liderazgo, fracasos, plazos).
   - `technical` o un tema (ej. `kubernetes`, `bases de datos`): una pregunta conceptual que se responda hablando en 1–3 minutos, no un ejercicio de código.
   - `system design`: un diseño acotado (ej. "How would you design a URL shortener?").
   Si en `resultados/ultima_practica.md` aparece la pregunta anterior, no la repitas.

2. Responde con este formato, en español salvo la pregunta:

   **Pregunta:** <pregunta en inglés>

   **Qué evalúa el entrevistador:** 1–2 líneas.

   **Estructura sugerida:** 3–4 viñetas (para behavioral, el método STAR).

   **Vocabulario útil:** 4–6 expresiones en inglés que encajen en la respuesta.

   **Para practicarla, corre en tu terminal:**
   ```bash
   uv run practicar.py --pregunta "<pregunta en inglés>"
   ```

3. No ejecutes `practicar.py` tú mismo: necesita el micrófono y que el usuario presione Enter en su terminal.
