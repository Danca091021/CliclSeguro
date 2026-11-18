"""escenas.py — Dibujo de la animación explicativa (vectorial). Ver specs/15_animacion.md.

Estilo "anuncio educativo": fondo azul con círculos flotantes, formas planas y
brillantes, movimiento con rebote, rótulo de color arriba, subtítulos que se
iluminan al ritmo de la voz y una barra de progreso.

Cada escena es una función `f(screen, t, d)` que dibuja su cuadro: `t` son los
milisegundos desde que empezó la escena y `d` su duración total. Todo se dibuja con
gfx (coordenadas lógicas 400x700, suavizado y escalable). La línea de tiempo
(cuánto dura cada escena) la calcula animacion.py a partir de los audios.
"""
import math

import pygame

import config
import gfx
import iconos
import ui

W, H = config.WIDTH, config.HEIGHT
CX = W // 2

AZUL, VERDE, ROJO, AMBAR = config.C_BLUE, config.C_GREEN, config.C_RED, config.C_AMBER
BLANCO = (255, 255, 255)
GRIS = (150, 162, 192)
OSCURO = (31, 41, 55)
COLORES = {"azul": AZUL, "verde": VERDE, "rojo": ROJO, "ambar": AMBAR}


# ── Utilidades de animación ───────────────────────────────────────

