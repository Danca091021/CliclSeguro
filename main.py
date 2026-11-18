"""main.py — Arranque del juego. Ventana nativa, sin SCALED."""
import sys
import pygame

import config
import datos
import gfx
import animacion
import escenas
import tutorial
import ui
import voces
from game import Game
from audio_manager import AudioManager

VOCES = voces.manifest()     # qué se dice en voz alta (specs/13_dia_y_voz.md)

# Pantalla nítida (spec 12): se declara compatible con la escala de Windows,
# la ventana se abre al tamaño REAL y todo se dibuja a esa resolución.
# (Sin pygame.SCALED: con escala > 100% desfasaba los clics.)
ESCALA = gfx.calcular_escala(config.WIDTH, config.HEIGHT, config.UI_ESCALA)
gfx.init(ESCALA)
pygame.init()
screen = pygame.display.set_mode((round(config.WIDTH * ESCALA),
                                  round(config.HEIGHT * ESCALA)))
pygame.display.set_caption(config.TITULO)


clock = pygame.time.Clock()

ui.init()
audio = AudioManager()
game = Game()

# Estado global
estado = "MENU"
corriendo = True

modal_data = None
modal_app_tipo = None

idx_actual = -1
verif_resultado = ""
verif_metodo = ""
gastos_actual = None
prestamo_resp = None

# Fase E: OTP y transferencia
otp_codigo = ""
otp_generado = False
trans_monto = ""
trans_modo_otro = False

pending_panel = None
pending_result = None

# Tutorial del Nivel 0: las herramientas del chat pulsan hasta que el
# jugador usa una por primera vez en la partida.
tutorial_tools_visto = False

# Animación drop-in de la tarjeta de evento en la lista de mensajes
evento_anim_idx = -1
evento_anim_ms = 0.0

panel_elapsed_ms = 0.0
panel_skipped = False
panel_done = False

cinematica_elapsed_ms = 0.0
cinematica_idx = 0           # pantalla actual de la intro (0..4)
cinematica_completa = False  # el jugador pidió mostrar todo el texto ya
cinematica_done = False      # el typewriter terminó (lo informa ui)

# Pantalla del día (DIA_INTRO) y fundidos entre pantallas completas
dia_elapsed_ms = 0.0
dia_done = False

# Animación explicativa (specs/15_animacion.md)
anim = None                  # animacion.Animacion en curso
anim_ms = 0.0
_anim_escena = None          # índice de la escena cuya voz ya sonó
_anim_desde_menu = False     # True: al terminar vuelve al menú

# Tutorial guiado (specs/14_tutorial.md)
tutorial_guia = None         # Tutorial en curso, o None
tut_ms = 0.0                 # tiempo en el paso actual (animación)
_tut_paso_hablado = None     # id del último paso cuya voz ya sonó
fade_ms = float(config.FADE_MS)
_estado_previo = "MENU"
# Se hace fundido al ENTRAR a estas pantallas completas...
_FADE_ENTRADA = {"MENU", "ANIMACION", "DIA_INTRO", "GASTOS_DIA", "RESUMEN", "DERROTA",
                 "CERTIFICADO", "FIN_SEMANA_SIN_MATRICULA", "FIN_SEMANA_PARCIAL",
                 "INSTRUCCIONES", "CREDITOS", "APRENDIZAJES"}
# ... y al llegar al Home desde estas (no al ir y venir entre apps/mensajes)
_FADE_HACIA_HOME_DESDE = {"DIA_INTRO", "GASTOS_DIA", "CINEMATICA"}
_intro_mostrada = False

scroll_y = 0
estado_anterior = None

last_buttons = {}


def _iniciar_partida_nueva():
    global estado, _intro_mostrada, scroll_y
    global gastos_actual, tutorial_tools_visto, tutorial_guia, _tut_paso_hablado
    tutorial_tools_visto = False
    tutorial_guia = (tutorial.Tutorial(datos.TUTORIAL_PASOS)
                     if config.TUTORIAL_ACTIVO else None)
    _tut_paso_hablado = None
    game.reiniciar_partida()
    audio.cambiar_musica("segura")
    scroll_y = 0
    gastos_actual = None
    if not _intro_mostrada and not config.SKIP_INTRO:
        _intro_mostrada = True
        if config.ANIMACION_ACTIVA:
            _iniciar_animacion(False)
        else:
            _mostrar_pagina_intro(0)
            estado = "CINEMATICA"
    else:
        _intro_mostrada = True
        _entrar_dia()


