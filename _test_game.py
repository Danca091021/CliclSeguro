"""_test_game.py — Verificación de lógica sin Pygame."""
import sys

# La consola de Windows (cp1252) no imprime "→", "✓", "═"; forzamos UTF-8.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import contextlib
import random

from game import Game
import config


# ── Ayudas ──────────────────────────────────────────────────────

@contextlib.contextmanager
def random_fijo(valor):
    """random.random() devuelve siempre `valor` (para probar probabilidades)."""
    orig = random.random
    random.random = lambda: valor
    try:
        yield
    finally:
        random.random = orig


@contextlib.contextmanager
def config_temp(**cambios):
    """Cambia valores de config durante el bloque y los restaura."""
    viejos = {k: getattr(config, k) for k in cambios}
    for k, v in cambios.items():
        setattr(config, k, v)
    try:
        yield
    finally:
        for k, v in viejos.items():
            setattr(config, k, v)


def idx_de(g, inc_id):
    """Índice del incidente `inc_id` en el nivel cargado."""
    for i, inc in g.incidentes_en_nivel():
        if inc.id == inc_id:
            return i
    raise AssertionError(f"incidente {inc_id} no está en el nivel {g.nivel.id}")


def responder_bien(g, n):
    """Responde bien los primeros n incidentes normales aún pendientes."""
    hechos = 0
    for i, inc in g.incidentes_en_nivel():
        if hechos >= n:
            break
        if not inc.es_evento and not g.esta_respondido(i):
            r = g.evaluar_decision_en(i, inc.respuesta_correcta)
            if r and r.get("needs_interaction"):
                r = g.confirmar_transferencia(i, inc.monto_solicitado)
            assert r and r["correcta"], inc.id
            hechos += 1


def test_1_nivel_1_perfecto():
    print("\n=== TEST 1: Nivel 1 perfecto ===")
    g = Game()
    # Nivel 0 carga por defecto, avanzar a Nivel 1
    g.siguiente_nivel()
    assert g.nivel.id == 1
    assert g.estado.privacidad == 100
    assert g.estado.dinero == 800  # ECONOMIA_V2
    assert g.estado.xp == 0

    for inc in g.nivel.incidentes:
        g.usar_herramienta("remitente")
        r = g.evaluar_decision(inc.respuesta_correcta)
        assert r["correcta"], f"Falló {inc.id}: {inc.respuesta_correcta}"
        g.siguiente_incidente()

    # N1: 3 legit × 25 + 3 fraude × 20 = 135
    print(f"  XP final N1: {g.estado.xp} (esperado 135)")
    assert g.estado.xp == 135, f"Esperado 135, fue {g.estado.xp}"
    print("  OK")


def test_2_fallo_aplica_impacto():
    print("\n=== TEST 2: Fallo aplica impacto ===")
    g = Game()
    g.siguiente_nivel()  # a N1
    inc = g.incidente_en_curso()
    assert inc.id == "n1_01"

    rep_antes = g.estado.reputacion
    r = g.evaluar_decision("IGNORAR")
    assert not r["correcta"]
    assert r["puntos"] == 0
    assert g.estado.reputacion == rep_antes - 10
    print(f"  Reputación: {rep_antes} → {g.estado.reputacion} ✓")
    print("  OK")


def test_3_derrota():
    print("\n=== TEST 3: Derrota con privacidad en 0 ===")
    g = Game()
    g.cargar_nivel_por_id(2)
    g.estado.privacidad = 10

    idx = None
    for i, inc in g.incidentes_en_nivel():
        if inc.id == "n2_05":
            idx = i
            break
    assert idx is not None

    # Desde el Bloque E, CONFIAR en un incidente OTP abre el banco
    # (needs_interaction); la decisión real es enviar el código.
    r = g.evaluar_decision_en(idx, "CONFIAR")
    assert r.get("needs_interaction") and r["interaccion"] == "otp"
    r = g.enviar_otp(idx)
    assert r is not None and not r["correcta"]
    assert g.estado.privacidad == 0
    assert g.chequear_derrota()
    print(f"  Privacidad: 10 → {g.estado.privacidad} ✓")
    print("  OK")


def test_4_reiniciar_nivel():
    print("\n=== TEST 4: Reiniciar nivel restaura todo ===")
    g = Game()
    g.siguiente_nivel()
    priv0, rep0, din0 = (g.estado.privacidad, g.estado.reputacion, g.estado.dinero)
    g.estado.privacidad = 20
    g.estado.reputacion = 40
    g.estado.dinero = 300
    g.reiniciar_nivel()
    assert g.estado.privacidad == priv0
    assert g.estado.reputacion == rep0
    assert g.estado.dinero == din0
    print(f"  Restaurado: priv={priv0}, rep={rep0}, dinero={din0} ✓")
    print("  OK")


def test_5_gate_n4():
    print("\n=== TEST 5: Gate del Nivel 4 ===")
    g = Game()
    g.cargar_nivel_por_id(3)
    g.estado.privacidad = 50
    g.estado.reputacion = 50
    g.estado.dinero = 400
    assert g.puede_pasar_n4()
    g.estado.privacidad = 20
    assert not g.puede_pasar_n4()
    print("  Bloqueo con priv=20 ✓")
    print("  OK")


def test_6_puntajes():
    print("\n=== TEST 6: Puntajes teóricos ===")
    g = Game()
    max_abs = g.puntaje_maximo()
    print(f"  Máximo absoluto: {max_abs}")
    print(f"  Umbral certificado: {config.UMBRAL_CERTIF}")
    print(f"  % del máximo: {config.UMBRAL_CERTIF / max_abs * 100:.1f}%")
    assert max_abs > 0
    print("  OK")


def test_7_partida_completa():
    print("\n=== TEST 7: Partida completa ===")
    g = Game()
    total = 0
    niveles_ok = 0
    while niveles_ok < 5:
        pendientes = [(i, inc) for i, inc in g.incidentes_en_nivel()
                      if not g.esta_respondido(i)]
        for idx, inc in pendientes:
            g.usar_herramienta_en(idx, "remitente")
            r = g.evaluar_decision_en(idx, inc.respuesta_correcta)
            # CONFIAR en un legítimo con transferencia abre el banco:
            # la decisión se cierra transfiriendo el monto pedido.
            if r and r.get("needs_interaction"):
                assert r["interaccion"] == "transferencia", inc.id
                r = g.confirmar_transferencia(idx, inc.monto_solicitado)
            assert r and r["correcta"], f"Falló {inc.id}"
            total += 1
        assert g.nivel_completado()
        niveles_ok += 1
        if g.nivel.id == 4:
            break
        g.siguiente_nivel()

    print(f"  Incidentes jugados: {total}")
    print(f"  Niveles completados: {niveles_ok}")
    print(f"  XP final: {g.estado.xp}")
    print(f"  Dinero final: ${g.estado.dinero}")
    print(f"  Resultado: {g.resultado_final()}")
    assert total == 34, total      # 33 puntuables + 1 mensaje de práctica
    assert niveles_ok == 5
    print("  OK")


def test_8_intro():
    print("\n=== TEST 8: Cinemática de intro (6 pantallas) ===")
    import datos
    paginas = datos.INTRO_PAGINAS
    # Historia: dónde estás, el dinero, el peligro, los recursos, la misión, practicar
    assert len(paginas) == 6
    claves = [p["key_voz"] for p in paginas]
    assert len(set(claves)) == 6, "key_voz duplicadas"
    datos_fmt = dict(dinero=config.DINERO_INICIAL_V2, matricula=config.MATRICULA)
    for p in paginas:
        assert p["titulo"] and p["texto"] and p["voz"], p["key_voz"]
        # Los marcadores deben poder rellenarse sin error
        p["texto"].format(**datos_fmt)
        p["voz"].format(**datos_fmt)
    seg = paginas[1]["texto"].format(**datos_fmt)
    assert "$800 " in seg and "$500 " in seg, seg
    todo = " ".join(p["texto"] for p in paginas).lower()
    for idea in ("privacidad", "dinero", "reputación", "viernes", "matrícula"):
        assert idea in todo, f"la historia no menciona «{idea}»"
    print("  OK")


# ════════════════════════════════════════════════════════════════
# BLOQUE G — Economía
# ════════════════════════════════════════════════════════════════

def test_9_gastos_diarios():
    print("\n=== TEST 9: Gastos diarios ===")
    g = Game()
    # Solo hay gasto en N2 y N3
    for nid in (0, 1, 4):
        g.cargar_nivel_por_id(nid)
        assert g.aplicar_gastos_dia() is None, f"N{nid} no debe tener gasto"

    g.cargar_nivel_por_id(2)
    gasto = g.aplicar_gastos_dia()
    assert gasto["monto"] == 20
    assert g.pagar_gasto_obligatorio() is True
    assert g.estado.dinero == 800 - 20
    # No se cobra dos veces
    assert g.aplicar_gastos_dia() is None
    assert g.pagar_gasto_obligatorio() is True
    assert g.estado.dinero == 780

    g.cargar_nivel_por_id(3)
    assert g.aplicar_gastos_dia()["monto"] == 30
    assert g.pagar_gasto_obligatorio() is True
    assert g.estado.dinero == 750
    print("  N2 -$20, N3 -$30, sin doble cobro ✓")

    # Sin fondos: derrota aunque priv/rep estén bien
    g = Game()
    g.estado.dinero = 10
    g.cargar_nivel_por_id(2)
    assert g.pagar_gasto_obligatorio() is False
    assert g.estado.dinero == 10, "no se cobra si no alcanza"
    assert g.chequear_derrota() is True
    assert g.estado.privacidad == 100 and g.estado.reputacion == 100
    print("  Sin fondos para el gasto → derrota ✓")
    print("  OK")


def test_10_matricula():
    print("\n=== TEST 10: Matrícula ===")
    g = Game()
    g.cargar_nivel_por_id(3)
    assert g.pagar_matricula() == {"ok": False, "razon": "no_es_viernes"}
    assert g.necesita_pagar_matricula() is False

    g = Game()
    g.estado.dinero = 499
    g.cargar_nivel_por_id(4)
    assert g.necesita_pagar_matricula() is True
    assert g.puede_pagar_matricula() is False
    assert g.pagar_matricula() == {"ok": False, "razon": "sin_dinero"}
    assert g.estado.matricula_pagada is False and g.estado.dinero == 499

    g = Game()
    g.estado.dinero = 500
    g.cargar_nivel_por_id(4)
    assert g.puede_pagar_matricula() is True
    assert g.pagar_matricula() == {"ok": True}
    assert g.estado.dinero == 0 and g.estado.matricula_pagada is True
    assert g.necesita_pagar_matricula() is False
    assert g.pagar_matricula() == {"ok": False, "razon": "ya_pagada"}
    assert g.estado.dinero == 0
    print("  $499 no alcanza; $500 sí; no se paga dos veces ✓")
    print("  OK")


