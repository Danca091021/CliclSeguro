"""config.py — Constantes y configuración global."""

# ============ VENTANA ============
WIDTH, HEIGHT = 400, 700
FPS = 60
TITULO = "Clic Seguro"

# ============ MARCO DEL TELÉFONO ============
PHONE_BODY       = (40, 40, 320, 620)
PHONE_BEZEL      = (52, 52, 296, 596)
PHONE_SCREEN     = (54, 54, 292, 592)
PHONE_SPEAKER    = (170, 42, 60, 5)
PHONE_CAMERA_XY  = (245, 44.5)
PHONE_HOME       = (170, 640, 60, 4)
VOL_UP           = (38, 170, 2, 30)
VOL_DOWN         = (38, 210, 2, 30)
POWER            = (360, 190, 2, 50)

# ============ COLORES ============
C_BG_WHITE      = (255, 255, 255)
C_BG_SOFT       = (249, 250, 251)
C_BORDER        = (229, 231, 235)
C_TEXT          = (31, 41, 55)
C_TEXT_2        = (107, 114, 128)
C_TEXT_3        = (156, 163, 175)
C_BLUE          = (37, 99, 235)
C_BLUE_LIGHT    = (219, 234, 254)
C_BLUE_DARK     = (30, 64, 175)
C_GREEN         = (16, 185, 129)
C_WA_GREEN      = (37, 211, 102)
C_RED           = (239, 68, 68)
C_AMBER         = (245, 158, 11)
C_AMBER_LIGHT   = (254, 243, 199)
C_GOLD          = (217, 119, 6)
C_PHONE_BODY    = (31, 41, 55)
C_BG_DESK       = (15, 23, 42)

# ============ MECÁNICAS ============
PRIV_INICIAL     = 100
REP_INICIAL      = 100

PTS_BASE_FRAUDE  = 15
PTS_BASE_LEGIT   = 20
PTS_HERRAMIENTA  = 5
PTS_REPORTAR     = 10

PUNTOS_MAXIMOS    = 800       # máximo teórico (lo verifica un test contra Game.puntaje_maximo)
UMBRAL_CERTIF    = 560       # 70% del máximo teórico (800) — ver specs/11_balance.md
UMBRAL_PASAR_N4  = 30

REP_NUEVO_DIA    = 10        # al pasar al día siguiente recuperas reputación (tope 100)

TIEMPO_URGENCIA  = 20

# ============ ECONOMÍA ============
ECONOMIA_V2 = True           # ← Activo a partir de Bloque C

DINERO_INICIAL = 500_000     # legacy (por si ECONOMIA_V2 = False)
DINERO_INICIAL_V2 = 800
MATRICULA = 500

GASTOS_DIARIOS = {
    2: {"concepto": "Comida y transporte", "monto": 20},
    3: {"concepto": "Recarga de celular",  "monto": 30},
}

MATERIALES_MONTO = 40

# ============ EVENTOS ALEATORIOS ============
EVENTO_ACTIVO = True
EVENTO_CHANCE = 0.60
EVENTO_DROP_MS = 300         # animación de caída de la tarjeta de evento
# Ayudar a un familiar cuesta dinero (transferencia por el monto exacto) y
# devuelve un poco de reputación; no ayudar resta reputación (impacto -15).
EVENTO_REP_AYUDA = 5         # reputación que se recupera al ayudar (tope 100)
EVENTOS_DISPONIBLES = [
    {"id": "ev_mama_carro", "monto": 80, "es_familiar": True, "parentesco": "Mamá",      "quien": "tu mamá",    "cuenta": "0011"},
    {"id": "ev_valen_bus",  "monto": 30, "es_familiar": True, "parentesco": "Valentina", "quien": "Valentina",  "cuenta": "0042"},
    {"id": "ev_hermano",    "monto": 50, "es_familiar": True, "parentesco": "Hermano",   "quien": "tu hermano", "cuenta": "0150"},
    {"id": "ev_farmacia",   "monto": 60, "es_familiar": True, "parentesco": "Mamá",      "quien": "tu mamá",    "cuenta": "0011"},
]

