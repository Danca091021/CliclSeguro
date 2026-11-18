"""_simular_balance.py — Jugadores automáticos para balancear (Bloque G).

Juega partidas completas contra la lógica real (game.py, sin Pygame) con
distintos perfiles de jugador y reporta cuántos llegan al certificado.

    python _simular_balance.py            # 2000 partidas por perfil
    python _simular_balance.py 500        # menos partidas (más rápido)

Un perfil se define con:
  p_acierto      probabilidad de elegir la respuesta correcta en cada mensaje
  p_herramienta  probabilidad de usar la herramienta "Remitente" (+5 pts)

Modelo del jugador simulado (supuestos, para defenderlos ante el profesor):
  * Responde los mensajes en el orden de la lista.
  * Si se equivoca: cae en la estafa (CONFIAR) si es fraude, y rechaza
    (IGNORAR) si es legítimo. Si cae en una transferencia, envía el monto
    EXACTO que piden (el juego no acepta otro).
  * Un evento familiar se ayuda (cuesta dinero, +5 reputación) con
    probabilidad p_acierto; si no, se ignora (-15 reputación). Si no le
    alcanza el saldo, no puede ayudar.
  * El Viernes paga la matrícula en cuanto puede; si no le alcanza pide el
    préstamo de mamá ($50 si con eso le alcanza, si no $100).
  * Si pierde un nivel, lo repite (hasta max_intentos veces por nivel).
  * Los eventos aleatorios se responden bien con la misma p_acierto.
"""
import random
import sys

import config
from game import Game

PERFILES = {
    #  nombre      (p_acierto, p_herramienta)
    "perfecta": (1.00, 1.00),   # todo bien y siempre investiga: el máximo posible
    "experta":  (1.00, 0.50),   # todo bien, investiga la mitad de las veces
    "buena":    (0.90, 0.70),
    "media":    (0.75, 0.50),
    "mala":     (0.40, 0.20),
}

_ACCIONES = ["CONFIAR", "VERIFICAR", "IGNORAR", "BLOQUEAR", "REPORTAR"]


def _accion_incorrecta(inc):
    """Qué hace el jugador cuando se equivoca (ver docstring del módulo)."""
    if inc.categoria == "fraude":
        return "CONFIAR"
    return "IGNORAR"


def _responder(g, idx, inc, p_acierto, p_herramienta, rng):
    """Responde un incidente (normal o evento). Devuelve el dict resultado."""
    if rng.random() < p_herramienta:
        g.usar_herramienta_en(idx, "remitente")

    if rng.random() < p_acierto:
        accion = inc.respuesta_correcta
    else:
        accion = _accion_incorrecta(inc)

    res = g.evaluar_decision_en(idx, accion)
    if res and res.get("needs_interaction"):
        # CONFIAR en una interacción bancaria: el jugador envía el código o
        # transfiere EXACTAMENTE lo pedido. Si no le alcanza el saldo, la
        # ayuda/estafa falla sin mover dinero (misma regla que el temporizador).
        res = g.resolver_por_tiempo(idx)
    return res


def _gestionar_matricula(g):
    """El Viernes: paga si puede; si no, pide préstamo y reintenta."""
    if g.estado.matricula_pagada:
        return
    if g.pagar_matricula().get("ok"):
        return
    if not g.estado.prestamo_pedido:
        falta = config.MATRICULA - g.estado.dinero
        if falta <= config.PRESTAMO_SEGURO_HASTA:
            g.pedir_prestamo_mama(config.PRESTAMO_SEGURO_HASTA)
        elif falta <= config.PRESTAMO_MAX:
            g.pedir_prestamo_mama(config.PRESTAMO_MAX)
        g.pagar_matricula()