def test_11_prestamo():
    print("\n=== TEST 11: Préstamo de mamá ===")
    # $50: seguro, una sola vez
    g = Game()
    r = g.pedir_prestamo_mama(50)
    assert r == {"aprobado": True, "razon": "seguro", "monto": 50}
    assert g.estado.dinero == 850 and g.estado.prestamo_pedido is True
    assert g.pedir_prestamo_mama(50) == {"aprobado": False, "razon": "ya_pediste"}
    assert g.estado.dinero == 850

    # $100 con random < 0.5 → rechazo (y consume el único intento)
    g = Game()
    with random_fijo(0.10):
        r = g.pedir_prestamo_mama(100)
    assert r == {"aprobado": False, "razon": "rechazo"}
    assert g.estado.dinero == 800
    assert g.estado.prestamo_negado is True and g.estado.prestamo_pedido is True
    assert g.pedir_prestamo_mama(50)["razon"] == "ya_pediste"

    # $100 con random >= 0.5 → aprobado
    g = Game()
    with random_fijo(0.90):
        r = g.pedir_prestamo_mama(100)
    assert r["aprobado"] is True and r["monto"] == 100
    assert g.estado.dinero == 900
    print("  $50 seguro, $100 con rechazo/aprobación, una sola vez ✓")

    # Montos inválidos no consumen el intento
    g = Game()
    for monto in (0, -5, 101, 1000):
        assert g.pedir_prestamo_mama(monto) == {
            "aprobado": False, "razon": "monto_invalido"}, monto
    assert g.estado.prestamo_pedido is False and g.estado.dinero == 800
    print("  Montos inválidos (0, -5, 101) no consumen el intento ✓")

    # Estadística: el rechazo de $100 ronda el 50%
    random.seed(7)
    g = Game()
    rechazos, n = 0, 2000
    for _ in range(n):
        g.estado.prestamo_pedido = False
        if not g.pedir_prestamo_mama(100)["aprobado"]:
            rechazos += 1
    frac = rechazos / n
    print(f"  Rechazo de $100 en {n} intentos: {frac:.1%} (esperado ~50%)")
    assert 0.45 <= frac <= 0.55
    print("  OK")


# ════════════════════════════════════════════════════════════════
# BLOQUE G — Verificación
# ════════════════════════════════════════════════════════════════

def test_12_verificacion():
    print("\n=== TEST 12: Verificación y penalización ===")
    g = Game()
    g.cargar_nivel_por_id(2)
    legit1 = idx_de(g, "n2_02")
    legit2 = idx_de(g, "n2_04")
    fraude = idx_de(g, "n2_07")

    # Llamar a un legítimo: -5 reputación, una sola vez por incidente
    txt = g.verificar_incidente(legit1, "llamada")
    assert txt == g.incidente_por_indice(legit1).verificacion_llamada and txt
    assert g.estado.reputacion == 100 - config.PENALIZACION_SOBRE_VERIFICAR == 95
    g.verificar_incidente(legit1, "llamada")
    assert g.estado.reputacion == 95, "la penalización no se repite"
    assert g.fue_verificado(legit1)

    # Oficial y búsqueda no penalizan, ni en legítimos
    for metodo in ("oficial", "busqueda"):
        assert g.verificar_incidente(legit2, metodo)
    assert g.estado.reputacion == 95

    # Llamar a un fraude no penaliza
    assert g.verificar_incidente(fraude, "llamada")
    assert g.estado.reputacion == 95
    print("  Llamada a legítimo -5 rep (una vez); oficial/búsqueda/fraude 0 ✓")

    # Verificar no responde el incidente ni mueve otros recursos
    assert not g.esta_respondido(legit1)
    assert g.estado.privacidad == 100 and g.estado.dinero == 800

    # La reputación no baja de 0
    g2 = Game()
    g2.cargar_nivel_por_id(2)
    g2.estado.reputacion = 3
    g2.verificar_incidente(idx_de(g2, "n2_02"), "llamada")
    assert g2.estado.reputacion == 0
    print("  Reputación con piso en 0 ✓")

    # VERIFICAR es respuesta correcta en incidentes diseñados para eso
    g3 = Game()
    g3.cargar_nivel_por_id(2)
    r = g3.evaluar_decision_en(idx_de(g3, "n2_01"), "VERIFICAR")
    assert r["correcta"] and r["puntos"] == config.PTS_BASE_LEGIT
    print("  VERIFICAR correcto en n2_01 (+20) ✓")

    # Todos los incidentes (34) tienen sus 3 textos de verificación
    g4 = Game()
    for _ in range(5):
        for _, inc in g4.incidentes_en_nivel():
            assert inc.verificacion_llamada, inc.id
            assert inc.verificacion_oficial, inc.id
            assert inc.verificacion_busqueda, inc.id
        g4.siguiente_nivel()
    print("  Todos los incidentes tienen 3 textos de verificación ✓")
    print("  OK")


# ════════════════════════════════════════════════════════════════
# BLOQUE G — OTP
# ════════════════════════════════════════════════════════════════

def test_13_otp():
    print("\n=== TEST 13: OTP (generar, enviar, arrepentirse) ===")
    g = Game()
    g.cargar_nivel_por_id(2)
    idx = idx_de(g, "n2_05")

    # CONFIAR abre el flujo bancario y NO consume el incidente
    r = g.evaluar_decision_en(idx, "CONFIAR")
    assert r == {"needs_interaction": True, "interaccion": "otp", "idx": idx}
    assert not g.esta_respondido(idx)
    assert g.estado.privacidad == 100 and g.estado.reputacion == 100

    # Código de 6 dígitos, estable mientras sea el mismo incidente
    c1 = g.generar_otp(idx)
    assert len(c1) == 6 and c1.isdigit()
    assert g.generar_otp(idx) == c1
    print(f"  Código de 6 dígitos y estable por incidente ({c1}) ✓")

    # Arrepentirse = no enviar: nada cambió y puede responder bien
    assert not g.esta_respondido(idx) and g.estado.privacidad == 100
    r = g.evaluar_decision_en(idx, "IGNORAR")
    assert r["correcta"] and g.estado.privacidad == 100
    assert g.estado.xp == config.PTS_BASE_FRAUDE
    print("  Arrepentirse y luego IGNORAR: correcto, sin daño (+15) ✓")

    # Enviar el código: daño, sin puntos, consejo desbloqueado
    g = Game()
    g.cargar_nivel_por_id(2)
    idx = idx_de(g, "n2_05")
    g.generar_otp(idx)
    r = g.enviar_otp(idx)
    assert r["correcta"] is False and r["puntos"] == 0
    assert r["via_banco"] == "otp"
    assert g.estado.privacidad == 100 - 40 and g.estado.reputacion == 100 - 20
    assert g.estado.xp == 0
    assert r["consejo"] is not None
    assert "otp_nunca_se_comparte" in g.estado.historial_consejos
    assert g.esta_respondido(idx)
    # No se puede enviar ni responder dos veces
    assert g.enviar_otp(idx) is None
    assert g.evaluar_decision_en(idx, "IGNORAR") is None
    assert g.estado.privacidad == 60
    print("  Enviar OTP: priv -40, rep -20, 0 pts, consejo, una sola vez ✓")

    # Con INTERACCION_ACTIVA = False, CONFIAR se evalúa directo (incorrecto)
    g = Game()
    g.cargar_nivel_por_id(2)
    with config_temp(INTERACCION_ACTIVA=False):
        r = g.evaluar_decision_en(idx_de(g, "n2_05"), "CONFIAR")
    assert r["correcta"] is False and g.estado.privacidad == 60
    print("  Con INTERACCION_ACTIVA=False no abre el banco ✓")
    print("  OK")


# ════════════════════════════════════════════════════════════════
# BLOQUE G — Transferencia
# ════════════════════════════════════════════════════════════════

def test_14_transferencia():
    print("\n=== TEST 14: Transferencia ===")
    # Datos: titular y cuenta visibles, monto positivo, en todas las transferencias
    g = Game()
    total = 0
    for _ in range(5):
        for _, inc in g.incidentes_en_nivel():
            if inc.interaccion == "transferencia":
                total += 1
                assert inc.titular_destino, f"{inc.id}: falta titular visible"
                assert inc.cuenta_destino, f"{inc.id}: falta cuenta"
                assert inc.monto_solicitado > 0, f"{inc.id}: monto"
        g.siguiente_nivel()
    assert total == 5, f"se esperaban 5 transferencias, hay {total}"
    print(f"  {total} transferencias con titular, cuenta y monto ✓")

    # Legítima (n3_08, Papelería $40): correcta, descuenta, da puntos
    g = Game()
    g.cargar_nivel_por_id(3)
    idx = idx_de(g, "n3_08")
    g.usar_herramienta_en(idx, "remitente")
    # Ni más ni menos: solo se acepta exactamente lo pedido ($40)
    for monto in (1, 39, 41, 50, 100, 800):
        assert g.motivo_monto_invalido(idx, monto) == "monto_incorrecto", monto
        assert g.confirmar_transferencia(idx, monto) is None, monto
    assert g.estado.dinero == 800 and not g.esta_respondido(idx)
    print("  Legítima: $39 y $41 rechazados (solo el monto exacto) ✓")
    r = g.confirmar_transferencia(idx, 40)
    assert r["correcta"] and r["via_banco"] == "transferencia"
    assert r["puntos"] == config.PTS_BASE_LEGIT + config.PTS_HERRAMIENTA
    assert g.estado.xp == 25 and g.estado.dinero == 760
    assert r["consejo"] is None
    print("  Legítima: +25 pts, -$40 ✓")

    # Montos inválidos: no pasa nada y no consumen el incidente
    g = Game()
    g.cargar_nivel_por_id(3)
    idx = idx_de(g, "n3_05")
    for monto in (0, -5, 801, 50.5, "50", None, True, 1, 49, 51):
        assert g.confirmar_transferencia(idx, monto) is None, repr(monto)
    assert g.estado.dinero == 800 and not g.esta_respondido(idx)
    print("  Monto 0, negativo, decimal, texto, bool, 1, 49, 51 → rechazado ✓")
    print("  (en un fraude también: la pérdida es exactamente lo que piden)")

    # Fraude (n3_05, "María P." $50): pierde lo enviado + daño, sin puntos
    r = g.confirmar_transferencia(idx, 50)
    assert r["correcta"] is False and r["puntos"] == 0
    assert g.estado.dinero == 750
    assert g.estado.reputacion == 90 and g.estado.privacidad == 100
    assert "verificar_por_voz" in g.estado.historial_consejos
    assert g.estado.xp == 0
    assert g.confirmar_transferencia(idx, 50) is None, "una sola vez"
    print("  Fraude: -$50, rep -10, consejo desbloqueado ✓")

    # Cancelar (no llamar a confirmar): se puede VERIFICAR y ganar puntos
    g = Game()
    g.cargar_nivel_por_id(3)
    idx = idx_de(g, "n3_05")
    assert g.evaluar_decision_en(idx, "CONFIAR")["needs_interaction"]
    assert not g.esta_respondido(idx) and g.estado.dinero == 800
    r = g.evaluar_decision_en(idx, "VERIFICAR")
    assert r["correcta"] and g.estado.xp == config.PTS_BASE_FRAUDE
    print("  Cancelar y VERIFICAR: correcto, sin pérdida ✓")
    print("  OK")


