"""ui.py — Dibujo con Pygame. Cada pantalla devuelve dict {nombre: rect}."""
import collections
import math
import os
import sys
import pygame
import config
import gfx
import iconos

_f = {}      # fuentes para DIBUJAR: tamaño lógico * escala (nítidas a cualquier escala)
_fm = {}     # fuentes para MEDIR: tamaño lógico. El diseño (saltos de línea,
             # recortes) no cambia con la escala.
_fs = {}     # respaldo con símbolos (⌂ ✕ ⚠ ✓ ...) que Segoe UI no trae

_BASE = "segoeui,arial,sans"
_SIMBOLOS = "segoeuisymbol,seguisym,dejavusans,arial"
# pygame.font.SysFont("segoeui") elige "Segoe UI Light" (muy fina, se ve débil
# y pixelada). Se cargan por ruta las versiones normal / negrita / símbolos.
_ARCHIVOS = {"normal": "segoeui.ttf", "negrita": "segoeuib.ttf",
             "simbolos": "seguisym.ttf"}
_TAMANOS = {            # nombre: (tamaño lógico, negrita)
    "title": (26, True), "h1": (18, True), "h2": (15, True),
    "body": (13, False), "small": (11, False), "tiny": (9, False),
    "btn": (12, True), "btn_lg": (14, True), "display": (44, True),
    "gigante": (96, True),
}
_texto_cache = collections.OrderedDict()


def init():
    """Crea las fuentes. Llamar DESPUÉS de gfx.init(escala)."""
    pygame.font.init()
    _f.clear()
    _fm.clear()
    _fs.clear()
    _texto_cache.clear()
    _glifo_falta.clear()
    _cuadro_vacio.clear()
    for nombre, (tam, negrita) in _TAMANOS.items():
        real = max(6, round(tam * gfx.S))
        _fm[nombre] = _fuente("negrita" if negrita else "normal", tam, _BASE, negrita)
        _f[nombre] = _fuente("negrita" if negrita else "normal", real, _BASE, negrita)
        _fs[nombre] = _fuente("simbolos", real, _SIMBOLOS, negrita)


def _fuente(clase, tam, respaldo, negrita):
    """Fuente de Windows por ruta; si no existe (otro sistema), SysFont."""
    carpeta = os.path.join(os.environ.get("WINDIR", r"C:\Windows"), "Fonts")
    ruta = os.path.join(carpeta, _ARCHIVOS[clase])
    if os.path.isfile(ruta):
        return pygame.font.Font(ruta, tam)
    return pygame.font.SysFont(respaldo, tam, bold=negrita)


_glifo_falta = {}
_cuadro_vacio = {}


def _falta(fuente, c):
    """¿La fuente no trae el glifo de este carácter? (se vería como un cuadro).
    font.metrics() no sirve: devuelve las medidas del cuadro. Se compara el
    dibujo del carácter contra el del cuadro (U+FFFF, que ninguna fuente trae)."""
    if ord(c) < 0x2000:
        return False
    clave = (id(fuente), c)
    r = _glifo_falta.get(clave)
    if r is None:
        ref = _cuadro_vacio.get(id(fuente))
        if ref is None:
            ref = pygame.image.tostring(fuente.render("\uFFFF", True, (0, 0, 0)), "RGBA")
            _cuadro_vacio[id(fuente)] = ref
        try:
            r = pygame.image.tostring(fuente.render(c, True, (0, 0, 0)), "RGBA") == ref
        except pygame.error:          # carácter que la fuente no puede dibujar
            r = True
        _glifo_falta[clave] = r
    return r


def _limpiar(txt):
    """Quita lo que pygame no puede dibujar: emojis (fuera del plano básico) y
    selectores de variación. Antes salían como cuadros."""
    return "".join(c for c in txt if ord(c) <= 0xFFFF and c not in "\ufe0f\u200d")