def jugar_partida(p_acierto, p_herramienta, seed=None, max_intentos=5,
                  eventos=True):
    """Juega una partida completa. Devuelve un dict con el resultado:
    resultado ('certificado' | 'parcial' | 'sin_matricula' | 'atascada'),
    xp, dinero, priv, rep, derrotas, repeticiones_n3."""
    rng = random.Random(seed)
    if seed is not None:
        random.seed(seed)            # game.py usa random para eventos/préstamo
    activo_antes = config.EVENTO_ACTIVO
    config.EVENTO_ACTIVO = eventos
    try:
        g = Game()
        derrotas = 0
        rep_n3 = 0
        while True:
            intentos = 0
            nivel_ok = False
            while intentos < max_intentos and not nivel_ok:
                intentos += 1
                # ── inicio de nivel: gasto diario ──
                if g.aplicar_gastos_dia() and not g.pagar_gasto_obligatorio():
                    derrotas += 1
                    g.reiniciar_nivel()
                    continue
                if g.necesita_pagar_matricula():
                    _gestionar_matricula(g)

                # ── incidentes ──
                perdio = False
                while not g.nivel_completado():
                    pendientes = [(i, inc) for i, inc in g.incidentes_en_nivel()
                                  if not g.esta_respondido(i) and not inc.es_evento]
                    idx, inc = pendientes[0]
                    _responder(g, idx, inc, p_acierto, p_herramienta, rng)
                    if g.chequear_derrota():
                        perdio = True
                        break
                    ev = g.intentar_evento_aleatorio()
                    if ev is not None:
                        eidx = len(g.nivel.incidentes) - 1
                        _responder(g, eidx, ev, p_acierto, 0.0, rng)
                        if g.chequear_derrota():
                            perdio = True
                            break
                if perdio:
                    derrotas += 1
                    g.reiniciar_nivel()
                    continue
                if g.resultado_nivel() == "repetir_n3":
                    rep_n3 += 1
                    g.reiniciar_nivel()
                    continue
                nivel_ok = True

            if not nivel_ok:
                resultado = "atascada"
                break
            if g.nivel.id == 4:
                resultado = g.resultado_final()
                break
            g.siguiente_nivel()
        e = g.estado
        return {"resultado": resultado, "xp": e.xp, "dinero": e.dinero,
                "priv": e.privacidad, "rep": e.reputacion,
                "derrotas": derrotas, "repeticiones_n3": rep_n3}
    finally:
        config.EVENTO_ACTIVO = activo_antes


def simular(perfil, n=2000, seed0=1000):
    p_ac, p_he = PERFILES[perfil]
    cuenta = {"certificado": 0, "parcial": 0, "sin_matricula": 0, "atascada": 0}
    xps, dineros, derrotas = [], [], []
    for k in range(n):
        r = jugar_partida(p_ac, p_he, seed=seed0 + k)
        cuenta[r["resultado"]] += 1
        xps.append(r["xp"])
        dineros.append(r["dinero"])
        derrotas.append(r["derrotas"] + r["repeticiones_n3"])
    xps.sort()
    return {
        "n": n, "cuenta": cuenta,
        "xp_prom": sum(xps) / n, "xp_min": xps[0], "xp_max": xps[-1],
        "xp_p10": xps[int(n * 0.10)], "xp_p90": xps[int(n * 0.90)],
        "dinero_prom": sum(dineros) / n,
        "repeticiones_prom": sum(derrotas) / n,
    }


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 2000
    umbral = config.UMBRAL_CERTIF
    print(f"Umbral certificado: {umbral} XP | partidas por perfil: {n}")
    print(f"{'perfil':9} {'acierto':>7} {'herram.':>7} | {'certif.':>7} {'parcial':>7} "
          f"{'s/matr.':>7} {'atasc.':>6} | {'XP prom':>7} {'p10':>4} {'p90':>4} "
          f"{'vs umbral':>9} | {'$ final':>7} {'repet.':>6}")
    for nombre, (pa, ph) in PERFILES.items():
        s = simular(nombre, n)
        c = s["cuenta"]
        print(f"{nombre:9} {pa:7.0%} {ph:7.0%} | "
              f"{c['certificado'] / n:7.1%} {c['parcial'] / n:7.1%} "
              f"{c['sin_matricula'] / n:7.1%} {c['atascada'] / n:6.1%} | "
              f"{s['xp_prom']:7.0f} {s['xp_p10']:4d} {s['xp_p90']:4d} "
              f"{(s['xp_prom'] / umbral - 1):+9.1%} | "
              f"{s['dinero_prom']:7.0f} {s['repeticiones_prom']:6.2f}")


if __name__ == "__main__":
    main()