# ════════════════════════════════════════════════════════════════
# BLOQUE G — Eventos aleatorios
# ════════════════════════════════════════════════════════════════

def test_15_eventos():
    print("\n=== TEST 15: Eventos aleatorios ===")
    # No se dispara en el Nivel 0
    g = Game()
    assert g.nivel.id == 0
    responder_bien(g, 1)
    with random_fijo(0.0):
        assert g.intentar_evento_aleatorio() is None
    print("  No en N0 ✓")

    # No se dispara antes de la primera respuesta
    g = Game()
    g.siguiente_nivel()
    with random_fijo(0.0):
        assert g.intentar_evento_aleatorio() is None

    # Umbral de probabilidad: 0.59 dispara, 0.61 no
    g = Game(); g.siguiente_nivel(); responder_bien(g, 1)
    with random_fijo(0.61):
        assert g.intentar_evento_aleatorio() is None
    assert g.fue_evento_disparado() is False
    with random_fijo(0.59):
        ev = g.intentar_evento_aleatorio()
    assert ev is not None and g.fue_evento_disparado() is True
    print("  Probabilidad 60% (0.59 dispara, 0.61 no) ✓")

    # Forma del evento
    assert ev.es_evento and ev.es_familiar and ev.categoria == "legitimo"
    assert ev.respuesta_correcta == "CONFIAR"
    # Ayudar = transferencia por el monto exacto (cuesta dinero)
    assert ev.interaccion == "transferencia" and ev.monto_solicitado > 0
    assert ev.cuenta_destino and "verificado" in ev.titular_destino
    eidx = len(g.nivel.incidentes) - 1
    assert g.incidente_por_indice(eidx) is ev
    assert eidx in g.estado.eventos_activos

    # Solo uno por nivel
    with random_fijo(0.0):
        assert g.intentar_evento_aleatorio() is None
    print("  Uno por nivel ✓")

    # El evento no cuenta para completar el nivel
    assert g.nivel_completado() is False
    responder_bien(g, 99)
    assert g.nivel_completado() is True and g.restantes_en_nivel() == 0
    assert not g.esta_respondido(eidx), "el evento sigue sin responder"
    print("  El nivel se completa sin atender el evento ✓")

    # Responder el evento: ayudar (transferencia exacta) sin XP; IGNORAR -15 rep
    assert g.evaluar_decision_en(eidx, "CONFIAR")["needs_interaction"]
    xp0, din0 = g.estado.xp, g.estado.dinero
    r = g.confirmar_transferencia(eidx, ev.monto_solicitado)
    assert r["correcta"] and g.estado.xp == xp0, "los eventos no dan XP"
    assert g.estado.dinero == din0 - ev.monto_solicitado
    g2 = Game(); g2.siguiente_nivel(); responder_bien(g2, 1)
    with random_fijo(0.0):
        ev2 = g2.intentar_evento_aleatorio()
    rep0 = g2.estado.reputacion
    r = g2.evaluar_decision_en(len(g2.nivel.incidentes) - 1, "IGNORAR")
    assert r["correcta"] is False and g2.estado.reputacion == rep0 - 15
    print("  Evento: sin XP; ignorarlo -15 rep ✓")

    # No se dispara cerca del final (quedan <2 normales por responder)
    g = Game(); g.siguiente_nivel()          # N1 tiene 6 normales
    responder_bien(g, 5)                     # queda 1
    with random_fijo(0.0):
        assert g.intentar_evento_aleatorio() is None
    g = Game(); g.siguiente_nivel()
    responder_bien(g, 4)                     # quedan 2
    with random_fijo(0.0):
        assert g.intentar_evento_aleatorio() is not None
    print("  No con 1 pendiente; sí con 2 ✓")

    # Frecuencia real ≈ 60% (reiniciar_nivel limpia el flag y el evento)
    random.seed(11)
    g = Game(); g.siguiente_nivel()
    disparos, n = 0, 2000
    for _ in range(n):
        g.reiniciar_nivel()
        responder_bien(g, 1)
        if g.intentar_evento_aleatorio() is not None:
            disparos += 1
    frac = disparos / n
    print(f"  Frecuencia en {n} niveles: {frac:.1%} (esperado ~60%)")
    assert 0.55 <= frac <= 0.65
    print("  OK")


# ════════════════════════════════════════════════════════════════
# BLOQUE G — Fin de semana
# ════════════════════════════════════════════════════════════════

def test_16_fin_de_semana():
    print("\n=== TEST 16: Fin de semana (resultado final) ===")
    g = Game()
    g.cargar_nivel_por_id(4)

    # Sin matrícula → regaño, aunque el XP sea altísimo
    g.estado.xp = 900
    assert g.resultado_final() == "sin_matricula"
    assert g.resultado_nivel() == "sin_matricula"

    # Con matrícula pero < umbral → parcial; >= umbral → certificado
    g.estado.matricula_pagada = True
    g.estado.xp = config.UMBRAL_CERTIF - 1
    assert g.resultado_final() == "parcial"
    g.estado.xp = config.UMBRAL_CERTIF
    assert g.resultado_final() == "certificado"
    g.estado.xp = g.puntaje_maximo()
    assert g.resultado_final() == "certificado"
    print(f"  sin matrícula→regaño; {config.UMBRAL_CERTIF - 1}→parcial; "
          f"{config.UMBRAL_CERTIF}→certificado ✓")

    # Pedir préstamo para alcanzar la matrícula
    g = Game(); g.estado.dinero = 460; g.cargar_nivel_por_id(4)
    assert not g.puede_pagar_matricula()
    assert g.pedir_prestamo_mama(50)["aprobado"]
    assert g.pagar_matricula() == {"ok": True}
    assert g.estado.dinero == 10 and g.estado.matricula_pagada
    print("  $460 + préstamo $50 → paga la matrícula ✓")

    # Si ni con préstamo alcanza → sin matrícula
    g = Game(); g.estado.dinero = 300; g.cargar_nivel_por_id(4)
    with random_fijo(0.9):
        assert g.pedir_prestamo_mama(100)["aprobado"]
    assert g.estado.dinero == 400
    assert g.pagar_matricula()["razon"] == "sin_dinero"
    g.estado.xp = 700
    assert g.resultado_final() == "sin_matricula"
    print("  $300 + préstamo $100 = $400 → sin matrícula ✓")

    # Gate N3 → N4: umbrales estrictos (> 30, > 30, > 100)
    g = Game(); g.cargar_nivel_por_id(3)
    g.estado.privacidad, g.estado.reputacion, g.estado.dinero = 31, 31, 101
    assert g.puede_pasar_n4() and g.resultado_nivel() == "continuar"
    for campo, valor in (("privacidad", 30), ("reputacion", 30), ("dinero", 100)):
        g.estado.privacidad, g.estado.reputacion, g.estado.dinero = 31, 31, 101
        setattr(g.estado, campo, valor)
        assert not g.puede_pasar_n4(), campo
        assert g.resultado_nivel() == "repetir_n3", campo
    print("  Gate N4: priv>30, rep>30, $>100 ✓")
    print("  OK")


# ════════════════════════════════════════════════════════════════
# BLOQUE G — Reiniciar nivel (regresiones de economía)
# ════════════════════════════════════════════════════════════════