def _c(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def _p(t, desde, dur=500.0):
    """Progreso 0..1 de un tramo que empieza en `desde` y dura `dur` ms."""
    return _c((t - desde) / dur)


def _suave(x):                       # frena al llegar
    return 1 - (1 - x) ** 3


def _rebote(x):                      # se pasa un poco y vuelve (efecto "pop")
    c1 = 1.70158
    c3 = c1 + 1
    return 1 + c3 * (x - 1) ** 3 + c1 * (x - 1) ** 2


def _alfa(x):
    return int(255 * _c(x))


def _lerp(a, b, x):
    return a + (b - a) * x


def _mezcla(c1, c2, x):
    return tuple(int(_lerp(a, b, x)) for a, b in zip(c1, c2))


# ── Fondo, rótulo, progreso y subtítulos ─────────────────────────

def _fondo(screen, t):
    n = 28
    arriba, abajo = (10, 17, 42), (24, 42, 100)
    for i in range(n):
        gfx.rect(screen, _mezcla(arriba, abajo, i / (n - 1)),
                 (0, int(i * H / n), W, int(H / n) + 2))
    for i in range(7):                                  # círculos que flotan
        r = 26 + (i * 17) % 44
        x = (i * 71 + 40 + t * 0.012 * (1 + i % 3)) % (W + 2 * r) - r
        y = (i * 113 + 90 + math.sin(t / 1800 + i) * 30) % H
        gfx.circle(screen, (255, 255, 255, 14), (x, y), r)


def _etiqueta(screen, texto, color, t):
    if not texto:
        return
    a = _alfa(_p(t, 0, 350))
    y = 64 - (1 - _suave(_p(t, 0, 450))) * 14
    ancho = ui._f["btn_lg"].size(texto)[0] / gfx.S + 34
    gfx.rect(screen, (*color, a), (CX - ancho / 2, y, ancho, 30), border_radius=15)
    ui._t(screen, texto, CX, y + 15, BLANCO, "btn_lg", "center", a)


def _barra(screen, anim, i, t_local):
    n = len(anim.escenas)
    hueco = 4
    ancho = (W - 32 - hueco * (n - 1)) / n
    for k in range(n):
        x = 16 + k * (ancho + hueco)
        gfx.rect(screen, (255, 255, 255, 45), (x, 14, ancho, 4), border_radius=2)
        f = 1.0 if k < i else (t_local / anim.duraciones[i] if k == i else 0.0)
        if f > 0:
            gfx.rect(screen, BLANCO, (x, 14, max(2, ancho * f), 4), border_radius=2)


def _disponer_subtitulo(texto):
    """Reparte las palabras de la narración en líneas centradas.
    -> [[(palabra, x_lógico), ...], ...]. Mide con la fuente con la que SE DIBUJA
    (dividida por la escala): con la de tamaño lógico las palabras salían ~5% más
    anchas de lo previsto y se pisaban ("algunosno")."""
    fr = ui._f["h2"]
    medir = lambda txt: fr.size(txt)[0] / gfx.S
    espacio = medir(" ")
    maximo = W - 64
    lineas, actual, ancho = [], [], 0
    for p in texto.split():
        pw = medir(p)
        if actual and ancho + espacio + pw > maximo:
            lineas.append(actual)
            actual, ancho = [p], pw
        else:
            ancho += (espacio if actual else 0) + pw
            actual.append(p)
    lineas.append(actual)
    resultado = []
    for linea in lineas:
        ancho_linea = sum(medir(p) for p in linea) + espacio * (len(linea) - 1)
        x = (W - ancho_linea) / 2
        fila = []
        for p in linea:
            fila.append((p, x))
            x += medir(p) + espacio
        resultado.append(fila)
    return resultado


def _subtitulo(screen, texto, progreso):
    """Frase de la narración; las palabras se iluminan al ritmo de la voz."""
    lineas = _disponer_subtitulo(texto)
    total = sum(len(f) for f in lineas)
    alto_linea = 23
    alto = len(lineas) * alto_linea + 18
    y0 = H - 56 - alto
    gfx.rect(screen, (0, 0, 0, 120), (20, y0, W - 40, alto), border_radius=14)
    iluminadas = progreso * total + 0.6
    n = 0
    for li, fila in enumerate(lineas):
        for palabra, x in fila:
            color = BLANCO if n < iluminadas else (118, 130, 165)
            ui._t(screen, palabra, x, y0 + 9 + li * alto_linea, color, "h2")
            n += 1


# ── Dibujos pequeños ─────────────────────────────────────────────

def _telefono(screen, cx, cy, w, h):
    gfx.rect(screen, (6, 10, 26), (cx - w / 2 - 6, cy - h / 2 - 6, w + 12, h + 12),
             border_radius=26)
    gfx.rect(screen, (243, 245, 252), (cx - w / 2, cy - h / 2, w, h), border_radius=20)
    gfx.rect(screen, (6, 10, 26), (cx - w * 0.17, cy - h / 2 + 3, w * 0.34, 8),
             border_radius=4)


def _burbuja_notif(screen, x, y, color, escala=1.0, alfa=255):
    if escala <= 0.02:
        return
    w, h = 126 * escala, 42 * escala
    gfx.rect(screen, (0, 0, 0, int(alfa * 0.25)), (x - w / 2 + 2, y - h / 2 + 4, w, h),
             border_radius=int(13 * escala))
    gfx.rect(screen, (255, 255, 255, alfa), (x - w / 2, y - h / 2, w, h),
             border_radius=int(13 * escala))
    gfx.circle(screen, (*color, alfa), (x - w / 2 + 21 * escala, y), 12 * escala)
    gfx.rect(screen, (188, 197, 216, alfa),
             (x - w / 2 + 41 * escala, y - 9 * escala, 66 * escala, 5 * escala),
             border_radius=2)
    gfx.rect(screen, (214, 220, 233, alfa),
             (x - w / 2 + 41 * escala, y + 3 * escala, 44 * escala, 5 * escala),
             border_radius=2)


# Íconos compartidos (los mismos de Instrucciones y Créditos)
_check, _cruz, _lupa = iconos.check, iconos.cruz, iconos.lupa
_candado, _moneda, _corazon = iconos.candado, iconos.moneda, iconos.corazon
_escudo, _auricular = iconos.escudo, iconos.auricular


def _tarjeta(screen, cx, cy, w, h, borde=None, alfa=255):
    gfx.rect(screen, (0, 0, 0, int(alfa * 0.22)), (cx - w / 2 + 2, cy - h / 2 + 5, w, h),
             border_radius=16)
    gfx.rect(screen, (255, 255, 255, alfa), (cx - w / 2, cy - h / 2, w, h), border_radius=16)
    if borde:
        gfx.rect(screen, (*borde, alfa), (cx - w / 2, cy - h / 2, w, h), width=3,
                 border_radius=16)


# ── Escenas ──────────────────────────────────────────────────────

def _escena_mensajes(screen, t, d):
    _telefono(screen, CX, 330, 150, 290)
    ui._t(screen, "Mensajes", CX, 218, OSCURO, "h2", "center")
    colores = [VERDE, AZUL, (225, 48, 108), AMBAR]
    for k in range(5):                                  # filas dentro del celular
        y = 252 + k * 42
        gfx.circle(screen, (*colores[k % 4], 230), (CX - 46, y), 12)
        gfx.rect(screen, (196, 203, 220), (CX - 28, y - 9, 70, 6), border_radius=3)
        gfx.rect(screen, (222, 227, 238), (CX - 28, y + 3, 48, 6), border_radius=3)

    puestos = [(74, 235, VERDE), (326, 268, AZUL), (72, 365, (225, 48, 108)),
               (328, 402, AMBAR), (76, 478, VERDE), (324, 512, AZUL)]
    for k, (x, y, col) in enumerate(puestos):           # llegan notificaciones
        p = _p(t, 300 + k * 420, 480)
        if p > 0:
            flota = math.sin((t + k * 310) / 480) * 3
            _burbuja_notif(screen, x, y + flota, col, _rebote(p), _alfa(p * 2))

    n = int(_c(t / (d * 0.72)) * 37)                    # el contador sube
    if n > 0:
        pulso = 1 + (0.1 * math.sin(t / 90) if n < 37 else 0)
        gfx.circle(screen, (0, 0, 0, 60), (271, 212), 23 * pulso)
        gfx.circle(screen, ROJO, (270, 208), 22 * pulso)
        ui._t(screen, str(n), 270, 208, BLANCO, "h1", "center")


def _escena_trampa(screen, t, d):
    ent = _suave(_p(t, 150, 650))
    atrapa = _suave(_p(t, 2900, 800))
    tiembla = math.sin(t / 38) * 4 * (1 if 2900 < t < 3700 else 0)
    cy = 305 + (1 - ent) * 70 - atrapa * 55
    cx = CX + tiembla

    if ent > 0:                                         # el mensaje "ganaste…"
        a = _alfa(ent)
        _tarjeta(screen, cx, cy, 306, 122, ROJO if atrapa > 0.4 else None, a)
        gfx.circle(screen, (*ROJO, a), (cx - 118, cy - 28), 17)
        ui._t(screen, "!", cx - 118, cy - 28, BLANCO, "h1", "center", a)
        ui._t(screen, "Premios Campus", cx - 92, cy - 40, OSCURO, "h2", "topleft", a)
        ui._t(screen, "¡Ganaste una beca! Reclámala hoy.", cx - 134, cy - 6,
              (75, 85, 99), "small", "topleft", a)
        ui._t(screen, "beca-campus-premios.com", cx - 134, cy + 18, AMBAR, "btn",
              "topleft", a)
        gfx.line(screen, (*AMBAR, a), (cx - 134, cy + 36), (cx + 22, cy + 36), 2)

    baja = _suave(_p(t, 1300, 1300))                    # el anzuelo baja
    if baja > 0:
        y_h = _lerp(-40, 206, baja) - atrapa * 55
        gfx.line(screen, (200, 210, 235), (CX, 0), (CX, y_h), 2)
        gancho = [(0, 0), (0, 24), (2, 38), (12, 47), (25, 43), (31, 33), (27, 23)]
        gfx.lines(screen, (236, 240, 250), False, [(CX + x, y_h + y) for x, y in gancho], 5)
        gfx.polygon(screen, (236, 240, 250), [(CX + 21, y_h + 24), (CX + 33, y_h + 24),
                                              (CX + 27, y_h + 34)])

    p_barras = _p(t, 1900, 500)                         # tus tres recursos…
    if p_barras > 0:
        a = _alfa(p_barras)
        nombres = [("Privacidad", "candado"), ("Dinero", "moneda"), ("Reputación", "corazon")]
        for k, (nombre, ico) in enumerate(nombres):
            y = 442 + k * 40
            drena = _suave(_p(t, 3500 + k * 380, 900))  # …se vacían
            color = _mezcla(VERDE, ROJO, drena)
            frac = 1 - 0.86 * drena
            if ico == "candado":
                _candado(screen, 52, y, 26, (255, 255, 255, a))
            elif ico == "moneda":
                _moneda(screen, 52, y, 26)
            else:
                _corazon(screen, 52, y, 26, (255, 130, 150, a))
            ui._t(screen, nombre, 78, y, BLANCO, "small", "midleft", a)
            gfx.rect(screen, (255, 255, 255, int(a * 0.2)), (156, y - 7, 200, 14),
                     border_radius=7)
            gfx.rect(screen, (*color, a), (156, y - 7, max(4, 200 * frac), 14),
                     border_radius=7)


def _escena_habitos(screen, t, d):
    ent = _rebote(_p(t, 150, 700))
    gfx.circle(screen, (255, 255, 255, 30), (CX, 262), 100 * _c(ent, 0, 1.2))
    gfx.circle(screen, AZUL, (CX, 262), 82 * ent)
    ui._t(screen, "3", CX, 262, BLANCO, "gigante", "center", _alfa(ent))
    ui._t(screen, "HÁBITOS", CX, 392, BLANCO, "display", "center", _alfa(_p(t, 600, 500)))
    for k, (x, ico) in enumerate([(CX - 96, "lupa"), (CX, "escudo"), (CX + 96, "candado")]):
        p = _rebote(_p(t, 1100 + k * 380, 520))
        if p <= 0.02:
            continue
        gfx.rect(screen, (255, 255, 255, 235), (x - 36 * p, 462 - 36 * p, 72 * p, 72 * p),
                 border_radius=18)
        if ico == "lupa":
            _lupa(screen, x, 462, 52 * p, AZUL)
        elif ico == "escudo":
            _escudo(screen, x, 462, 52 * p, VERDE)
            _check(screen, x, 464, 26 * p, BLANCO, 3)
        else:
            _candado(screen, x, 464, 48 * p, ROJO)


def _escena_investiga(screen, t, d):
    ent = _suave(_p(t, 150, 650))
    if ent > 0:
        a = _alfa(ent)
        cx = CX + (1 - ent) * 160
        _tarjeta(screen, cx, 290, 330, 176, None, a)
        x0 = cx - 150
        gfx.circle(screen, (*GRIS, a), (x0 + 20, 238), 17)
        ui._t(screen, "Soporte Univers1dad", x0 + 46, 224, OSCURO, "h2", "topleft", a)
        ui._t(screen, "soporte@univers1dad-soporte.com", x0 + 46, 246, GRIS, "tiny",
              "topleft", a)
        gfx.line(screen, (225, 229, 238, a), (x0, 268), (x0 + 300, 268), 1)
        ui._t(screen, "Su correo será suspendido por falta de", x0, 280,
              (55, 65, 81), "small", "topleft", a)
        ui._t(screen, "actualización. Haga clic aquí:", x0, 297, (55, 65, 81), "small",
              "topleft", a)
        ui._t(screen, "univers1dad-soporte.com/activar", x0, 328, AMBAR, "btn",
              "topleft", a)
    ruta = [(900, (70, 190)), (1900, (176, 238)), (2700, (176, 238)), (3500, (190, 338))]
    if t >= ruta[0][0]:                                  # la lupa investiga
        if t >= ruta[-1][0]:
            x, y = ruta[-1][1]
        else:
            for (t0, (x0_, y0_)), (t1, (x1_, y1_)) in zip(ruta, ruta[1:]):
                if t0 <= t < t1:
                    f = _suave((t - t0) / (t1 - t0))
                    x, y = _lerp(x0_, x1_, f), _lerp(y0_, y1_, f)
                    break
        _lupa(screen, x, y, 74, AZUL, 6, (37, 99, 235, 34))
    p = _p(t, 4000, 500)
    if p > 0:                                            # ¡dominio falso!
        a = _alfa(p)
        gfx.rect(screen, (*ROJO, a), (CX - 154, 322, 244, 30), width=3, border_radius=8)
        e = _rebote(_p(t, 4300, 450))
        if e > 0.02:
            w = 190 * e
            gfx.rect(screen, ROJO, (CX - w / 2, 378 - 17 * e, w, 34 * e), border_radius=17)
            ui._t(screen, "¡Dominio falso!", CX, 378, BLANCO, "btn_lg", "center", _alfa(e))
            _cruz(screen, CX + 128, 378, 20, ROJO, 4)


def _escena_verifica(screen, t, d):
    e1 = _suave(_p(t, 150, 600))
    if e1 > 0:
        a = _alfa(e1)
        cy = 190 - (1 - e1) * 40
        _tarjeta(screen, CX, cy, 322, 88, None, a)
        gfx.circle(screen, (*ROJO, a), (CX - 130, cy), 17)
        ui._t(screen, "?", CX - 130, cy, BLANCO, "h1", "center", a)
        ui._t(screen, "Llame ya al 300 555 0999", CX - 100, cy - 20, OSCURO, "h2",
              "topleft", a)
        ui._t(screen, "para evitar el bloqueo", CX - 100, cy + 4, (75, 85, 99), "small",
              "topleft", a)
    p = _rebote(_p(t, 1500, 500))
    if p > 0.02:
        gfx.circle(screen, (0, 0, 0, 70), (CX + 118, 190), 25 * p)
        gfx.circle(screen, ROJO, (CX + 118, 190), 22 * p)
        _cruz(screen, CX + 118, 190, 22 * p, BLANCO, 4)
        ui._t(screen, "No llames a ese número", CX, 252, (255, 160, 160), "btn", "center",
              _alfa(p))
    e2 = _suave(_p(t, 2300, 650))
    if e2 > 0:
        a = _alfa(e2)
        cy = 352 + (1 - e2) * 50
        _tarjeta(screen, CX, cy, 322, 88, VERDE, a)
        gfx.circle(screen, (*AZUL, a), (CX - 130, cy), 18)
        ui._t(screen, "B", CX - 130, cy, BLANCO, "h1", "center", a)
        ui._t(screen, "Banco Nacional", CX - 100, cy - 22, OSCURO, "h2", "topleft", a)
        ui._t(screen, "Número oficial guardado", CX - 100, cy + 3, (75, 85, 99), "small",
              "topleft", a)
        q = _rebote(_p(t, 3000, 500))
        if q > 0.02:
            _escudo(screen, CX + 124, cy, 40 * q, VERDE)
            _check(screen, CX + 124, cy + 2, 20 * q, BLANCO, 3)
    if t > 3500:                                         # ¡llamar al número de siempre!
        a = _alfa(_p(t, 3500, 400))
        for k in range(3):
            fase = ((t - 3500) / 1300 + k / 3) % 1
            gfx.circle(screen, (*VERDE, int(150 * (1 - fase) * a / 255)), (CX, 482),
                       40 + 52 * fase, 3)
        gfx.circle(screen, (0, 0, 0, 70), (CX + 2, 485), 41)
        gfx.circle(screen, VERDE, (CX, 482), 38)
        _auricular(screen, CX, 482, 40 + 3 * math.sin(t / 90), BLANCO)


def _escena_codigos(screen, t, d):
    ui._t(screen, "CÓDIGO DE VERIFICACIÓN", CX, 214, (170, 182, 214), "small", "center",
          _alfa(_p(t, 100, 300)))
    for k, dig in enumerate("482915"):                  # el código aparece
        p = _rebote(_p(t, 250 + k * 210, 420))
        if p <= 0.02:
            continue
        x = CX - 129 + k * 44 + 19
        gfx.rect(screen, (255, 255, 255), (x - 19 * p, 262 - 26 * p, 38 * p, 52 * p),
                 border_radius=9)
        ui._t(screen, dig, x, 262, OSCURO, "title", "center", _alfa(p))
    e = _suave(_p(t, 1700, 650))
    if e > 0:                                            # "Soy del banco, dame tu código"
        a = _alfa(e)
        cx = CX + (1 - e) * 140
        _tarjeta(screen, cx, 375, 312, 62, None, a)
        gfx.circle(screen, (*AZUL, a), (cx - 128, 375), 15)
        ui._t(screen, "B", cx - 128, 375, BLANCO, "h2", "center", a)
        ui._t(screen, "Soy del banco. Dame tu código.", cx - 106, 375, OSCURO, "btn",
              "midleft", a)
    s = _p(t, 2900, 420)
    if s > 0:                                            # ¡NO! (sello)
        k = _rebote(s)
        escala = _lerp(2.6, 1.0, _c(k))
        sacude = math.sin(t / 30) * 3 * (1 - s) if s < 1 else 0
        r = 88 * escala
        a = _alfa(s * 1.6)
        gfx.circle(screen, (*ROJO, min(255, int(a * 0.9))), (CX + sacude, 262), r, int(13 * escala))
        gfx.line(screen, (*ROJO, min(255, int(a * 0.9))),
                 (CX - r * 0.7 + sacude, 262 - r * 0.7), (CX + r * 0.7 + sacude, 262 + r * 0.7),
                 int(13 * escala))
    if t > 3800:
        a = _alfa(_p(t, 3800, 450))
        _candado(screen, CX - 86, 462, 40, (255, 255, 255, a))
        ui._t(screen, "Es la llave de tu cuenta", CX - 56, 462, BLANCO, "h2", "midleft", a)


def _escena_prisa(screen, t, d):
    e = _suave(_p(t, 150, 600))
    if e > 0:
        a = _alfa(e)
        cy = 190 - (1 - e) * 40
        _tarjeta(screen, CX, cy, 322, 86, ROJO, a)
        ui._t(screen, "¡ÚLTIMO AVISO!", CX - 136, cy - 24, ROJO, "h2", "topleft", a)
        ui._t(screen, "Su cuenta será bloqueada hoy.", CX - 136, cy + 2, (55, 65, 81),
              "body", "topleft", a)
    corre = _c((t - 900) / 3300)                         # cuenta regresiva 20 -> 0
    seg = int(math.ceil(20 * (1 - corre))) if t >= 900 else 20
    peligro = seg <= 5
    ap = _alfa(_p(t, 700, 400))
    if ap > 0:
        sacude = math.sin(t / 45) * (3 if peligro and corre < 1 else 0)
        pulso = 1 + (0.05 * math.sin(t / 110) if peligro and corre < 1 else 0)
        w, h = 200 * pulso, 80 * pulso
        color = _mezcla((24, 32, 60), (110, 18, 28), 1 if peligro else 0)
        gfx.rect(screen, (*color, ap), (CX - w / 2 + sacude, 330 - h / 2, w, h),
                 border_radius=22)
        gfx.rect(screen, (*(ROJO if peligro else GRIS), ap),
                 (CX - w / 2 + sacude, 330 - h / 2, w, h), width=3, border_radius=22)
        ui._t(screen, f"00:{seg:02d}", CX + sacude, 330, BLANCO if not peligro else (255, 190, 190),
              "display", "center", ap)
    r = _rebote(_p(t, 4500, 520))
    if r > 0.02:                                         # ¡ALTO!
        pts = [(CX + math.cos(math.pi / 8 + k * math.pi / 4) * 50 * r,
                452 + math.sin(math.pi / 8 + k * math.pi / 4) * 50 * r) for k in range(8)]
        gfx.polygon(screen, (0, 0, 0, 70), [(x + 2, y + 4) for x, y in pts])
        gfx.polygon(screen, ROJO, pts)
        gfx.polygon(screen, (255, 255, 255, 220), pts, 3)
        ui._t(screen, "ALTO", CX, 452, BLANCO, "title", "center", _alfa(r))
    a = _alfa(_p(t, 5300, 450))
    if a > 0:
        ui._t(screen, "Detente y verifica", CX, 516, (255, 214, 120), "h1", "center", a)


def _escena_mision(screen, t, d):
    ent = _alfa(_p(t, 100, 400))
    xs = [60 + i * 70 for i in range(5)]
    y = 168
    gfx.line(screen, (60, 74, 120), (xs[0], y), (xs[-1], y), 3)
    avance = _suave(_p(t, 500, 2100)) * 4               # el marcador viaja D -> V
    for i, letra in enumerate("DLXJV"):
        paso = avance >= i - 0.02
        color = AMBAR if (i == 4 and paso) else (VERDE if paso else (55, 66, 108))
        gfx.circle(screen, (*color, ent), (xs[i], y), 18)
        ui._t(screen, letra, xs[i], y, BLANCO if paso else GRIS, "h2", "center", ent)
    mx = _lerp(xs[0], xs[4], avance / 4)
    gfx.circle(screen, (255, 255, 255, ent), (mx, y), 25, 3)
    e = _suave(_p(t, 2700, 650))
    if e > 0:                                            # la matrícula
        a = _alfa(e)
        cy = 292 + (1 - e) * 50
        _tarjeta(screen, CX, cy, 300, 84, AMBAR, a)
        ui._t(screen, "MATRÍCULA", CX - 128, cy - 26, GRIS, "tiny", "topleft", a)
        ui._t(screen, "$500", CX - 128, cy - 8, OSCURO, "display", "topleft", a)
        q = _rebote(_p(t, 3500, 500))
        if q > 0.02:
            gfx.circle(screen, VERDE, (CX + 100, cy), 24 * q)
            _check(screen, CX + 100, cy + 1, 28 * q, BLANCO, 4)
    for k, (nombre, ico) in enumerate([("Privacidad", "candado"), ("Dinero", "moneda"),
                                       ("Reputación", "corazon")]):
        p = _rebote(_p(t, 4200 + k * 330, 500))
        if p <= 0.02:
            continue
        x = CX - 100 + k * 100
        gfx.rect(screen, (255, 255, 255, 235), (x - 40 * p, 424 - 40 * p, 80 * p, 80 * p),
                 border_radius=18)
        if ico == "candado":
            _candado(screen, x, 422, 44 * p, AZUL)
        elif ico == "moneda":
            _moneda(screen, x, 422, 44 * p)
        else:
            _corazon(screen, x, 422, 44 * p, (236, 72, 100))
        ui._t(screen, nombre, x, 480, BLANCO, "small", "center", _alfa(p))


def _escena_cierre(screen, t, d):
    p = _rebote(_p(t, 200, 750))
    lado = 128 * _c(p, 0, 1.25)
    for k in range(6):                                   # destellos
        ang = k * math.pi / 3 + t / 1500
        r = 104 + 8 * math.sin(t / 300 + k)
        a = int(140 * _p(t, 600 + k * 120, 400) * (0.6 + 0.4 * math.sin(t / 260 + k)))
        gfx.circle(screen, (255, 255, 255, max(0, a)),
                   (CX + math.cos(ang) * r, 250 + math.sin(ang) * r), 4)
    if lado > 2:
        gfx.rect(screen, config.C_BLUE_LIGHT, (CX - lado / 2, 250 - lado / 2, lado, lado),
                 border_radius=int(28 * _c(p)))
        gfx.rect(screen, AZUL, (CX - lado * 0.26, 250 - lado * 0.3, lado * 0.52, lado * 0.6),
                 border_radius=int(10 * _c(p)))
        _check(screen, CX, 252, lado * 0.34, BLANCO, 5)
    ui._t(screen, "CLIC SEGURO", CX, 372, BLANCO, "display", "center", _alfa(_p(t, 900, 600)))
    ui._t(screen, "Cada clic tiene consecuencias", CX, 424, (170, 182, 214), "h2",
          "center", _alfa(_p(t, 1500, 600)))


ESCENAS = {
    "mensajes": _escena_mensajes, "trampa": _escena_trampa, "habitos": _escena_habitos,
    "investiga": _escena_investiga, "verifica": _escena_verifica,
    "codigos": _escena_codigos, "prisa": _escena_prisa, "mision": _escena_mision,
    "cierre": _escena_cierre,
}


# ── Cuadro completo ──────────────────────────────────────────────

def draw_animacion(screen, anim, t_ms):
    """Dibuja el cuadro de la animación en el instante t_ms (desde su inicio).
    Devuelve {"anim_saltar": Rect}."""
    i, t, d = anim.escena_en(t_ms)
    escena = anim.escenas[i]
    _fondo(screen, t_ms)
    ESCENAS[escena["id"]](screen, t, d)
    _etiqueta(screen, escena.get("etiqueta", ""), COLORES.get(escena.get("color"), AZUL), t)
    _barra(screen, anim, i, t)
    _subtitulo(screen, escena["voz"], anim.progreso_voz(i, t))
    saltar = pygame.Rect(W - 108, 26, 96, 26)
    ui._btn(screen, saltar, "Saltar ›", (255, 255, 255, 28), (214, 224, 246),
            (255, 255, 255, 80), "small")
    return {"anim_saltar": saltar}