def _iniciar_animacion(desde_menu):
    """Animación explicativa con voz (estilo anuncio educativo). Desde el menú
    ("Ver animación") vuelve al menú; al empezar la primera partida sigue la historia."""
    global estado, anim, anim_ms, _anim_escena, _anim_desde_menu
    escenas_ = datos.ANIMACION_ESCENAS
    anim = animacion.Animacion(
        escenas_, [voces.duracion_ms(f"anim_{e['id']}") for e in escenas_])
    anim_ms = 0.0
    _anim_escena = None
    _anim_desde_menu = desde_menu
    audio.detener_voz()
    estado = "ANIMACION"


def _terminar_animacion():
    global estado
    audio.detener_voz()
    if _anim_desde_menu:
        estado = "MENU"
    else:
        _mostrar_pagina_intro(0)
        estado = "CINEMATICA"


def _texto_intro(pagina, clave="texto"):
    """Rellena los marcadores de la página ({dinero}) desde config."""
    return pagina[clave].format(dinero=config.DINERO_INICIAL_V2,
                                matricula=config.MATRICULA)


def _mostrar_pagina_intro(i):
    """Reinicia el typewriter y la voz para la pantalla i de la intro."""
    global cinematica_idx, cinematica_elapsed_ms
    global cinematica_completa, cinematica_done
    cinematica_idx = i
    cinematica_elapsed_ms = 0.0
    cinematica_completa = False
    cinematica_done = False
    audio.detener_voz()
    p = datos.INTRO_PAGINAS[i]
    audio.hablar(p["key_voz"], _texto_intro(p, "voz"))


def _avanzar_intro():
    """Primer clic: completa el texto. Segundo clic: siguiente pantalla.
    Tras la última, entra al Nivel 0 (Home)."""
    global cinematica_completa
    if not cinematica_done:
        cinematica_completa = True
    elif cinematica_idx + 1 < len(datos.INTRO_PAGINAS):
        _mostrar_pagina_intro(cinematica_idx + 1)
    else:
        _terminar_intro()


def _terminar_intro():
    audio.detener_voz()
    _entrar_dia()


def _entrar_dia():
    """Muestra el día de la semana (nombre, semana y objetivo) y lo dice en voz
    alta. Solo al empezar la partida y al avanzar de día, no al repetir."""
    global estado, dia_elapsed_ms, dia_done
    dia_elapsed_ms = 0.0
    dia_done = False
    audio.detener_voz()
    audio.hablar(f"dia_{game.nivel.id}", f"{game.nivel.dia}. {game.nivel.titulo}.")
    estado = "DIA_INTRO"


def _avanzar_dia():
    """Primer toque: salta la animación. Segundo: empieza el día."""
    global dia_elapsed_ms
    if not dia_done:
        dia_elapsed_ms = 1e9
    else:
        audio.detener_voz()
        _entrar_home_con_gastos()


def _entrar_home_con_gastos():
    global estado, gastos_actual
    gasto = game.aplicar_gastos_dia()
    if gasto is not None:
        gastos_actual = gasto
        estado = "GASTOS_DIA"
    else:
        estado = "HOME"


def _abrir_detalle(idx):
    global estado, idx_actual
    idx_actual = idx
    game.estado.incidente_actual = idx
    game.iniciar_timer_para(idx)
    estado = "CHAT"


