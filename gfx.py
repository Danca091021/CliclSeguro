"""gfx.py — Capa de dibujo con escala y suavizado (anti-aliasing).

Por qué existe
--------------
En Windows con escala de pantalla > 100% (p. ej. 125%), un programa que no
declara soportarla ve su ventana de 400x700 *estirada* por el sistema: todo se
ve borroso y pixelado, y agrandar la ventana no lo arregla porque el dibujo
sigue siendo de 400x700 píxeles.

Solución (spec 12): el programa se declara compatible con la escala, abre la
ventana al tamaño real (400*S x 700*S píxeles) y dibuja a esa resolución.

Cómo funciona
-------------
ui.py sigue dibujando en coordenadas LÓGICAS (400x700). Las funciones de este
módulo las multiplican por la escala `S` y dibujan con suavizado:

  * formas (círculos, polígonos, rectángulos redondeados, líneas inclinadas) se
    dibujan 2-4 veces más grandes y se reducen (supersampling); el resultado se
    guarda en una caché porque la interfaz casi no cambia entre frames;
  * rectángulos rectos y líneas horizontales/verticales se dibujan directos
    (ya quedan nítidos al caer en píxeles enteros).

Las firmas imitan a pygame.draw (rect, circle, ellipse, line, lines, polygon).
No depende de config ni de la lógica del juego.
"""
import collections
import ctypes
import math
import sys

import pygame

S = 1.0                          # escala actual (píxeles reales por píxel lógico)

_cache = collections.OrderedDict()
_CACHE_MAX = 1500


def init(escala):
    """Fija la escala de dibujo y vacía la caché."""
    global S
    S = float(escala)
    _cache.clear()


# ============================================================
# Conversión lógico -> real
# ============================================================

def px(valor):
    return int(round(valor * S))


def rect_px(r):
    """Rect lógico -> Rect en píxeles reales (redondeando bordes, no tamaños,
    para que rectángulos contiguos no dejen huecos)."""
    r = pygame.Rect(r)
    x0, y0 = round(r.x * S), round(r.y * S)
    x1, y1 = round(r.right * S), round(r.bottom * S)
    return pygame.Rect(x0, y0, x1 - x0, y1 - y0)


def surface(ancho, alto, fondo=None):
    """Superficie con el tamaño lógico dado, en píxeles reales.
    Sin `fondo`: transparente. Con `fondo`: opaca de ese color."""
    tam = (max(1, px(ancho)), max(1, px(alto)))
    if fondo is None:
        return pygame.Surface(tam, pygame.SRCALPHA)
    s = pygame.Surface(tam)
    s.fill(fondo)
    return s


def a_logico(pos):
    """Posición del ratón en píxeles reales -> coordenadas lógicas 400x700."""
    return (pos[0] / S, pos[1] / S)


def blit(destino, origen, pos):
    destino.blit(origen, (round(pos[0] * S), round(pos[1] * S)))


def clip(superficie, rect):
    """Recorte de dibujo en coordenadas lógicas (None lo quita)."""
    superficie.set_clip(None if rect is None else rect_px(rect))


def overlay(superficie, color):
    """Cubre toda la superficie con un color translúcido (modales)."""
    capa = pygame.Surface(superficie.get_size(), pygame.SRCALPHA)
    capa.fill(color)
    superficie.blit(capa, (0, 0))


# ============================================================
# Formas con suavizado (cacheadas)
# ============================================================

def _factor(w, h):
    """Cuánto agrandar para suavizar: menos en formas enormes (memoria)."""
    area = w * h
    if area <= 40_000:
        return 4
    if area <= 250_000:
        return 3
    return 2


def _suave(superficie, color, caja, clave, dibujar):
    """Dibuja una forma suavizada dentro de `caja` (Rect en píxeles reales).
    dibujar(grande, K, color) la pinta en una superficie K veces mayor con
    coordenadas relativas a caja.topleft."""
    w, h = caja.w, caja.h
    if w <= 0 or h <= 0:
        return
    col = tuple(color)
    if len(col) == 3:
        col += (255,)
    k = (w, h, clave, col)
    img = _cache.get(k)
    if img is None:
        K = _factor(w, h)
        grande = pygame.Surface((w * K, h * K), pygame.SRCALPHA)
        # Mismo RGB con alfa 0: así los bordes reducidos no se oscurecen.
        grande.fill((col[0], col[1], col[2], 0))
        dibujar(grande, K, col)
        img = pygame.transform.smoothscale(grande, (w, h))
        _cache[k] = img
        if len(_cache) > _CACHE_MAX:
            _cache.popitem(last=False)
    else:
        _cache.move_to_end(k)
    superficie.blit(img, caja.topleft)


def _grosor(width):
    return 0 if not width else max(1, round(width * S))


def _caja_puntos(puntos, margen):
    xs = [p[0] for p in puntos]
    ys = [p[1] for p in puntos]
    x0, y0 = math.floor(min(xs)) - margen, math.floor(min(ys)) - margen
    x1, y1 = math.ceil(max(xs)) + margen, math.ceil(max(ys)) + margen
    return pygame.Rect(x0, y0, x1 - x0, y1 - y0)


