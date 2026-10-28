"""Practica de entrevistas en ingles.

Graba tu respuesta desde el microfono, la transcribe localmente con Whisper
y le pide a Claude (via el CLI de Claude Code, con tu suscripcion) correcciones
de gramatica, vocabulario y naturalidad. El resultado se guarda en
resultados/ultima_practica.md, que se reemplaza en cada ejecucion.

Uso:
    uv run practicar.py
    uv run practicar.py --pregunta "Tell me about yourself"
"""

import argparse
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path

import numpy as np
import numpy.typing as npt
import sounddevice as sd
from faster_whisper import WhisperModel

SAMPLE_RATE = 16_000  # Whisper trabaja a 16 kHz
WHISPER_MODEL = "small.en"  # "base.en" es mas rapido, "medium.en" mas preciso
RESULT_FILE = Path(__file__).parent / "resultados" / "ultima_practica.md"

SYSTEM_PROMPT = """You are an English coach helping a Spanish-speaking systems engineer \
prepare for job interviews in English. You receive a transcript of a spoken answer.

Give feedback in Spanish (the corrected sentences stay in English), using this Markdown structure:

### Errores gramaticales
A list: original fragment -> corrected fragment, plus a one-line explanation. \
Ignore punctuation and capitalization: they come from the transcriber, not from the speaker.

### Vocabulario y naturalidad
Phrases that are correct but sound unnatural or too literal from Spanish, with how a native \
speaker would say them in an interview. Include technical vocabulary when relevant.

### Version mejorada
The full answer rewritten in natural, professional English, keeping the speaker's ideas and level \
(do not invent experience).

### Consejo para la entrevista
One or two short tips on the content or structure of the answer (e.g. STAR method), if useful.

If the answer has no errors in a section, say so briefly. Be direct and concrete."""


def grabar() -> npt.NDArray[np.float32]:
    """Graba del microfono hasta que el usuario presiona Enter.

    Returns:
        Audio mono a ``SAMPLE_RATE`` Hz en float32. Vacio si no se capto nada.
    """
    bloques: list[npt.NDArray[np.float32]] = []

    def callback(
        indata: npt.NDArray[np.float32],
        frames: int,
        time: object,  # struct CFFI con marcas de tiempo; no se usa
        status: sd.CallbackFlags,
    ) -> None:
        """Acumula cada bloque de audio que entrega sounddevice."""
        if status:
            print(status, file=sys.stderr)
        bloques.append(indata.copy())

    input("Presiona Enter para empezar a grabar...")
    with sd.InputStream(samplerate=SAMPLE_RATE, channels=1, dtype="float32", callback=callback):
        input("Grabando... habla en ingles y presiona Enter para terminar.")

    if not bloques:
        return np.zeros(0, dtype=np.float32)
    return np.concatenate(bloques).flatten()


def transcribir(audio: npt.NDArray[np.float32]) -> str:
    """Transcribe el audio a texto en ingles con Whisper, localmente.

    Args:
        audio: Audio mono a ``SAMPLE_RATE`` Hz en float32.

    Returns:
        La transcripcion completa, o una cadena vacia si no se detecto voz.
    """
    print(f"Transcribiendo con Whisper ({WHISPER_MODEL})...")
    modelo = WhisperModel(WHISPER_MODEL, device="cpu", compute_type="int8")
    # Sin condicionamiento ni prompt, Whisper "corrige" menos lo que dijiste.
    segmentos, _ = modelo.transcribe(
        audio, language="en", condition_on_previous_text=False, vad_filter=True
    )
    return " ".join(s.text.strip() for s in segmentos).strip()


def corregir(transcripcion: str, pregunta: str | None) -> str:
    """Pide a Claude correcciones de la respuesta usando el CLI de Claude Code.

    Args:
        transcripcion: Texto de la respuesta hablada.
        pregunta: Pregunta de entrevista que se respondio, si se indico.

    Returns:
        Las correcciones en Markdown.

    Raises:
        SystemExit: Si el CLI ``claude`` no esta instalado o la llamada falla.
    """
    print("Pidiendo correcciones a Claude...")
    contenido = f"Transcript of my answer:\n\n{transcripcion}"
    if pregunta:
        contenido = f"Interview question: {pregunta}\n\n{contenido}"

    if shutil.which("claude") is None:
        sys.exit("No se encontro el comando 'claude'. Instala Claude Code e inicia sesion.")

    # Sin herramientas, sin guardar la sesion y sin cargar configuracion de proyectos:
    # solo una respuesta de texto con nuestro system prompt.
    resultado = subprocess.run(
        [
            "claude",
            "-p",
            "--system-prompt",
            SYSTEM_PROMPT,
            "--tools",
            "",
            "--no-session-persistence",
            "--setting-sources",
            "",
        ],
        input=contenido,
        capture_output=True,
        text=True,
        cwd=tempfile.gettempdir(),
        check=False,
    )
    if resultado.returncode != 0:
        sys.exit(f"Error al llamar a Claude:\n{resultado.stderr or resultado.stdout}")
    return resultado.stdout.strip()


def guardar(transcripcion: str, correcciones: str, pregunta: str | None) -> Path:
    """Guarda la practica en ``RESULT_FILE``, reemplazando la anterior.

    Args:
        transcripcion: Texto de la respuesta hablada.
        correcciones: Correcciones devueltas por Claude.
        pregunta: Pregunta de entrevista que se respondio, si se indico.

    Returns:
        La ruta del archivo guardado.
    """
    RESULT_FILE.parent.mkdir(exist_ok=True)
    ahora = datetime.now()
    archivo = RESULT_FILE
    partes = [f"# Practica {ahora:%Y-%m-%d %H:%M}\n"]
    if pregunta:
        partes.append(f"**Pregunta:** {pregunta}\n")
    partes.append(f"## Lo que dije\n\n{transcripcion}\n")
    partes.append(f"## Correcciones\n\n{correcciones}\n")
    archivo.write_text("\n".join(partes), encoding="utf-8")
    return archivo


def main() -> None:
    """Ejecuta el flujo completo: grabar, transcribir, corregir y guardar."""
    parser = argparse.ArgumentParser(description="Practica entrevistas en ingles.")
    parser.add_argument("--pregunta", "-p", help="Pregunta de entrevista que vas a responder")
    args = parser.parse_args()

    if args.pregunta:
        print(f"\nPregunta: {args.pregunta}\n")

    audio = grabar()
    if len(audio) < SAMPLE_RATE:  # menos de 1 segundo
        sys.exit("La grabacion es demasiado corta.")

    transcripcion = transcribir(audio)
    if not transcripcion:
        sys.exit("No se detecto voz. Revisa el permiso de microfono de tu terminal.")
    print(f"\nLo que dijiste:\n{transcripcion}\n")

    correcciones = corregir(transcripcion, args.pregunta)
    print(correcciones)

    archivo = guardar(transcripcion, correcciones, args.pregunta)
    print(f"\nGuardado en {archivo}")


if __name__ == "__main__":
    main()