def _entrar_message_list():
    global estado, scroll_y
    viewport_h = config.PHONE_SCREEN[3] - 156
    total_h = len(game.nivel.incidentes) * (
        config.MSG_CARD_H + config.MSG_CARD_GAP) + 10
    max_scroll = max(0, total_h - viewport_h)

    scroll_to = 0
    for i, inc in game.incidentes_en_nivel():
        if not game.esta_respondido(i):
            card_bottom = 4 + (i + 1) * (config.MSG_CARD_H + config.MSG_CARD_GAP)
            if card_bottom > viewport_h:
                scroll_to = max(scroll_to, card_bottom - viewport_h + 10)
    scroll_y = min(scroll_to, max_scroll)
    estado = "MESSAGE_LIST"


def _volver_a_lista():
    global idx_actual
    game.pausar_timer()
    idx_actual = -1
    _entrar_message_list()


def _hablar_error(result):
    """Voz que explica qué se hizo mal (solo si falló). Si fue por el
    temporizador, primero dice que se acabó el tiempo."""
    if result is None or result.get("correcta"):
        return
    inc = game.incidente_por_indice(result["idx"])
    if inc is None:
        return
    if result.get("parcial"):            # no cayó, pero lo ideal era otra cosa
        clave = f"parcial_{inc.respuesta_correcta.lower()}"
        audio.hablar(clave, VOCES.get(clave, result["feedback"]))
        return
    items = []
    if result.get("auto_por_timer"):
        items.append(("err_tiempo", VOCES["err_tiempo"]))
    clave = f"err_{inc.id}"
    items.append((clave, VOCES.get(clave, inc.feedback_err)))
    audio.hablar_varios(items)


def _entrar_derrota():
    """Pantalla de derrota; una voz explica por qué se perdió."""
    global estado
    audio.play("err")
    estado = "DERROTA"
    clave = f"derrota_{game.motivo_derrota() or 'privacidad'}"
    audio.detener_voz()
    audio.hablar(clave, VOCES[clave])


def aplicar_decision(accion, auto=False):
    global estado, pending_panel, pending_result
    if auto:
        # Se agotó el tiempo: Camilo confía; en OTP/transferencia completa
        # la interacción (antes esto fallaba con KeyError 'consejo').
        result = game.resolver_por_tiempo(idx_actual)
    else:
        result = game.evaluar_decision_en(idx_actual, accion)
    if result is None or result.get("needs_interaction"):
        return
    if game.chequear_derrota():
        _entrar_derrota()
        return
    pending_result = result
    pending_panel = result["consejo"] if result["consejo"] else None
    estado = "FEEDBACK"
    audio.play("ok" if result["correcta"] else "err")
    _hablar_error(result)


def _ir_tras_feedback():
    global estado, panel_elapsed_ms, panel_skipped, panel_done
    audio.detener_voz()          # corta la explicación del error
    if pending_panel:
        panel_elapsed_ms = 0.0
        panel_skipped = False
        panel_done = False
        audio.play("ding")
        audio.hablar(pending_panel.key_voz, pending_panel.texto)
        estado = "PANEL"
    else:
        _finalizar_incidente()


def _finalizar_incidente():
    global estado, evento_anim_idx, evento_anim_ms
    evento = game.intentar_evento_aleatorio()
    if evento is not None:
        # El evento se agrega al final de la lista del nivel
        evento_anim_idx = len(game.nivel.incidentes) - 1
        evento_anim_ms = 0.0
        audio.play("notif")
    if game.nivel_completado():
        audio.play("notif")
        estado = "RESUMEN"
    else:
        _entrar_message_list()


