"""_capturas.py — Captura TODAS las pantallas en muchos estados (herramienta de desarrollo).

Sirve para revisar el aspecto del juego sin jugarlo, y para comprobar que un
cambio en ui.py no mueve ningún botón.

    python _capturas.py                 # escala 1.0 -> capturas/
    python _capturas.py 1.5             # escala 1.5
    python _capturas.py 1.25 salida     # carpeta de salida personalizada

Genera un PNG por caso y un rects.json con los botones (coordenadas lógicas
400x700, independientes de la escala).
"""
import json
import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)

import pygame  # noqa: E402


def _primer_incidente(g, condicion):
    for i, inc in g.incidentes_en_nivel():
        if condicion(inc):
            return i, inc
    raise LookupError("incidente no encontrado")


def casos(ui, escala):
    """Itera (nombre, botones) dibujando cada pantalla sobre `screen`."""
    import config
    import datos
    from game import Game

    screen = pygame.display.get_surface()
    ui.set_mouse((-1, -1))

    def juego(nivel=0, dinero=None, **estado):
        g = Game()
        if dinero is not None:
            g.estado.dinero = dinero
        g.cargar_nivel_por_id(nivel)
        for k, v in estado.items():
            setattr(g.estado, k, v)
        return g

    def listo(nombre, botones):
        rects = {k: list(v) for k, v in botones.items()
                 if isinstance(v, pygame.Rect)}
        return nombre, screen.copy(), rects

    # ── Menú, intro, créditos ─────────────────────────────────────────────
    yield listo("menu", ui.draw_menu(screen))
    pag = datos.INTRO_PAGINAS[1]
    txt = pag["texto"].format(dinero=config.DINERO_INICIAL_V2,
                             matricula=config.MATRICULA)
    yield listo("cinematica_escribiendo",
                ui.draw_cinematica(screen, pag, txt, 1, 5, 1500))
    yield listo("cinematica_completa",
                ui.draw_cinematica(screen, pag, txt, 1, 5, 6000, True))
    yield listo("creditos", ui.draw_creditos(screen))

    # ── Animación explicativa: cada escena en tres momentos ───────────────
    import animacion
    import escenas
    import voces
    esc = datos.ANIMACION_ESCENAS
    anim = animacion.Animacion(
        esc, [voces.duracion_ms(f"anim_{e['id']}") for e in esc])
    for i, e in enumerate(esc):
        for f, letra in ((0.3, "a"), (0.65, "b"), (0.97, "c")):
            t = anim.inicios[i] + anim.voz_ms[i] * f
            yield listo(f"anim_{e['id']}_{letra}", escenas.draw_animacion(screen, anim, t))

    # ── Pantalla del día ──────────────────────────────────────────────────
    for nivel in (0, 2, 4):
        for ms, etiqueta in ((300, "inicio"), (1300, "marcador"), (3500, "completo")):
            yield listo(f"dia_n{nivel}_{etiqueta}",
                        ui.draw_dia_intro(screen, juego(nivel), ms))

    # ── Tutorial guiado: cada paso sobre su pantalla real ────────────────
    def tut(id_paso, dibujar, ms=1400):
        paso = next(p for p in datos.TUTORIAL_PASOS if p["id"] == id_paso)
        base = dibujar()
        foco = None
        if paso["foco"]:
            foco = base.get(paso["foco"])
            if not isinstance(foco, pygame.Rect):
                foco = base.get("_zonas", {}).get(paso["foco"])
            assert foco is not None, (
                f"tutorial: el foco «{paso['foco']}» no existe en la pantalla "
                f"del paso «{id_paso}»")
        indice = [p["id"] for p in datos.TUTORIAL_PASOS].index(id_paso) + 1
        b = ui.draw_tutorial(screen, paso, foco, indice,
                             len(datos.TUTORIAL_PASOS), ms)
        return listo(f"tutorial_{id_paso}", b)

    g0 = juego(0)
    yield tut("semana", lambda: ui.draw_home(screen, g0))
    yield tut("banco", lambda: ui.draw_home(screen, g0))
    yield tut("abrir_mensajes", lambda: ui.draw_home(screen, g0))
    yield tut("recursos", lambda: ui.draw_message_list(screen, g0, 0))
    yield tut("abrir_mama", lambda: ui.draw_message_list(screen, g0, 0))
    yield tut("leer", lambda: ui.draw_chat(screen, g0, 0))
    yield tut("remitente", lambda: ui.draw_chat(screen, g0, 0))

    def modal(g, i, herramienta):
        ui.draw_chat(screen, g, i)
        return ui.draw_modal(screen, g.usar_herramienta_en(i, herramienta))

    yield tut("senales", lambda: modal(g0, 0, "remitente"))
    yield tut("confiar", lambda: ui.draw_chat(screen, g0, 0))
    g_ok = juego(0)
    g_ok.usar_herramienta_en(0, "remitente")
    res_ok = g_ok.evaluar_decision_en(0, "CONFIAR")
    yield tut("acierto", lambda: ui.draw_feedback(screen, res_ok, False))
    yield tut("abrir_sospechoso", lambda: ui.draw_message_list(screen, g_ok, 0))
    yield tut("senal_estafa", lambda: ui.draw_chat(screen, g_ok, 1))
    yield tut("enlace", lambda: ui.draw_chat(screen, g_ok, 1))
    yield tut("dominio", lambda: modal(g_ok, 1, "enlace"))
    yield tut("acciones", lambda: ui.draw_chat(screen, g_ok, 1))
    yield tut("reportar", lambda: ui.draw_chat(screen, g_ok, 1))
    g_ok.usar_herramienta_en(1, "enlace")
    res_rep = g_ok.evaluar_decision_en(1, "REPORTAR")
    yield tut("reportado", lambda: ui.draw_feedback(screen, res_rep, False))
    yield tut("consejo", lambda: ui.draw_panel(screen, res_rep["consejo"], 9000, True))
    yield tut("fin", lambda: ui.draw_resumen(screen, g_ok))

    # ── Instrucciones y aprendizajes (con scroll) ─────────────────────────
    yield listo("instrucciones_0", ui.draw_instrucciones(screen, 0))
    yield listo("instrucciones_mitad", ui.draw_instrucciones(screen, 130))
    g = juego(2)
    yield listo("aprendizajes_vacio", ui.draw_aprendizajes(screen, g, 0))
    g.estado.historial_consejos = list(g.consejos.keys())[:6]
    yield listo("aprendizajes_0", ui.draw_aprendizajes(screen, g, 0))
    yield listo("aprendizajes_200", ui.draw_aprendizajes(screen, g, 200))

    # ── Home en cada día ──────────────────────────────────────────────────
    for n in range(5):
        yield listo(f"home_n{n}", ui.draw_home(screen, juego(n)))
    yield listo("home_viernes_sin_dinero",
                ui.draw_home(screen, juego(4, dinero=300)))

    # ── Apps del celular (modales) ────────────────────────────────────────
    g = juego(2)
    for tipo in ("ajustes", "contactos", "cai", "correo", "fotos",
                 "calendario", "musica", "llamadas", "instagram", "banco"):
        ui.draw_home(screen, g)
        yield listo(f"app_{tipo}", ui.draw_modal_app(screen, tipo, g))
    g.activar_seguridad()
    ui.draw_home(screen, g)
    yield listo("app_ajustes_activado", ui.draw_modal_app(screen, "ajustes", g))

    # ── Lista de mensajes ─────────────────────────────────────────────────
    g = juego(3)
    yield listo("lista_n3_0", ui.draw_message_list(screen, g, 0))
    yield listo("lista_n3_100", ui.draw_message_list(screen, g, 100))
    yield listo("lista_n3_fin", ui.draw_message_list(screen, g, 400))
    for i in (0, 1):
        g.evaluar_decision_en(i, g.incidente_por_indice(i).respuesta_correcta)
    import random
    orig = random.random
    random.random = lambda: 0.0
    ev = g.intentar_evento_aleatorio()
    random.random = orig
    eidx = len(g.nivel.incidentes) - 1
    yield listo("lista_evento_fin", ui.draw_message_list(screen, g, 400, eidx, 400))
    yield listo("lista_evento_cayendo",
                ui.draw_message_list(screen, g, 400, eidx, 120))

    # ── Chat ──────────────────────────────────────────────────────────────
    g = juego(0)
    yield listo("chat_n0_tutorial", ui.draw_chat(screen, g, 0, True))
    yield listo("chat_n0", ui.draw_chat(screen, g, 0, False))
    g = juego(2)
    i, _ = _primer_incidente(g, lambda x: x.id == "n2_05")
    g.iniciar_timer_para(i)
    g.estado.tiempo_restante = 14.0
    yield listo("chat_n2_timer", ui.draw_chat(screen, g, i))
    g.estado.tiempo_restante = 3.0
    yield listo("chat_n2_timer_rojo", ui.draw_chat(screen, g, i))
    g = juego(1)
    i, _ = _primer_incidente(g, lambda x: x.enlace is not None)
    g.usar_herramienta_en(i, "remitente")
    g.verificar_incidente(i, "oficial")
    yield listo("chat_con_enlace_verificado", ui.draw_chat(screen, g, i))
    ui.set_mouse((200, 400))     # hover sobre un botón
    yield listo("chat_hover", ui.draw_chat(screen, g, i))
    ui.set_mouse((-1, -1))

    # ── Modales de herramientas ───────────────────────────────────────────
    for herramienta in ("remitente", "enlace", "contactos"):
        data = g.usar_herramienta_en(i, herramienta)
        ui.draw_chat(screen, g, i)
        yield listo(f"modal_{herramienta}", ui.draw_modal(screen, data))

    # ── Verificación ──────────────────────────────────────────────────────
    yield listo("verificacion_vacia", ui.draw_verificacion(screen, g, i, "", ""))
    yield listo("verificacion_llamada", ui.draw_verificacion(
        screen, g, i, g.verificar_incidente(i, "llamada"), "llamada"))

    # ── Economía ──────────────────────────────────────────────────────────
    yield listo("gastos_dia", ui.draw_gastos_dia(screen, config.GASTOS_DIARIOS[2]))
    g = juego(4, dinero=300)
    yield listo("matricula_pago", ui.draw_matricula_pago(screen, g, None))
    yield listo("matricula_prestamo_ok", ui.draw_matricula_pago(
        screen, g, {"aprobado": True, "razon": "seguro", "monto": 50}))
    yield listo("matricula_prestamo_no", ui.draw_matricula_pago(
        screen, g, {"aprobado": False, "razon": "rechazo"}))
    yield listo("fin_semana_sin_matricula", ui.draw_fin_semana(screen, g, "sin_matricula"))
    yield listo("fin_semana_parcial", ui.draw_fin_semana(screen, g, "parcial"))

    # ── Feedback y panel ──────────────────────────────────────────────────
    g = juego(2)
    i, inc = _primer_incidente(g, lambda x: x.id == "n2_07")
    g.usar_herramienta_en(i, "remitente")
    ok = g.evaluar_decision_en(i, inc.respuesta_correcta)
    yield listo("feedback_ok", ui.draw_feedback(screen, ok, False))
    g = juego(2)
    i, inc = _primer_incidente(g, lambda x: x.id == "n2_07")
    mal = g.evaluar_decision_en(i, "CONFIAR", auto_por_timer=True)
    yield listo("feedback_error_timer", ui.draw_feedback(screen, mal, True))
    g = juego(3)
    i, inc = _primer_incidente(g, lambda x: x.id == "n3_05")
    parcial = g.evaluar_decision_en(i, "BLOQUEAR")
    yield listo("feedback_parcial", ui.draw_feedback(screen, parcial, True))
    consejo = g.consejos["otp_nunca_se_comparte"]
    yield listo("panel_escribiendo", ui.draw_panel(screen, consejo, 900, False))
    yield listo("panel_completo", ui.draw_panel(screen, consejo, 9000, True))

    # ── Fin de nivel ──────────────────────────────────────────────────────
    g = juego(1)
    for j, x in g.incidentes_en_nivel():
        g.evaluar_decision_en(j, x.respuesta_correcta)
    yield listo("resumen_n1", ui.draw_resumen(screen, g))
    g.estado.privacidad = 20
    yield listo("resumen_recursos_bajos", ui.draw_resumen(screen, g))
    g = juego(3)
    g.estado.privacidad = 20
    yield listo("resumen_repetir_n3", ui.draw_resumen(screen, g))
    for xp, pagada, nombre in ((700, True, "certificado"), (300, True, "parcial"),
                               (700, False, "sin_matricula")):
        g = juego(4, xp=xp, matricula_pagada=pagada)
        yield listo(f"resumen_n4_{nombre}", ui.draw_resumen(screen, g))
    g = juego(4, xp=700, matricula_pagada=True)
    yield listo("certificado", ui.draw_certificado(screen, g))

    # ── Derrotas ──────────────────────────────────────────────────────────
    for campo, valor, nombre in (("privacidad", 0, "privacidad"),
                                 ("dinero", 0, "dinero"),
                                 ("reputacion", 0, "reputacion")):
        g = juego(2)
        setattr(g.estado, campo, valor)
        yield listo(f"derrota_{nombre}", ui.draw_derrota(screen, g))
    g = juego(2, dinero=10)
    g.pagar_gasto_obligatorio()
    yield listo("derrota_gasto", ui.draw_derrota(screen, g))

    # ── Banco ─────────────────────────────────────────────────────────────
    g = juego(2)
    i, _ = _primer_incidente(g, lambda x: x.id == "n2_05")
    yield listo("banco_otp", ui.draw_banco_otp(screen, g, i, "", False))
    yield listo("banco_otp_codigo", ui.draw_banco_otp(screen, g, i, "482915", True))
    g = juego(3)
    i, _ = _primer_incidente(g, lambda x: x.id == "n3_08")
    yield listo("banco_transf_vacia", ui.draw_banco_transferencia(screen, g, i, "", False))
    yield listo("banco_transf_40", ui.draw_banco_transferencia(screen, g, i, "40", False))
    yield listo("banco_transf_41", ui.draw_banco_transferencia(screen, g, i, "41", False))
    yield listo("banco_transf_otro", ui.draw_banco_transferencia(screen, g, i, "4", True))
    g.estado.dinero = 20
    yield listo("banco_transf_sin_saldo", ui.draw_banco_transferencia(screen, g, i, "40", False))


def generar(escala=1.0, salida="capturas", guardar_png=True):
    pygame.init()
    try:
        import gfx
        gfx.init(escala)
    except ImportError:          # versión anterior de ui.py (sin gfx)
        if escala != 1.0:
            raise SystemExit("Esta versión de ui.py no soporta escala")
    import config
    pygame.display.set_mode((round(config.WIDTH * escala),
                             round(config.HEIGHT * escala)))
    import ui
    ui.init()
    os.makedirs(salida, exist_ok=True)
    todos = {}
    for nombre, imagen, rects in casos(ui, escala):
        todos[nombre] = rects
        if guardar_png:
            pygame.image.save(imagen, os.path.join(salida, nombre + ".png"))
    with open(os.path.join(salida, "rects.json"), "w", encoding="utf-8") as f:
        json.dump(todos, f, ensure_ascii=False, indent=1, sort_keys=True)
    return todos


if __name__ == "__main__":
    esc = float(sys.argv[1]) if len(sys.argv) > 1 else 1.0
    carpeta = sys.argv[2] if len(sys.argv) > 2 else os.path.join(AQUI, "capturas")
    res = generar(esc, carpeta)
    print(f"{len(res)} capturas a escala {esc} en {carpeta}")
