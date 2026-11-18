"""voces.py — Qué se dice en voz alta (sin pygame). Ver specs/13_dia_y_voz.md.

Reúne en un solo lugar TODAS las frases con voz del juego y sabe dónde están
sus audios. Lo usan tres módulos:

  * audio_manager.py → busca el audio de cada frase (ruta_audio) y elige la voz
                       en español para el modo "robot" (elegir_voz);
  * generar_voces.py → genera los audios .wav a partir de manifest();
  * main.py          → consulta el texto de cada frase por su clave.

Claves del manifiesto:
  intro_p1..p5        pantallas de la intro (datos.INTRO_PAGINAS)
  dia_0..dia_4        el día de la semana al empezar cada nivel
  anim_<escena>       narración de la animación explicativa (datos.ANIMACION_ESCENAS)
  tut_<paso>          cada paso del tutorial guiado (datos.TUTORIAL_PASOS)
  consejo_*           el consejo que se desbloquea al fallar (datos.CONSEJOS)
  err_<id incidente>  qué hiciste mal en ese mensaje (datos.VOZ_ERRORES)
  err_evento_<id>     no ayudaste a un familiar (config.EVENTOS_DISPONIBLES)
  err_tiempo          se agotó el tiempo (se dice antes de la explicación)
  parcial_<acción>    no caíste, pero lo ideal era otra cosa (datos.VOZ_PARCIAL)
  derrota_<motivo>    por qué perdiste el nivel (datos.VOZ_DERROTA)
"""
import hashlib
import json
import os
import re
import wave

import config
import datos

CARPETA = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                       "assets", "audio", "voz", "grabado")
EXTENSIONES = (".ogg", ".wav")
ARCHIVO_HUELLAS = "manifest.json"


def manifest():
    """{clave: texto hablado} de todas las frases con voz, en orden estable."""
    m = {}
    for p in datos.INTRO_PAGINAS:
        m[p["key_voz"]] = p["voz"].format(dinero=config.DINERO_INICIAL_V2,
                                          matricula=config.MATRICULA)
    for nivel in datos.NIVELES:
        m[f"dia_{nivel['id']}"] = f"{nivel['dia']}. {nivel['titulo']}."
    for consejo in datos.CONSEJOS.values():
        m[consejo["key_voz"]] = consejo["texto"]
    for escena in datos.ANIMACION_ESCENAS:
        m[f"anim_{escena['id']}"] = escena["voz"]
    for paso in datos.TUTORIAL_PASOS:
        m[f"tut_{paso['id']}"] = paso["voz"]
    for inc_id, texto in datos.VOZ_ERRORES.items():
        m[f"err_{inc_id}"] = texto
    for ev in config.EVENTOS_DISPONIBLES:
        m[f"err_evento_{ev['id']}"] = (
            f"Fallaste. No ayudaste a {ev.get('quien', ev['parentesco'])}. Tu familia lo nota "
            "y pierdes un poco de respeto.")
    m["err_tiempo"] = datos.VOZ_ERROR_TIEMPO
    for accion, texto in datos.VOZ_PARCIAL.items():
        m[f"parcial_{accion}"] = texto
    for motivo, texto in datos.VOZ_DERROTA.items():
        m[f"derrota_{motivo}"] = texto
    return m


# ── Audios en disco ───────────────────────────────────────────────

def ruta_audio(clave, carpeta=None):
    """Ruta del audio de `clave` (.ogg o .wav) si existe; si no, None."""
    carpeta = carpeta or CARPETA
    for ext in EXTENSIONES:
        ruta = os.path.join(carpeta, clave + ext)
        if os.path.isfile(ruta):
            return ruta
    return None


def duracion_ms(clave, carpeta=None):
    """Lo que dura el audio de `clave` en milisegundos (se lee del .wav). Si no hay
    audio, o es .ogg, se estima por la longitud del texto (~68 ms por carácter)."""
    ruta = ruta_audio(clave, carpeta)
    if ruta and ruta.endswith(".wav"):
        try:
            with wave.open(ruta) as w:
                return int(w.getnframes() / w.getframerate() * 1000)
        except (OSError, wave.Error):
            pass
    return int(len(manifest().get(clave, "")) * 68)


def huella(texto):
    """Identifica el texto con el que se generó un audio (detecta audios viejos)."""
    return hashlib.sha1(texto.encode("utf-8")).hexdigest()[:12]


def leer_huellas(carpeta=None):
    ruta = os.path.join(carpeta or CARPETA, ARCHIVO_HUELLAS)
    try:
        with open(ruta, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def estado_audios(carpeta=None):
    """-> (faltan, obsoletos): claves sin audio, y claves cuyo audio se generó
    con un texto distinto del actual (el texto cambió y hay que regenerar)."""
    carpeta = carpeta or CARPETA
    huellas = leer_huellas(carpeta)
    faltan, obsoletos = [], []
    for clave, texto in manifest().items():
        if ruta_audio(clave, carpeta) is None:
            faltan.append(clave)
        elif huellas.get(clave) != huella(texto):
            obsoletos.append(clave)
    return faltan, obsoletos


# ── Elegir la voz en español (modo "robot") ───────────────────────

def es_voz_espanola(voz):
    """¿Esta voz de pyttsx3 habla español?
    Ojo: el id de las voces de Windows es una ruta del registro que incluye la
    palabra "voices", así que buscar "es" en el id daba SIEMPRE verdadero y se
    elegía la última voz (en inglés). Se mira solo el nombre del token y el idioma."""
    idiomas = " ".join(str(i).lower() for i in (getattr(voz, "languages", None) or []))
    if re.search(r"(^|[^a-z])es([^a-z]|$)", idiomas):
        return True
    nombre = (getattr(voz, "name", "") or "").lower()
    if "spanish" in nombre or "español" in nombre:
        return True
    token = (getattr(voz, "id", "") or "").lower().replace("/", "\\").rsplit("\\", 1)[-1]
    return re.search(r"(^|[_\-.])es([_\-.]|$)", token) is not None


def elegir_voz(voces):
    """La mejor voz en español de la lista (es-MX/es-CO/es-US antes que es-ES)."""
    candidatas = [v for v in voces if es_voz_espanola(v)]
    if not candidatas:
        return None

    def puntaje(v):
        texto = ((getattr(v, "id", "") or "") + " "
                 + " ".join(str(i) for i in (getattr(v, "languages", None) or []))).lower()
        if re.search(r"es[_\-](mx|co|us|419)", texto):
            return 0
        return 1

    return sorted(candidatas, key=puntaje)[0]