def test_17_reiniciar_nivel_economia():
    print("\n=== TEST 17: Reiniciar nivel no regala ni cobra doble ===")
    # XP: repetir un nivel no suma dos veces
    g = Game(); g.siguiente_nivel()
    responder_bien(g, 2)
    assert g.estado.xp == 40
    g.reiniciar_nivel()
    assert g.estado.xp == 0
    responder_bien(g, 2)
    assert g.estado.xp == 40, "XP duplicado al repetir el nivel"
    g.reiniciar_nivel(); responder_bien(g, 99)
    xp_n1 = g.estado.xp
    g.siguiente_nivel()
    g.reiniciar_nivel()
    assert g.estado.xp == xp_n1, "reiniciar N2 no debe perder el XP de N1"
    print("  XP restaurado (sin duplicar) ✓")

    # Gasto diario: pagado antes de morir → no se reembolsa ni se recobra
    g = Game(); g.cargar_nivel_por_id(2)
    assert g.pagar_gasto_obligatorio()
    g.estado.dinero = 700                      # perdió dinero jugando
    g.reiniciar_nivel()
    assert g.estado.dinero == 780, "el gasto pagado no se reembolsa"
    assert g.aplicar_gastos_dia() is None, "no se cobra dos veces"
    print("  Gasto diario: $780 tras reiniciar (ni reembolso ni doble cobro) ✓")

    # Murió por no poder pagar el gasto: al repetir se vuelve a pedir
    g = Game(); g.estado.dinero = 10; g.cargar_nivel_por_id(2)
    assert g.pagar_gasto_obligatorio() is False and g.chequear_derrota()
    g.reiniciar_nivel()
    assert not g.chequear_derrota() and g.estado.dinero == 10
    assert g.aplicar_gastos_dia() is not None, "el gasto sigue pendiente"
    print("  Murió por gasto: sigue pendiente al repetir ✓")

    # Matrícula pagada: se queda pagada y el dinero no vuelve
    g = Game(); g.cargar_nivel_por_id(4)
    assert g.pagar_matricula()["ok"]
    g.estado.dinero = 100
    g.reiniciar_nivel()
    assert g.estado.dinero == 300 and g.estado.matricula_pagada
    assert g.necesita_pagar_matricula() is False
    print("  Matrícula: $300 y sigue pagada tras reiniciar ✓")

    # Préstamo: el dinero prestado se conserva (el préstamo es de una vez)
    g = Game(); g.estado.dinero = 400; g.cargar_nivel_por_id(4)
    assert g.pedir_prestamo_mama(50)["aprobado"]
    g.estado.dinero = 20
    g.reiniciar_nivel()
    assert g.estado.dinero == 450 and g.estado.prestamo_pedido
    print("  Préstamo: $450 tras reiniciar ✓")

    # Eventos: se descartan al reiniciar y puede salir otro
    g = Game(); g.siguiente_nivel(); n_normales = len(g.nivel.incidentes)
    responder_bien(g, 1)
    with random_fijo(0.0):
        assert g.intentar_evento_aleatorio() is not None
    assert len(g.nivel.incidentes) == n_normales + 1
    g.reiniciar_nivel()
    assert len(g.nivel.incidentes) == n_normales, "evento viejo sigue en la lista"
    assert g.estado.eventos_activos == []
    print("  Evento descartado al reiniciar ✓")
    print("  OK")


# ════════════════════════════════════════════════════════════════
# BLOQUE G — Balance (usa _simular_balance.py)
# ════════════════════════════════════════════════════════════════

def test_18_balance():
    print("\n=== TEST 18: Balance (partidas simuladas) ===")
    import _simular_balance as sim

    # Partida perfecta determinista, con economía real (gastos, matrícula)
    r = sim.jugar_partida(1.0, 1.0, seed=1, eventos=False)
    assert r["resultado"] == "certificado"
    assert r["xp"] == Game().puntaje_maximo() == 800
    assert r["dinero"] == 800 - 20 - 30 - 40 - config.MATRICULA == 210
    assert r["derrotas"] == 0
    print(f"  Perfecta: {r['xp']} XP, ${r['dinero']} al final, certificado ✓")

    # El umbral es el 70% del máximo teórico (decisión del equipo, spec 01/11)
    maximo = Game().puntaje_maximo()
    assert config.UMBRAL_CERTIF == round(0.70 * maximo) == 560

    # Jugador experto (todo bien, investiga la mitad): margen cómodo sobre el
    # umbral (con 560 ronda +28%; aceptamos 22%–35%)
    s = sim.simular("experta", 200)
    margen = s["xp_prom"] / config.UMBRAL_CERTIF - 1
    print(f"  Experta: {s['xp_prom']:.0f} XP = {margen:+.1%} sobre el umbral")
    assert 0.22 <= margen <= 0.35
    assert s["cuenta"]["certificado"] == 200

    # El juego discrimina: más habilidad → más certificados
    cert = {p: sim.simular(p, 200)["cuenta"]["certificado"]
            for p in ("perfecta", "buena", "media", "mala")}
    print("  Certificados de 200:", cert)
    assert cert["perfecta"] >= cert["buena"] > cert["media"] >= cert["mala"]
    assert cert["perfecta"] == 200
    assert cert["mala"] == 0, "jugar al azar no debe dar certificado"
    assert cert["buena"] >= 190, "90% de aciertos debería certificar casi siempre"
    print("  OK")


# ════════════════════════════════════════════════════════════════
# BLOQUE H — Eventos que cuestan, temporizador y derrota explicada
# ════════════════════════════════════════════════════════════════

def _evento_en(g, monto=80):
    """Dispara un evento en el nivel cargado y fija su monto. -> (ev, idx)."""
    responder_bien(g, 1)
    with random_fijo(0.0):
        ev = g.intentar_evento_aleatorio()
    assert ev is not None
    ev.monto_solicitado = monto
    return ev, len(g.nivel.incidentes) - 1


def test_19_evento_ayudar_cuesta():
    print("\n=== TEST 19: Ayudar en un evento cuesta dinero y da respeto ===")
    g = Game(); g.siguiente_nivel()
    ev, eidx = _evento_en(g, 80)

    # Ayudar: -$80, +5 reputación (poco), sin XP
    g.estado.reputacion = 90
    xp0 = g.estado.xp
    din0 = g.estado.dinero
    r = g.confirmar_transferencia(eidx, 80)
    assert r["correcta"] and r["via_banco"] == "transferencia"
    assert g.estado.dinero == din0 - 80
    assert g.estado.reputacion == 90 + config.EVENTO_REP_AYUDA == 95
    assert r["impacto_aplicado"] == {"dinero": -80, "reputacion": 5}
    assert g.estado.xp == xp0 and r["puntos"] == 0 and r["consejo"] is None
    print("  Ayudar: -$80, +5 reputación, 0 XP ✓")

    # Tope de reputación en 100
    g = Game(); g.siguiente_nivel(); ev, eidx = _evento_en(g, 50)
    g.estado.reputacion = 98
    r = g.confirmar_transferencia(eidx, 50)
    assert g.estado.reputacion == 100 and r["impacto_aplicado"]["reputacion"] == 2
    print("  La reputación no pasa de 100 ✓")

    # Monto exacto
    g = Game(); g.siguiente_nivel(); ev, eidx = _evento_en(g, 80)
    for monto in (79, 81, 1, 160):
        assert g.confirmar_transferencia(eidx, monto) is None, monto
    assert not g.esta_respondido(eidx)

    # Saldo: no puedes quedarte en $0 por ayudar (sería una derrota)
    g.estado.dinero = 80
    assert not g.saldo_alcanza_para(eidx)
    assert g.motivo_monto_invalido(eidx, 80) == "saldo_insuficiente"
    assert g.confirmar_transferencia(eidx, 80) is None
    g.estado.dinero = 79
    assert not g.saldo_alcanza_para(eidx)
    g.estado.dinero = 81
    assert g.saldo_alcanza_para(eidx)
    print("  Saldo $80 o menos no alcanza para un evento de $80 ✓")

    # Sin dinero para ayudar: ignorar resta respeto
    g.estado.dinero = 50
    rep0 = g.estado.reputacion
    r = g.evaluar_decision_en(eidx, "IGNORAR")
    assert r["correcta"] is False and g.estado.reputacion == rep0 - 15
    assert g.estado.dinero == 50
    print("  Sin saldo: ignorar → -15 reputación ✓")

    # Ayudar puede poner en riesgo la matrícula (el dilema del juego)
    g = Game(); g.estado.dinero = 560; g.cargar_nivel_por_id(4)
    assert g.puede_pagar_matricula()
    ev, eidx = _evento_en(g, 80)
    assert g.confirmar_transferencia(eidx, 80)["correcta"]
    assert g.estado.dinero == 480 and not g.puede_pagar_matricula()
    print("  Con $560, ayudar $80 deja $480: ya no alcanza la matrícula ✓")
    print("  OK")


def test_20_temporizador_agotado():
    print("\n=== TEST 20: Temporizador agotado (resolver_por_tiempo) ===")
    claves = {"idx", "accion", "correcta", "puntos", "herramienta_usada",
              "feedback", "consejo", "impacto_aplicado", "estado_post",
              "auto_por_timer"}

    def resolver(nivel, inc_id, dinero=800):
        g = Game(); g.estado.dinero = dinero; g.cargar_nivel_por_id(nivel)
        idx = idx_de(g, inc_id)
        r = g.resolver_por_tiempo(idx)
        # main.py exige estas claves (antes fallaba con KeyError: 'consejo')
        assert claves <= set(r), (inc_id, claves - set(r))
        assert r["auto_por_timer"] is True and g.esta_respondido(idx)
        assert g.resolver_por_tiempo(idx) is None, "una sola vez"
        return g, r

    # OTP: se envía el código
    g, r = resolver(2, "n2_05")
    assert r["via_banco"] == "otp" and not r["correcta"]
    assert g.estado.privacidad == 60 and g.estado.reputacion == 80
    print("  OTP: se envía el código (priv -40, rep -20) ✓")

    # Fraude por transferencia: paga exactamente lo pedido
    g, r = resolver(2, "n2_06")
    assert r["via_banco"] == "transferencia" and not r["correcta"]
    assert g.estado.dinero == 750 and g.estado.privacidad == 80
    print("  Fraude: transfiere los $50 pedidos ✓")

    # Legítima: confiar era correcto
    g, r = resolver(3, "n3_08")
    assert r["correcta"] and g.estado.dinero == 760 and g.estado.xp == 20
    print("  Legítima: paga $40 y suma 20 ✓")

    # Sin saldo: la transferencia no se hace, pero hay consecuencia
    g, r = resolver(2, "n2_06", dinero=30)
    assert r["via_banco"] == "sin_fondos" and not r["correcta"]
    assert g.estado.dinero == 30, "no se mueve dinero"
    assert g.estado.privacidad == 80
    assert "banco_canal_oficial" in g.estado.historial_consejos
    g, r = resolver(3, "n3_08", dinero=30)
    assert not r["correcta"] and g.estado.dinero == 30
    assert g.estado.reputacion == 90
    print("  Sin saldo: sin mover dinero, con consecuencia ✓")

    # Mensaje normal: confía y cae
    g, r = resolver(2, "n2_07")
    assert not r["correcta"] and r["accion"] == "CONFIAR"
    print("  Mensaje sin interacción: Confiar automático ✓")

    # Evento: confía → ayuda (con saldo)
    g = Game(); g.cargar_nivel_por_id(2)
    ev, eidx = _evento_en(g, 50)
    g.estado.reputacion = 80
    r = g.resolver_por_tiempo(eidx)
    assert r["correcta"] and g.estado.reputacion == 85 and r["auto_por_timer"]
    print("  Evento: ayuda automáticamente ✓")

    # Con INTERACCION_ACTIVA = False se evalúa como CONFIAR normal
    g = Game(); g.cargar_nivel_por_id(2)
    with config_temp(INTERACCION_ACTIVA=False):
        r = g.resolver_por_tiempo(idx_de(g, "n2_05"))
    assert claves <= set(r) and not r["correcta"]
    print("  OK")


