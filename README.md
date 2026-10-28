# Entrevistas en inglés

Herramienta para practicar entrevistas de trabajo en inglés: grabas tu respuesta,
Whisper la transcribe en tu máquina y Claude te devuelve correcciones de gramática,
vocabulario y una versión mejorada de lo que dijiste.

## Inicio rápido

Requisitos: macOS, [uv](https://docs.astral.sh/uv/) y [Claude Code](https://claude.com/claude-code)
con sesión iniciada. No necesitas API key.

```bash
uv sync
uv run practicar.py --pregunta "Tell me about yourself"
```

Presiona Enter para empezar a grabar, responde en inglés y presiona Enter para terminar.
El resultado se muestra en la terminal y se guarda en `resultados/ultima_practica.md`,
que se reemplaza en cada práctica.

Desde Claude Code, en esta carpeta:
- `/pregunta-entrevista [tipo o tema]`: te propone una pregunta para practicar.
- `/repasar-practica`: repasa tus errores de la última práctica con ejercicios.

## Documentación

- [Guía de uso](docs/guia-de-uso.md): instalación, flujo de práctica, el archivo de resultado, skills y ajustes.
- [Arquitectura](docs/arquitectura.md): cómo funciona el script, decisiones de diseño y dependencias.
- [Solución de problemas](docs/solucion-de-problemas.md): micrófono, transcripción, Claude Code e instalación.

## Desarrollo

El código sigue PEP 8 con [ruff](https://docs.astral.sh/ruff/) y se verifican los tipos con
[mypy](https://mypy.readthedocs.io/) en modo estricto (configurados en `pyproject.toml`):

```bash
uv run ruff format .   # formatea el código
uv run ruff check .    # lint: PEP 8, imports, docstrings, anotaciones
uv run mypy .          # verificación de tipos
```

Antes de hacer push, `/descripcion-pr [rama base]` en Claude Code verifica ruff y mypy y genera
la descripción del PR en `.git/PR_DESCRIPTION.md`.