def handle_click(name):
    global estado, modal_data, modal_app_tipo, corriendo, idx_actual
    global scroll_y, estado_anterior, _intro_mostrada
    global verif_resultado, verif_metodo, gastos_actual, prestamo_resp
    global otp_codigo, otp_generado, trans_monto, trans_modo_otro
    global pending_panel, pending_result, tutorial_tools_visto

    if estado == "MENU":
        if name == "play":
            audio.play("click")
            _iniciar_partida_nueva()
        elif name == "animacion":
            audio.play("click")
            _iniciar_animacion(True)
        elif name == "instrucciones":
            audio.play("click")
            scroll_y = 0
            estado_anterior = "MENU"
            estado = "INSTRUCCIONES"
        elif name == "creditos":
            audio.play("click")
            estado = "CREDITOS"
        elif name == "salir":
            corriendo = False

    elif estado == "CINEMATICA":
        if name == "skip_intro":
            audio.play("click")
            _terminar_intro()
        elif name == "avanzar":
            audio.play("click")
            _avanzar_intro()

    elif estado == "ANIMACION":
        if name == "anim_saltar":
            audio.play("click")
            _terminar_animacion()

    elif estado == "DIA_INTRO":
        if name == "continuar":
            audio.play("click")
            _avanzar_dia()

    elif estado == "GASTOS_DIA":
        if name == "pagar_gasto":
            audio.play("cash")
            if game.pagar_gasto_obligatorio():
                gastos_actual = None
                estado = "HOME"
            else:
                _entrar_derrota()

    elif estado == "INSTRUCCIONES":
        if name == "volver_menu":
            audio.play("click")
            scroll_y = 0
            estado = estado_anterior or "MENU"
            estado_anterior = None
        elif name == "ver_aprendizajes":
            audio.play("click")
            scroll_y = 0
            estado_anterior = "INSTRUCCIONES"
            estado = "APRENDIZAJES"

    elif estado == "APRENDIZAJES":
        if name == "volver_menu":
            audio.play("click")
            scroll_y = 0
            destino = estado_anterior or "MENU"
            estado_anterior = None
            estado = destino

    elif estado == "CREDITOS":
        if name == "volver_menu":
            audio.play("click")
            estado = "MENU"

    elif estado == "HOME":
        if name == "pagar_matricula":
            audio.play("cash")
            game.pagar_matricula()
        elif name == "abrir_prestamo":
            audio.play("click")
            prestamo_resp = None
            estado = "MATRICULA_PAGO"
        elif name == "app_mensajes":
            audio.play("click")
            _entrar_message_list()
        elif name.startswith("app_"):
            audio.play("click")
            modal_app_tipo = name[4:]
            estado = "MODAL_APP"

    elif estado == "MATRICULA_PAGO":
        if name == "volver_home":
            audio.play("click")
            prestamo_resp = None
            estado = "HOME"
        elif name == "pagar_matricula":
            audio.play("cash")
            res = game.pagar_matricula()
            if res.get("ok"):
                prestamo_resp = None
                estado = "HOME"
        elif name == "prestamo_50":
            audio.play("click")
            prestamo_resp = game.pedir_prestamo_mama(50)
        elif name == "prestamo_100":
            audio.play("click")
            prestamo_resp = game.pedir_prestamo_mama(100)

    elif estado == "MODAL_APP":
        if name == "cerrar_app":
            audio.play("click")
            modal_app_tipo = None
            estado = "HOME"
        elif name == "activar_proteccion":
            audio.play("ok")
            game.activar_seguridad()

    elif estado == "MESSAGE_LIST":
        if name == "volver_home":
            audio.play("click")
            game.pausar_timer()
            estado = "HOME"
        elif name.startswith("open_"):
            audio.play("click")
            _abrir_detalle(int(name[5:]))

    elif estado == "CHAT":
        if name == "volver_lista":
            audio.play("click")
            _volver_a_lista()
        elif name.startswith("verif_"):
            verif_metodo = name[6:]
            verif_resultado = game.verificar_incidente(idx_actual, verif_metodo)
            audio.play("click")
            estado = "VERIFICACION"
        elif name.startswith("tool_"):
            data = game.usar_herramienta_en(idx_actual, name[5:])
            if data:
                audio.play("click")
                tutorial_tools_visto = True
                modal_data = data
                estado = "MODAL"
        elif name.startswith("action_"):
            accion = name[7:].upper()
            if accion == "VERIFICAR":
                audio.play("click")
                verif_resultado = ""
                verif_metodo = ""
                estado = "VERIFICACION"
            else:
                inc = game.incidente_por_indice(idx_actual)
                # Fase E: interceptar CONFIAR en interacciones
                if (accion == "CONFIAR"
                        and inc.interaccion == "otp"
                        and config.INTERACCION_ACTIVA):
                    audio.play("click")
                    otp_codigo = ""
                    otp_generado = False
                    game.pausar_timer()
                    estado = "BANCO_OTP"
                elif (accion == "CONFIAR"
                      and inc.interaccion == "transferencia"
                      and config.INTERACCION_ACTIVA):
                    audio.play("click")
                    trans_monto = ""
                    trans_modo_otro = False
                    game.pausar_timer()
                    estado = "BANCO_TRANSFERENCIA"
                else:
                    audio.play("click")
                    aplicar_decision(accion)

    elif estado == "BANCO_OTP":
        if name == "cancelar_otp":
            audio.play("click")
            estado = "CHAT"
            game.iniciar_timer_para(idx_actual)
        elif name == "generar_otp":
            audio.play("otp_ready")
            otp_codigo = game.generar_otp(idx_actual)
            otp_generado = True
        elif name == "enviar_otp":
            audio.play("err")
            result = game.enviar_otp(idx_actual)
            pending_result = result
            pending_panel = result["consejo"] if result["consejo"] else None
            if game.chequear_derrota():
                _entrar_derrota()
            else:
                estado = "FEEDBACK"
                _hablar_error(result)

    elif estado == "BANCO_TRANSFERENCIA":
        if name == "cancelar_transferencia":
            audio.play("click")
            estado = "CHAT"
            game.iniciar_timer_para(idx_actual)
        elif name.startswith("monto_"):
            if name == "monto_otro":
                audio.play("click")
                trans_monto = ""
                trans_modo_otro = True
            else:
                audio.play("click")
                try:
                    trans_monto = str(int(name[6:]))
                except ValueError:
                    pass
                trans_modo_otro = False
        elif name.startswith("numpad_"):
            audio.play("click")
            k = name[7:]
            if k == "C":
                trans_monto = ""
            elif k == "⌫":
                trans_monto = trans_monto[:-1]
            else:
                if len(trans_monto) < 6:
                    trans_monto += k
        elif name == "confirmar_transferencia":
            try:
                monto_int = int(trans_monto) if trans_monto else 0
            except ValueError:
                monto_int = 0
            # La pantalla solo muestra Confirmar con un monto válido (exacto y
            # con saldo); esto es la defensa del lado de la lógica.
            if game.motivo_monto_invalido(idx_actual, monto_int) is None:
                audio.play("cash")
                result = game.confirmar_transferencia(idx_actual, monto_int)
                if result:
                    pending_result = result
                    pending_panel = result["consejo"] if result["consejo"] else None
                    if game.chequear_derrota():
                        _entrar_derrota()
                    else:
                        estado = "FEEDBACK"
                        _hablar_error(result)

    elif estado == "VERIFICACION":
        if name == "volver_chat":
            audio.play("click")
            verif_resultado = ""
            verif_metodo = ""
            estado = "CHAT"
        elif name.startswith("verif_"):
            audio.play("click")
            metodo = name[6:]
            verif_metodo = metodo
            verif_resultado = game.verificar_incidente(idx_actual, metodo)

    elif estado == "MODAL":
        if name == "cerrar_modal":
            audio.play("click")
            modal_data = None
            estado = "CHAT"

    elif estado == "FEEDBACK":
        if name == "siguiente":
            audio.play("click")
            _ir_tras_feedback()

    elif estado == "PANEL":
        if name == "entendido":
            audio.play("click")
            _finalizar_incidente()

    elif estado == "RESUMEN":
        if name == "continuar":
            audio.play("click")
            if game.nivel.id == 4:
                estado = "CERTIFICADO"
            else:
                game.siguiente_nivel()
                _entrar_dia()
        elif name == "repetir":
            audio.play("click")
            game.reiniciar_nivel()
            _entrar_home_con_gastos()   # re-cobra el gasto si murió por no poder pagarlo
        elif name == "ver_fin_semana":
            audio.play("click")
            if not game.estado.matricula_pagada:
                estado = "FIN_SEMANA_SIN_MATRICULA"
            else:
                estado = "FIN_SEMANA_PARCIAL"
        elif name == "menu":
            audio.play("click")
            game.reiniciar_partida()
            audio.cambiar_musica("segura")
            _intro_mostrada = True
            estado = "MENU"

    elif estado == "FIN_SEMANA_SIN_MATRICULA":
        if name == "repetir_viernes":
            audio.play("click")
            game.reiniciar_nivel()
            _entrar_home_con_gastos()   # re-cobra el gasto si murió por no poder pagarlo
        elif name == "menu":
            audio.play("click")
            game.reiniciar_partida()
            audio.cambiar_musica("segura")
            _intro_mostrada = True
            estado = "MENU"

    elif estado == "FIN_SEMANA_PARCIAL":
        if name == "repetir_viernes":
            audio.play("click")
            game.reiniciar_nivel()
            _entrar_home_con_gastos()   # re-cobra el gasto si murió por no poder pagarlo
        elif name == "menu":
            audio.play("click")
            game.reiniciar_partida()
            audio.cambiar_musica("segura")
            _intro_mostrada = True
            estado = "MENU"

    elif estado == "DERROTA":
        if name in ("repetir_nivel", "menu"):
            audio.detener_voz()
        if name == "repetir_nivel" and game.info_derrota()["puede_repetir"]:
            audio.play("click")
            game.reiniciar_nivel()
            _entrar_home_con_gastos()   # re-cobra el gasto si murió por no poder pagarlo
        elif name == "menu":
            audio.play("click")
            game.reiniciar_partida()
            audio.cambiar_musica("segura")
            _intro_mostrada = True
            estado = "MENU"

    elif estado == "CERTIFICADO":
        if name == "menu":
            audio.play("click")
            game.reiniciar_partida()
            audio.cambiar_musica("segura")
            _intro_mostrada = True
            estado = "MENU"
        elif name == "ver_aprendizajes":
            audio.play("click")
            scroll_y = 0
            estado_anterior = "CERTIFICADO"
            estado = "APRENDIZAJES"



