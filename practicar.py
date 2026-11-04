"""Practica de entrevistas en ingles.

Graba tu respuesta desde el microfono, la transcribe localmente con Whisper
y le pide a Claude (via el CLI de Claude Code, con tu suscripcion) correcciones
de gramatica, vocabulario y naturalidad. El resultado se guarda en
resultados/ultima_practica.md, que se reemplaza en cada ejecucion. Al final, lee en
voz alta y en ingles una recomendacion breve de tutor (solo se oye, no se guarda).

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
TUTOR_VOICE = "Samantha (Mejorada)"  # voz en ingles de macOS; lista con: say -v '?'

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

TUTOR_PROMPT = """You are a warm, encouraging English tutor talking to a Spanish-speaking systems \
engineer right after they practiced an interview answer. You receive the transcript and the \
written feedback. Reply with a short spoken recommendation in simple English: two or three \
sentences, under 50 words, focused on the single most useful thing to improve. \
Your reply will be read aloud by a text-to-speech voice, so use plain sentences only: \
no Markdown, lists, symbols or quotes."""


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


def llamar_claude(system_prompt: str, contenido: str) -> str:
    """Envia un mensaje a Claude con el CLI de Claude Code y devuelve su respuesta.

    Args:
        system_prompt: Instrucciones de sistema para Claude.
        contenido: Mensaje que recibe Claude por stdin.

    Returns:
        La respuesta de Claude como texto.

    Raises:
        RuntimeError: Si el CLI ``claude`` no esta instalado o la llamada falla.
    """
    if shutil.which("claude") is None:
        raise RuntimeError(
            "No se encontro el comando 'claude'. Instala Claude Code e inicia sesion."
        )

    # Sin herramientas, sin guardar la sesion y sin cargar configuracion de proyectos:
    # solo una respuesta de texto con nuestro system prompt.
    resultado = subprocess.run(
        [
            "claude",
            "-p",
            "--system-prompt",
            system_prompt,
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
        raise RuntimeError(f"Error al llamar a Claude:\n{resultado.stderr or resultado.stdout}")
    return resultado.stdout.strip()


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

    try:
        return llamar_claude(SYSTEM_PROMPT, contenido)
    except RuntimeError as error:
        sys.exit(str(error))


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


def leer_consejo(transcripcion: str, correcciones: str) -> None:
    """Lee en voz alta, en ingles, una recomendacion breve de tutor.

    Es un paso opcional al final de la practica: si falla, avisa y no interrumpe el script.

    Args:
        transcripcion: Texto de la respuesta hablada.
        correcciones: Correcciones devueltas por Claude.
    """
    if shutil.which("say") is None:
        print("No se encontro el comando 'say': se omite el consejo hablado.", file=sys.stderr)
        return

    print("\nPreparando el consejo de tu tutor...")
    contenido = f"Transcript of my answer:\n\n{transcripcion}\n\nFeedback:\n\n{correcciones}"
    try:
        consejo = llamar_claude(TUTOR_PROMPT, contenido)
    except RuntimeError as error:
        print(f"No se pudo generar el consejo hablado. {error}", file=sys.stderr)
        return

    print(f"\nTu tutor dice:\n{consejo}")
    # "--" evita que say interprete el texto como opciones.
    resultado = subprocess.run(["say", "-v", TUTOR_VOICE, "--", consejo], check=False)
    if resultado.returncode != 0:
        print(f"No se pudo leer el consejo con la voz {TUTOR_VOICE}.", file=sys.stderr)


def main() -> None:
    """Ejecuta el flujo completo: grabar, transcribir, corregir, guardar y leer el consejo."""
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

    leer_consejo(transcripcion, correcciones)


if __name__ == "__main__":
    main()