def test_21_derrota_explicada():
    print("\n=== TEST 21: Motivo de la derrota ===")
    g = Game(); g.siguiente_nivel()
    assert g.motivo_derrota() is None
    assert g.info_derrota()["puede_repetir"] is True

    for campo, motivo in (("privacidad", "privacidad"), ("dinero", "dinero"),
                          ("reputacion", "reputacion")):
        g = Game(); g.siguiente_nivel()
        setattr(g.estado, campo, 0)
        info = g.info_derrota()
        assert info["motivo"] == motivo and info["puede_repetir"], campo
    print("  Privacidad / dinero / reputación en 0 → se puede repetir ✓")

    # No poder pagar el gasto: no se ofrece repetir (mismo saldo = misma derrota)
    g = Game(); g.estado.dinero = 10; g.cargar_nivel_por_id(2)
    assert g.pagar_gasto_obligatorio() is False
    info = g.info_derrota()
    assert info == {"motivo": "gasto", "puede_repetir": False, "dinero": 10,
                    "concepto": "Comida y transporte", "monto": 20}, info
    g = Game(); g.estado.dinero = 25; g.cargar_nivel_por_id(3)
    assert g.pagar_gasto_obligatorio() is False
    info = g.info_derrota()
    assert info["concepto"] == "Recarga de celular" and info["monto"] == 30
    assert not info["puede_repetir"]
    print("  Sin dinero para el gasto → explica concepto y monto, sin repetir ✓")

    # Al empezar de nuevo desaparece la derrota
    g.reiniciar_partida()
    assert g.motivo_derrota() is None
    print("  OK")


def test_22_matricula_exacta_no_es_derrota():
    print("\n=== TEST 22: Pagar la matrícula y quedar en $0 no es derrota ===")
    # El Viernes con exactamente $500: pagar deja $0 y NO se pierde
    g = Game(); g.estado.dinero = 500; g.cargar_nivel_por_id(4)
    assert g.pagar_matricula() == {"ok": True}
    assert g.estado.dinero == 0
    assert g.estado_estado() == "jugando" and not g.chequear_derrota()
    assert g.motivo_derrota() is None
    r = g.evaluar_decision_en(0, g.incidente_por_indice(0).respuesta_correcta)
    assert r["correcta"] and not g.chequear_derrota()
    print("  Viernes: $500 → paga → $0 → sigue jugando ✓")

    # Pero $0 sin haber pagado, o en cualquier otro nivel, sí es derrota
    g = Game(); g.estado.dinero = 0; g.cargar_nivel_por_id(4)
    assert g.chequear_derrota() and g.motivo_derrota() == "dinero"
    g = Game(); g.estado.dinero = 0; g.cargar_nivel_por_id(3)
    assert g.chequear_derrota() and g.motivo_derrota() == "dinero"
    print("  $0 sin matrícula pagada, o antes del Viernes → derrota ✓")

    # Regresión: esta partida perfecta quedaba atascada (llegaba con $500 justos)
    import _simular_balance as sim
    r = sim.jugar_partida(1.0, 0.5, seed=1036)
    assert r["resultado"] == "certificado" and r["derrotas"] == 0, r
    print("  Partida simulada que antes se atascaba: certificado ✓")
    print("  OK")


def test_23_reputacion_dia_nuevo():
    print("\n=== TEST 23: +10 de reputación al empezar un día nuevo ===")
    assert config.REP_NUEVO_DIA == 10
    g = Game()
    g.siguiente_nivel()                       # N1
    g.estado.reputacion = 50
    g.siguiente_nivel()                       # N2
    assert g.estado.reputacion == 60
    print("  Rep 50 → 60 al pasar al día siguiente ✓")

    # Tope de 100
    g.estado.reputacion = 95
    g.siguiente_nivel()
    assert g.estado.reputacion == 100
    print("  Con rep 95 → 100 (tope) ✓")

    # Queda en el punto de partida: repetir el nivel no pierde el bono
    g = Game(); g.siguiente_nivel(); g.estado.reputacion = 40
    g.siguiente_nivel()                       # 50 al empezar N2
    g.estado.reputacion = 5                   # lo pierde jugando
    g.reiniciar_nivel()
    assert g.estado.reputacion == 50
    print("  Repetir el nivel vuelve a 50 (incluye el bono) ✓")

    # Solo al AVANZAR de día: no al repetir, ni al cargar un nivel por id,
    # ni al empezar la partida
    g = Game(); g.estado.reputacion = 40
    g.reiniciar_nivel()                       # vuelve al 100 del inicio, sin bono extra
    assert g.estado.reputacion == 100
    g = Game(); g.estado.reputacion = 40; g.cargar_nivel_por_id(3)
    assert g.estado.reputacion == 40
    g = Game()
    assert g.estado.reputacion == 100
    print("  No se aplica al repetir, al cargar por id ni al inicio ✓")

    # Al final de la semana no hay día siguiente: no cambia nada
    g = Game(); g.cargar_nivel_por_id(4); g.estado.reputacion = 30
    assert g.siguiente_nivel() is False and g.estado.reputacion == 30
    print("  OK")


# ════════════════════════════════════════════════════════════════
# BLOQUE I — Apartado visual (gfx.py / ui.py). Usan pygame SIN ventana.
# ════════════════════════════════════════════════════════════════

def _pygame_sin_ventana():
    import os
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
    import pygame
    pygame.init()
    return pygame


def test_24_gfx_escala_y_suavizado():
    print("\n=== TEST 24: gfx — escala, ratón y suavizado ===")
    pygame = _pygame_sin_ventana()
    import gfx

    gfx.init(1.5)
    assert gfx.px(10) == 15
    assert tuple(gfx.rect_px((10, 20, 100, 40))) == (15, 30, 150, 60)
    assert gfx.a_logico((150, 300)) == (100.0, 200.0)
    print("  Conversión lógico↔real y ratón a escala 1.5 ✓")

    # Rectángulos contiguos no dejan huecos aunque la escala sea fraccionaria
    gfx.init(1.25)
    a = gfx.rect_px((0, 0, 10, 10))
    b = gfx.rect_px((10, 0, 10, 10))
    assert a.right == b.left
    print("  Sin huecos entre rectángulos contiguos (escala 1.25) ✓")

    # Superficies: tamaño real; con fondo son opacas
    gfx.init(1.5)
    s = gfx.surface(100, 50)
    assert s.get_size() == (150, 75) and s.get_flags() & pygame.SRCALPHA
    o = gfx.surface(10, 10, (255, 255, 255))
    assert o.get_at((0, 0))[:3] == (255, 255, 255)

    # Suavizado: un círculo tiene píxeles de borde intermedios (ni fondo ni color)
    gfx.init(1.25)
    lienzo = pygame.Surface((80, 80))
    lienzo.fill((255, 255, 255))
    gfx.circle(lienzo, (200, 0, 0), (32, 32), 20)
    assert lienzo.get_at((40, 40))[:3] == (200, 0, 0), "el centro debe ser del color"
    assert lienzo.get_at((2, 2))[:3] == (255, 255, 255), "la esquina debe quedar vacía"
    intermedios = sum(1 for x in range(80) for y in range(80)
                      if lienzo.get_at((x, y))[:3] not in ((255, 255, 255), (200, 0, 0)))
    assert intermedios > 40, f"sin suavizado ({intermedios} píxeles de borde)"
    print(f"  Círculo suavizado ({intermedios} píxeles de borde intermedios) ✓")

    # Rectángulo recto y línea horizontal: nítidos (sin píxeles intermedios)
    lienzo.fill((255, 255, 255))
    gfx.rect(lienzo, (0, 0, 200), (10, 10, 40, 20))
    gfx.line(lienzo, (0, 0, 200), (10, 50), (60, 50), 1)
    colores = {lienzo.get_at((x, y))[:3] for x in range(80) for y in range(80)}
    assert colores == {(255, 255, 255), (0, 0, 200)}, colores
    print("  Rectas nítidas, sin difuminar ✓")

    # La caché reutiliza la forma entre cuadros
    n = len(gfx._cache)
    gfx.circle(lienzo, (200, 0, 0), (32, 32), 20)
    assert len(gfx._cache) == n
    print("  Caché de formas reutilizada ✓")

    # Escala: 'auto' respeta el mínimo; un número se respeta tal cual
    assert gfx.calcular_escala(400, 700, 1.5) == 1.5
    assert gfx.calcular_escala(400, 700, "auto") >= 0.75
    gfx.init(1.0)
    print("  OK")


def test_25_ui_botones_no_dependen_de_la_escala():
    print("\n=== TEST 25: ui — mismos botones a cualquier escala; textos ===")
    import tempfile
    pygame = _pygame_sin_ventana()
    import _capturas
    import gfx

    with tempfile.TemporaryDirectory() as tmp:
        a = _capturas.generar(1.0, tmp, guardar_png=False)
        b = _capturas.generar(1.5, tmp, guardar_png=False)
        c = _capturas.generar(1.25, tmp, guardar_png=False)
    assert len(a) >= 60, f"solo {len(a)} pantallas capturadas"
    assert set(a) == set(b) == set(c)
    for nombre in a:
        assert a[nombre] == b[nombre] == c[nombre], \
            f"{nombre}: los botones cambian con la escala"
    print(f"  {len(a)} pantallas: botones idénticos a escala 1.0, 1.25 y 1.5 ✓")

    # Texto: sin emojis (pygame no los dibuja) y con símbolos de respaldo
    import ui
    gfx.init(1.0)
    ui.init()
    assert ui._limpiar("📞 Llamar ⚠️ ya") == " Llamar ⚠ ya"
    assert ui._render("", (0, 0, 0), "body").get_width() >= 1      # cadena vacía
    import sys
    if sys.platform == "win32":
        # Segoe UI no trae ⚠ ✕ ⌂ ✓; Segoe UI Symbol sí
        for simbolo in "⚠✕⌂✓":
            assert ui._falta(ui._f["body"], simbolo), simbolo
            assert not ui._falta(ui._fs["body"], simbolo), simbolo
        assert not ui._falta(ui._f["body"], "→")
        print("  Símbolos ⚠ ✕ ⌂ ✓ dibujados con la fuente de símbolos ✓")
    print("  OK")