def _procesar_click(nombre_boton):
    """Un clic sobre un botón. Si el tutorial está activo, primero atiende sus
    propios botones; los del juego se ejecutan normal y luego se avisa al tutorial
    (que solo deja pulsar el botón resaltado, así que esto avanza el paso)."""
    global tutorial_guia
    if nombre_boton.startswith("tut_"):
        audio.play("click")
        if nombre_boton == "tut_siguiente":
            tutorial_guia.siguiente()
        elif nombre_boton == "tut_saltar":
            tutorial_guia.saltar()
            audio.detener_voz()
        return
    antes = estado
    handle_click(nombre_boton)
    if tutorial_guia is not None and not tutorial_guia.terminado:
        tutorial_guia.click(antes, nombre_boton)


while corriendo:
    dt_ms = clock.tick(config.FPS)
    dt_seg = dt_ms / 1000.0

    # 1. Lógica
    if estado == "CHAT" and game.estado.timer_activo \
            and game.estado.timer_indice == idx_actual:
        expiro = game.tick_timer(dt_seg)
        if expiro is not None:
            audio.play("err")
            aplicar_decision("CONFIAR", auto=True)

    if estado == "CINEMATICA":
        cinematica_elapsed_ms += dt_ms
    if estado == "DIA_INTRO":
        dia_elapsed_ms += dt_ms
    if estado == "ANIMACION":
        anim_ms += dt_ms
        if anim.terminada(anim_ms):
            _terminar_animacion()
        else:
            _i = anim.escena_en(anim_ms)[0]
            if _i != _anim_escena:             # escena nueva: suena su narración
                _anim_escena = _i
                _e = anim.escenas[_i]
                audio.detener_voz()
                audio.hablar(f"anim_{_e['id']}", _e["voz"])

    if estado in ("HOME", "MESSAGE_LIST", "CHAT", "MODAL", "MODAL_APP",
                  "FEEDBACK", "PANEL", "VERIFICACION",
                  "BANCO_OTP", "BANCO_TRANSFERENCIA"):
        audio.cambiar_musica("tension" if game.hay_tension() else "segura")
    audio.actualizar(dt_ms)

    if estado == "PANEL":
        panel_elapsed_ms += dt_ms

    if evento_anim_idx >= 0:
        evento_anim_ms += dt_ms
        if evento_anim_ms >= config.EVENTO_DROP_MS:
            evento_anim_idx = -1

    # 2. Dibujar (el mouse se publica antes, para el hover de los botones)
    ui.set_mouse(gfx.a_logico(pygame.mouse.get_pos()))
    if estado == "MENU":
        last_buttons = ui.draw_menu(screen)
    elif estado == "CINEMATICA":
        _pag = datos.INTRO_PAGINAS[cinematica_idx]
        last_buttons = ui.draw_cinematica(
            screen, _pag, _texto_intro(_pag), cinematica_idx,
            len(datos.INTRO_PAGINAS), cinematica_elapsed_ms,
            cinematica_completa)
        cinematica_done = last_buttons.get("_done", False)
    elif estado == "ANIMACION":
        last_buttons = escenas.draw_animacion(screen, anim, anim_ms)
    elif estado == "DIA_INTRO":
        last_buttons = ui.draw_dia_intro(screen, game, dia_elapsed_ms)
        dia_done = last_buttons.get("_done", False)
    elif estado == "GASTOS_DIA":
        last_buttons = ui.draw_gastos_dia(screen, gastos_actual)
    elif estado == "INSTRUCCIONES":
        last_buttons = ui.draw_instrucciones(screen, scroll_y)
    elif estado == "APRENDIZAJES":
        last_buttons = ui.draw_aprendizajes(screen, game, scroll_y)
    elif estado == "CREDITOS":
        last_buttons = ui.draw_creditos(screen)
    elif estado == "HOME":
        last_buttons = ui.draw_home(screen, game)
    elif estado == "MATRICULA_PAGO":
        last_buttons = ui.draw_matricula_pago(screen, game, prestamo_resp)
    elif estado == "MODAL_APP":
        last_buttons = ui.draw_modal_app(screen, modal_app_tipo, game)
    elif estado == "MESSAGE_LIST":
        last_buttons = ui.draw_message_list(screen, game, scroll_y,
                                            evento_anim_idx, evento_anim_ms)
    elif estado == "CHAT":
        last_buttons = ui.draw_chat(
            screen, game, idx_actual,
            pulsar_tools=(game.nivel.id == 0 and not tutorial_tools_visto
                          and tutorial_guia is None))
    elif estado == "BANCO_OTP":
        last_buttons = ui.draw_banco_otp(screen, game, idx_actual,
                                          otp_codigo, otp_generado)
    elif estado == "BANCO_TRANSFERENCIA":
        last_buttons = ui.draw_banco_transferencia(screen, game, idx_actual,
                                                    trans_monto, trans_modo_otro)
    elif estado == "VERIFICACION":
        last_buttons = ui.draw_verificacion(screen, game, idx_actual,
                                            verif_resultado, verif_metodo)
    elif estado == "MODAL":
        last_buttons = ui.draw_modal(screen, modal_data)
    elif estado == "FEEDBACK":
        last_buttons = ui.draw_feedback(screen, pending_result,
                                        not pending_result["correcta"])
    elif estado == "PANEL":
        last_buttons = ui.draw_panel(screen, pending_panel,
                                     panel_elapsed_ms, panel_skipped)
        panel_done = last_buttons.get("_done", False)
    elif estado == "RESUMEN":
        last_buttons = ui.draw_resumen(screen, game)
    elif estado == "DERROTA":
        last_buttons = ui.draw_derrota(screen, game)
    elif estado == "CERTIFICADO":
        last_buttons = ui.draw_certificado(screen, game)
    elif estado == "FIN_SEMANA_SIN_MATRICULA":
        last_buttons = ui.draw_fin_semana(screen, game, "sin_matricula")
    elif estado == "FIN_SEMANA_PARCIAL":
        last_buttons = ui.draw_fin_semana(screen, game, "parcial")

    # Tutorial guiado: oscurece la pantalla, enfoca un elemento y deja pulsar solo ese
    if tutorial_guia is not None and tutorial_guia.terminado:
        tutorial_guia = None
    if tutorial_guia is not None:
        _paso = tutorial_guia.paso_en(estado)
        _foco = None
        if _paso is not None and _paso["foco"]:
            _foco = last_buttons.get(_paso["foco"])
            if not isinstance(_foco, pygame.Rect):
                _foco = last_buttons.get("_zonas", {}).get(_paso["foco"])
        if _paso is not None and _paso["tipo"] == "click" and _foco is None:
            _paso = None        # el botón no está a la vista: juego libre (nunca se atasca)
        if _paso is not None:
            if _paso["id"] != _tut_paso_hablado:      # paso nuevo: voz y animación
                _tut_paso_hablado = _paso["id"]
                tut_ms = 0.0
                audio.detener_voz()
                audio.hablar(f"tut_{_paso['id']}", _paso["voz"])
            tut_ms += dt_ms
            _solo = {_paso["foco"]: _foco} if _paso["tipo"] == "click" else {}
            last_buttons = {
                **ui.draw_tutorial(screen, _paso, _foco, tutorial_guia.indice + 1,
                                   tutorial_guia.total, tut_ms),
                **_solo}

    # Fundido de entrada (negro -> pantalla) al cambiar a una pantalla completa
    if estado != _estado_previo:
        entra = (estado in _FADE_ENTRADA
                 or (estado == "HOME" and _estado_previo in _FADE_HACIA_HOME_DESDE))
        fade_ms = 0.0 if entra else float(config.FADE_MS)
        _estado_previo = estado
    if fade_ms < config.FADE_MS:
        gfx.overlay(screen, (0, 0, 0, int(255 * (1 - fade_ms / config.FADE_MS))))
        fade_ms += dt_ms

    pygame.display.flip()

    # 3. Eventos
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            corriendo = False

        elif event.type == pygame.KEYDOWN:
            if (tutorial_guia is not None and not tutorial_guia.terminado
                    and event.key in (pygame.K_SPACE, pygame.K_RETURN)
                    and (tutorial_guia.paso_en(estado) or {}).get("tipo") == "info"):
                audio.play("click")
                tutorial_guia.siguiente()
            elif estado == "MENU":
                if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    audio.play("click")
                    _iniciar_partida_nueva()
            elif estado == "ANIMACION":
                if event.key in (pygame.K_SPACE, pygame.K_RETURN, pygame.K_ESCAPE):
                    audio.play("click")
                    _terminar_animacion()
            elif estado == "DIA_INTRO":
                if event.key in (pygame.K_SPACE, pygame.K_RETURN):
                    audio.play("click")
                    _avanzar_dia()
            elif estado == "CINEMATICA":
                if event.key in (pygame.K_SPACE, pygame.K_RETURN):
                    audio.play("click")
                    _avanzar_intro()
                elif event.key == pygame.K_ESCAPE:
                    audio.play("click")
                    _terminar_intro()

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for bname, rect in last_buttons.items():
                if (isinstance(rect, pygame.Rect)
                        and rect.collidepoint(gfx.a_logico(event.pos))):
                    _procesar_click(bname)
                    break

        elif event.type == pygame.MOUSEWHEEL:
            if estado in ("INSTRUCCIONES", "APRENDIZAJES", "MESSAGE_LIST"):
                delta = -event.y * config.SCROLL_VELOCIDAD
                nuevo = scroll_y + delta
                if nuevo < 0:
                    nuevo = 0
                if estado in ("INSTRUCCIONES", "APRENDIZAJES"):
                    # el tope lo calcula ui al dibujar (altura del contenido)
                    nuevo = min(nuevo, last_buttons.get("_max_scroll", nuevo))
                if estado == "MESSAGE_LIST":
                    total_h = len(game.nivel.incidentes) * (
                        config.MSG_CARD_H + config.MSG_CARD_GAP) + 10
                    viewport_h = config.PHONE_SCREEN[3] - 156
                    max_s = max(0, total_h - viewport_h)
                    if nuevo > max_s:
                        nuevo = max_s
                scroll_y = nuevo

pygame.quit()
sys.exit()