def _render_texto(txt, color, font):
    f = _f[font]
    if not txt:
        return pygame.Surface((1, 1), pygame.SRCALPHA)
    if not any(_falta(f, c) for c in set(txt)):
        return f.render(txt, True, color)
    # Hay símbolos que Segoe UI no trae: cada tramo con la fuente que lo tiene
    trozos = []
    for c in txt:
        fu = _fs[font] if _falta(f, c) else f
        if trozos and trozos[-1][1] is fu:
            trozos[-1][0] += c
        else:
            trozos.append([c, fu])
    imgs = [fu.render(t, True, color) for t, fu in trozos]
    w = sum(i.get_width() for i in imgs)
    h = max(i.get_height() for i in imgs)
    out = pygame.Surface((w, h), pygame.SRCALPHA)
    out.fill((color[0], color[1], color[2], 0))      # sin bordes oscuros
    x = 0
    for i in imgs:
        out.blit(i, (x, (h - i.get_height()) // 2))
        x += i.get_width()
    return out


def _render(txt, color, font):
    txt = _limpiar(txt)
    clave = (txt, tuple(color), font)
    img = _texto_cache.get(clave)
    if img is None:
        img = _render_texto(txt, color, font)
        _texto_cache[clave] = img
        if len(_texto_cache) > 800:
            _texto_cache.popitem(last=False)
    return img


def _t(screen, txt, x, y, color=None, font="body", anchor="topleft", alfa=255):
    """Dibuja texto. (x, y) son coordenadas lógicas; devuelve su rect lógico.
    alfa < 255 lo hace translúcido (animaciones de aparición)."""
    color = color or config.C_TEXT
    img = _render(txt, color, font)
    if alfa < 255:
        img = img.copy()          # copia: no tocar la caché
        img.set_alpha(max(0, alfa))
    e = gfx.S
    r = img.get_rect(**{anchor: (round(x * e), round(y * e))})
    screen.blit(img, r)
    return pygame.Rect(r.x / e, r.y / e, r.w / e, r.h / e)


def _truncate(txt, max_chars):
    if len(txt) <= max_chars:
        return txt
    return txt[:max_chars - 1].rstrip() + "…"


def _fit_linea(txt, max_width, font="body"):
    f = _fm[font]
    if f.size(txt)[0] <= max_width:
        return txt
    while len(txt) > 0 and f.size(txt + "…")[0] > max_width:
        txt = txt[:-1]
    return txt.rstrip() + "…"


def _wrap_lines(txt, rect, font="body"):
    f = _fm[font]
    palabras = txt.split()
    lineas, cur = [], ""
    for w in palabras:
        if f.size(w)[0] > rect.width:
            w = _fit_linea(w, rect.width, font)
        test = (cur + " " + w).strip()
        if f.size(test)[0] <= rect.width:
            cur = test
        else:
            if cur:
                lineas.append(cur)
            cur = w
    if cur:
        lineas.append(cur)
    return lineas


def _wrap(screen, txt, rect, color, font="body"):
    lines = _wrap_lines(txt, rect, font)
    y = rect.y
    alto = _fm[font].get_height()
    for ln in lines:
        if y + alto > rect.bottom:
            break
        _t(screen, ln, rect.x, y, color, font)
        y += alto + 2


def _draw_typing(screen, lines, x, y, visible_chars, color, font="body"):
    fm = _fm[font]
    remaining = visible_chars
    cx, cy = x, y
    for line in lines:
        if remaining <= 0:
            return (x, y, False)
        if remaining >= len(line):
            _t(screen, line, x, y, color, font)
            cx = x + fm.size(line)[0]
            cy = y
            remaining -= len(line)
            y += fm.get_height() + 2
        else:
            parte = line[:remaining]
            _t(screen, parte, x, y, color, font)
            cx = x + fm.size(parte)[0]
            cy = y
            return (cx, cy, False)
    return (cx, cy, True)


_mouse = (-1, -1)


def set_mouse(pos):
    """main.py lo llama una vez por frame (posición LÓGICA), antes de dibujar."""
    global _mouse
    _mouse = pos


def _btn(screen, rect, label, bg, fg, border=None, font="btn", hover=None):
    """Botón con borde azul al pasar el mouse.
    hover=None -> se calcula con la posición del mouse; hover=False lo
    desactiva (botones deshabilitados)."""
    if hover is None:
        hover = config.HOVER_ENABLED and rect.collidepoint(_mouse)
    gfx.rect(screen, bg, rect, border_radius=8)
    if hover:
        # Sobre un botón azul relleno el borde azul sería invisible.
        borde = config.C_BLUE_DARK if bg == config.C_BLUE else config.C_BLUE
        gfx.rect(screen, borde, rect, width=2, border_radius=8)
    elif border:
        gfx.rect(screen, border, rect, width=2, border_radius=8)
    _t(screen, label, rect.centerx, rect.centery, fg, font, "center")


def _bar(screen, x, y, w, h, frac, color):
    gfx.rect(screen, config.C_BORDER, (x, y, w, h), border_radius=h // 2)
    fill = int(w * max(0.0, min(1.0, frac)))
    if fill > 0:
        gfx.rect(screen, color, (x, y, fill, h), border_radius=h // 2)


def _phone(screen):
    screen.fill(config.C_BG_DESK)
    gfx.rect(screen, config.C_PHONE_BODY, config.PHONE_BODY, border_radius=32)
    gfx.rect(screen, (0, 0, 0), config.PHONE_BEZEL, border_radius=20)
    gfx.rect(screen, config.C_BG_WHITE, config.PHONE_SCREEN, border_radius=18)
    gfx.rect(screen, (55, 65, 81), config.PHONE_SPEAKER, border_radius=2)
    gfx.circle(screen, (17, 24, 39),
                       (int(config.PHONE_CAMERA_XY[0]),
                        int(config.PHONE_CAMERA_XY[1])), 3)
    gfx.rect(screen, (75, 85, 99), config.PHONE_HOME, border_radius=2)


def _status_bar(screen, game, extra=""):
    sx, sy = config.PHONE_SCREEN[0], config.PHONE_SCREEN[1]
    sw = config.PHONE_SCREEN[2]
    _t(screen, game.nivel.dia, sx + 14, sy + 8, config.C_TEXT, "small")
    _t(screen, f"{game.estado.xp} pts", sx + sw // 2, sy + 8,
       config.C_TEXT_2, "small", "midtop")
    if extra:
        _t(screen, extra, sx + sw - 14, sy + 8, config.C_TEXT_2, "small", "topright")
    gfx.line(screen, config.C_BORDER,
                     (sx + 8, sy + 30), (sx + sw - 8, sy + 30))


def _hud(screen, game):
    sx, sy = config.PHONE_SCREEN[0], config.PHONE_SCREEN[1]
    sw = config.PHONE_SCREEN[2]
    est = game.estado
    y = sy + 38
    px = sx + 70
    pw = sw - 84 - 32        # deja sitio al número (100, $800) a la derecha

    _t(screen, "Priv", sx + 14, y, config.C_TEXT_2, "tiny")
    _bar(screen, px, y + 3, pw, 6, est.privacidad / 100,
         config.C_GREEN if est.privacidad > 30 else config.C_RED)
    _t(screen, str(est.privacidad), sx + sw - 14, y, config.C_TEXT, "tiny", "topright")
    y += 16

    # Dinero con máximo dinámico
    max_dinero = max(
        config.DINERO_INICIAL_V2 if config.ECONOMIA_V2 else config.DINERO_INICIAL,
        est.dinero, 1,
    )
    frac_dinero = est.dinero / max_dinero
    color_dinero = config.C_BLUE if est.dinero >= 100 else config.C_RED
    _t(screen, "Dinero", sx + 14, y, config.C_TEXT_2, "tiny")
    _bar(screen, px, y + 3, pw, 6, frac_dinero, color_dinero)
    if config.ECONOMIA_V2 and est.dinero < 10000:
        dinero_txt = f"${est.dinero}"
    else:
        dinero_txt = f"${est.dinero:,}".replace(",", ".")
    _t(screen, dinero_txt, sx + sw - 14, y, config.C_TEXT, "tiny", "topright")
    y += 16

    _t(screen, "Rep", sx + 14, y, config.C_TEXT_2, "tiny")
    _bar(screen, px, y + 3, pw, 6, est.reputacion / 100,
         config.C_GREEN if est.reputacion > 30 else config.C_RED)
    _t(screen, str(est.reputacion), sx + sw - 14, y, config.C_TEXT, "tiny", "topright")
    gfx.line(screen, config.C_BORDER,
                     (sx + 8, y + 14), (sx + sw - 8, y + 14))


def _draw_timer(screen, segundos):
    sx, sw = config.PHONE_SCREEN[0], config.PHONE_SCREEN[2]
    w, h = 62, 24
    x = sx + sw - 14 - w
    y = config.PHONE_SCREEN[1] + 115
    gfx.rect(screen, config.C_TIMER_BG, (x, y, w, h), border_radius=12)
    gfx.rect(screen, config.C_TIMER_BORDE, (x, y, w, h),
                     width=2, border_radius=12)
    seg = max(0, int(segundos))
    color = config.C_TIMER_FG if seg > 5 else config.C_RED
    txt = f"00:{seg:02d}"
    _t(screen, txt, x + w // 2, y + h // 2, color, "small", "center")


# ============================================================
# MENÚ
# ============================================================

def draw_menu(screen):
    _phone(screen)
    sx, sy = config.PHONE_SCREEN[0], config.PHONE_SCREEN[1]
    sw = config.PHONE_SCREEN[2]

    logo = pygame.Rect(sx + sw // 2 - 45, sy + 90, 90, 90)
    gfx.rect(screen, config.C_BLUE_LIGHT, logo, border_radius=20)
    gfx.rect(screen, config.C_BLUE,
                     (logo.x + 22, logo.y + 20, 46, 50), border_radius=8)

    _t(screen, "CLIC SEGURO", sx + sw // 2, sy + 200, config.C_TEXT, "title", "midtop")
    _t(screen, "Cada clic tiene consecuencias", sx + sw // 2, sy + 235,
       config.C_TEXT_2, "small", "midtop")

    btn_play = pygame.Rect(sx + 30, sy + 300, sw - 60, 48)
    _btn(screen, btn_play, "Jugar", config.C_BLUE_LIGHT, config.C_BLUE_DARK,
         config.C_BLUE, "btn_lg")
    btn_anim = pygame.Rect(sx + 30, sy + 358, sw - 60, 38)
    _btn(screen, btn_anim, "Ver animación", config.C_BG_WHITE, config.C_TEXT, config.C_BORDER)
    btn_inst = pygame.Rect(sx + 30, sy + 404, sw - 60, 38)
    _btn(screen, btn_inst, "Instrucciones", config.C_BG_WHITE, config.C_TEXT, config.C_BORDER)
    btn_cred = pygame.Rect(sx + 30, sy + 450, sw - 60, 38)
    _btn(screen, btn_cred, "Créditos", config.C_BG_WHITE, config.C_TEXT, config.C_BORDER)
    btn_salir = pygame.Rect(sx + 30, sy + 496, sw - 60, 38)
    _btn(screen, btn_salir, "Salir", config.C_BG_WHITE, config.C_TEXT, config.C_BORDER)

    _t(screen, "Proyecto de aula · Programación III",
       sx + sw // 2, sy + 556, config.C_TEXT_3, "tiny", "midtop")
    return {"play": btn_play, "animacion": btn_anim, "instrucciones": btn_inst,
            "creditos": btn_cred, "salir": btn_salir}


def draw_cinematica(screen, pagina, texto, idx, total, elapsed_ms, completo=False):
    """Una pantalla narrativa de la intro (spec 10).
    pagina: dict de datos.INTRO_PAGINAS; texto: ya formateado.
    completo=True muestra todo el texto sin esperar el typewriter.
    Devuelve botones + "_done" (True cuando el texto terminó de escribirse).
    El orden importa: main.py recorre el dict y se queda con el primer
    rect que contiene el clic, por eso "skip_intro" va antes que "avanzar"."""
    screen.fill((0, 0, 0))
    cx = config.WIDTH // 2

    # Título: fade-in
    alpha = 255 if completo else min(
        255, int(elapsed_ms / config.CINEMATICA_FADE_MS * 255))
    tit = _render(_fit_linea(pagina["titulo"], config.WIDTH - 60, "title"),
                  config.C_BG_WHITE, "title").copy()   # copia: no tocar la caché
    tit.set_alpha(alpha)
    e = gfx.S
    screen.blit(tit, tit.get_rect(center=(round(cx * e),
                                          round((config.HEIGHT // 2 - 50) * e))))

    # Texto: typewriter centrado, empieza cuando termina el fade
    f = _fm["body"]
    lineas = _wrap_lines(texto, pygame.Rect(0, 0, config.WIDTH - 80, 200), "body")
    t = max(0.0, elapsed_ms - config.CINEMATICA_FADE_MS)
    restantes = 99999 if completo else int(t / 1000 * config.TYPEWRITER_CPS)
    y = config.HEIGHT // 2 - 5
    todo = True
    for ln in lineas:
        if restantes <= 0:
            todo = False
            break
        full_w = f.size(ln)[0]
        x = cx - full_w // 2          # centrar según la línea completa
        vis = ln[:restantes]
        _t(screen, vis, x, y, (200, 200, 210), "body")
        if len(vis) < len(ln):
            todo = False
            break
        restantes -= len(ln)
        y += f.get_height() + 4

    # Indicador de progreso (puntos)
    for i in range(total):
        col = config.C_BLUE if i == idx else (60, 60, 70)
        gfx.circle(screen, col, (cx - (total - 1) * 8 + i * 16,
                                         config.HEIGHT - 50), 3)

    # Pista: solo cuando ya se puede avanzar (parpadea suave)
    if todo:
        ultima = (idx == total - 1)
        pulso = 120 + int(30 * (1 + math.sin(elapsed_ms / 300.0)))
        _t(screen, "Click para empezar" if ultima else "Click para continuar",
           cx, config.HEIGHT - 80, (pulso, pulso, pulso + 10), "tiny", "center")

    btn_skip = pygame.Rect(config.WIDTH - 104, 14, 92, 28)
    _btn(screen, btn_skip, "Saltar intro", (0, 0, 0), (120, 120, 130),
         (50, 50, 60), "small")
    return {"skip_intro": btn_skip,
            "avanzar": pygame.Rect(0, 0, config.WIDTH, config.HEIGHT),
            "_done": todo}


def draw_dia_intro(screen, game, elapsed_ms):
    """Pantalla de "día nuevo" (spec 13): el nombre del día, la semana con el
    marcador avanzando desde el día anterior, y el título y objetivo del nivel.
    Devuelve {"continuar": toda la pantalla, "_done": ya se puede continuar}."""
    screen.fill((0, 0, 0))
    W, H = config.WIDTH, config.HEIGHT
    cx = W // 2
    nivel = game.nivel
    acento = config.COLOR_DIA.get(nivel.id, config.COLOR_DIA[1])["acento"]

    def aparece(desde, dur=450):
        return max(0.0, min(1.0, (elapsed_ms - desde) / dur))

    def suave(t):
        return 1 - (1 - t) ** 3

    # ── La semana: el marcador viaja del día anterior al actual ──
    xs = [60 + i * 70 for i in range(len(DIAS_SEMANA))]
    y = 205
    a_sem = int(255 * suave(aparece(0, 500)))
    gfx.line(screen, (45, 45, 55), (xs[0], y), (xs[-1], y), 2)
    anterior = max(0, nivel.id - 1)
    t = suave(aparece(500, 900))
    marcador_x = xs[anterior] + (xs[nivel.id] - xs[anterior]) * t
    llego = t >= 0.99
    for i, d in enumerate(DIAS_SEMANA):
        if i < nivel.id:
            col, letra = config.C_GREEN, (255, 255, 255)
        elif i == nivel.id and llego:
            col, letra = acento, (255, 255, 255)
        else:
            col, letra = (55, 55, 66), (150, 150, 162)
        gfx.circle(screen, col, (xs[i], y), 14)
        _t(screen, d, xs[i], y, letra, "h2", "center", a_sem)
    gfx.circle(screen, acento, (marcador_x, y), 21, 3)

    # ── Nombre del día, título y objetivo ──
    sube = int(18 * (1 - suave(aparece(250, 550))))
    _t(screen, nivel.dia.upper(), cx, 300 + sube, (255, 255, 255), "display",
       "midtop", int(255 * suave(aparece(250, 550))))
    ancho_barra = int(150 * suave(aparece(700, 500)))
    if ancho_barra > 0:
        gfx.rect(screen, acento, (cx - ancho_barra // 2, 362, ancho_barra, 4),
                 border_radius=2)
    _t(screen, nivel.titulo, cx, 386, (235, 235, 240), "h1", "midtop",
       int(255 * aparece(1000)))
    objetivo = _wrap_lines(nivel.objetivo, pygame.Rect(0, 0, W - 90, 120), "body")
    for i, linea in enumerate(objetivo[:4]):
        _t(screen, linea, cx, 426 + i * 21, (150, 150, 162), "body", "midtop",
           int(255 * aparece(1300)))

    listo = elapsed_ms >= config.DIA_INTRO_LISTO_MS
    if listo:
        pulso = 120 + int(30 * (1 + math.sin(elapsed_ms / 300.0)))
        _t(screen, "Toca para empezar el día", cx, H - 80,
           (pulso, pulso, pulso + 10), "tiny", "center")
    return {"continuar": pygame.Rect(0, 0, W, H), "_done": listo}


def draw_tutorial(screen, paso, foco, indice, total, elapsed_ms):
    """Capa del tutorial guiado (spec 14), dibujada ENCIMA de la pantalla real:
    oscurece todo menos `foco` (un Rect lógico o None), lo rodea con un anillo que
    late, y muestra un globo con el texto del paso y una flecha hacia el foco.
    Devuelve los botones propios: "tut_siguiente" (solo pasos informativos) y
    "tut_saltar"."""
    fondo = screen.copy()
    gfx.overlay(screen, (8, 12, 30, 178))
    sx, sy, sw, sh = config.PHONE_SCREEN
    hueco = None

    if foco is not None:
        hueco = pygame.Rect(foco).inflate(12, 12)
        r = gfx.rect_px(hueco).clip(screen.get_rect())
        if r.w > 0 and r.h > 0:
            # "Agujero" con esquinas redondeadas: se devuelve el brillo original
            trozo = fondo.subsurface(r).copy().convert_alpha()
            mascara = pygame.Surface(r.size, pygame.SRCALPHA)
            mascara.fill((255, 255, 255, 0))
            gfx.rect(mascara, (255, 255, 255, 255), (0, 0, hueco.w, hueco.h),
                     border_radius=12)
            trozo.blit(mascara, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
            screen.blit(trozo, r.topleft)
        pulso = (math.sin(elapsed_ms / 220.0) + 1) / 2
        alfa = 130 + 16 * round(125 * pulso / 16)
        gfx.rect(screen, (*config.C_BLUE, min(255, alfa)),
                 hueco.inflate(8, 8), width=2, border_radius=15)
        gfx.rect(screen, (*config.C_BLUE, 255), hueco, width=3, border_radius=12)

    # ── Globo con el texto ──
    ancho = 248
    bx = sx + (sw - ancho) // 2
    lineas = _wrap_lines(paso["texto"], pygame.Rect(0, 0, ancho - 28, 400), "body")
    alto_linea = _fm["body"].get_height() + 3
    es_info = paso["tipo"] == "info"
    alto = 26 + len(lineas) * alto_linea + 12 + (34 if es_info else 16) + 10

    arriba = False
    if hueco is not None:
        arriba = hueco.centery > sy + sh * 0.5
        by = hueco.top - alto - 18 if arriba else hueco.bottom + 18
        by = max(sy + 30, min(by, sy + sh - alto - 10))
    else:
        by = sy + (sh - alto) // 2
    caja = pygame.Rect(bx, by, ancho, alto)

    gfx.rect(screen, (0, 0, 0, 80), caja.move(2, 4), border_radius=14)
    if hueco is not None:                         # flecha hacia el foco
        ax = max(bx + 26, min(hueco.centerx, bx + ancho - 26))
        if arriba:
            gfx.polygon(screen, config.C_BLUE, [(ax - 11, caja.bottom - 2),
                                                (ax + 11, caja.bottom - 2), (ax, caja.bottom + 11)])
            gfx.polygon(screen, config.C_BG_WHITE, [(ax - 9, caja.bottom - 2),
                                                    (ax + 9, caja.bottom - 2), (ax, caja.bottom + 8)])
        else:
            gfx.polygon(screen, config.C_BLUE, [(ax - 11, caja.top + 2),
                                                (ax + 11, caja.top + 2), (ax, caja.top - 11)])
            gfx.polygon(screen, config.C_BG_WHITE, [(ax - 9, caja.top + 2),
                                                    (ax + 9, caja.top + 2), (ax, caja.top - 8)])
    gfx.rect(screen, config.C_BG_WHITE, caja, border_radius=14)
    gfx.rect(screen, config.C_BLUE, caja, width=2, border_radius=14)
    if hueco is not None:                         # tapa la base de la flecha
        ax = max(bx + 26, min(hueco.centerx, bx + ancho - 26))
        y_base = caja.bottom - 2 if arriba else caja.top + 2
        gfx.polygon(screen, config.C_BG_WHITE,
                    [(ax - 9, y_base - 1), (ax + 9, y_base - 1),
                     (ax + 9, y_base + 1), (ax - 9, y_base + 1)])

    _t(screen, f"Paso {indice} de {total}", bx + 14, by + 10,
       config.C_TEXT_3, "tiny")
    for i, linea in enumerate(lineas):
        _t(screen, linea, bx + 14, by + 26 + i * alto_linea, config.C_TEXT, "body")

    btns = {}
    if es_info:
        boton = pygame.Rect(bx + ancho - 14 - 112, caja.bottom - 10 - 30, 112, 30)
        _btn(screen, boton, paso.get("boton", "Siguiente"), config.C_BLUE,
             config.C_BG_WHITE, font="btn")
        btns["tut_siguiente"] = boton
    else:
        _t(screen, "Toca lo resaltado", bx + 14, caja.bottom - 26,
           config.C_BLUE, "small")

    saltar = pygame.Rect(sx + sw - 116, sy + 4, 110, 22)
    _btn(screen, saltar, "Saltar tutorial", (24, 32, 60), (205, 215, 240),
         (70, 85, 130), "tiny")
    btns["tut_saltar"] = saltar
    return btns


def _encabezado(screen, titulo, con_volver=True):
    """Banda azul superior de las pantallas de información (Cómo jugar, Créditos…).
    Devuelve el botón "← Volver"."""
    sx, sy, sw = config.PHONE_SCREEN[0], config.PHONE_SCREEN[1], config.PHONE_SCREEN[2]
    gfx.rect(screen, config.C_BLUE, (sx, sy, sw, 62), border_radius=18)
    gfx.rect(screen, config.C_BLUE, (sx, sy + 30, sw, 32))        # esquinas de abajo rectas
    gfx.rect(screen, config.C_BLUE_DARK, (sx, sy + 60, sw, 2))
    _t(screen, titulo, sx + sw // 2, sy + 21, config.C_BG_WHITE, "h1", "midtop")
    btn = pygame.Rect(sx + 8, sy + 16, 70, 30)
    _btn(screen, btn, "← Volver", (255, 255, 255, 36), config.C_BG_WHITE,
         (255, 255, 255, 100), "small")
    return btn


def draw_instrucciones(screen, scroll_y):
    _phone(screen)
    sx, sy, sw, sh = config.PHONE_SCREEN
    btn_volver = _encabezado(screen, "Cómo jugar")

    top = sy + 62
    bottom = sy + sh - 60
    viewport = pygame.Rect(sx, top, sw, bottom - top)
    cont = gfx.surface(viewport.width, 1900, config.C_BG_WHITE)
    M = 12                                  # margen lateral
    ANCHO = viewport.width - 2 * M
    cy = 14

    def seccion(titulo, color):
        nonlocal cy
        gfx.circle(cont, color, (M + 5, cy + 7), 4)
        _t(cont, titulo, M + 16, cy, config.C_TEXT_2, "small")
        cy += 22

    def fila(icono, color, titulo, desc):
        """Tarjeta con un ícono en un círculo de color, un título y una descripción."""
        nonlocal cy
        lineas = _wrap_lines(desc, pygame.Rect(0, 0, ANCHO - 68, 300), "small")
        alto = max(50, 29 + len(lineas) * 14)
        card = pygame.Rect(M, cy, ANCHO, alto)
        gfx.rect(cont, config.C_BG_WHITE, card, border_radius=12)
        gfx.rect(cont, config.C_BORDER, card, width=1, border_radius=12)
        mid = cy + alto / 2
        gfx.circle(cont, color, (M + 28, mid), 18)
        icono(cont, M + 28, mid, 24, config.C_BG_WHITE)
        _t(cont, titulo, M + 58, cy + 9, config.C_TEXT, "h2")
        for i, ln in enumerate(lineas):
            _t(cont, ln, M + 58, cy + 28 + i * 14, config.C_TEXT_2, "small")
        cy += alto + 7

    def nota(texto, fondo, borde, color_texto):
        nonlocal cy
        lineas = _wrap_lines(texto, pygame.Rect(0, 0, ANCHO - 24, 300), "small")
        alto = 16 + len(lineas) * 14
        card = pygame.Rect(M, cy, ANCHO, alto)
        gfx.rect(cont, fondo, card, border_radius=10)
        gfx.rect(cont, borde, card, width=1, border_radius=10)
        for i, ln in enumerate(lineas):
            _t(cont, ln, M + 12, cy + 8 + i * 14, color_texto, "small")
        cy += alto + 14

    def dolar(c, x, y, s, color):
        _t(c, "$", x, y, color, "h1", "center")

    GRIS_ACC = (107, 114, 128)
    ROSA = (236, 72, 100)

    # ── Quién eres ──
    hero = pygame.Rect(M, cy, ANCHO, 110)
    gfx.rect(cont, config.C_BLUE_LIGHT, hero, border_radius=16)
    gfx.circle(cont, config.C_BLUE, (M + 36, cy + 36), 24)
    _t(cont, "C", M + 36, cy + 36, config.C_BG_WHITE, "title", "center")
    _t(cont, "Eres Camilo", M + 70, cy + 13, config.C_BLUE_DARK, "h1")
    _t(cont, "Estudiante de primer semestre", M + 70, cy + 36, config.C_TEXT_2, "small")
    texto = (f"Tienes ${config.DINERO_INICIAL_V2} y el viernes debes pagar "
             f"${config.MATRICULA} de matrícula. Investiga antes de decidir.")
    for i, ln in enumerate(_wrap_lines(texto, pygame.Rect(0, 0, ANCHO - 24, 100), "small")[:3]):
        _t(cont, ln, M + 12, cy + 64 + i * 14, config.C_TEXT, "small")
    cy += 110 + 16

    # ── Las 5 acciones ──
    seccion("TUS 5 ACCIONES", config.C_BLUE)
    fila(iconos.check, config.C_GREEN, "Confiar", "Solo si es un mensaje legítimo que ya verificaste.")
    lupa_fina = lambda c, x, y, s, col: iconos.lupa(c, x, y, s, col, 3, (255, 255, 255, 0))
    fila(lupa_fina, config.C_BLUE, "Verificar",
         "Investiga con una llamada, el canal oficial o una búsqueda. Es la opción más segura.")
    fila(iconos.ojo_tachado, GRIS_ACC, "Ignorar",
         "Spam u ofertas falsas. No respondas y sigue con tu día.")
    fila(iconos.prohibido, config.C_RED, "Bloquear",
         "Quien insiste, te acosa o ya identificaste como falso.")
    fila(iconos.bandera, config.C_AMBER, "Reportar",
         "Suplantación, acoso o estafa. Suma puntos extra desde el Jueves.")
    nota("Solo pierdes recursos si caes en la trampa (confiar). Ignorar o bloquear "
         "una estafa no te cuesta nada.", (236, 253, 245), (167, 243, 208), (6, 95, 70))

    # ── Herramientas ──
    seccion("INVESTIGA ANTES · +5 PUNTOS CADA UNA", config.C_BLUE)
    ancho_t = (ANCHO - 16) // 3
    for k, (nom, icono) in enumerate([("Remitente", iconos.persona),
                                      ("Enlace", iconos.enlace),
                                      ("Contactos", iconos.agenda)]):
        r = pygame.Rect(M + k * (ancho_t + 8), cy, ancho_t, 68)
        gfx.rect(cont, (243, 246, 252), r, border_radius=12)
        icono(cont, r.centerx, r.y + 25, 28, config.C_BLUE)
        _t(cont, nom, r.centerx, r.y + 49, config.C_TEXT, "small", "center")
    cy += 68 + 10
    nota("Al verificar puedes llamar, consultar el canal oficial o buscar en internet. "
         "Llamar a un contacto real cuesta reputación.", (243, 246, 252), config.C_BORDER,
         config.C_TEXT_2)

    # ── Recursos ──
    seccion("TUS 3 RECURSOS", config.C_GREEN)
    fila(iconos.candado, config.C_BLUE, "Privacidad", "Baja si das datos o códigos.")
    fila(dolar, config.C_AMBER, "Saldo",
         "Baja si caes en estafas, pagas gastos o ayudas a tu familia.")
    fila(iconos.corazon, ROSA, "Reputación",
         "Baja si te suplantan o no ayudas. Recuperas +%d cada día." % config.REP_NUEVO_DIA)
    nota("Si un recurso llega a 0, pierdes el nivel.", (254, 242, 242), (254, 202, 202),
         (153, 27, 27))

    # ── Tiempo y gastos ──
    seccion("TIEMPO, GASTOS Y AYUDA", config.C_AMBER)
    fila(iconos.reloj, config.C_AMBER, "Cuenta regresiva",
         f"Desde el Miércoles, los mensajes urgentes tienen {config.TIEMPO_URGENCIA} segundos. "
         "Verificar pausa el tiempo.")
    fila(dolar, config.C_GREEN, "Gastos del día",
         "Comida, celular… Si no puedes pagar un gasto, pierdes la partida.")
    fila(iconos.persona, config.C_BLUE, "Tu familia",
         "Te pedirán ayuda: ayudar cuesta dinero, pero te da respeto.")

    # ── Certificado ──
    seccion("EL CERTIFICADO", config.C_GREEN)
    card = pygame.Rect(M, cy, ANCHO, 96)
    gfx.rect(cont, (236, 253, 245), card, border_radius=14)
    gfx.rect(cont, (167, 243, 208), card, width=1, border_radius=14)
    _t(cont, f"Necesitas {config.UMBRAL_CERTIF} de {config.PUNTOS_MAXIMOS} puntos",
       M + 14, cy + 12, (6, 95, 70), "h2")
    _t(cont, "y la matrícula pagada el viernes.", M + 14, cy + 32, (6, 95, 70), "small")
    barra = pygame.Rect(M + 14, cy + 62, ANCHO - 28, 12)
    gfx.rect(cont, (209, 250, 229), barra, border_radius=6)
    llena = int(barra.width * config.UMBRAL_CERTIF / config.PUNTOS_MAXIMOS)
    gfx.rect(cont, config.C_GREEN, (barra.x, barra.y, llena, barra.height), border_radius=6)
    gfx.circle(cont, config.C_BG_WHITE, (barra.x + llena, barra.centery), 9)
    gfx.circle(cont, config.C_GREEN, (barra.x + llena, barra.centery), 9, 3)
    _t(cont, f"{config.UMBRAL_CERTIF}", barra.x + llena, barra.y + 22, (6, 95, 70),
       "tiny", "midtop")
    _t(cont, f"{config.PUNTOS_MAXIMOS}", barra.right, barra.y + 22, config.C_TEXT_3,
       "tiny", "midtop")
    cy += 96 + 14

    seccion("MIS APRENDIZAJES", config.C_BLUE)
    nota("Cada consejo que desbloqueas al fallar o al reportar se guarda ahí, para repasar.",
         (243, 246, 252), config.C_BORDER, config.C_TEXT_2)

    contenido_alto = cy + 6
    max_scroll = max(0, contenido_alto - viewport.height)
    scroll_y = min(scroll_y, max_scroll)
    # gfx.clip + blit simple (NO area=): con area + destino desplazado el
    # contenido se dibujaba a 2*scroll_y y se salía del viewport.
    gfx.clip(screen, viewport)
    gfx.blit(screen, cont, (viewport.x, viewport.y - scroll_y))
    gfx.clip(screen, None)

    if contenido_alto > viewport.height:
        rel = scroll_y / max_scroll if max_scroll > 0 else 0
        sb_x = sx + sw - 6
        sb_h = max(30, int(viewport.height * viewport.height / contenido_alto))
        sb_y = viewport.y + int((viewport.height - sb_h) * rel)
        gfx.rect(screen, (220, 220, 230), (sb_x, viewport.y, 3, viewport.height), border_radius=2)
        gfx.rect(screen, (150, 150, 160), (sb_x, sb_y, 3, sb_h), border_radius=2)

    gfx.rect(screen, config.C_BG_WHITE, (sx, bottom, sw, 60))
    gfx.line(screen, config.C_BORDER, (sx, bottom), (sx + sw, bottom))
    btn_ap = pygame.Rect(sx + 14, bottom + 12, sw - 28, 36)
    _btn(screen, btn_ap, "Ver mis aprendizajes", config.C_BLUE, config.C_BG_WHITE, font="btn")

    return {"volver_menu": btn_volver, "ver_aprendizajes": btn_ap,
            "_max_scroll": max_scroll}


def draw_aprendizajes(screen, game, scroll_y):
    _phone(screen)
    sx, sy = config.PHONE_SCREEN[0], config.PHONE_SCREEN[1]
    sw = config.PHONE_SCREEN[2]
    sh = config.PHONE_SCREEN[3]

    gfx.rect(screen, config.C_BG_WHITE, (sx, sy, sw, 60))
    gfx.line(screen, config.C_BORDER, (sx, sy + 58), (sx + sw, sy + 58))

    btn_volver = pygame.Rect(sx + 8, sy + 15, 70, 30)
    _btn(screen, btn_volver, "← Volver", config.C_BG_WHITE, config.C_BLUE, None, "small")
    _t(screen, "Mis aprendizajes", sx + sw // 2, sy + 22, config.C_TEXT, "h2", "midtop")

    top = sy + 60
    bottom = sy + sh - 20
    viewport = pygame.Rect(sx, top, sw, bottom - top)

    consejos = game.estado.historial_consejos
    if not consejos:
        _t(screen, "Aún no has desbloqueado consejos.", sx + sw // 2, top + 60,
           config.C_TEXT_2, "body", "midtop")
        return {"volver_menu": btn_volver}

    cont_alto = len(consejos) * 130 + 20
    cont = gfx.surface(viewport.width, cont_alto, config.C_BG_WHITE)
    cy = 10

    for key in consejos:
        c = game.consejos.get(key)
        if not c:
            continue
        card = pygame.Rect(8, cy, viewport.width - 16, 120)
        gfx.rect(cont, config.C_BG_WHITE, card, border_radius=10)
        gfx.rect(cont, config.C_BORDER, card, width=1, border_radius=10)
        gfx.rect(cont, config.C_AMBER,
                         (card.x, card.y, 4, card.height), border_radius=2)
        _t(cont, _fit_linea(c.titulo, card.width - 28, "h2"),
           card.x + 14, card.y + 10, config.C_TEXT, "h2")
        lineas = _wrap_lines(c.texto, pygame.Rect(0, 0, card.width - 28, 200), "tiny")
        yy = card.y + 32
        for ln in lineas[:4]:
            _t(cont, ln, card.x + 14, yy, config.C_TEXT_2, "tiny")
            yy += 12
        cy += 130

    max_scroll = max(0, cont_alto - viewport.height)
    scroll_y = min(scroll_y, max_scroll)
    # set_clip + blit simple (NO area=), ver draw_instrucciones.
    gfx.clip(screen, viewport)
    gfx.blit(screen, cont, (viewport.x, viewport.y - scroll_y))
    gfx.clip(screen, None)

    if cont_alto > viewport.height:
        rel = scroll_y / (cont_alto - viewport.height) if (cont_alto - viewport.height) > 0 else 0
        sb_x = sx + sw - 6
        sb_h = max(30, int(viewport.height * viewport.height / cont_alto))
        sb_y = viewport.y + int((viewport.height - sb_h) * rel)
        gfx.rect(screen, (220, 220, 230),
                         (sb_x, viewport.y, 3, viewport.height), border_radius=2)
        gfx.rect(screen, (150, 150, 160),
                         (sb_x, sb_y, 3, sb_h), border_radius=2)

    return {"volver_menu": btn_volver, "_max_scroll": max_scroll}


def draw_creditos(screen):
    _phone(screen)
    sx, sy, sw, sh = config.PHONE_SCREEN
    cx = sx + sw // 2

    # ── Banda superior: degradado azul, logo y título ──
    alto_h = 178
    gfx.rect(screen, config.C_BLUE_DARK, (sx, sy, sw, alto_h), border_radius=18)
    gfx.rect(screen, config.C_BLUE_DARK, (sx, sy + 40, sw, alto_h - 40))
    for k in range(10):                                    # el azul se aclara hacia abajo
        t = (k + 1) / 10
        color = tuple(int(a + (b - a) * t * 0.55) for a, b in
                      zip(config.C_BLUE_DARK, config.C_BLUE))
        gfx.rect(screen, color, (sx, sy + 40 + k * (alto_h - 40) / 10, sw, (alto_h - 40) / 10 + 1))
    logo = pygame.Rect(cx - 32, sy + 38, 64, 64)
    gfx.rect(screen, (0, 0, 0, 50), logo.move(0, 4), border_radius=16)
    gfx.rect(screen, config.C_BLUE_LIGHT, logo, border_radius=16)
    gfx.rect(screen, config.C_BLUE, (logo.x + 17, logo.y + 14, 30, 36), border_radius=7)
    iconos.check(screen, logo.centerx, logo.centery + 1, 20, config.C_BG_WHITE, 3)
    _t(screen, "CLIC SEGURO", cx, sy + 112, config.C_BG_WHITE, "title", "midtop")
    _t(screen, "Simulador educativo de ciberseguridad", cx, sy + 146,
       (196, 214, 250), "small", "midtop")
    btn_volver = pygame.Rect(sx + 8, sy + 10, 70, 28)
    _btn(screen, btn_volver, "← Volver", (255, 255, 255, 36), config.C_BG_WHITE,
         (255, 255, 255, 100), "small")

    # ── Equipo ──
    x0, ancho = sx + 14, sw - 28
    y = sy + alto_h + 14
    _t(screen, "DESARROLLADO POR", x0 + 2, y, config.C_TEXT_2, "tiny")
    y += 15
    for ini_, nombre, color in (("JS", "José David Saza Montero", config.C_BLUE),
                                ("DC", "Daniel Calderón", config.C_GREEN)):
        card = pygame.Rect(x0, y, ancho, 40)
        gfx.rect(screen, config.C_BG_WHITE, card, border_radius=12)
        gfx.rect(screen, config.C_BORDER, card, width=1, border_radius=12)
        gfx.circle(screen, color, (card.x + 24, card.centery), 15)
        _t(screen, ini_, card.x + 24, card.centery, config.C_BG_WHITE, "btn", "center")
        _t(screen, nombre, card.x + 48, card.centery, config.C_TEXT, "h2", "midleft")
        y += 46

    # ── Proyecto ──
    y += 4
    card = pygame.Rect(x0, y, ancho, 62)
    gfx.rect(screen, config.C_BLUE_LIGHT, card, border_radius=12)
    iconos.escudo(screen, card.x + 26, card.centery, 30, config.C_BLUE)
    iconos.check(screen, card.x + 26, card.centery + 1, 15, config.C_BG_WHITE, 3)
    _t(screen, "Programación III", card.x + 50, card.y + 8, config.C_BLUE_DARK, "h2")
    _t(screen, "Ingeniería de Sistemas", card.x + 50, card.y + 29, config.C_TEXT_2, "small")
    _t(screen, "Noviembre de 2026", card.x + 50, card.y + 43, config.C_TEXT_2, "small")
    y += 62 + 14

    # ── ODS ──
    _t(screen, "OBJETIVOS DE DESARROLLO SOSTENIBLE", x0 + 2, y, config.C_TEXT_2, "tiny")
    y += 15
    for numero, texto, color in (("4", "Educación de calidad", (197, 25, 45)),
                                 ("9", "Industria, innovación e infraestructura", (243, 109, 37)),
                                 ("16", "Paz, justicia e instituciones sólidas", (0, 104, 157))):
        fila = pygame.Rect(x0, y, ancho, 28)
        gfx.rect(screen, config.C_BG_WHITE, fila, border_radius=9)
        gfx.rect(screen, config.C_BORDER, fila, width=1, border_radius=9)
        gfx.rect(screen, color, (fila.x, fila.y, 38, fila.height), border_radius=9)
        gfx.rect(screen, color, (fila.x + 20, fila.y, 18, fila.height))
        _t(screen, numero, fila.x + 19, fila.centery, config.C_BG_WHITE, "btn_lg", "center")
        _t(screen, _fit_linea(texto, ancho - 52, "small"), fila.x + 48, fila.centery,
           config.C_TEXT, "small", "midleft")
        y += 33

    # ── Pie ──
    y += 6
    _t(screen, f"Hecho con Python {sys.version_info.major}.{sys.version_info.minor}"
       f" y Pygame {pygame.version.ver}", cx, y, config.C_TEXT_3, "tiny", "midtop")
    _t(screen, "Cali, Colombia · 2026", cx, y + 15, config.C_TEXT_3, "tiny", "midtop")

    return {"volver_menu": btn_volver}


# ============================================================
# HOME
# ============================================================

DIAS_SEMANA = ["D", "L", "X", "J", "V"]


def _app_icon(screen, x, y, color, tipo):
    r = pygame.Rect(x, y, 44, 44)
    gfx.rect(screen, color, r, border_radius=12)
    cx, cy = r.centerx, r.centery

    if tipo == "contactos":
        gfx.circle(screen, config.C_BG_WHITE, (cx, cy - 6), 6)
        gfx.ellipse(screen, config.C_BG_WHITE, (cx - 11, cy + 2, 22, 14))
    elif tipo == "ajustes":
        gfx.circle(screen, config.C_BG_WHITE, (cx, cy), 9, 3)
        gfx.circle(screen, config.C_BG_WHITE, (cx, cy), 3)
    elif tipo == "cai":
        gfx.polygon(screen, config.C_BG_WHITE, [
            (cx, cy - 11), (cx + 9, cy - 5), (cx + 9, cy + 6),
            (cx, cy + 12), (cx - 9, cy + 6), (cx - 9, cy - 5),
        ])
    elif tipo == "correo":
        gfx.rect(screen, config.C_BG_WHITE,
                         (cx - 12, cy - 8, 24, 16), border_radius=2)
        gfx.line(screen, config.C_BLUE, (cx - 12, cy - 8), (cx, cy + 1), 2)
        gfx.line(screen, config.C_BLUE, (cx + 12, cy - 8), (cx, cy + 1), 2)
    elif tipo == "fotos":
        gfx.circle(screen, config.C_RED, (cx - 8, cy - 6), 5)
        gfx.circle(screen, config.C_BLUE, (cx + 6, cy + 4), 5)
        gfx.circle(screen, config.C_AMBER, (cx - 4, cy + 6), 5)
        gfx.circle(screen, config.C_GREEN, (cx + 8, cy - 4), 5)
        gfx.circle(screen, config.C_BG_WHITE, (cx, cy), 3)
    elif tipo == "calendario":
        gfx.rect(screen, config.C_RED, (cx - 12, cy - 11, 24, 8), border_radius=2)
        gfx.rect(screen, config.C_BG_WHITE, (cx - 12, cy - 5, 24, 16), border_radius=2)
        _t(screen, "12", cx, cy + 4, config.C_TEXT, "h2", "center")
    elif tipo == "musica":
        gfx.circle(screen, config.C_BG_WHITE, (cx - 6, cy + 8), 4)
        gfx.circle(screen, config.C_BG_WHITE, (cx + 8, cy + 6), 4)
        gfx.rect(screen, config.C_BG_WHITE, (cx - 3, cy - 8, 2, 18))
        gfx.rect(screen, config.C_BG_WHITE, (cx + 11, cy - 10, 2, 18))
        gfx.rect(screen, config.C_BG_WHITE, (cx - 3, cy - 8, 16, 3))
    elif tipo == "mensajes":
        gfx.ellipse(screen, config.C_BG_WHITE, (cx - 11, cy - 9, 22, 16))
        gfx.polygon(screen, config.C_BG_WHITE, [
            (cx - 6, cy + 5), (cx - 2, cy + 5), (cx - 4, cy + 10),
        ])
    elif tipo == "llamadas":
        gfx.polygon(screen, config.C_BG_WHITE, [
            (cx - 8, cy - 9), (cx - 5, cy - 9), (cx - 3, cy - 4),
            (cx - 6, cy - 1), (cx + 5, cy + 8), (cx + 8, cy + 5),
            (cx + 11, cy + 8), (cx + 11, cy + 11), (cx + 8, cy + 12),
            (cx - 4, cy + 2), (cx - 11, cy - 6),
        ])
    elif tipo == "instagram":
        gfx.rect(screen, config.C_BG_WHITE,
                         (cx - 11, cy - 11, 22, 22), width=2, border_radius=6)
        gfx.circle(screen, config.C_BG_WHITE, (cx, cy), 5, 2)
        gfx.circle(screen, config.C_BG_WHITE, (cx + 7, cy - 7), 2)
    elif tipo == "banco":
        _t(screen, "$", cx, cy, config.C_BG_WHITE, "h1", "center")

    return r


def _mini_icono(screen, tipo, cx, cy, color):
    """Íconos de ~16 px (vectoriales, nítidos a cualquier escala)."""
    if tipo == "llamada":                      # auricular
        pts = [(-8, -9), (-5, -9), (-3, -4), (-6, -1), (5, 8), (8, 5),
               (11, 8), (11, 11), (8, 12), (-4, 2), (-11, -6)]
        gfx.polygon(screen, color, [(cx + x * 0.62, cy + y * 0.62 - 1) for x, y in pts])
    elif tipo == "oficial":                    # edificio con columnas
        gfx.polygon(screen, color, [(cx - 9, cy - 3), (cx, cy - 9), (cx + 9, cy - 3)])
        for dx in (-6, -1, 4):
            gfx.rect(screen, color, (cx + dx, cy - 1, 3, 8))
        gfx.rect(screen, color, (cx - 9, cy + 8, 18, 2))
    elif tipo == "busqueda":                   # lupa
        gfx.circle(screen, color, (cx - 2, cy - 2), 6, 2)
        gfx.line(screen, color, (cx + 2.5, cy + 2.5), (cx + 8, cy + 8), 2)


def _draw_app(screen, x, y, label, color, tipo, botones, key, badge=0, badge_color=None):
    icon_rect = _app_icon(screen, x, y, color, tipo)
    _t(screen, label, icon_rect.centerx, icon_rect.bottom + 4,
       config.C_TEXT, "tiny", "midtop")

    if badge > 0:
        bx = icon_rect.right - 4
        by = icon_rect.y + 4
        gfx.circle(screen, badge_color or config.C_RED, (bx, by), 8)
        _t(screen, str(badge), bx, by, config.C_BG_WHITE, "tiny", "center")

    botones[f"app_{key}"] = icon_rect
    return icon_rect


def draw_home(screen, game):
    _phone(screen)
    sx, sy = config.PHONE_SCREEN[0], config.PHONE_SCREEN[1]
    sw = config.PHONE_SCREEN[2]
    sh = config.PHONE_SCREEN[3]
    btns = {}

    _t(screen, game.nivel.dia, sx + 14, sy + 8, config.C_TEXT, "small")
    _t(screen, f"{game.estado.xp} pts", sx + sw // 2, sy + 8,
       config.C_TEXT_2, "small", "midtop")
    _t(screen, f"{game.restantes_en_nivel()} nuevas",
       sx + sw - 14, sy + 8, config.C_TEXT_2, "small", "topright")
    gfx.line(screen, config.C_BORDER,
                     (sx + 8, sy + 30), (sx + sw - 8, sy + 30))

    saludo = config.SALUDO_POR_NIVEL.get(game.nivel.id, config.SALUDO_DEFECTO)
    _t(screen, saludo, sx + 14, sy + 42, config.C_TEXT_2, "small")
    _t(screen, config.NOMBRE_JUGADOR, sx + 14, sy + 60, config.C_TEXT, "h1")

    # ── Banner de matrícula (solo viernes sin pagar) ──
    y_widget = sy + 96
    if game.necesita_pagar_matricula():
        banner = pygame.Rect(sx + 14, y_widget, sw - 28, 62)
        gfx.rect(screen, (254, 242, 242), banner, border_radius=12)
        gfx.rect(screen, config.C_RED, banner, width=2, border_radius=12)
        _t(screen, "MATRÍCULA VENCE HOY", banner.x + 12, banner.y + 8,
           config.C_RED, "tiny")
        _t(screen, f"${config.MATRICULA}", banner.x + 12, banner.y + 24,
           config.C_TEXT, "h2")
        if game.puede_pagar_matricula():
            btn_pagar = pygame.Rect(banner.x + banner.width - 110,
                                    banner.y + 16, 100, 30)
            _btn(screen, btn_pagar, "Pagar", config.C_RED, config.C_BG_WHITE,
                 font="btn")
            btns["pagar_matricula"] = btn_pagar
        else:
            btn_pedir = pygame.Rect(banner.x + banner.width - 130,
                                    banner.y + 16, 120, 30)
            _btn(screen, btn_pedir, "Pedir préstamo", config.C_AMBER,
                 config.C_BG_WHITE, font="small")
            btns["abrir_prestamo"] = btn_pedir
        y_widget = banner.bottom + 8

    # ── Widget semana ──
    dia_actual = game.indice_dia_actual()
    tono = config.COLOR_DIA.get(dia_actual, config.COLOR_DIA[1])
    w = pygame.Rect(sx + 14, y_widget, sw - 28, 62)
    gfx.rect(screen, tono["fondo"], w, border_radius=12)
    gfx.rect(screen, tono["borde"], w, width=1, border_radius=12)
    _t(screen, "TU SEMANA", w.x + 12, w.y + 10, config.C_TEXT_2, "tiny")

    for i, d in enumerate(DIAS_SEMANA):
        cx = w.x + 26 + i * 26
        cy = w.y + 42
        if i < dia_actual:
            gfx.circle(screen, config.C_GREEN, (cx, cy), 9)
            col_d = config.C_BG_WHITE
        elif i == dia_actual:
            gfx.circle(screen, config.C_BG_WHITE, (cx, cy), 10)
            gfx.circle(screen, tono["acento"], (cx, cy), 10, 2)
            col_d = tono["acento"]
        else:
            gfx.circle(screen, tono["borde"], (cx, cy), 9)
            col_d = config.C_TEXT_2
        _t(screen, d, cx, cy, col_d, "tiny", "center")

    # ── Grid apps ──
    y1 = w.bottom + 24
    _t(screen, "APLICACIONES", sx + 14, y1 - 14, config.C_TEXT_2, "tiny")
    col_w = (sw - 28 - 3 * 8) // 4
    x1 = sx + 14
    _draw_app(screen, x1,                   y1, "Contactos", config.C_AMBER,
              "contactos", btns, "contactos")
    _draw_app(screen, x1 + col_w + 8,       y1, "Ajustes",   (107, 114, 128),
              "ajustes", btns, "ajustes")
    _draw_app(screen, x1 + 2 * (col_w + 8), y1, "CAI",       config.C_RED,
              "cai", btns, "cai")
    _draw_app(screen, x1 + 3 * (col_w + 8), y1, "Correo",    config.C_BLUE,
              "correo", btns, "correo")

    y2 = y1 + 72
    x2 = sx + 14 + (col_w // 2)
    _draw_app(screen, x2,                   y2, "Fotos",      config.C_BG_WHITE,
              "fotos", btns, "fotos")
    _draw_app(screen, x2 + col_w + 8,       y2, "Calendario", config.C_BG_WHITE,
              "calendario", btns, "calendario")
    _draw_app(screen, x2 + 2 * (col_w + 8), y2, "Música",     (236, 72, 153),
              "musica", btns, "musica")

    # ── Dock ──
    dock = pygame.Rect(sx + 8, sy + sh - 100, sw - 16, 82)
    gfx.rect(screen, (240, 242, 248), dock, border_radius=20)
    gfx.rect(screen, config.C_BORDER, dock, width=1, border_radius=20)

    dy = dock.y + 12
    dw = (dock.width - 32) // 4
    dx = dock.x + 8
    notif = game.restantes_en_nivel()
    _draw_app(screen, dx,                dy, "Mensajes",  config.C_WA_GREEN,
              "mensajes", btns, "mensajes", badge=notif)
    _draw_app(screen, dx + dw + 8,       dy, "Llamadas",  (52, 211, 153),
              "llamadas", btns, "llamadas")
    _draw_app(screen, dx + 2 * (dw + 8), dy, "Instagram", (225, 48, 108),
              "instagram", btns, "instagram")
    _draw_app(screen, dx + 3 * (dw + 8), dy, "Banco",     config.C_BLUE,
              "banco", btns, "banco")

    if notif > 0:
        _t(screen, f"Tienes {notif} notificación(es) sin abrir",
           sx + sw // 2, dock.y - 20, config.C_TEXT_2, "tiny", "midtop")

    btns["_zonas"] = {"semana": w}
    return btns


# ============================================================
# MODALES DE APPS
# ============================================================

def draw_modal_app(screen, tipo, game):
    gfx.overlay(screen, (0, 0, 0, 140))

    cx, cy = 65, 140
    cw, ch = 270, 400
    gfx.rect(screen, config.C_BG_WHITE, (cx, cy, cw, ch), border_radius=16)

    titulos = {
        "ajustes": "Ajustes de seguridad", "contactos": "Contactos",
        "cai": "CAI Virtual", "correo": "Correo", "fotos": "Fotos",
        "calendario": "Calendario", "musica": "Música", "llamadas": "Llamadas",
        "instagram": "Instagram", "banco": "Banco Nacional",
    }
    _t(screen, titulos.get(tipo, "App"), cx + 20, cy + 20, config.C_TEXT, "h2")
    gfx.line(screen, config.C_BORDER,
                     (cx + 20, cy + 50), (cx + cw - 20, cy + 50))

    y = cy + 70
    btns = {}

    if tipo == "ajustes":
        _t(screen, "Activa la protección:", cx + 20, y, config.C_TEXT_2, "small")
        y += 22
        _t(screen, "· Verificación en dos pasos (2FA)", cx + 20, y, config.C_TEXT, "body")
        y += 18
        _t(screen, "· Perfil privado en redes", cx + 20, y, config.C_TEXT, "body")
        y += 24
        _t(screen, "+15 de Privacidad (una vez)", cx + 20, y, config.C_TEXT_2, "small")
        y += 32
        if game.seguridad_activada():
            gfx.rect(screen, (236, 253, 245),
                             (cx + 20, y, cw - 40, 36), border_radius=8)
            _t(screen, "✓ Protección ya activada",
               cx + cw // 2, y + 18, config.C_GREEN, "small", "center")
        else:
            btn = pygame.Rect(cx + 20, y, cw - 40, 42)
            _btn(screen, btn, "Activar protección (+15)",
                 config.C_BLUE, config.C_BG_WHITE, font="btn_lg")
            btns["activar_proteccion"] = btn
        y += 52

    elif tipo == "contactos":
        lista = [("Mamá", "+57 310 555 0011"), ("Valentina", "+57 315 555 0042"),
                 ("Andrés", "+57 316 555 0077"),
                 ("Prof. Rodríguez", "prof.rodriguez@universidad.edu.co")]
        _t(screen, "Contactos guardados:", cx + 20, y, config.C_TEXT_2, "small")
        y += 22
        for nom, num in lista:
            gfx.circle(screen, config.C_AMBER, (cx + 34, y + 12), 8)
            _t(screen, nom, cx + 50, y + 2, config.C_TEXT, "body")
            _t(screen, _fit_linea(num, cw - 70, "tiny"),
               cx + 50, y + 18, config.C_TEXT_2, "tiny")
            y += 36

    elif tipo == "cai":
        _t(screen, "Canal oficial de denuncia", cx + 20, y, config.C_BLUE_DARK, "h2")
        y += 26
        _t(screen, "Denuncia fraudes, suplantación,", cx + 20, y, config.C_TEXT, "small")
        y += 16
        _t(screen, "extorsión o acoso.", cx + 20, y, config.C_TEXT, "small")
        y += 28
        _t(screen, "Usa el botón Reportar en el chat.", cx + 20, y, config.C_TEXT_2, "small")

    elif tipo == "correo":
        _t(screen, "Los correos aparecen como", cx + 20, y, config.C_TEXT, "small")
        y += 16
        _t(screen, "incidentes del chat.", cx + 20, y, config.C_TEXT, "small")
        y += 28
        _t(screen, "Revisa remitente y dominio.", cx + 20, y, config.C_TEXT_2, "small")

    elif tipo == "fotos":
        _t(screen, "Aún no tienes fotos.", cx + cw // 2, y + 20,
           config.C_TEXT_2, "body", "midtop")

    elif tipo == "calendario":
        _t(screen, f"Semana del {game.nivel.dia}", cx + 20, y, config.C_TEXT, "h2")
        y += 30
        dia_actual = game.indice_dia_actual()
        for i, d in enumerate(DIAS_SEMANA):
            cx_d = cx + 40 + i * 42
            cy_d = y + 20
            if i < dia_actual:
                gfx.circle(screen, config.C_GREEN, (cx_d, cy_d), 14)
                col_d = config.C_BG_WHITE
            elif i == dia_actual:
                gfx.circle(screen, config.C_BLUE_LIGHT, (cx_d, cy_d), 15)
                gfx.circle(screen, config.C_BLUE, (cx_d, cy_d), 15, 2)
                col_d = config.C_BLUE_DARK
            else:
                gfx.circle(screen, config.C_BORDER, (cx_d, cy_d), 14)
                col_d = config.C_TEXT_2
            _t(screen, d, cx_d, cy_d, col_d, "h2", "center")
        y += 60
        _t(screen, f"Día {game.nivel.id} de 4", cx + 20, y, config.C_TEXT_2, "small")

    elif tipo == "musica":
        _t(screen, "No es momento de música.", cx + 20, y, config.C_TEXT, "small")
        y += 20
        _t(screen, "Concéntrate en los mensajes.", cx + 20, y, config.C_TEXT_2, "small")

    elif tipo == "llamadas":
        _t(screen, "Recibirás llamadas falsas.", cx + 20, y, config.C_TEXT, "small")
        y += 20
        _t(screen, "Verifica el número antes de", cx + 20, y, config.C_TEXT_2, "small")
        y += 16
        _t(screen, "contestar.", cx + 20, y, config.C_TEXT_2, "small")

    elif tipo == "instagram":
        _t(screen, "Los mensajes de Instagram", cx + 20, y, config.C_TEXT, "small")
        y += 16
        _t(screen, "aparecen en el chat.", cx + 20, y, config.C_TEXT, "small")

    elif tipo == "banco":
        _t(screen, "Tu saldo actual:", cx + 20, y, config.C_TEXT_2, "small")
        y += 20
        if config.ECONOMIA_V2 and game.estado.dinero < 10000:
            _t(screen, f"${game.estado.dinero}", cx + 20, y, config.C_BLUE_DARK, "h1")
        else:
            _t(screen, f"${game.estado.dinero:,}".replace(",", "."),
               cx + 20, y, config.C_BLUE_DARK, "h1")
        y += 40
        if game.estado.matricula_pagada:
            _t(screen, "✓ Matrícula pagada", cx + 20, y, config.C_GREEN, "small")
        elif config.ECONOMIA_V2 and game.nivel.id == 4:
            _t(screen, "Matrícula pendiente: $500", cx + 20, y, config.C_RED, "small")

    btn_cerrar = pygame.Rect(cx + 20, cy + ch - 60, cw - 40, 42)
    _btn(screen, btn_cerrar, "Cerrar",
         config.C_TEXT, config.C_BG_WHITE, config.C_BORDER, "small")
    btns["cerrar_app"] = btn_cerrar
    return btns


# ============================================================
# LISTA DE MENSAJES
# ============================================================

def draw_message_list(screen, game, scroll_y, evento_idx=-1, evento_ms=0.0):
    """evento_idx/evento_ms: tarjeta de evento que cae desde el borde
    superior del viewport durante config.EVENTO_DROP_MS."""
    _phone(screen)
    sx, sy = config.PHONE_SCREEN[0], config.PHONE_SCREEN[1]
    sw = config.PHONE_SCREEN[2]
    sh = config.PHONE_SCREEN[3]

    _status_bar(screen, game,
                f"{len(game.estado.indices_respondidos)}/{len(game.nivel.incidentes)}")
    _hud(screen, game)

    btns = {}
    y = sy + 112
    btn_home = pygame.Rect(sx + 8, y, 28, 28)
    _btn(screen, btn_home, "⌂", config.C_BG_WHITE, config.C_BLUE,
         config.C_BORDER, "h2")
    btns["volver_home"] = btn_home
    _t(screen, "Mensajes", sx + 44, y + 2, config.C_TEXT, "h1")
    _t(screen, f"{game.restantes_en_nivel()} pendientes",
       sx + sw - 14, y + 6, config.C_TEXT_2, "tiny", "topright")
    y += 30
    gfx.line(screen, config.C_BORDER, (sx + 8, y), (sx + sw - 8, y))
    y += 6

    top = y
    bottom = sy + sh - 8
    viewport_h = bottom - top
    viewport = pygame.Rect(sx + 6, top, sw - 12, viewport_h)

    items = game.incidentes_en_nivel()
    CARD_H = config.MSG_CARD_H
    GAP = config.MSG_CARD_GAP
    total_h = len(items) * (CARD_H + GAP) + 10
    max_scroll = max(0, total_h - viewport_h)

    content = gfx.surface(viewport.width, max(total_h, viewport_h),
                          config.C_BG_WHITE)

    cy = 4
    for idx, inc in items:
        responded = game.esta_respondido(idx)

        # Animación drop-in: solo cambia DÓNDE se dibuja la tarjeta (cy).
        # Como el rect del clic más abajo se calcula con ese mismo cy, dibujo
        # y clic coinciden en cada frame (mismo criterio que el fix del scroll).
        cy_layout = cy
        if idx == evento_idx and evento_ms < config.EVENTO_DROP_MS:
            t = max(0.0, evento_ms) / config.EVENTO_DROP_MS
            e = 1 - (1 - t) ** 3                       # ease-out cúbico
            inicio = min(scroll_y - CARD_H, cy_layout)  # justo sobre el viewport
            cy = int(inicio + (cy_layout - inicio) * e)

        card = pygame.Rect(0, cy, viewport.width, CARD_H)

        if responded:
            gfx.rect(content, (248, 250, 252), card, border_radius=10)
            gfx.rect(content, config.C_BORDER, card, width=1, border_radius=10)
            gfx.rect(content, config.C_GREEN,
                             (0, cy + 4, 4, CARD_H - 8), border_radius=2)
        elif inc.es_evento:
            gfx.rect(content, (255, 251, 235), card, border_radius=10)
            gfx.rect(content, config.C_AMBER, card, width=1, border_radius=10)
            gfx.rect(content, config.C_AMBER,
                             (0, cy + 4, 4, CARD_H - 8), border_radius=2)
        elif inc.requiere_urgencia and game.nivel.id >= 2:
            gfx.rect(content, config.C_BG_WHITE, card, border_radius=10)
            gfx.rect(content, config.C_BORDER, card, width=1, border_radius=10)
            gfx.rect(content, config.C_AMBER,
                             (0, cy + 4, 4, CARD_H - 8), border_radius=2)
        else:
            gfx.rect(content, config.C_BG_WHITE, card, border_radius=10)
            gfx.rect(content, config.C_BORDER, card, width=1, border_radius=10)
            gfx.rect(content, config.C_BLUE,
                             (0, cy + 4, 4, CARD_H - 8), border_radius=2)

        av_cx = 28
        av_cy = cy + CARD_H // 2
        if responded:
            gfx.circle(content, config.C_GREEN, (av_cx, av_cy), 13)
            gfx.lines(content, config.C_BG_WHITE, False,
                              [(av_cx - 5, av_cy), (av_cx - 1, av_cy + 4),
                               (av_cx + 6, av_cy - 5)], 2)
        else:
            gfx.circle(content, config.C_BLUE_LIGHT, (av_cx, av_cy), 13)
            inicial = inc.remitente.nombre[0].upper()
            _t(content, inicial, av_cx, av_cy, config.C_BLUE_DARK, "h2", "center")

        color_nom = config.C_TEXT if not responded else config.C_TEXT_2
        nombre_txt = _fit_linea(inc.remitente.nombre, viewport.width - 100, "h2")
        _t(content, nombre_txt, 52, cy + 6, color_nom, "h2")

        preview = inc.texto.replace("\n", " ")
        if len(preview) > 55:
            preview = preview[:55].rstrip() + "…"
        prev_rect = pygame.Rect(0, 0, viewport.width - 100, 40)
        lines = _wrap_lines(preview, prev_rect, "small")[:2]
        py = cy + 24
        for ln in lines:
            _t(content, ln, 52, py,
               config.C_TEXT_2 if not responded else config.C_TEXT_3, "small")
            py += 13

        if responded:
            _t(content, "✓", viewport.width - 16, cy + 12,
               config.C_GREEN, "h2", "topright")
        elif inc.es_evento:
            badge = pygame.Rect(viewport.width - 64, cy + 10, 52, 16)
            gfx.rect(content, config.C_AMBER_LIGHT, badge, border_radius=8)
            _t(content, "EVENTO", badge.centerx, badge.centery,
               config.C_TIMER_FG, "tiny", "center")
        elif inc.requiere_urgencia and game.nivel.id >= 2:
            badge = pygame.Rect(viewport.width - 64, cy + 10, 52, 16)
            gfx.rect(content, config.C_TIMER_BG, badge, border_radius=8)
            _t(content, "URGENTE", badge.centerx, badge.centery,
               config.C_TIMER_FG, "tiny", "center")

        _t(content, "›", viewport.width - 10, cy + CARD_H // 2,
           config.C_TEXT_3, "h1", "midright")

        screen_rect = pygame.Rect(
            viewport.x,
            viewport.y + cy - scroll_y,
            viewport.width,
            CARD_H,
        )
        if not responded:
            clipped = screen_rect.clip(viewport)
            if clipped.height > 10:
                btns[f"open_{idx}"] = clipped

        cy = cy_layout + CARD_H + GAP

    # ── FIX: blit sin area + set_clip ──
    # Con esto, el pixel (0, cy) de content va a
    # (viewport.x, viewport.y + cy - scroll_y) en pantalla,
    # EXACTAMENTE donde está el rect del clic.
    gfx.clip(screen, viewport)
    gfx.blit(screen, content, (viewport.x, viewport.y - scroll_y))
    gfx.clip(screen, None)

    # Scrollbar
    if total_h > viewport.height:
        rel = scroll_y / max_scroll if max_scroll > 0 else 0
        sb_x = sx + sw - 4
        sb_h = max(24, int(viewport.height * viewport.height / total_h))
        sb_y = viewport.y + int((viewport.height - sb_h) * rel)
        gfx.rect(screen, (220, 220, 230),
                         (sb_x, viewport.y, 3, viewport.height), border_radius=2)
        gfx.rect(screen, (150, 150, 160),
                         (sb_x, sb_y, 3, sb_h), border_radius=2)
        if scroll_y < max_scroll - 4:
            hint = gfx.surface(viewport.width, 22)
            hint.fill((255, 255, 255, 220))
            _t(hint, "↓ desliza para ver más", viewport.width // 2, 11,
               config.C_TEXT_2, "tiny", "center")
            gfx.blit(screen, hint, (viewport.x, bottom - 22))

    btns["_zonas"] = {"hud": pygame.Rect(sx + 8, sy + 34, sw - 16, 52)}
    return btns

# ============================================================
# CHAT (detalle de incidente)
# ============================================================

def _pulso_borde(screen, rect):
    """Anillo azul que late alrededor de un botón (tutorial contextual).
    Usa el reloj de pygame: no necesita estado en main.py."""
    s = (math.sin(pygame.time.get_ticks() / 250.0) + 1) / 2     # 0..1
    grosor = 2 + int(2 * s)
    aro = rect.inflate(4 + int(6 * s), 4 + int(6 * s))
    alfa = 90 + 16 * round(120 * s / 16)    # escalonado: gfx reutiliza la forma
    gfx.rect(screen, (*config.C_BLUE, alfa), aro, width=grosor, border_radius=11)


def draw_chat(screen, game, idx, pulsar_tools=False):
    """pulsar_tools=True: tutorial del Nivel 0, resalta las herramientas."""
    _phone(screen)
    sx, sy = config.PHONE_SCREEN[0], config.PHONE_SCREEN[1]
    sw = config.PHONE_SCREEN[2]
    inc = game.incidente_por_indice(idx)
    btns = {}

    _status_bar(screen, game,
                f"{len(game.estado.indices_respondidos)}/{len(game.nivel.incidentes)}")
    _hud(screen, game)

    y = sy + 112
    btn_volver = pygame.Rect(sx + 10, y, 70, 24)
    _btn(screen, btn_volver, "← Lista", config.C_BG_WHITE, config.C_BLUE, None, "tiny")
    btns["volver_lista"] = btn_volver

    y = sy + 145
    max_nombre = 22 if not inc.remitente.en_contactos else 28
    nombre_corto = _truncate(inc.remitente.nombre, max_nombre)
    max_num = 26 if not inc.remitente.en_contactos else 32
    numero_corto = _truncate(inc.remitente.numero, max_num)

    _t(screen, nombre_corto, sx + 14, y, config.C_TEXT, "h2")
    _t(screen, numero_corto, sx + 14, y + 20, config.C_TEXT_2, "tiny")
    if not inc.remitente.en_contactos:
        _t(screen, "no está en contactos", sx + sw - 14, y + 20,
           config.C_RED, "tiny", "topright")

    if game.timer_para(idx) and game.estado.timer_activo:
        _draw_timer(screen, game.estado.tiempo_restante)

    y = sy + 185
    texto_rect = pygame.Rect(0, 0, sw - 48, 300)
    lineas = _wrap_lines(inc.texto, texto_rect, "small")
    if len(lineas) > 6:
        lineas = lineas[:6]
        lineas[-1] = _fit_linea(lineas[-1] + "…", texto_rect.width, "small")
    alto = len(lineas) * 14 + 22
    box_h = max(50, min(alto, 130))
    box = pygame.Rect(sx + 14, y, sw - 28, box_h)
    gfx.rect(screen, (243, 244, 246), box, border_radius=12)
    ty = box.y + 10
    for ln in lineas:
        _t(screen, ln, box.x + 14, ty, config.C_TEXT, "small")
        ty += 14

    y = box.bottom + 18

    # Indicador "Verificado"
    verificado = game.fue_verificado(idx)
    if verificado:
        _t(screen, "✓ Verificado", sx + sw - 14, y, config.C_GREEN, "tiny", "topright")

    if pulsar_tools:
        _t(screen, "Toca una herramienta para investigar", sx + 14, y,
           config.C_BLUE, "tiny")
    else:
        _t(screen, "HERRAMIENTAS (opcional, +5 pts)", sx + 14, y,
           config.C_TEXT_2, "tiny")
    y += 16
    bw = (sw - 28 - 16) // 3
    for i, (k, lbl) in enumerate([("remitente", "Remitente"),
                                  ("enlace", "Enlace"),
                                  ("contactos", "Contactos")]):
        r = pygame.Rect(sx + 14 + i * (bw + 8), y, bw, 34)
        disabled = (k == "enlace" and inc.enlace is None)
        bg = (240, 240, 240) if disabled else config.C_BG_WHITE
        fg = config.C_TEXT_3 if disabled else config.C_TEXT
        _btn(screen, r, lbl, bg, fg, config.C_BORDER, "small",
             hover=False if disabled else None)
        if not disabled:
            btns[f"tool_{k}"] = r
            if pulsar_tools:
                _pulso_borde(screen, r)
    y += 46

    _t(screen, "¿Qué hace Camilo?", sx + 14, y, config.C_TEXT, "h2")
    y += 22

    # Botón Verificar (destacado con azul claro)
    # Fila 1: Confiar / Verificar / Ignorar
    aw = (sw - 28 - 16) // 3
    acciones_fila1 = [("confiar", "Confiar"), ("verificar", "Verificar"),
                      ("ignorar", "Ignorar")]
    for i, (k, lbl) in enumerate(acciones_fila1):
        r = pygame.Rect(sx + 14 + i * (aw + 8), y, aw, 42)
        is_verificar = (k == "verificar")
        bg = config.C_BLUE_LIGHT if is_verificar else config.C_BG_WHITE
        fg = config.C_BLUE_DARK if is_verificar else config.C_TEXT
        # Verificar se destaca solo con su fondo; el borde azul es del hover.
        _btn(screen, r, lbl, bg, fg, config.C_BORDER)
        btns[f"action_{k}"] = r
    y += 50

    # Fila 2: Bloquear / Reportar
    aw2 = (sw - 28 - 8) // 2
    for i, (k, lbl) in enumerate([("bloquear", "Bloquear"),
                                   ("reportar", "Reportar")]):
        r = pygame.Rect(sx + 14 + i * (aw2 + 8), y, aw2, 42)
        _btn(screen, r, lbl, config.C_BG_WHITE, config.C_TEXT, config.C_BORDER)
        btns[f"action_{k}"] = r

    btns["_zonas"] = {"mensaje": box}
    return btns


def draw_modal(screen, modal):
    gfx.overlay(screen, (0, 0, 0, 140))

    cx, cy = 65, 130
    cw, ch = 270, 420
    gfx.rect(screen, config.C_BG_WHITE, (cx, cy, cw, ch), border_radius=16)
    _t(screen, "Información", cx + 20, cy + 20, config.C_TEXT, "h2")
    gfx.line(screen, config.C_BORDER,
                     (cx + 20, cy + 50), (cx + cw - 20, cy + 50))

    y = cy + 65
    tipo = modal["tipo"]

    if tipo == "remitente":
        r = modal["remitente"]
        filas = [
            ("Nombre", r.nombre, config.C_TEXT),
            ("Número", r.numero, config.C_TEXT),
            ("En contactos", "Sí" if r.en_contactos else "No",
             config.C_GREEN if r.en_contactos else config.C_RED),
            ("Cuenta creada", f"{r.cuenta_dias} días",
             config.C_AMBER if r.cuenta_dias < 30 else config.C_TEXT),
            ("Reportes", str(r.reportes),
             config.C_AMBER if r.reportes > 0 else config.C_TEXT),
            ("Verificado", "Sí" if r.verificado else "No",
             config.C_GREEN if r.verificado else config.C_RED),
        ]
        for lbl, val, col in filas:
            _t(screen, lbl, cx + 20, y, config.C_TEXT_2, "small")
            _t(screen, _fit_linea(val, cw - 110, "small"),
               cx + cw - 20, y, col, "small", "topright")
            y += 22
        y += 10
        gfx.rect(screen, config.C_AMBER_LIGHT,
                         (cx + 20, y, cw - 40, 90), border_radius=10)
        _t(screen, "PISTA", cx + 32, y + 10, (146, 64, 14), "tiny")
        _wrap(screen, r.pista, pygame.Rect(cx + 32, y + 26, cw - 64, 60),
              (120, 53, 15), "small")

    elif tipo == "enlace":
        e = modal["enlace"]
        _t(screen, "URL del mensaje:", cx + 20, y, config.C_TEXT_2, "small")
        y += 18
        _t(screen, _fit_linea(e.url, cw - 40, "body"),
           cx + 20, y, config.C_TEXT, "body")
        y += 28
        _t(screen, "Dominio OFICIAL" if e.oficial else "Dominio NO oficial",
           cx + 20, y, config.C_GREEN if e.oficial else config.C_RED, "h2")
        y += 28
        gfx.rect(screen, config.C_AMBER_LIGHT,
                         (cx + 20, y, cw - 40, 90), border_radius=10)
        _t(screen, "PISTA", cx + 32, y + 10, (146, 64, 14), "tiny")
        _wrap(screen, e.pista, pygame.Rect(cx + 32, y + 26, cw - 64, 60),
              (120, 53, 15), "small")

    elif tipo == "contactos":
        r = modal["remitente"]
        _t(screen, "Comparando con tu agenda:", cx + 20, y, config.C_TEXT_2, "small")
        y += 22
        _t(screen, _fit_linea(r.nombre, cw - 40, "h2"),
           cx + 20, y, config.C_TEXT, "h2")
        y += 22
        _t(screen, _fit_linea(r.numero, cw - 40, "small"),
           cx + 20, y, config.C_TEXT_2, "small")
        y += 32
        if r.en_contactos:
            _t(screen, "OK: COINCIDE con tu contacto", cx + 20, y, config.C_GREEN, "h2")
        else:
            _t(screen, "X: NO está en tus contactos", cx + 20, y, config.C_RED, "h2")

    btn = pygame.Rect(cx + 20, cy + ch - 60, cw - 40, 42)
    _btn(screen, btn, "Entendido", config.C_BLUE, config.C_BG_WHITE)
    return {"cerrar_modal": btn}


# ============================================================
# VERIFICACIÓN (nueva)
# ============================================================

def draw_verificacion(screen, game, idx, resultado, metodo_actual):
    _phone(screen)
    sx, sy = config.PHONE_SCREEN[0], config.PHONE_SCREEN[1]
    sw = config.PHONE_SCREEN[2]

    inc = game.incidente_por_indice(idx)
    btns = {}

    # Header
    y = sy + 30
    btn_volver = pygame.Rect(sx + 8, y, 70, 30)
    _btn(screen, btn_volver, "← Chat", config.C_BG_WHITE, config.C_BLUE, None, "small")
    btns["volver_chat"] = btn_volver
    _t(screen, "Verificación", sx + sw // 2, y + 6, config.C_TEXT, "h2", "midtop")
    gfx.line(screen, config.C_BORDER, (sx + 8, y + 40), (sx + sw - 8, y + 40))

    y = y + 56
    _t(screen, "Sobre:", sx + 14, y, config.C_TEXT_2, "tiny")
    y += 14
    _t(screen, _fit_linea(inc.remitente.nombre, sw - 28, "h2"),
       sx + 14, y, config.C_TEXT, "h2")
    y += 24
    _t(screen, _fit_linea(inc.remitente.numero, sw - 28, "tiny"),
       sx + 14, y, config.C_TEXT_2, "tiny")
    y += 24
    gfx.line(screen, config.C_BORDER, (sx + 8, y), (sx + sw - 8, y))
    y += 12

    _t(screen, "¿Cómo quieres investigar?", sx + 14, y, config.C_TEXT, "h2")
    y += 24

    # 3 botones de método
    metodos = [("llamada", "Llamar al remitente", "Puede costar reputación si es legítimo"),
               ("oficial", "Canal oficial", "Consulta el canal del banco o empresa"),
               ("busqueda", "Buscar en internet", "Ve reportes de otros usuarios")]

    for metodo_id, label, sub in metodos:
        card = pygame.Rect(sx + 14, y, sw - 28, 56)
        ya_verificado = game.fue_verificado(idx)
        es_actual = (metodo_actual == metodo_id)
        bg = config.C_BLUE_LIGHT if es_actual else config.C_BG_WHITE
        bd = config.C_BLUE if es_actual else config.C_BORDER
        gfx.rect(screen, bg, card, border_radius=10)
        gfx.rect(screen, bd, card, width=1, border_radius=10)
        _mini_icono(screen, metodo_id, card.x + 24, card.y + 28, config.C_BLUE_DARK)
        _t(screen, label, card.x + 46, card.y + 8, config.C_TEXT, "body")
        _t(screen, sub, card.x + 46, card.y + 28, config.C_TEXT_2, "tiny")
        btns[f"verif_{metodo_id}"] = card
        y += 62

    # Resultado
    y += 4
    gfx.line(screen, config.C_BORDER, (sx + 8, y), (sx + sw - 8, y))
    y += 12
    _t(screen, "RESULTADO", sx + 14, y, config.C_TEXT_2, "tiny")
    y += 16

    if resultado:
        res_box = pygame.Rect(sx + 14, y, sw - 28, 100)
        gfx.rect(screen, config.C_AMBER_LIGHT, res_box, border_radius=10)
        gfx.rect(screen, config.C_AMBER, res_box, width=1, border_radius=10)
        _wrap(screen, resultado, res_box.inflate(-20, -20), (120, 53, 15), "small")
    else:
        _t(screen, "Selecciona un método para investigar.",
           sx + 14, y + 10, config.C_TEXT_3, "small")

    return btns


# ============================================================
# GASTOS DEL DÍA (nueva)
# ============================================================

def draw_gastos_dia(screen, gasto):
    _phone(screen)
    sx, sy = config.PHONE_SCREEN[0], config.PHONE_SCREEN[1]
    sw = config.PHONE_SCREEN[2]

    gfx.overlay(screen, (0, 0, 0, 160))

    card = pygame.Rect(sx + 30, sy + 200, sw - 60, 260)
    gfx.rect(screen, config.C_BG_WHITE, card, border_radius=16)
    gfx.rect(screen, config.C_BLUE, (card.x + 14, card.y, card.width - 28, 4),
                     border_radius=2)

    # Icono
    gfx.circle(screen, config.C_BLUE_LIGHT, (card.centerx, card.y + 60), 30)
    _t(screen, "$", card.centerx, card.y + 60, config.C_BLUE_DARK, "title", "center")

    _t(screen, "Gasto del día", card.centerx, card.y + 105, config.C_TEXT_2, "small", "midtop")
    _t(screen, gasto["concepto"], card.centerx, card.y + 125, config.C_TEXT, "h1", "midtop")
    _t(screen, f"${gasto['monto']}", card.centerx, card.y + 158, config.C_RED, "h1", "midtop")

    btn = pygame.Rect(card.x + 20, card.y + card.height - 70, card.width - 40, 44)
    _btn(screen, btn, f"Pagar ${gasto['monto']}", config.C_BLUE, config.C_BG_WHITE,
         font="btn_lg")
    return {"pagar_gasto": btn}


# ============================================================
# MATRÍCULA (nueva)
# ============================================================

def draw_matricula_pago(screen, game, prestamo_resp):
    _phone(screen)
    sx, sy = config.PHONE_SCREEN[0], config.PHONE_SCREEN[1]
    sw = config.PHONE_SCREEN[2]

    btns = {}
    y = sy + 30
    btn_volver = pygame.Rect(sx + 8, y, 70, 30)
    _btn(screen, btn_volver, "← Volver", config.C_BG_WHITE, config.C_BLUE, None, "small")
    btns["volver_home"] = btn_volver

    # Card principal
    card = pygame.Rect(sx + 14, sy + 80, sw - 28, 320)
    gfx.rect(screen, (254, 242, 242), card, border_radius=14)
    gfx.rect(screen, config.C_RED, card, width=2, border_radius=14)

    gfx.circle(screen, config.C_RED, (card.centerx, card.y + 55), 28)
    _t(screen, "!", card.centerx, card.y + 55, config.C_BG_WHITE, "title", "center")

    _t(screen, "Matrícula vence hoy", card.centerx, card.y + 100,
       config.C_RED, "h1", "midtop")
    _t(screen, f"${config.MATRICULA}", card.centerx, card.y + 135,
       config.C_TEXT, "title", "midtop")

    _t(screen, "Tu saldo:", card.centerx, card.y + 185,
       config.C_TEXT_2, "small", "midtop")
    if config.ECONOMIA_V2 and game.estado.dinero < 10000:
        dinero_txt = f"${game.estado.dinero}"
    else:
        dinero_txt = f"${game.estado.dinero:,}".replace(",", ".")
    _t(screen, dinero_txt, card.centerx, card.y + 205,
       config.C_TEXT, "h1", "midtop")

    if game.puede_pagar_matricula():
        btn_pagar = pygame.Rect(card.x + 20, card.y + card.height - 70,
                                card.width - 40, 44)
        _btn(screen, btn_pagar, f"Pagar ${config.MATRICULA}",
             config.C_BLUE, config.C_BG_WHITE, font="btn_lg")
        btns["pagar_matricula"] = btn_pagar
    else:
        _t(screen, "No te alcanza. Pide prestado a mamá.",
           card.centerx, card.y + 240, config.C_TEXT_2, "small", "midtop")

        if not game.estado.prestamo_pedido:
            btn_50 = pygame.Rect(card.x + 20, card.y + card.height - 110,
                                 (card.width - 52) // 2, 40)
            btn_100 = pygame.Rect(card.x + 32 + (card.width - 52) // 2,
                                  card.y + card.height - 110,
                                  (card.width - 52) // 2, 40)
            _btn(screen, btn_50, "Pedir $50", config.C_BLUE_LIGHT,
                 config.C_BLUE_DARK, config.C_BLUE, "small")
            _btn(screen, btn_100, "Pedir $100", config.C_AMBER_LIGHT,
                 config.C_TIMER_FG, config.C_AMBER, "small")
            btns["prestamo_50"] = btn_50
            btns["prestamo_100"] = btn_100
        else:
            if game.estado.prestamo_negado:
                _t(screen, "Mamá no puede prestarte esta vez.",
                   card.centerx, card.y + 265, config.C_RED, "small", "midtop")
            else:
                _t(screen, "Mamá ya te prestó. Ahora puedes pagar.",
                   card.centerx, card.y + 265, config.C_GREEN, "small", "midtop")

    # Resultado de préstamo
    if prestamo_resp:
        if prestamo_resp.get("aprobado"):
            info = pygame.Rect(sx + 14, sy + 420, sw - 28, 60)
            gfx.rect(screen, (236, 253, 245), info, border_radius=10)
            _t(screen, f"Mamá te prestó ${prestamo_resp['monto']}",
               info.centerx, info.centery - 8, config.C_GREEN, "h2", "center")
            _t(screen, "(con un regaño incluido)",
               info.centerx, info.centery + 12, config.C_TEXT_2, "tiny", "center")
        else:
            info = pygame.Rect(sx + 14, sy + 420, sw - 28, 60)
            gfx.rect(screen, (254, 242, 242), info, border_radius=10)
            _t(screen, "Mamá no puede prestarte.",
               info.centerx, info.centery - 8, config.C_RED, "h2", "center")
            _t(screen, "Tendrás que arreglártelas.",
               info.centerx, info.centery + 12, config.C_TEXT_2, "tiny", "center")

    return btns


# ============================================================
# FIN DE SEMANA (nueva)
# ============================================================

def draw_fin_semana(screen, game, motivo):
    """
    motivo ∈ {"sin_matricula", "parcial"}
    """
    _phone(screen)
    sx, sy = config.PHONE_SCREEN[0], config.PHONE_SCREEN[1]
    sw = config.PHONE_SCREEN[2]

    btns = {}

    if motivo == "sin_matricula":
        # Escena: mamá regaña
        gfx.rect(screen, (254, 242, 242),
                         (sx + 14, sy + 25, sw - 28, 130), border_radius=14)
        gfx.circle(screen, config.C_RED, (sx + sw // 2, sy + 65), 28)
        _t(screen, "!", sx + sw // 2, sy + 65, config.C_BG_WHITE, "title", "center")
        _t(screen, "Fin del semestre", sx + sw // 2, sy + 105,
           config.C_RED, "h1", "midtop")
        _t(screen, "No pudiste pagar la matrícula", sx + sw // 2, sy + 130,
           config.C_TEXT_2, "small", "midtop")

        # Texto del regaño
        y = sy + 180
        text_rect = pygame.Rect(sx + 20, y, sw - 40, 220)
        _t(screen, "MENSAJE DE MAMÁ", text_rect.x, text_rect.y, config.C_TEXT_2, "tiny")
        y += 18
        regaño = (
            "Hijo, te lo advertí. Ese dinero era para tu matrícula. "
            "Mañana hablamos con la universidad para ver qué se puede hacer. "
            "La próxima vez, verifica antes de confiar. No vuelvas a caer en eso."
        )
        _wrap(screen, regaño, pygame.Rect(text_rect.x, y, text_rect.width, 200),
              config.C_TEXT, "small")

        # Botones
        btn_retry = pygame.Rect(sx + 20, sy + 440, sw - 40, 44)
        _btn(screen, btn_retry, "Reintentar viernes", config.C_BLUE,
             config.C_BG_WHITE, font="btn_lg")
        btns["repetir_viernes"] = btn_retry

        btn_menu = pygame.Rect(sx + 20, sy + 495, sw - 40, 38)
        _btn(screen, btn_menu, "Volver al menú", config.C_BG_WHITE,
             config.C_TEXT_2, config.C_BORDER, "small")
        btns["menu"] = btn_menu

    else:  # parcial
        gfx.rect(screen, (254, 251, 235),
                         (sx + 14, sy + 25, sw - 28, 120), border_radius=14)
        _t(screen, "Casi lo logras", sx + sw // 2, sy + 55,
           (146, 64, 14), "h1", "midtop")
        _t(screen, "Pagaste la matrícula, pero no alcanzaste", sx + sw // 2, sy + 90,
           config.C_TEXT_2, "small", "midtop")
        _t(screen, f"el 70% de los puntos ({config.UMBRAL_CERTIF}).",
           sx + sw // 2, sy + 106, config.C_TEXT_2, "small", "midtop")

        y = sy + 170
        _t(screen, f"Puntaje final: {game.estado.xp}", sx + sw // 2, y,
           config.C_TEXT, "h1", "midtop")
        _t(screen, f"Necesitabas {config.UMBRAL_CERTIF}",
           sx + sw // 2, y + 30, config.C_TEXT_2, "small", "midtop")

        y += 90
        _t(screen, "Repasa tus aprendizajes y vuelve a intentarlo.",
           sx + sw // 2, y, config.C_TEXT_2, "small", "midtop")

        btn_retry = pygame.Rect(sx + 20, sy + 440, sw - 40, 44)
        _btn(screen, btn_retry, "Reintentar viernes", config.C_BLUE,
             config.C_BG_WHITE, font="btn_lg")
        btns["repetir_viernes"] = btn_retry

        btn_menu = pygame.Rect(sx + 20, sy + 495, sw - 40, 38)
        _btn(screen, btn_menu, "Volver al menú", config.C_BG_WHITE,
             config.C_TEXT_2, config.C_BORDER, "small")
        btns["menu"] = btn_menu

    return btns


# ============================================================
# FEEDBACK
# ============================================================

def draw_feedback(screen, result, is_error):
    _phone(screen)
    sx, sy = config.PHONE_SCREEN[0], config.PHONE_SCREEN[1]
    sw = config.PHONE_SCREEN[2]

    parcial = bool(result.get("parcial"))      # no cayó, pero había algo mejor
    color = (config.C_AMBER if parcial
             else config.C_RED if is_error else config.C_GREEN)
    card = pygame.Rect(sx + 14, sy + 40, sw - 28, 480)
    gfx.rect(screen, config.C_BG_WHITE, card, border_radius=14)
    gfx.rect(screen, color, (card.x + 14, card.y, card.width - 28, 4),
                     border_radius=2)

    gfx.circle(screen, color, (card.centerx, card.y + 55), 24)
    if parcial:
        _t(screen, "!", card.centerx, card.y + 55, config.C_BG_WHITE, "title", "center")
    elif is_error:
        gfx.line(screen, config.C_BG_WHITE,
                         (card.centerx - 8, card.y + 47),
                         (card.centerx + 8, card.y + 63), 3)
        gfx.line(screen, config.C_BG_WHITE,
                         (card.centerx + 8, card.y + 47),
                         (card.centerx - 8, card.y + 63), 3)
    else:
        gfx.lines(screen, config.C_BG_WHITE, False,
                          [(card.centerx - 9, card.y + 55),
                           (card.centerx - 3, card.y + 62),
                           (card.centerx + 10, card.y + 48)], 3)

    _t(screen, "No caíste, pero…" if parcial
       else "Fallaste" if is_error else "¡Bien hecho!",
       card.centerx, card.y + 98, color, "h1", "midtop")

    if result.get("auto_por_timer"):
        _t(screen, "Se agotó el tiempo → Confiar automático",
           card.centerx, card.y + 118, config.C_AMBER, "tiny", "midtop")

    y = card.y + 140
    _t(screen, f"Acción: {result['accion']}", card.x + 20, y, config.C_TEXT_2, "small")
    y += 24

    if is_error and result["impacto_aplicado"]:
        imp = result["impacto_aplicado"]
        for k, et in [("privacidad", "Privacidad"),
                      ("dinero", "Saldo"),
                      ("reputacion", "Reputación")]:
            v = imp.get(k, 0)
            if v < 0:
                if k == "dinero" and config.ECONOMIA_V2 and abs(v) < 10000:
                    txt = f"-${abs(v)}"
                elif k == "dinero":
                    txt = f"${v:,}".replace(",", ".")
                else:
                    txt = str(v)
                _t(screen, f"{txt} {et}", card.x + 20, y, config.C_RED, "body")
                y += 18
    elif parcial:
        _t(screen, "No pierdes nada, pero tampoco sumas puntos.",
           card.x + 20, y, config.C_TEXT_2, "small")
        y += 20
    elif not is_error:
        if result["puntos"] > 0:
            _t(screen, f"+{result['puntos']} puntos", card.x + 20, y,
               config.C_GREEN, "h2")
            y += 20
            if result["herramienta_usada"]:
                _t(screen, "(incluye +5 por herramienta)",
                   card.x + 20, y, config.C_TEXT_2, "tiny")
                y += 16
        # Un acierto también puede costar dinero (pagar/ayudar) o dar respeto
        imp = result.get("impacto_aplicado") or {}
        if imp.get("dinero", 0) < 0:
            _t(screen, f"-${abs(imp['dinero'])} Saldo", card.x + 20, y,
               config.C_AMBER, "body")
            y += 18
        if imp.get("reputacion", 0) > 0:
            _t(screen, f"+{imp['reputacion']} Reputación", card.x + 20, y,
               config.C_GREEN, "body")
            y += 18

    y += 8
    gfx.line(screen, config.C_BORDER,
                     (card.x + 20, y), (card.x + card.width - 20, y))
    y += 12
    _wrap(screen, result["feedback"],
          pygame.Rect(card.x + 20, y, card.width - 40, 110), config.C_TEXT, "small")

    btn = pygame.Rect(card.x + 20, card.y + card.height - 60, card.width - 40, 42)
    _btn(screen, btn, "Siguiente", config.C_BLUE, config.C_BG_WHITE, font="btn_lg")
    return {"siguiente": btn}


def draw_panel(screen, consejo, elapsed_ms=0, skipped=False):
    _phone(screen)
    sx, sy = config.PHONE_SCREEN[0], config.PHONE_SCREEN[1]
    sw = config.PHONE_SCREEN[2]

    gfx.rect(screen, config.C_AMBER_LIGHT,
                     (sx + 14, sy + 30, sw - 28, 70), border_radius=12)
    _t(screen, "El Consejo de Camilo", sx + 28, sy + 50, (146, 64, 14), "h2")
    _t(screen, "Aprende lo que pasó y por qué", sx + 28, sy + 72,
       (120, 53, 15), "small")

    card = pygame.Rect(sx + 14, sy + 115, sw - 28, 380)
    gfx.rect(screen, config.C_BG_WHITE, card, border_radius=14)
    gfx.rect(screen, config.C_BORDER, card, width=1, border_radius=14)

    y = card.y + 20
    _t(screen, "TIPO DE ATAQUE", card.x + 20, y, config.C_TEXT_2, "tiny")
    y += 14
    gfx.rect(screen, (254, 226, 226),
                     (card.x + 20, y, 140, 20), border_radius=10)
    _t(screen, consejo.tipo.upper(), card.x + 30, y + 5, (153, 27, 27), "tiny")
    y += 32
    gfx.line(screen, config.C_BORDER,
                     (card.x + 20, y), (card.x + card.width - 20, y))
    y += 14

    _t(screen, _fit_linea(consejo.titulo, card.width - 40, "h2"),
       card.x + 20, y, config.C_TEXT, "h2")
    y += 28

    texto_rect = pygame.Rect(card.x + 20, y, card.width - 40, 180)
    lines = _wrap_lines(consejo.texto, texto_rect, "small")
    visible = 99999 if skipped else int((elapsed_ms / 1000) * config.TYPEWRITER_CPS)
    end_x, end_y, all_visible = _draw_typing(
        screen, lines, texto_rect.x, texto_rect.y, visible, (55, 65, 81), "small"
    )

    if not all_visible and not skipped:
        if int(elapsed_ms / 500) % 2 == 0:
            gfx.rect(screen, config.C_BLUE,
                             (end_x + 1, end_y, 2, _fm["small"].get_height()))

    y += 160
    gfx.line(screen, config.C_BORDER,
                     (card.x + 20, y), (card.x + card.width - 20, y))
    y += 14
    _t(screen, "Guardado en Aprendizajes", card.x + 20, y, config.C_GREEN, "small")

    btn = pygame.Rect(card.x + 20, card.y + card.height - 55, card.width - 40, 42)
    _btn(screen, btn, "Entendido", config.C_BLUE, config.C_BG_WHITE, font="btn_lg")
    return {"entendido": btn, "_done": all_visible or skipped}


# ============================================================
# RESUMEN, DERROTA, CERTIFICADO
# ============================================================

def draw_resumen(screen, game):
    _phone(screen)
    sx, sy = config.PHONE_SCREEN[0], config.PHONE_SCREEN[1]
    sw = config.PHONE_SCREEN[2]

    _t(screen, f"Fin del {game.nivel.dia}", sx + sw // 2, sy + 40,
       config.C_TEXT, "h1", "midtop")
    _t(screen, f"Puntos totales: {game.estado.xp}", sx + sw // 2, sy + 68,
       config.C_GREEN, "h2", "midtop")
    gfx.line(screen, config.C_BORDER,
                     (sx + 20, sy + 100), (sx + sw - 20, sy + 100))

    y = sy + 120
    _t(screen, "Estado final:", sx + 20, y, config.C_TEXT_2, "small")
    y += 20
    est = game.estado
    dinero_txt = f"${est.dinero}" if (config.ECONOMIA_V2 and est.dinero < 10000) \
                 else f"${est.dinero:,}".replace(",", ".")
    for et, val, col in [
        ("Privacidad", est.privacidad,
         config.C_GREEN if est.privacidad > 30 else config.C_RED),
        ("Dinero", dinero_txt, config.C_TEXT),
        ("Reputación", est.reputacion,
         config.C_GREEN if est.reputacion > 30 else config.C_RED),
    ]:
        _t(screen, et, sx + 20, y, config.C_TEXT, "small")
        _t(screen, str(val), sx + sw - 20, y, col, "small", "topright")
        y += 18

    # Estado matrícula
    if config.ECONOMIA_V2 and game.nivel.id == 4:
        y += 6
        if est.matricula_pagada:
            _t(screen, "✓ Matrícula pagada", sx + 20, y, config.C_GREEN, "small")
        else:
            _t(screen, "✗ Matrícula pendiente", sx + 20, y, config.C_RED, "small")
        y += 16

    y += 8
    gfx.line(screen, config.C_BORDER,
                     (sx + 20, y), (sx + sw - 20, y))
    y += 14

    btns = {}

    if game.recursos_bajos():
        warn = pygame.Rect(sx + 20, y, sw - 40, 36)
        gfx.rect(screen, (254, 242, 242), warn, border_radius=8)
        _t(screen, "Recursos bajos, repetir recomendado",
           warn.centerx, warn.centery, config.C_RED, "small", "center")
        y += 44

    res = game.resultado_nivel()

    if game.nivel.id == 4:
        if res == "sin_matricula":
            _t(screen, "No pagaste la matrícula.", sx + 20, y, config.C_RED, "small")
            y += 22
            btn = pygame.Rect(sx + 20, y, sw - 40, 44)
            _btn(screen, btn, "Ver consecuencias", config.C_RED,
                 config.C_BG_WHITE, font="btn_lg")
            btns["ver_fin_semana"] = btn
            y += 52
        elif res == "parcial":
            _t(screen, "No alcanzaste el 70%. Repite el viernes.",
               sx + 20, y, config.C_RED, "small")
            y += 22
            btn = pygame.Rect(sx + 20, y, sw - 40, 44)
            _btn(screen, btn, "Ver resultado", config.C_AMBER,
                 config.C_BG_WHITE, font="btn_lg")
            btns["ver_fin_semana"] = btn
            y += 52
        else:
            btn = pygame.Rect(sx + 20, y, sw - 40, 44)
            _btn(screen, btn, "Ver certificado", config.C_BLUE,
                 config.C_BG_WHITE, font="btn_lg")
            btns["continuar"] = btn
            y += 52

    elif res == "repetir_n3":
        _t(screen, "Necesitas >30 en Priv y Rep para pasar.",
           sx + 20, y, config.C_RED, "small")
        y += 20
        _t(screen, "Repite el jueves para mejorar.",
           sx + 20, y, config.C_TEXT_2, "tiny")
        y += 24
        btn = pygame.Rect(sx + 20, y, sw - 40, 44)
        _btn(screen, btn, "Repetir jueves", config.C_BLUE,
             config.C_BG_WHITE, font="btn_lg")
        btns["repetir"] = btn
        y += 52

    else:
        _t(screen, f"Mañana recuperas +{config.REP_NUEVO_DIA} de reputación.",
           sx + 20, y, config.C_GREEN, "tiny")
        y += 18
        btn = pygame.Rect(sx + 20, y, sw - 40, 44)
        _btn(screen, btn, "Continuar al siguiente día",
             config.C_BLUE, config.C_BG_WHITE, font="btn_lg")
        btns["continuar"] = btn
        y += 52
        btn_r = pygame.Rect(sx + 20, y, sw - 40, 40)
        _btn(screen, btn_r, "Repetir este día",
             config.C_BG_WHITE, config.C_TEXT, config.C_BORDER)
        btns["repetir"] = btn_r
        y += 48

    btn_m = pygame.Rect(sx + 20, y, sw - 40, 32)
    _btn(screen, btn_m, "Volver al menú",
         config.C_BG_WHITE, config.C_TEXT_2, config.C_BORDER, "small")
    btns["menu"] = btn_m
    return btns


def draw_derrota(screen, game):
    _phone(screen)
    sx, sy = config.PHONE_SCREEN[0], config.PHONE_SCREEN[1]
    sw = config.PHONE_SCREEN[2]

    gfx.rect(screen, (254, 242, 242),
                     (sx + 14, sy + 30, sw - 28, 100), border_radius=12)
    gfx.circle(screen, config.C_RED, (sx + sw // 2, sy + 65), 22)
    gfx.line(screen, config.C_BG_WHITE,
                     (sx + sw // 2 - 7, sy + 58),
                     (sx + sw // 2 + 7, sy + 72), 3)
    gfx.line(screen, config.C_BG_WHITE,
                     (sx + sw // 2 + 7, sy + 58),
                     (sx + sw // 2 - 7, sy + 72), 3)
    _t(screen, "Fin del nivel", sx + sw // 2, sy + 95,
       (153, 27, 27), "h2", "midtop")

    est = game.estado
    info = game.info_derrota()
    motivo = info["motivo"]
    if motivo == "gasto":
        razon = f"No pudiste pagar: {info['concepto']}"
        detalle = (f"Hoy necesitabas ${info['monto']} y solo tenías "
                   f"${info['dinero']}. Sin dinero para lo básico no puedes "
                   "seguir la semana.")
    elif motivo == "dinero":
        razon = "Tu saldo llegó a 0"
        detalle = ("Las estafas y los pagos te dejaron sin dinero. Sin saldo "
                   "no puedes cubrir los gastos del día ni la matrícula.")
    elif motivo == "reputacion":
        razon = "Tu reputación llegó a 0"
        detalle = ("Tu familia y tus contactos dejaron de confiar en ti: "
                   "te suplantaron la cuenta o no ayudaste cuando debías.")
    else:
        razon = "Tu privacidad llegó a 0"
        detalle = ("Entregaste demasiados datos o códigos y perdiste el "
                   "control de tu información.")
    _t(screen, _fit_linea(razon, sw - 40, "body"), sx + sw // 2, sy + 142,
       config.C_RED, "body", "midtop")
    _wrap(screen, detalle, pygame.Rect(sx + 20, sy + 166, sw - 40, 72),
          config.C_TEXT, "small")

    y = sy + 248
    gfx.line(screen, config.C_BORDER,
                     (sx + 20, y), (sx + sw - 20, y))
    y += 12
    for et, val, col in [
        ("Privacidad", est.privacidad,
         config.C_RED if est.privacidad <= 0 else config.C_TEXT),
        ("Dinero", f"${est.dinero}" if (config.ECONOMIA_V2 and est.dinero < 10000)
         else f"${est.dinero:,}".replace(",", "."),
         config.C_RED if est.dinero <= 0 else config.C_TEXT),
        ("Reputación", est.reputacion,
         config.C_RED if est.reputacion <= 0 else config.C_TEXT),
    ]:
        _t(screen, et, sx + 20, y, config.C_TEXT_2, "small")
        _t(screen, str(val), sx + sw - 20, y, col, "small", "topright")
        y += 20

    y += 16
    btns = {}
    if info["puede_repetir"]:
        _t(screen, "La seguridad se aprende fallando.", sx + 20, y,
           config.C_TEXT_2, "small")
        y += 16
        _t(screen, "Repite el nivel para intentarlo otra vez.", sx + 20, y,
           config.C_TEXT_2, "tiny")
        btn = pygame.Rect(sx + 20, sy + 420, sw - 40, 44)
        _btn(screen, btn, "Repetir el nivel", config.C_BLUE,
             config.C_BG_WHITE, font="btn_lg")
        btns["repetir_nivel"] = btn
        btn_m = pygame.Rect(sx + 20, sy + 475, sw - 40, 36)
        _btn(screen, btn_m, "Volver al menú",
             config.C_BG_WHITE, config.C_TEXT_2, config.C_BORDER, "small")
    else:
        # Repetir dejaría el mismo saldo y volvería a perder: no se ofrece.
        _wrap(screen,
              "Repetir el nivel no cambiaría tu saldo, así que no se ofrece. "
              "Empieza una partida nueva y cuida tu dinero desde el Domingo.",
              pygame.Rect(sx + 20, y, sw - 40, 70), config.C_TEXT_2, "small")
        btn_m = pygame.Rect(sx + 20, sy + 420, sw - 40, 44)
        _btn(screen, btn_m, "Empezar de nuevo", config.C_BLUE,
             config.C_BG_WHITE, font="btn_lg")
    btns["menu"] = btn_m
    return btns


def draw_certificado(screen, game):
    _phone(screen)
    sx, sy = config.PHONE_SCREEN[0], config.PHONE_SCREEN[1]
    sw = config.PHONE_SCREEN[2]

    gfx.rect(screen, (255, 251, 235),
                     (sx + 14, sy + 25, sw - 28, 420), border_radius=12)
    gfx.rect(screen, (217, 119, 6),
                     (sx + 14, sy + 25, sw - 28, 420), width=2, border_radius=12)
    gfx.rect(screen, (245, 158, 11),
                     (sx + 22, sy + 33, sw - 44, 404), width=1, border_radius=8)

    gfx.circle(screen, (245, 158, 11), (sx + sw // 2, sy + 80), 28)
    gfx.circle(screen, (251, 191, 36), (sx + sw // 2, sy + 80), 22)
    gfx.circle(screen, config.C_BG_WHITE, (sx + sw // 2, sy + 80), 16)
    gfx.polygon(screen, (245, 158, 11), [
        (sx + sw // 2 - 8, sy + 80), (sx + sw // 2 - 4, sy + 74),
        (sx + sw // 2, sy + 78), (sx + sw // 2 + 4, sy + 74),
        (sx + sw // 2 + 8, sy + 80), (sx + sw // 2 + 5, sy + 86),
        (sx + sw // 2 - 5, sy + 86),
    ])

    _t(screen, "CERTIFICADO", sx + sw // 2, sy + 125, (146, 64, 14), "small", "midtop")
    _t(screen, "Ciudadano Digital", sx + sw // 2, sy + 145, config.C_TEXT, "h1", "midtop")
    _t(screen, "otorgado a", sx + sw // 2, sy + 172, config.C_TEXT_2, "tiny", "midtop")
    _t(screen, "Camilo", sx + sw // 2, sy + 192, config.C_BLUE_DARK, "h1", "midtop")
    gfx.line(screen, (217, 119, 6),
                     (sx + 80, sy + 222), (sx + sw - 80, sy + 222))

    _t(screen, "por completar la semana con", sx + sw // 2, sy + 235,
       config.C_TEXT_2, "tiny", "midtop")
    _t(screen, f"{game.estado.xp} puntos", sx + sw // 2, sy + 255,
       config.C_GREEN, "h1", "midtop")
    _t(screen, f"de un máximo de {game.puntaje_maximo()}",
       sx + sw // 2, sy + 285, config.C_TEXT_3, "tiny", "midtop")

    gfx.line(screen, (252, 211, 77),
                     (sx + 40, sy + 310), (sx + sw - 40, sy + 310))
    _t(screen, f"Consejos aprendidos: {len(game.estado.historial_consejos)}",
       sx + sw // 2, sy + 325, config.C_TEXT, "small", "midtop")
    _t(screen, '"La seguridad empieza por detenerse',
       sx + sw // 2, sy + 360, (146, 64, 14), "tiny", "midtop")
    _t(screen, 'antes de hacer clic."',
       sx + sw // 2, sy + 375, (146, 64, 14), "tiny", "midtop")

    btn_ap = pygame.Rect(sx + 20, sy + 460, sw - 40, 36)
    _btn(screen, btn_ap, "Ver mis aprendizajes",
         config.C_BG_WHITE, config.C_TEXT, config.C_BORDER, "small")
    btn = pygame.Rect(sx + 20, sy + 505, sw - 40, 44)
    _btn(screen, btn, "Volver al menú", config.C_BLUE,
         config.C_BG_WHITE, font="btn_lg")
    return {"ver_aprendizajes": btn_ap, "menu": btn}

# ============================================================
# BANCO OTP (Fase E)
# ============================================================

def draw_banco_otp(screen, game, idx, codigo, ya_generado):
    """App del banco para generar y enviar un código OTP."""
    _phone(screen)
    sx, sy = config.PHONE_SCREEN[0], config.PHONE_SCREEN[1]
    sw = config.PHONE_SCREEN[2]
    inc = game.incidente_por_indice(idx)
    btns = {}

    # Header tipo app del banco
    gfx.rect(screen, config.C_BLUE, (sx, sy, sw, 70))
    _t(screen, "Banco Nacional", sx + 16, sy + 24, config.C_BG_WHITE, "h2")
    _t(screen, "Seguridad y verificación", sx + 16, sy + 46,
       config.C_BLUE_LIGHT, "tiny")
    gfx.line(screen, config.C_BLUE_DARK, (sx, sy + 70), (sx + sw, sy + 70))

    # Botón cerrar (X) arriba derecha
    btn_cerrar = pygame.Rect(sx + sw - 40, sy + 20, 30, 30)
    _btn(screen, btn_cerrar, "✕", config.C_BLUE_DARK, config.C_BG_WHITE, None, "h2")
    btns["cancelar_otp"] = btn_cerrar

    y = sy + 95
    _t(screen, "SOLICITUD DE CÓDIGO", sx + 14, y, config.C_TEXT_2, "tiny")
    y += 16

    # Card del remitente
    card = pygame.Rect(sx + 14, y, sw - 28, 80)
    gfx.rect(screen, config.C_BG_WHITE, card, border_radius=12)
    gfx.rect(screen, config.C_BORDER, card, width=1, border_radius=12)

    _t(screen, "Solicitado por:", card.x + 12, card.y + 10, config.C_TEXT_2, "tiny")
    _t(screen, _fit_linea(inc.remitente.nombre, card.width - 24, "h2"),
       card.x + 12, card.y + 26, config.C_TEXT, "h2")
    _t(screen, _fit_linea(inc.remitente.numero, card.width - 24, "tiny"),
       card.x + 12, card.y + 50, config.C_TEXT_2, "tiny")
    y = card.bottom + 20

    if not ya_generado:
        _t(screen, "El remitente solicita tu código de", sx + 14, y,
           config.C_TEXT, "small")
        y += 16
        _t(screen, "verificación de 6 dígitos.", sx + 14, y, config.C_TEXT, "small")
        y += 32

        btn_generar = pygame.Rect(sx + 14, y, sw - 28, 50)
        _btn(screen, btn_generar, "Generar código de 6 dígitos",
             config.C_BLUE, config.C_BG_WHITE, font="btn_lg")
        btns["generar_otp"] = btn_generar
    else:
        # Advertencia
        warn = pygame.Rect(sx + 14, y, sw - 28, 40)
        gfx.rect(screen, (254, 242, 242), warn, border_radius=8)
        _t(screen, "⚠ NUNCA compartas este código",
           warn.centerx, warn.centery, config.C_RED, "small", "center")
        y += 50

        # Código grande
        _t(screen, "TU CÓDIGO", sx + sw // 2, y, config.C_TEXT_2, "tiny", "midtop")
        y += 18
        codigo_fmt = f"{codigo[:3]} {codigo[3:]}" if len(codigo) == 6 else codigo
        code_box = pygame.Rect(sx + 14, y, sw - 28, 70)
        gfx.rect(screen, config.C_BLUE_LIGHT, code_box, border_radius=12)
        gfx.rect(screen, config.C_BLUE, code_box, width=2, border_radius=12)
        _t(screen, codigo_fmt, code_box.centerx, code_box.centery,
           config.C_BLUE_DARK, "title", "center")
        y = code_box.bottom + 16

        _t(screen, "Este código permite entrar a tu", sx + 14, y,
           config.C_TEXT_2, "tiny")
        y += 12
        _t(screen, "cuenta. Solo tú debes usarlo.", sx + 14, y, config.C_TEXT_2, "tiny")
        y += 30

        # Advertencia final
        _t(screen, "¿Deseas enviarlo a", sx + 14, y, config.C_TEXT, "small")
        y += 14
        _t(screen, _fit_linea(inc.remitente.nombre, sw - 28, "body"),
           sx + 14, y, config.C_RED, "body")
        y += 24

        btn_enviar = pygame.Rect(sx + 14, y, sw - 28, 50)
        _btn(screen, btn_enviar, f"Enviar a {_truncate(inc.remitente.nombre, 18)}",
             config.C_RED, config.C_BG_WHITE, font="btn_lg")
        btns["enviar_otp"] = btn_enviar
        y += 58

        btn_arr = pygame.Rect(sx + 14, y, sw - 28, 44)
        _btn(screen, btn_arr, "Arrepentirme (no enviar)",
             config.C_BG_WHITE, config.C_TEXT, config.C_BORDER, "small")
        btns["cancelar_otp"] = btn_arr

    return btns


# ============================================================
# BANCO TRANSFERENCIA (Fase E)
# ============================================================

def draw_banco_transferencia(screen, game, idx, monto_str, modo_otro):
    """App del banco para enviar dinero con monto seleccionable."""
    _phone(screen)
    sx, sy = config.PHONE_SCREEN[0], config.PHONE_SCREEN[1]
    sw = config.PHONE_SCREEN[2]
    inc = game.incidente_por_indice(idx)
    btns = {}

    # Header tipo app del banco
    gfx.rect(screen, config.C_BLUE, (sx, sy, sw, 70))
    _t(screen, "Banco Nacional", sx + 16, sy + 24, config.C_BG_WHITE, "h2")
    _t(screen, "Enviar dinero", sx + 16, sy + 46, config.C_BLUE_LIGHT, "tiny")
    gfx.line(screen, config.C_BLUE_DARK, (sx, sy + 70), (sx + sw, sy + 70))

    btn_cerrar = pygame.Rect(sx + sw - 40, sy + 20, 30, 30)
    _btn(screen, btn_cerrar, "✕", config.C_BLUE_DARK, config.C_BG_WHITE, None, "h2")
    btns["cancelar_transferencia"] = btn_cerrar

    y = sy + 88
    _t(screen, "DESTINATARIO", sx + 14, y, config.C_TEXT_2, "tiny")
    y += 14

    # Card destinatario (con titular visible = clave anti-suplantación)
    card = pygame.Rect(sx + 14, y, sw - 28, 100)
    gfx.rect(screen, config.C_BG_WHITE, card, border_radius=12)
    gfx.rect(screen, config.C_BORDER, card, width=1, border_radius=12)

    _t(screen, _fit_linea(inc.remitente.nombre, card.width - 24, "h2"),
       card.x + 12, card.y + 8, config.C_TEXT, "h2")
    _t(screen, "Cuenta: **** " + (inc.cuenta_destino or "0000"),
       card.x + 12, card.y + 32, config.C_TEXT_2, "tiny")
    if inc.monto_solicitado > 0:
        # Se acepta exactamente este monto (ni más ni menos)
        _t(screen, f"Te piden ${inc.monto_solicitado}", card.right - 12,
           card.y + 32, config.C_TIMER_FG, "tiny", "topright")

    _t(screen, "Titular:", card.x + 12, card.y + 54, config.C_TEXT_2, "tiny")
    titular_txt = inc.titular_destino or "(desconocido)"
    _t(screen, _fit_linea(titular_txt, card.width - 24, "small"),
       card.x + 12, card.y + 70, config.C_TEXT, "small")

    # Si el titular no coincide con el remitente, resaltar en ámbar
    nombre_rem = inc.remitente.nombre.lower()
    titular_low = titular_txt.lower()
    if (inc.categoria == "fraude"
            and nombre_rem not in titular_low
            and "verificado" not in titular_low):
        warn_badge = pygame.Rect(card.right - 70, card.y + 54, 58, 14)
        gfx.rect(screen, config.C_AMBER_LIGHT, warn_badge, border_radius=7)
        _t(screen, "⚠ revisa", warn_badge.centerx, warn_badge.centery,
           config.C_TIMER_FG, "tiny", "center")

    y = card.bottom + 14

    # Monto actual
    _t(screen, "MONTO A ENVIAR", sx + 14, y, config.C_TEXT_2, "tiny")
    y += 14
    monto_display = f"$ {monto_str or '0'}"
    monto_box = pygame.Rect(sx + 14, y, sw - 28, 50)
    gfx.rect(screen, (255, 251, 235), monto_box, border_radius=10)
    gfx.rect(screen, config.C_AMBER, monto_box, width=2, border_radius=10)
    _t(screen, monto_display, monto_box.centerx, monto_box.centery,
       (146, 64, 14), "title", "center")
    y = monto_box.bottom + 12

    # Verificar saldo
    try:
        monto_int = int(monto_str) if monto_str else 0
    except ValueError:
        monto_int = 0
    # El monto debe ser exactamente lo que piden, y alcanzar con el saldo
    motivo = (game.motivo_monto_invalido(idx, monto_int)
              if monto_int > 0 else "monto_invalido")
    aviso = None
    if not game.saldo_alcanza_para(idx) or motivo == "saldo_insuficiente":
        aviso = "⚠ No te alcanza el saldo para esto"
    elif motivo == "monto_incorrecto":
        aviso = f"⚠ Debe ser exactamente ${inc.monto_solicitado}"
    if aviso:
        _t(screen, aviso, sx + 14, y, config.C_RED, "tiny")
        y += 14

    if modo_otro:
        # Numpad 3x4
        _t(screen, "Ingresa el monto:", sx + 14, y, config.C_TEXT_2, "tiny")
        y += 14
        teclas = [("1", "2", "3"), ("4", "5", "6"),
                  ("7", "8", "9"), ("C", "0", "⌫")]
        bw = (sw - 28 - 16) // 3
        bh = 40
        for r, fila in enumerate(teclas):
            for c, k in enumerate(fila):
                kr = pygame.Rect(sx + 14 + c * (bw + 8), y + r * (bh + 6), bw, bh)
                color = config.C_BG_WHITE
                fg = config.C_TEXT
                if k == "C":
                    color = (254, 226, 226); fg = config.C_RED
                elif k == "⌫":
                    color = config.C_AMBER_LIGHT; fg = config.C_TIMER_FG
                _btn(screen, kr, k, color, fg, config.C_BORDER, "h2")
                btns[f"numpad_{k}"] = kr
        y += 4 * (bh + 6) + 6

    else:
        # Botones rápidos de monto
        _t(screen, "Selecciona un monto:", sx + 14, y, config.C_TEXT_2, "tiny")
        y += 14
        monto_req = inc.monto_solicitado or 50
        # El monto pedido siempre está entre las opciones (0 = "Otro")
        otros = [m for m in (50, 100, 200) if m != monto_req][:2]
        opciones = sorted({monto_req, *otros}) + [0]
        bw = (sw - 28 - 24) // 4
        for i, m in enumerate(opciones):
            br = pygame.Rect(sx + 14 + i * (bw + 8), y, bw, 40)
            label = f"${m}" if m > 0 else "Otro"
            is_selected = (monto_int == m and m > 0) or (m == 0 and monto_str == "")
            bg = config.C_BLUE_LIGHT if is_selected else config.C_BG_WHITE
            bd = config.C_BLUE if is_selected else config.C_BORDER
            _btn(screen, br, label, bg, config.C_TEXT, bd, "small")
            if m > 0:
                btns[f"monto_{m}"] = br
            else:
                btns["monto_otro"] = br
        y += 52

    # Botones Confirmar / Cancelar
    if monto_int > 0 and motivo is None:
        btn_conf = pygame.Rect(sx + 14, y, sw - 28, 50)
        _btn(screen, btn_conf, f"Confirmar ${monto_int}",
             config.C_RED, config.C_BG_WHITE, font="btn_lg")
        btns["confirmar_transferencia"] = btn_conf
        y += 58

    btn_cancel = pygame.Rect(sx + 14, y, sw - 28, 38)
    _btn(screen, btn_cancel, "Cancelar",
         config.C_BG_WHITE, config.C_TEXT, config.C_BORDER, "small")
    btns["cancelar_transferencia"] = btn_cancel

    return btns