PRESTAMO_MAX = 100
PRESTAMO_SEGURO_HASTA = 50
PRESTAMO_PROB_RECHAZO = 0.5

# ============ INTERACCIÓN BANCARIA (Bloque E) ============
# False en Bloque C. Bloque E lo activa para habilitar
# los flujos de OTP y transferencia.
INTERACCION_ACTIVA = True

# ============ DIFICULTAD ============
PENALIZACION_SOBRE_VERIFICAR = 5

# ============ TIMER ============
C_TIMER_BG    = (254, 243, 199)
C_TIMER_FG    = (146, 64, 14)
C_TIMER_BORDE = (245, 158, 11)

# ============ AUDIO ============
VOL_MUSICA_SEGURA = 0.30
VOL_MUSICA_TENSION = 0.35
MUSICA_FADE_MS = 800
UMBRAL_TENSION = 30

# ============ VOZ ============
# "grabado": reproduce assets/audio/voz/grabado/<clave>.wav|.ogg (créalos con
#            `python generar_voces.py`); si falta uno, cae a "robot".
# "robot":   voz en español de Windows en vivo (pyttsx3).
# "silencio": sin voz.
MODO_VOZ = "grabado"

# ============ TYPEWRITER ============
TYPEWRITER_CPS = 30

# ============ CINEMÁTICA ============
SKIP_INTRO = False
CINEMATICA_FADE_MS = 400     # fade-in del título de cada pantalla

# ============ ANIMACIÓN EXPLICATIVA ============
ANIMACION_ACTIVA = True      # se muestra al empezar la primera partida (specs/15_animacion.md)

# ============ TUTORIAL GUIADO ============
TUTORIAL_ACTIVO = True       # práctica guiada en el Domingo (specs/14_tutorial.md)

# ============ PANTALLA DEL DÍA Y FUNDIDOS ============
FADE_MS = 200                # fundido de entrada entre pantallas completas (spec 09)
DIA_INTRO_LISTO_MS = 2000    # cuándo la pantalla del día acepta continuar

# ============ SCROLL ============
SCROLL_VELOCIDAD = 40

# ============ LISTA DE MENSAJES ============
MSG_CARD_H = 66
MSG_CARD_GAP = 4

# ============ PROTAGONISTA ============
# El personaje es siempre Camilo (la historia está escrita en torno a él).
NOMBRE_JUGADOR = "Camilo"
SALUDO_POR_NIVEL = {0: "Buenas tardes,"}   # el Domingo es a las 6 PM
SALUDO_DEFECTO = "Buenos días,"

# ============ UI ============
HOVER_ENABLED = True
# Escala de la ventana: "auto" usa la escala de pantalla de Windows (125%, 150%...)
# para dibujar nítido; un número (1.0, 1.5, 2.0) la fuerza. Ver specs/12_visual.md
UI_ESCALA = "auto"

# Tono del widget "Tu semana" en el home, por id de nivel (0=Dom ... 4=Vie).
# fondo = relleno de la tarjeta, borde = contorno, acento = día actual.
COLOR_DIA = {
    0: {"fondo": (243, 244, 246), "borde": (209, 213, 219), "acento": (107, 114, 128)},  # Dom gris
    1: {"fondo": (239, 246, 255), "borde": (191, 219, 254), "acento": (37, 99, 235)},    # Lun azul
    2: {"fondo": (236, 253, 245), "borde": (167, 243, 208), "acento": (16, 185, 129)},   # Mié verde
    3: {"fondo": (255, 247, 237), "borde": (254, 215, 170), "acento": (234, 88, 12)},    # Jue naranja
    4: {"fondo": (254, 242, 242), "borde": (254, 202, 202), "acento": (239, 68, 68)},    # Vie rojo suave
}