def _rel(puntos, caja):
    """Puntos relativos a la caja, cuantizados a 1/4 de píxel (clave estable)."""
    return tuple((round((x - caja.x) * 4) / 4, round((y - caja.y) * 4) / 4)
                 for x, y in puntos)


def rect(superficie, color, rect, width=0, border_radius=0):
    r = rect_px(rect)
    if r.w <= 0 or r.h <= 0:
        return
    grosor = _grosor(width)
    radio = max(0, round(border_radius * S))
    opaco = len(color) == 3 or color[3] == 255
    if radio == 0 and opaco:
        pygame.draw.rect(superficie, color, r, grosor)
        return
    radio = min(radio, min(r.w, r.h) // 2)

    def dibujar(grande, K, col):
        pygame.draw.rect(grande, col, (0, 0, r.w * K, r.h * K), grosor * K,
                         border_radius=radio * K)

    _suave(superficie, color, r, ("r", grosor, radio), dibujar)


def circle(superficie, color, center, radius, width=0):
    cx, cy, rad = center[0] * S, center[1] * S, radius * S
    caja = _caja_puntos([(cx - rad, cy - rad), (cx + rad, cy + rad)], 1)
    (rx, ry), = _rel([(cx, cy)], caja)
    rr = round(rad * 4) / 4
    grosor = _grosor(width)

    def dibujar(grande, K, col):
        pygame.draw.circle(grande, col, (rx * K, ry * K), rr * K, grosor * K)

    _suave(superficie, color, caja, ("c", rx, ry, rr, grosor), dibujar)


def ellipse(superficie, color, rect, width=0):
    r = rect_px(rect)
    grosor = _grosor(width)

    def dibujar(grande, K, col):
        pygame.draw.ellipse(grande, col, (0, 0, r.w * K, r.h * K), grosor * K)

    _suave(superficie, color, r, ("e", grosor), dibujar)


def polygon(superficie, color, points, width=0):
    pts = [(x * S, y * S) for x, y in points]
    grosor = _grosor(width)
    caja = _caja_puntos(pts, 1 + grosor)
    rel = _rel(pts, caja)

    def dibujar(grande, K, col):
        pygame.draw.polygon(grande, col, [(x * K, y * K) for x, y in rel],
                            grosor * K)

    _suave(superficie, color, caja, ("p", rel, grosor), dibujar)


def line(superficie, color, start, end, width=1):
    x1, y1, x2, y2 = start[0] * S, start[1] * S, end[0] * S, end[1] * S
    grosor = max(1, round(width * S))
    if abs(x1 - x2) < 1e-6 or abs(y1 - y2) < 1e-6:
        # Horizontal o vertical: directa y nítida
        pygame.draw.line(superficie, color, (round(x1), round(y1)),
                         (round(x2), round(y2)), grosor)
        return
    lines(superficie, color, False, [start, end], width)


def lines(superficie, color, closed, points, width=1):
    pts = [(x * S, y * S) for x, y in points]
    grosor = max(1, round(width * S))
    caja = _caja_puntos(pts, grosor + 1)
    rel = _rel(pts, caja)

    def dibujar(grande, K, col):
        g = [(x * K, y * K) for x, y in rel]
        pygame.draw.lines(grande, col, closed, g, grosor * K)
        if grosor > 1:           # uniones y puntas redondeadas
            for x, y in g:
                pygame.draw.circle(grande, col, (x, y), grosor * K / 2)

    _suave(superficie, color, caja, ("l", rel, closed, grosor), dibujar)


# ============================================================
# Ventana: escala de pantalla (Windows)
# ============================================================

def _declarar_dpi_aware():
    """Pide a Windows que NO estire la ventana. Debe ir antes de crearla."""
    if sys.platform != "win32":
        return
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(1)      # System DPI aware
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass


def _escala_de_windows():
    if sys.platform != "win32":
        return 1.0
    try:
        factor = ctypes.c_int(0)
        ctypes.windll.shcore.GetScaleFactorForDevice(0, ctypes.byref(factor))
        if factor.value >= 100:
            return factor.value / 100.0
    except Exception:
        pass
    try:
        return ctypes.windll.user32.GetDpiForSystem() / 96.0
    except Exception:
        return 1.0


def calcular_escala(ancho, alto, preferida="auto"):
    """Escala de dibujo para una interfaz lógica de ancho x alto.
    'auto' usa la escala de Windows y la limita para que la ventana quepa en
    el escritorio. Un número se respeta tal cual (es una decisión explícita)."""
    _declarar_dpi_aware()
    if preferida != "auto":
        return max(0.5, round(float(preferida), 2))
    escala = _escala_de_windows()
    try:
        pygame.display.init()
        dw, dh = pygame.display.get_desktop_sizes()[0]
        # margen para la barra de título y la barra de tareas
        escala = min(escala, (dh - 110) / alto, (dw - 40) / ancho)
    except Exception:
        pass
    return max(0.75, round(escala, 2))