# ════════════════════════════════════════════════════════════════
# BLOQUE J — Voz, día de la semana y nombre (specs/13_dia_y_voz.md)
# ════════════════════════════════════════════════════════════════

def test_26_voces_manifiesto():
    print("\n=== TEST 26: Voz — manifiesto, textos y elección de la voz ===")
    import os
    import datos
    import voces

    m = voces.manifest()
    g = Game()
    ids = set()
    for _ in range(5):
        ids |= {inc.id for _, inc in g.incidentes_en_nivel()}
        g.siguiente_nivel()
    assert len(ids) == 34          # 33 puntuables + 1 de práctica
    assert set(datos.VOZ_ERRORES) == ids

    # Cobertura: intro, 5 días, consejos, un error por mensaje, eventos, tiempo, derrotas
    for i in range(1, 6):
        assert f"intro_p{i}" in m
    for i in range(5):
        assert f"dia_{i}" in m
    for c in datos.CONSEJOS.values():
        assert c["key_voz"] in m, c["key_voz"]
    for inc_id in ids:
        assert f"err_{inc_id}" in m, inc_id
    for paso in datos.TUTORIAL_PASOS:
        assert f"tut_{paso['id']}" in m, paso["id"]
    for i in range(1, 7):
        assert f"intro_p{i}" in m
    for ev in config.EVENTOS_DISPONIBLES:
        assert f"err_evento_{ev['id']}" in m
    for motivo in ("privacidad", "dinero", "reputacion", "gasto"):
        assert f"derrota_{motivo}" in m
    assert "err_tiempo" in m
    print(f"  {len(m)} frases con voz: historia, tutorial, días, consejos, errores, eventos, tiempo y derrotas ✓")

    # Estilo: los errores explican (empiezan con "Fallaste"), son cortos y sin cifras
    for clave, texto in m.items():
        assert texto.strip() and len(texto) <= 330, f"{clave}: {len(texto)} caracteres"
        if clave.startswith("err_") and clave != "err_tiempo":
            assert texto.startswith("Fallaste."), clave
            assert not any(ch.isdigit() or ch == "$" for ch in texto), \
                f"{clave}: evita cifras y monedas en lo hablado"
    assert voces.huella("a") != voces.huella("b")
    print("  Errores: empiezan con «Fallaste», ≤ 330 caracteres y sin cifras ✓")

    # Elegir la voz en español: el id de Windows contiene la palabra "voices"
    class Voz:
        def __init__(self, id, name, languages):
            self.id, self.name, self.languages = id, name, languages
    base = "HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Speech\\Voices\\Tokens\\"
    helena = Voz(base + "TTS_MS_ES-ES_HELENA_11.0", "Microsoft Helena Desktop - Spanish (Spain)", ["es-ES"])
    zira = Voz(base + "TTS_MS_EN-US_ZIRA_11.0", "Microsoft Zira Desktop - English (United States)", ["en-US"])
    sabina = Voz(base + "TTS_MS_ES-MX_SABINA_11.0", "Microsoft Sabina Desktop - Spanish (Mexico)", ["es-MX"])
    assert voces.es_voz_espanola(helena) and not voces.es_voz_espanola(zira)
    assert voces.elegir_voz([helena, zira]) is helena
    assert voces.elegir_voz([zira, helena]) is helena, "no debe ganar la última voz"
    assert voces.elegir_voz([helena, sabina, zira]) is sabina, "es-MX antes que es-ES"
    assert voces.elegir_voz([zira]) is None
    print("  Elige Helena aunque Zira (inglés) esté de última; es-MX antes que es-ES ✓")

    # Los audios generados están al día respecto de los textos
    hay = os.path.isdir(voces.CARPETA) and any(
        f.endswith(".wav") for f in os.listdir(voces.CARPETA))
    if hay:
        faltan, obsoletos = voces.estado_audios()
        assert not faltan and not obsoletos, \
            f"audios sin generar/desactualizados: {faltan + obsoletos} → python generar_voces.py"
        print(f"  {len(m)} audios al día con los textos ✓")
    else:
        print("  (aún no hay audios: ejecuta `python generar_voces.py`)")
    print("  OK")


def test_27_voz_en_el_juego():
    print("\n=== TEST 27: Voz — reproducción y corte ===")
    pygame = _pygame_sin_ventana()
    import voces
    from audio_manager import AudioManager

    audio = AudioManager()
    if audio.canal_voz is None or voces.ruta_audio("err_n2_05") is None:
        print("  (sin mezclador de audio o sin audios: se omite)")
        return
    with config_temp(MODO_VOZ="grabado"):
        audio.hablar("err_n2_05", "texto")
        assert audio.canal_voz.get_busy(), "debe sonar el audio grabado"
        audio.detener_voz()
        assert not audio.canal_voz.get_busy(), "detener_voz debe cortar la voz"
        print("  Audio grabado suena y se corta con detener_voz ✓")

        audio.hablar_varios([("err_tiempo", "a"), ("err_n2_05", "b")])
        assert audio.canal_voz.get_busy()
        assert audio._ultimo_hablado[0] == "err_n2_05"
        # la segunda frase queda EN COLA (suena cuando termine la primera)
        assert audio.canal_voz.get_queue() is not None
        audio.detener_voz()
        assert audio.canal_voz.get_queue() is None, "detener_voz vacía la cola"
        print("  Tiempo agotado: dos frases seguidas (aviso + explicación) ✓")

    with config_temp(MODO_VOZ="silencio"):
        audio.hablar("err_n2_05", "texto")
        audio.hablar_varios([("err_tiempo", "a")])
        assert not audio.canal_voz.get_busy(), "en silencio no suena nada"
    print("  Modo silencio: nada suena ✓")
    print("  OK")


def test_28_menu_sin_nombre_y_dia():
    print("\n=== TEST 28: Sin campo de nombre; saludo y pantalla del día ===")
    pygame = _pygame_sin_ventana()
    import gfx
    gfx.init(1.0)
    pygame.display.set_mode((400, 700))
    import ui
    ui.init()
    import inspect
    assert list(inspect.signature(ui.draw_menu).parameters) == ["screen"]
    assert list(inspect.signature(ui.draw_home).parameters) == ["screen", "game"]
    assert config.NOMBRE_JUGADOR == "Camilo"
    # Saludo según el día: el Domingo es a las 6 PM
    assert config.SALUDO_POR_NIVEL.get(0) == "Buenas tardes,"
    assert config.SALUDO_POR_NIVEL.get(3, config.SALUDO_DEFECTO) == "Buenos días,"
    print("  Menú y Home ya no reciben nombre; saludo según el día ✓")

    # Pantalla del día: un nombre por nivel, y solo acepta continuar al final
    screen = pygame.display.get_surface()
    g = Game()
    dias = []
    for _ in range(5):
        pronto = ui.draw_dia_intro(screen, g, 100)
        tarde = ui.draw_dia_intro(screen, g, config.DIA_INTRO_LISTO_MS + 1)
        assert pronto["_done"] is False and tarde["_done"] is True
        assert "continuar" in pronto and isinstance(pronto["continuar"], pygame.Rect)
        dias.append(g.nivel.dia)
        g.siguiente_nivel()
    assert dias == ["Domingo", "Lunes", "Miércoles", "Jueves", "Viernes"]
    print(f"  Pantalla del día para {', '.join(dias)} ✓")
    print("  OK")


# ════════════════════════════════════════════════════════════════
# BLOQUE K — Tutorial guiado (specs/14_tutorial.md)
# ════════════════════════════════════════════════════════════════

def test_29_tutorial_logica():
    print("\n=== TEST 29: Tutorial — motor, datos y mensaje de práctica ===")
    import datos
    from tutorial import Tutorial

    pasos = datos.TUTORIAL_PASOS
    ids = [p["id"] for p in pasos]
    assert len(set(ids)) == len(ids) >= 15, "ids de paso únicos"
    estados = {"HOME", "MESSAGE_LIST", "CHAT", "MODAL", "FEEDBACK", "PANEL", "RESUMEN"}
    for p in pasos:
        assert p["tipo"] in ("info", "click"), p["id"]
        assert p["estado"] in estados, p["id"]
        assert p["texto"].strip() and p["voz"].strip(), p["id"]
        if p["tipo"] == "click":
            assert p["foco"], f"{p['id']}: un paso de clic necesita un botón"
        assert len(p["texto"]) <= 130, f"{p['id']}: globo demasiado largo"
    assert pasos[-1]["estado"] == "RESUMEN" and pasos[-1]["foco"] is None
    print(f"  {len(pasos)} pasos válidos (tipos, pantallas, textos cortos) ✓")

    # Motor: en un paso de clic solo vale el botón resaltado
    t = Tutorial([
        {"id": "a", "estado": "HOME", "tipo": "info", "foco": "zona"},
        {"id": "b", "estado": "HOME", "tipo": "click", "foco": "boton"},
        {"id": "c", "estado": "CHAT", "tipo": "info", "foco": None},
    ])
    assert t.paso["id"] == "a" and t.total == 3
    assert not t.permite("HOME", "boton"), "en un paso informativo no se pulsa nada"
    assert t.click("HOME", "boton") is False and t.paso["id"] == "a"
    t.siguiente()
    assert t.paso["id"] == "b"
    assert t.permite("HOME", "boton") and not t.permite("HOME", "otro")
    t.siguiente()
    assert t.paso["id"] == "b", "«Siguiente» no debe saltarse un paso de clic"
    assert t.click("HOME", "otro") is False and t.paso["id"] == "b", "clic equivocado"
    assert t.click("HOME", "boton") is True and t.paso["id"] == "c"
    t.siguiente()
    assert t.terminado and t.paso is None
    print("  Info: solo «Siguiente»; clic: solo el botón resaltado ✓")

    # Si el juego está en otra pantalla, el tutorial se pausa (nunca atasca)
    t = Tutorial(pasos)
    assert t.paso_en("MENU") is None and t.permite("MENU", "play")
    assert t.paso_en(pasos[0]["estado"]) is pasos[0]
    t.saltar()
    assert t.terminado and t.permite("HOME", "cualquiera")
    assert Tutorial([]).terminado
    print("  Pantalla distinta → juego libre; «Saltar» termina ✓")

    # Los datos del Nivel 0 cuadran con los pasos (open_0 = mamá, open_1 = práctica)
    g = Game()
    n0 = [inc for _, inc in g.incidentes_en_nivel()]
    assert [i.id for i in n0] == ["n0_01", "n0_02"]
    mama, practica = n0
    assert mama.categoria == "legitimo" and mama.respuesta_correcta == "CONFIAR"
    assert practica.es_tutorial and practica.categoria == "fraude"
    assert practica.enlace is not None and not practica.enlace.oficial, \
        "la práctica enseña la herramienta Enlace"
    assert practica.respuesta_correcta == "REPORTAR"
    assert practica.consejo, "al reportar se desbloquea un consejo (paso «consejo»)"
    assert not practica.requiere_urgencia
    print("  Nivel 0: mamá (legítimo) + práctica (fraude con enlace) ✓")

    # La práctica NO puntúa, no cambia el máximo y equivocarse no cuesta nada
    assert g.puntaje_maximo() == 800
    g.usar_herramienta_en(1, "enlace")
    r = g.evaluar_decision_en(1, "REPORTAR")
    assert r["correcta"] and r["puntos"] == 0 and g.estado.xp == 0
    assert r["consejo"] is not None
    g2 = Game()
    antes = (g2.estado.privacidad, g2.estado.dinero, g2.estado.reputacion)
    r = g2.evaluar_decision_en(1, "CONFIAR")
    assert not r["correcta"] and r["puntos"] == 0
    assert (g2.estado.privacidad, g2.estado.dinero, g2.estado.reputacion) == antes
    assert not g2.chequear_derrota()
    print("  La práctica no puntúa ni penaliza; el máximo sigue en 800 ✓")

    # Seguir las instrucciones del tutorial completa el Nivel 0 con 25 XP
    g3 = Game()
    g3.usar_herramienta_en(0, "remitente")
    assert g3.evaluar_decision_en(0, "CONFIAR")["correcta"]
    assert not g3.nivel_completado()
    g3.usar_herramienta_en(1, "enlace")
    g3.evaluar_decision_en(1, "REPORTAR")
    assert g3.nivel_completado() and g3.estado.xp == 25
    print("  Recorrido del tutorial: Nivel 0 completo con 25 XP ✓")
    print("  OK")


