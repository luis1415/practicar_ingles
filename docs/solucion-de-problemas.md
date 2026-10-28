# Solución de problemas

### "No se detectó voz" o la transcripción sale vacía
La app desde la que ejecutas el script no tiene permiso de micrófono. Actívalo en
**Ajustes del Sistema → Privacidad y seguridad → Micrófono** para Terminal, iTerm o
VS Code, y reinicia esa app.

Para comprobar qué micrófono se usa:

```bash
uv run python -c "import sounddevice as sd; print(sd.query_devices())"
```

### La transcripción "corrige" mis errores
Whisper tiende a escribir lo que se esperaría oír, no exactamente lo que dijiste, así que
algunos errores (por ejemplo, "I have lead" → "I have") pueden no llegar a Claude. Si pasa
seguido, cambia `WHISPER_MODEL` a `medium.en` en `practicar.py`, y habla a un ritmo normal,
sin pausas largas a mitad de frase.

### "No se encontró el comando 'claude'"
Instala Claude Code e inicia sesión una vez de forma interactiva:

```bash
claude
```

Luego comprueba que `claude --version` funciona en la misma terminal donde corres el script.

### "Error al llamar a Claude"
El mensaje incluye la salida de Claude Code. Las causas habituales son:
- la sesión de Claude Code expiró: abre `claude` e inicia sesión de nuevo;
- alcanzaste el límite de uso de tu suscripción: espera a que se renueve;
- no hay conexión a internet.

### `onnxruntime` no se instala ("doesn't have a source distribution or wheel")
Pasa en Macs Intel si se elimina la sección `[tool.uv]` de `pyproject.toml`. Restáurala:

```toml
[tool.uv]
required-environments = ["sys_platform == 'darwin' and platform_machine == 'x86_64'"]
```

y vuelve a correr `uv sync`.

### Aviso "unauthenticated requests to the HF Hub"
Es solo un aviso al descargar el modelo de Whisper desde Hugging Face. Se puede ignorar.

### Aviso "VIRTUAL_ENV ... does not match the project environment"
Tienes otro entorno virtual activo (por ejemplo, de pyenv). uv lo ignora y usa `.venv/`
del proyecto, así que no afecta. Para que desaparezca, ejecuta `deactivate` antes.

### Los skills no aparecen en Claude Code
Abre Claude Code desde la carpeta del proyecto. Si ya estaba abierto cuando se crearon
los skills, inicia una sesión nueva.
