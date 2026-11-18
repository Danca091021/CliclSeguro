"""iconos.py — Íconos vectoriales compartidos (animación, instrucciones, créditos).

Todos se dibujan con gfx (suavizado, escalables) y tienen la misma firma:
    icono(screen, cx, cy, s, color)
donde (cx, cy) es el centro y `s` el tamaño aproximado en píxeles lógicos.
"""
import math

import gfx


def check(screen, cx, cy, s, color, ancho=4):
    gfx.lines(screen, color, False, [(cx - s * 0.42, cy), (cx - s * 0.08, cy + s * 0.34),
                                     (cx + s * 0.46, cy - s * 0.32)], ancho)


def cruz(screen, cx, cy, s, color, ancho=5):
    gfx.line(screen, color, (cx - s * 0.4, cy - s * 0.4), (cx + s * 0.4, cy + s * 0.4), ancho)
    gfx.line(screen, color, (cx - s * 0.4, cy + s * 0.4), (cx + s * 0.4, cy - s * 0.4), ancho)


def lupa(screen, cx, cy, s, color, ancho=5, lente=(255, 255, 255, 38)):
    gfx.circle(screen, lente, (cx - s * 0.1, cy - s * 0.1), s * 0.33)
    gfx.circle(screen, color, (cx - s * 0.1, cy - s * 0.1), s * 0.33, ancho)
    gfx.line(screen, color, (cx + s * 0.14, cy + s * 0.14), (cx + s * 0.46, cy + s * 0.46),
             ancho + 2)


def candado(screen, cx, cy, s, color):
    arco = [(cx + math.cos(math.pi * (1 - k / 10)) * s * 0.24,
             cy - s * 0.08 - math.sin(math.pi * k / 10) * s * 0.3) for k in range(11)]
    gfx.lines(screen, color, False, arco, max(3, int(s * 0.1)))
    gfx.rect(screen, color, (cx - s * 0.34, cy - s * 0.08, s * 0.68, s * 0.48),
             border_radius=max(3, int(s * 0.1)))
    gfx.circle(screen, (255, 255, 255, 200), (cx, cy + s * 0.14), s * 0.07)


def moneda(screen, cx, cy, s):
    import ui                      # import tardío: ui también importa este módulo
    gfx.circle(screen, (245, 158, 11), (cx, cy), s * 0.4)
    gfx.circle(screen, (255, 255, 255, 110), (cx, cy), s * 0.31, 2)
    ui._t(screen, "$", cx, cy, (120, 70, 10), "h1", "center")


def corazon(screen, cx, cy, s, color):
    r = s * 0.2
    gfx.circle(screen, color, (cx - r, cy - r * 0.5), r)
    gfx.circle(screen, color, (cx + r, cy - r * 0.5), r)
    gfx.polygon(screen, color, [(cx - r * 1.92, cy - r * 0.15), (cx + r * 1.92, cy - r * 0.15),
                                (cx, cy + r * 2.3)])


def escudo(screen, cx, cy, s, color):
    gfx.polygon(screen, color, [(cx, cy - s * 0.46), (cx + s * 0.38, cy - s * 0.28),
                                (cx + s * 0.38, cy + s * 0.08), (cx, cy + s * 0.47),
                                (cx - s * 0.38, cy + s * 0.08), (cx - s * 0.38, cy - s * 0.28)])


def auricular(screen, cx, cy, s, color):
    pts = [(-8, -9), (-5, -9), (-3, -4), (-6, -1), (5, 8), (8, 5),
           (11, 8), (11, 11), (8, 12), (-4, 2), (-11, -6)]
    k = s / 24
    gfx.polygon(screen, color, [(cx + x * k, cy + (y - 1.5) * k) for x, y in pts])


def bandera(screen, cx, cy, s, color):
    gfx.line(screen, color, (cx - s * 0.26, cy - s * 0.42), (cx - s * 0.26, cy + s * 0.46),
             max(2, int(s * 0.11)))
    gfx.polygon(screen, color, [(cx - s * 0.26, cy - s * 0.4), (cx + s * 0.42, cy - s * 0.2),
                                (cx - s * 0.26, cy + s * 0.04)])


def prohibido(screen, cx, cy, s, color, ancho=None):
    w = ancho or max(2, int(s * 0.11))
    gfx.circle(screen, color, (cx, cy), s * 0.4, w)
    gfx.line(screen, color, (cx - s * 0.28, cy - s * 0.28), (cx + s * 0.28, cy + s * 0.28), w)


def ojo_tachado(screen, cx, cy, s, color):
    w = max(2, int(s * 0.09))
    gfx.ellipse(screen, color, (cx - s * 0.46, cy - s * 0.24, s * 0.92, s * 0.48), w)
    gfx.circle(screen, color, (cx, cy), s * 0.12)
    gfx.line(screen, color, (cx - s * 0.4, cy + s * 0.4), (cx + s * 0.4, cy - s * 0.4),
             max(2, int(s * 0.1)))


def persona(screen, cx, cy, s, color):
    gfx.circle(screen, color, (cx, cy - s * 0.17), s * 0.19)
    gfx.ellipse(screen, color, (cx - s * 0.34, cy + s * 0.07, s * 0.68, s * 0.42))


def enlace(screen, cx, cy, s, color):
    w = max(2, int(s * 0.1))
    gfx.rect(screen, color, (cx - s * 0.46, cy - s * 0.17, s * 0.56, s * 0.34), width=w,
             border_radius=int(s * 0.17))
    gfx.rect(screen, color, (cx - s * 0.1, cy - s * 0.17, s * 0.56, s * 0.34), width=w,
             border_radius=int(s * 0.17))


def agenda(screen, cx, cy, s, color):
    w = max(2, int(s * 0.09))
    gfx.rect(screen, color, (cx - s * 0.3, cy - s * 0.42, s * 0.6, s * 0.84), width=w,
             border_radius=int(s * 0.1))
    gfx.circle(screen, color, (cx - s * 0.02, cy - s * 0.12), s * 0.11)
    gfx.ellipse(screen, color, (cx - s * 0.2, cy + s * 0.02, s * 0.36, s * 0.22))
    for k in range(3):
        gfx.rect(screen, color, (cx + s * 0.3, cy - s * 0.28 + k * s * 0.24, s * 0.12, s * 0.1),
                 border_radius=2)


def reloj(screen, cx, cy, s, color):
    w = max(2, int(s * 0.1))
    gfx.circle(screen, color, (cx, cy), s * 0.4, w)
    gfx.lines(screen, color, False, [(cx, cy - s * 0.24), (cx, cy), (cx + s * 0.17, cy + s * 0.1)], w)


def mensaje(screen, cx, cy, s, color):
    gfx.ellipse(screen, color, (cx - s * 0.42, cy - s * 0.34, s * 0.84, s * 0.58))
    gfx.polygon(screen, color, [(cx - s * 0.22, cy + s * 0.14), (cx - s * 0.06, cy + s * 0.14),
                                (cx - s * 0.26, cy + s * 0.42)])