def test_30_tutorial_en_pantalla():
    print("\n=== TEST 30: Tutorial — cada paso se dibuja sobre su pantalla ===")
    import tempfile
    pygame = _pygame_sin_ventana()
    import datos
    import _capturas

    with tempfile.TemporaryDirectory() as tmp:
        # _capturas falla si el foco de un paso no existe en su pantalla
        rects = _capturas.generar(1.0, tmp, guardar_png=False)
    for paso in datos.TUTORIAL_PASOS:
        botones = rects[f"tutorial_{paso['id']}"]
        assert "tut_saltar" in botones, paso["id"]
        assert ("tut_siguiente" in botones) == (paso["tipo"] == "info"), paso["id"]
        if "tut_siguiente" in botones:      # el botón cabe dentro del teléfono
            x, y, w, h = botones["tut_siguiente"]
            sx, sy, sw, sh = config.PHONE_SCREEN
            assert sx <= x and x + w <= sx + sw and sy <= y and y + h <= sy + sh, paso["id"]
    print(f"  {len(datos.TUTORIAL_PASOS)} pasos dibujados con su foco; "
          "«Siguiente» solo en los informativos ✓")
    print("  OK")


# ════════════════════════════════════════════════════════════════
# BLOQUE L — Animación explicativa (specs/15_animacion.md)
# ════════════════════════════════════════════════════════════════

def test_31_animacion_tiempos():
    print("\n=== TEST 31: Animación — línea de tiempo, datos y audios ===")
    import os
    import wave
    import datos
    import voces
    from animacion import Animacion

    esc = datos.ANIMACION_ESCENAS
    ids = [e["id"] for e in esc]
    assert len(set(ids)) == len(ids) >= 8
    for e in esc:
        assert e["voz"].strip() and e["color"] in ("azul", "verde", "rojo", "ambar"), e["id"]
        assert e["min_ms"] >= 3000, e["id"]
        assert f"anim_{e['id']}" in voces.manifest(), e["id"]
    assert esc[-1]["id"] == "cierre"
    print(f"  {len(esc)} escenas con narración, color y voz en el manifiesto ✓")

    # Tiempos: cada escena dura su voz + pausa (o su mínimo) y se encadenan
    pruebas = [{"id": "a", "min_ms": 3000}, {"id": "b", "min_ms": 3000},
               {"id": "c", "min_ms": 9000}]
    a = Animacion(pruebas, [2000, 8000, 1000])
    pad = Animacion.PAD_MS
    assert a.duraciones == [3000, 8000 + pad, 9000]      # mínimo, voz+pausa, mínimo
    assert a.inicios == [0, 3000, 3000 + 8000 + pad]
    assert a.total == sum(a.duraciones)
    assert a.escena_en(0) == (0, 0, 3000)
    assert a.escena_en(2999)[0] == 0 and a.escena_en(3000)[0] == 1
    assert a.escena_en(3000 + 500) == (1, 500, 8000 + pad)
    assert a.escena_en(a.total - 1)[0] == 2
    assert a.escena_en(a.total + 5000) == (2, 9000, 9000),         "pasado el final se queda en el último instante de la última escena"
    assert a.escena_en(-50)[0] == 0
    assert a.terminada(a.total) and not a.terminada(a.total - 1)
    assert a.progreso_voz(1, 0) == 0.0 and a.progreso_voz(1, 4000) == 0.5
    assert a.progreso_voz(1, 99999) == 1.0
    print("  Duración = voz + pausa (o mínimo); escenas encadenadas; límites ✓")

    # La duración se lee del audio real (.wav) y coincide con su cabecera
    for e in esc:
        clave = f"anim_{e['id']}"
        ruta = voces.ruta_audio(clave)
        if ruta and ruta.endswith(".wav"):
            with wave.open(ruta) as w:
                real = int(w.getnframes() / w.getframerate() * 1000)
            assert voces.duracion_ms(clave) == real, clave
    # Sin audio se estima por la longitud del texto
    assert voces.duracion_ms("anim_mensajes", carpeta=os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "no_existe")) > 1000
    real = Animacion(esc, [voces.duracion_ms(f"anim_{i}") for i in ids])
    assert 35_000 <= real.total <= 100_000, f"la animación dura {real.total / 1000:.0f} s"
    print(f"  Duraciones desde los .wav; animación completa de {real.total / 1000:.0f} s ✓")
    print("  OK")


def test_32_animacion_dibujo():
    print("\n=== TEST 32: Animación — cada escena se dibuja y se mueve ===")
    import hashlib
    pygame = _pygame_sin_ventana()
    import gfx
    gfx.init(1.0)
    screen = pygame.display.set_mode((400, 700))
    import ui
    ui.init()
    import datos
    import voces
    import escenas
    from animacion import Animacion

    esc = datos.ANIMACION_ESCENAS
    assert set(escenas.ESCENAS) == {e["id"] for e in esc}, "escena sin dibujo o dibujo sin escena"
    anim = Animacion(esc, [voces.duracion_ms(f"anim_{e['id']}") for e in esc])

    def huella(surf):
        return hashlib.md5(pygame.image.tostring(surf, "RGB")).hexdigest()

    for i, e in enumerate(esc):
        for f in (0.0, 0.1, 0.3, 0.5, 0.75, 0.97, 1.0):
            t = anim.inicios[i] + anim.duraciones[i] * f
            botones = escenas.draw_animacion(screen, anim, t)
            r = botones["anim_saltar"]
            assert screen.get_rect().contains(r), "el botón Saltar cabe en la pantalla"
        # La ESCENA sola (sin el fondo, que siempre se mueve) debe animarse y llenarse
        marcas, llenado = [], 0
        for f in (0.05, 0.2, 0.4, 0.6, 0.8, 0.97):
            screen.fill((0, 0, 0))
            escenas.ESCENAS[e["id"]](screen, anim.duraciones[i] * f, anim.duraciones[i])
            marcas.append(huella(screen))
            llenado = sum(1 for x in range(0, 400, 4) for y in range(0, 700, 4)
                          if screen.get_at((x, y))[:3] != (0, 0, 0))
        # Una escena puede quedarse quieta al final (para leerla), pero no estar congelada
        assert len(set(marcas)) >= 3 and marcas[0] != marcas[-1],             f"{e['id']}: la escena casi no se mueve"
        assert llenado > 150, f"{e['id']}: la escena termina casi vacía ({llenado})"
    # Cuadros extremos: antes del inicio y después del final no fallan
    escenas.draw_animacion(screen, anim, -500)
    escenas.draw_animacion(screen, anim, anim.total + 9999)
    print(f"  {len(esc)} escenas dibujadas en 7 instantes cada una, todas animadas ✓")

    # Subtítulos: las palabras no se pisan a ninguna escala. Se compara la posición de
    # cada palabra con lo que REALMENTE mide al dibujarla (antes salían pegadas).
    for escala in (1.0, 1.25, 1.5):
        gfx.init(escala)
        pygame.display.set_mode((round(400 * escala), round(700 * escala)))
        ui.init()
        screen = pygame.display.get_surface()
        peor = 99.0
        for e in esc:
            for fila in escenas._disponer_subtitulo(e["voz"]):
                for (p, x), (q, x2) in zip(fila, fila[1:]):
                    real = ui._render(p, (255, 255, 255), "h2").get_width() / gfx.S
                    peor = min(peor, x2 - (x + real))
                ultima, xu = fila[-1]
                real = ui._render(ultima, (255, 255, 255), "h2").get_width() / gfx.S
                assert 20 <= fila[0][1] and xu + real <= 400 - 20, "se sale de la caja"
            escenas.draw_animacion(screen, anim, anim.inicios[esc.index(e)] + 900)
        assert peor >= 2.5, f"escala {escala}: palabras pegadas (hueco mínimo {peor:.1f} px)"
    gfx.init(1.0)
    print("  Subtítulos a escala 1.0, 1.25 y 1.5 sin errores ✓")
    print("  OK")


# ════════════════════════════════════════════════════════════════
# BLOQUE M — Ignorar/bloquear no es "aceptar" (bug reportado al probar)
# ════════════════════════════════════════════════════════════════

