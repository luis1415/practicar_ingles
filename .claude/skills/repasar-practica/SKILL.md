---
name: repasar-practica
description: Repasa la última práctica guardada en resultados/ultima_practica.md: resume los errores clave y propone ejercicios cortos para fijarlos. Usar cuando el usuario diga "repasa mi práctica", "qué hice mal", "ayúdame con mis errores" o "quiero ejercicios" después de correr practicar.py.
allowed-tools: Read
---

# Repasar la última práctica

1. Lee `resultados/ultima_practica.md`. Si no existe, dile al usuario que primero corra `uv run practicar.py` y termina.

2. Responde en español (los ejemplos van en inglés) con:

   **Los 3 errores más importantes:** los que más afectan cómo suena en una entrevista, priorizando los que parecen hábitos (tiempos verbales, plurales, preposiciones, frases traducidas literalmente del español). Para cada uno, la regla en una línea.

   **Ejercicios:** 5 frases cortas en inglés con un error del mismo tipo, numeradas, para que el usuario las corrija. No des las respuestas todavía.

   **Frase para repetir en voz alta:** una frase de la versión mejorada que use bien lo que falló.

3. Cuando el usuario responda los ejercicios, corrígelos uno por uno y explica brevemente los que falle.

No modifiques `resultados/ultima_practica.md`: se reemplaza en cada práctica.