def _todos_los_incidentes():
    """[(nivel, idx, incidente)] de los 34 mensajes del juego."""
    g = Game()
    out = []
    for nivel in range(5):
        out += [(nivel, i, inc) for i, inc in g.incidentes_en_nivel()]
        g.siguiente_nivel()
    return out


def _decidir(nivel, idx, accion, verificar=None, herramienta=False):
    """Una decisión en una partida nueva -> (resultado, juego, recursos antes)."""
    g = Game()
    g.cargar_nivel_por_id(nivel)
    if verificar:
        g.verificar_incidente(idx, verificar)
    if herramienta:
        g.usar_herramienta_en(idx, "remitente")
    antes = (g.estado.privacidad, g.estado.dinero, g.estado.reputacion)
    r = g.evaluar_decision_en(idx, accion)
    despues = (g.estado.privacidad, g.estado.dinero, g.estado.reputacion)
    return r, g, tuple(d - a for d, a in zip(despues, antes))


def test_33_ignorar_y_bloquear_no_castigan_sin_caer():
    print("\n=== TEST 33: Ignorar/bloquear una estafa no quita recursos ===")
    import voces
    fraudes = [(n, i, inc) for n, i, inc in _todos_los_incidentes()
               if inc.categoria == "fraude"]
    assert len(fraudes) == 16

    # 1) INVARIANTE: en ningún fraude, ignorar/bloquear/reportar quita recursos
    #    (solo el acoso castiga el silencio: callar ES el error ahí)
    for nivel, idx, inc in fraudes:
        for accion in ("IGNORAR", "BLOQUEAR", "REPORTAR"):
            if accion == "IGNORAR" and inc.penaliza_ignorar:
                continue
            r, g, delta = _decidir(nivel, idx, accion)
            assert delta == (0, 0, 0), \
                f"{inc.id} {accion} quitó recursos {delta} sin haber caído"
            assert r["impacto_aplicado"] is None, inc.id
            assert not g.chequear_derrota(), inc.id
    print("  16 fraudes × (ignorar, bloquear, reportar): 0 recursos perdidos ✓")

    # 2) Los casos que reportó el jugador
    for nivel, id_, perdia in ((3, "n3_05", 50), (4, "n4_10", 150), (2, "n2_06", 50),
                               (4, "n4_09", 50)):
        idx = next(i for n, i, x in fraudes if x.id == id_)
        r, g, delta = _decidir(nivel, idx, "IGNORAR")
        assert r["parcial"] and not r["correcta"] and r["puntos"] == 0
        assert delta == (0, 0, 0), (id_, delta)
        assert "No caíste" in r["feedback"] and "verificar" in r["feedback"].lower() \
            or id_ in ("n2_06",), r["feedback"]
        assert not g.chequear_derrota()
    idx = next(i for n, i, x in fraudes if x.id == "n3_05")
    r, g, delta = _decidir(3, idx, "BLOQUEAR")
    assert r["parcial"] and r["puntos"] == 0 and delta == (0, 0, 0), \
        "Valentina hackeada: bloquear ya no descuenta el dinero"
    assert "verificar_por_voz" in g.estado.historial_consejos, "se explica qué era lo ideal"
    print("  Valentina hackeada / falso tío / falsos bancos: sin pérdida, con explicación ✓")

    # 3) Caer SÍ cuesta: confiar aplica el daño de la estafa (la práctica del Domingo
    #    es la excepción: no cuesta ni puntúa por diseño)
    for nivel, idx, inc in fraudes:
        if inc.interaccion != "ninguna" or inc.penaliza_ignorar or inc.es_tutorial:
            continue
        r, g, delta = _decidir(nivel, idx, "CONFIAR")
        assert not r["correcta"] and not r["parcial"], inc.id
        assert any(d < 0 for d in delta), f"{inc.id}: confiar debe costar"
    # el temporizador confía por el jugador (también cae)
    idx = next(i for n, i, x in fraudes if x.id == "n2_05")
    g = Game(); g.cargar_nivel_por_id(2)
    r = g.resolver_por_tiempo(idx)
    assert not r["correcta"] and g.estado.privacidad < 100
    print("  Confiar (y el temporizador agotado) siguen costando ✓")

    # 4) Si ya investigó (verificar), ignorar/bloquear/reportar son respuestas válidas
    for nivel, idx, inc in fraudes:
        if inc.penaliza_ignorar or inc.es_tutorial:
            continue
        for metodo in ("llamada", "oficial", "busqueda"):
            for accion in ("IGNORAR", "BLOQUEAR", "REPORTAR"):
                r, g, delta = _decidir(nivel, idx, accion, verificar=metodo)
                assert r["correcta"] and not r["parcial"], (inc.id, metodo, accion)
                assert r["puntos"] == config.PTS_BASE_FRAUDE or (
                    accion == "REPORTAR" and inc.nivel >= 3
                    and inc.respuesta_correcta == "REPORTAR"), (inc.id, r["puntos"])
                assert delta == (0, 0, 0)
    print("  Verificar primero y luego bloquear/ignorar/reportar: correcto (+15) ✓")

    # 5) Acoso: callar sigue castigando; bloquear/reportar bien; verificar no lo cambia
    for id_ in ("n3_06", "n3_07", "n4_08"):
        nivel, idx, inc = next(f for f in fraudes if f[2].id == id_)
        assert inc.penaliza_ignorar
        r, g, delta = _decidir(nivel, idx, "IGNORAR")
        assert not r["correcta"] and not r["parcial"] and delta[2] == -25, id_
        r, g, delta = _decidir(nivel, idx, "IGNORAR", verificar="oficial")
        assert not r["correcta"] and delta[2] == -25, "verificar no justifica callar el acoso"
        for accion in ("BLOQUEAR", "REPORTAR"):
            assert _decidir(nivel, idx, accion)[0]["correcta"], (id_, accion)
    print("  Acoso: callar sigue costando (−25 reputación); bloquear/reportar bien ✓")

    # 6) Otras reglas: multa falsa admite bloquear; los legítimos no cambian
    nivel, idx, inc = next(f for f in fraudes if f[2].id == "n2_07")
    r, g, delta = _decidir(nivel, idx, "BLOQUEAR")
    assert r["correcta"] and r["puntos"] == config.PTS_BASE_FRAUDE
    for nivel, idx, inc in _todos_los_incidentes():
        if inc.categoria == "legitimo" and "IGNORAR" not in inc.respuestas_aceptables:
            r, g, delta = _decidir(nivel, idx, "IGNORAR")
            assert not r["correcta"] and not r["parcial"], inc.id
            assert delta[2] < 0, f"{inc.id}: ignorar a alguien real debe costar reputación"
    print("  Multa falsa admite bloquear; ignorar a una persona real sigue costando ✓")

    # 7) Cada «ideal» posible tiene su explicación hablada
    manifiesto = voces.manifest()
    for _, _, inc in fraudes:
        assert f"parcial_{inc.respuesta_correcta.lower()}" in manifiesto, inc.id
    print("  Voz para cada «no caíste, pero lo ideal era…» ✓")
    print("  OK")


def test_34_instrucciones_creditos_e_iconos():
    print("\n=== TEST 34: Instrucciones, Créditos e íconos ===")
    pygame = _pygame_sin_ventana()
    import gfx
    import iconos
    assert config.PUNTOS_MAXIMOS == Game().puntaje_maximo() == 800
    assert config.UMBRAL_CERTIF == round(0.70 * config.PUNTOS_MAXIMOS)
    print("  PUNTOS_MAXIMOS coincide con el máximo real (800) ✓")

    for escala in (1.0, 1.25, 2.0):
        gfx.init(escala)
        screen = pygame.display.set_mode((round(400 * escala), round(700 * escala)))
        import ui
        ui.init()
        # Cada ícono dibuja algo visible, a cualquier escala
        for nombre in ("check", "cruz", "lupa", "candado", "corazon", "escudo", "auricular",
                       "bandera", "prohibido", "ojo_tachado", "persona", "enlace",
                       "agenda", "reloj", "mensaje"):
            screen.fill((0, 0, 0))
            getattr(iconos, nombre)(screen, 60, 60, 40, (255, 255, 255))
            visibles = sum(1 for x in range(0, screen.get_width(), 2)
                           for y in range(0, screen.get_height(), 2)
                           if screen.get_at((x, y))[:3] != (0, 0, 0))
            assert visibles > 12, f"{nombre}: ícono vacío a escala {escala}"
        screen.fill((0, 0, 0))
        iconos.moneda(screen, 60, 60, 40)
        assert screen.get_at((int(60 * escala), int(60 * escala)))[:3] != (0, 0, 0)
    gfx.init(1.0)
    pygame.display.set_mode((400, 700))
    ui.init()
    print("  15 íconos dibujan algo visible a escala 1.0, 1.25 y 2.0 ✓")

    # Instrucciones: recorre todo su contenido con scroll y cuadra con las reglas reales
    screen = pygame.display.get_surface()
    botones = ui.draw_instrucciones(screen, 0)
    assert set(k for k in botones if not k.startswith("_")) == {"volver_menu", "ver_aprendizajes"}
    assert botones["_max_scroll"] > 300, "Instrucciones debe tener contenido para desplazar"
    for sc in (0, botones["_max_scroll"] // 2, botones["_max_scroll"], botones["_max_scroll"] + 999):
        ui.draw_instrucciones(screen, sc)          # no falla ni pasado el final
    creditos = ui.draw_creditos(screen)
    assert set(creditos) == {"volver_menu"}
    # el encabezado azul y el botón Volver caben dentro del teléfono
    sx, sy, sw, sh = config.PHONE_SCREEN
    assert pygame.Rect(sx, sy, sw, sh).contains(creditos["volver_menu"])
    print("  Instrucciones (con scroll) y Créditos se dibujan; botones dentro del teléfono ✓")
    print("  OK")


if __name__ == "__main__":
    # Corre todos los test_* en el orden en que están definidos
    pruebas = [f for n, f in list(globals().items())
               if n.startswith("test_") and callable(f)]
    for prueba in pruebas:
        prueba()
    print("\n═══════════════════════════════════════════")
    print(f"  ✅ TODOS LOS TESTS PASARON ({len(pruebas)})")
    print("═══════════════════════════════════════════")