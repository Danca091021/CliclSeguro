"""
game.py — Lógica del juego. Sin Pygame.
Fix: nivel_completado ignora eventos, no dispara eventos cerca del final.
"""
import random
from modelos import (
    EstadoJugador, Incidente, Nivel, Remitente, Impacto,
    cargar_consejos, cargar_niveles,
)
import datos
import config


class Game:
    def __init__(self):
        self.consejos = cargar_consejos(datos.CONSEJOS)
        self.niveles = cargar_niveles(datos.NIVELES)
        self.estado = EstadoJugador()

        if config.ECONOMIA_V2:
            self.estado.dinero = config.DINERO_INICIAL_V2
            self.estado.dinero_inicio_nivel = config.DINERO_INICIAL_V2

        self._seguridad_activada = False
        self._evento_disparado = False
        self._perdio_por_gasto = False
        self._otp_incidente = -1
        self._otp_codigo = ""
        self._cargar_nivel(self.niveles[0])

    # ============================================================
    # Nivel
    # ============================================================

    def _cargar_nivel(self, nivel):
        self.nivel = nivel
        self.estado.nivel_actual = nivel.id
        self.estado.incidente_actual = 0
        self.estado.indices_respondidos = []
        self.estado.herramientas_por_incidente = {}
        self.estado.verificados = set()
        self.estado.priv_inicio_nivel = self.estado.privacidad
        self.estado.rep_inicio_nivel = self.estado.reputacion
        self.estado.dinero_inicio_nivel = self.estado.dinero
        self.estado.xp_inicio_nivel = self.estado.xp
        self.estado.timer_activo = False
        self.estado.timer_indice = -1
        self.estado.tiempo_restante = 0.0
        self._evento_disparado = False  # Reiniciar flag por nivel

    def cargar_nivel_por_id(self, nivel_id):
        for nv in self.niveles:
            if nv.id == nivel_id:
                self._cargar_nivel(nv)
                return True
        return False

    def incidentes_en_nivel(self):
        return list(enumerate(self.nivel.incidentes))

    def incidente_por_indice(self, idx):
        if 0 <= idx < len(self.nivel.incidentes):
            return self.nivel.incidentes[idx]
        return None

    def esta_respondido(self, idx):
        return idx in self.estado.indices_respondidos

    def nivel_completado(self):
        """El nivel termina cuando se responden todos los incidentes normales."""
        total_normales = sum(1 for inc in self.nivel.incidentes if not inc.es_evento)
        respondidos_normales = sum(
            1 for i in self.estado.indices_respondidos
            if not self.nivel.incidentes[i].es_evento
        )
        return respondidos_normales >= total_normales

    def restantes_en_nivel(self):
        total_normales = sum(1 for inc in self.nivel.incidentes if not inc.es_evento)
        respondidos_normales = sum(
            1 for i in self.estado.indices_respondidos
            if not self.nivel.incidentes[i].es_evento
        )
        return max(0, total_normales - respondidos_normales)

    def seguridad_activada(self):
        return self._seguridad_activada

    def indice_dia_actual(self):
        return self.nivel.id

    # ============================================================
    # Timer
    # ============================================================

    def iniciar_timer_para(self, idx):
        inc = self.incidente_por_indice(idx)
        if (inc and inc.requiere_urgencia and self.nivel.id >= 2
                and not self.esta_respondido(idx)):
            if self.estado.timer_indice != idx:
                self.estado.tiempo_restante = float(config.TIEMPO_URGENCIA)
            self.estado.timer_activo = True
            self.estado.timer_indice = idx
        else:
            self.estado.timer_activo = False
            self.estado.timer_indice = -1

    def pausar_timer(self):
        self.estado.timer_activo = False

    def tick_timer(self, dt_seg):
        if not self.estado.timer_activo:
            return None
        self.estado.tiempo_restante -= dt_seg
        if self.estado.tiempo_restante <= 0:
            self.estado.tiempo_restante = 0.0
            idx = self.estado.timer_indice
            self.estado.timer_activo = False
            self.estado.timer_indice = -1
            return idx
        return None

    def timer_para(self, idx):
        return self.estado.timer_activo and self.estado.timer_indice == idx

    # ============================================================
    # Música reactiva
    # ============================================================

    def hay_tension(self):
        e = self.estado
        return min(e.privacidad, e.dinero, e.reputacion) < config.UMBRAL_TENSION

    # ============================================================
    # Herramientas
    # ============================================================

    def usar_herramienta_en(self, idx, nombre):
        inc = self.incidente_por_indice(idx)
        if inc is None or self.esta_respondido(idx):
            return None
        if nombre == "remitente":
            self.estado.herramientas_por_incidente.setdefault(idx, set()).add("remitente")
            return {"tipo": "remitente", "remitente": inc.remitente}
        if nombre == "enlace":
            if inc.enlace is None:
                return None
            self.estado.herramientas_por_incidente.setdefault(idx, set()).add("enlace")
            return {"tipo": "enlace", "enlace": inc.enlace}
        if nombre == "contactos":
            self.estado.herramientas_por_incidente.setdefault(idx, set()).add("contactos")
            return {"tipo": "contactos", "remitente": inc.remitente}
        return None

    def herramienta_usada_en(self, idx):
        return len(self.estado.herramientas_por_incidente.get(idx, set())) > 0

    # ============================================================
    # Verificación
    # ============================================================

    def verificar_incidente(self, idx, metodo):
        inc = self.incidente_por_indice(idx)
        if inc is None:
            return None

        ya_verificado = idx in self.estado.verificados
        self.estado.verificados.add(idx)

        if (metodo == "llamada"
                and inc.categoria == "legitimo"
                and not ya_verificado):
            self.estado.reputacion = max(
                0, self.estado.reputacion - config.PENALIZACION_SOBRE_VERIFICAR
            )

        if metodo == "llamada":
            return inc.verificacion_llamada or "No responde."
        if metodo == "oficial":
            return inc.verificacion_oficial or "No hay canal oficial disponible."
        if metodo == "busqueda":
            return inc.verificacion_busqueda or "Sin resultados."
        return None

    def fue_verificado(self, idx):
        return idx in self.estado.verificados

    # ============================================================
    # Evaluación
    # ============================================================

    def evaluar_decision_en(self, idx, accion, auto_por_timer=False,
                            ignorar_interaccion=False):
        inc = self.incidente_por_indice(idx)
        if inc is None or self.esta_respondido(idx):
            return None

        if (accion == "CONFIAR"
                and not ignorar_interaccion
                and inc.interaccion in ("otp", "transferencia")
                and config.INTERACCION_ACTIVA):
            return {
                "needs_interaction": True,
                "interaccion": inc.interaccion,
                "idx": idx,
            }

        herramienta_usada = self.herramienta_usada_en(idx)
        aceptables = set(inc.respuestas_aceptables)
        if inc.categoria == "fraude" and idx in self.estado.verificados:
            # Si ya lo investigó (llamada, canal oficial o búsqueda) sabe que es falso:
            # bloquear o reportar son respuestas válidas (y ignorar, salvo en el acoso).
            aceptables |= {"BLOQUEAR", "REPORTAR"}
            if not inc.penaliza_ignorar:
                aceptables.add("IGNORAR")
        correcta = accion in aceptables

        if not correcta and accion == "REPORTAR" and inc.categoria == "fraude":
            correcta = True

        # ¿Cayó en la trampa? Solo si CONFIÓ (o, en el acoso, si CALLÓ). Ignorar,
        # bloquear o reportar una estafa NUNCA aplica su daño: no enviaste nada.
        cayo = (accion == "CONFIAR"
                or (accion == "IGNORAR" and inc.penaliza_ignorar))
        parcial = (not correcta) and inc.categoria == "fraude" and not cayo

        puntos = 0
        if correcta:
            base = (config.PTS_BASE_FRAUDE if inc.categoria == "fraude"
                    else config.PTS_BASE_LEGIT)
            puntos = base
            if herramienta_usada:
                puntos += config.PTS_HERRAMIENTA
            if (accion == "REPORTAR" and inc.categoria == "fraude"
                    and inc.nivel >= 3
                    and accion == inc.respuesta_correcta):
                puntos += config.PTS_REPORTAR
            if inc.es_tutorial:
                puntos = 0                # la práctica no puntúa
            elif not inc.es_evento:
                self.estado.xp += puntos

        impacto_aplicado = None
        if not correcta and not parcial:
            impacto_aplicado = self._aplicar_impacto(inc.impacto)

        consejo = None
        if inc.consejo:
            desbloquear = (not correcta) or (
                accion == "REPORTAR" and inc.categoria == "fraude")
            if desbloquear:
                consejo = self.consejos.get(inc.consejo)
                if consejo and consejo.key not in self.estado.historial_consejos:
                    self.estado.historial_consejos.append(consejo.key)

        self.estado.indices_respondidos.append(idx)
        self.estado.timer_activo = False
        self.estado.timer_indice = -1

        return {
            "idx": idx,
            "accion": accion,
            "correcta": correcta,
            "puntos": puntos,
            "herramienta_usada": herramienta_usada,
            "feedback": (inc.feedback_ok if correcta
                         else self.texto_parcial(inc) if parcial
                         else inc.feedback_err),
            "parcial": parcial,
            "consejo": consejo,
            "impacto_aplicado": impacto_aplicado,
            "estado_post": self.estado_estado(),
            "auto_por_timer": auto_por_timer,
        }

    @staticmethod
    def texto_parcial(inc):
        """Feedback cuando NO cayó en la estafa pero había una respuesta mejor."""
        ideal = {"VERIFICAR": "verificar antes de actuar",
                 "REPORTAR": "reportarlo", "IGNORAR": "ignorarlo",
                 "BLOQUEAR": "bloquear al remitente"}.get(inc.respuesta_correcta,
                                                         "otra respuesta")
        return ("No caíste en la trampa, pero esta no era la mejor respuesta. "
                f"Aquí lo ideal era {ideal}.")

    def _aplicar_impacto(self, impacto):
        antes = {k: getattr(self.estado, k)
                 for k in ("privacidad", "dinero", "reputacion")}
        if impacto.privacidad < 0:
            self.estado.privacidad = max(0, min(100,
                self.estado.privacidad + impacto.privacidad))
        if impacto.dinero < 0:
            self.estado.dinero = max(0, self.estado.dinero + impacto.dinero)
        if impacto.reputacion < 0:
            self.estado.reputacion = max(0, min(100,
                self.estado.reputacion + impacto.reputacion))
        return {k: getattr(self.estado, k) - antes[k] for k in antes}

    # ============================================================
    # Navegación
    # ============================================================

    def siguiente_nivel(self):
        idx = self.nivel.id + 1
        if idx >= len(self.niveles):
            return False
        # Un día nuevo: te perdonan un poco. Se suma ANTES de cargar el nivel
        # para que quede dentro del punto de partida (al repetir no se pierde).
        self.estado.reputacion = min(
            100, self.estado.reputacion + config.REP_NUEVO_DIA)
        self._cargar_nivel(self.niveles[idx])
        return True

    def reiniciar_nivel(self):
        """Vuelve al inicio del nivel actual.
        Restaura priv/rep/dinero/XP al snapshot del inicio del nivel.
        Las transacciones persistentes (gasto diario, matrícula, préstamo)
        ajustan el snapshot al ocurrir, así que NO se reembolsan ni se
        cobran dos veces. Los eventos aleatorios se descartan."""
        self.estado.privacidad = self.estado.priv_inicio_nivel
        self.estado.reputacion = self.estado.rep_inicio_nivel
        self.estado.dinero = self.estado.dinero_inicio_nivel
        self.estado.xp = self.estado.xp_inicio_nivel
        self.nivel.incidentes = [i for i in self.nivel.incidentes
                                 if not i.es_evento]
        self.estado.eventos_activos = []
        self.estado.indices_respondidos = []
        self.estado.herramientas_por_incidente = {}
        self.estado.verificados = set()
        self.estado.timer_activo = False
        self.estado.timer_indice = -1
        self._perdio_por_gasto = False
        self._evento_disparado = False

    def reiniciar_partida(self):
        self.estado = EstadoJugador()
        if config.ECONOMIA_V2:
            self.estado.dinero = config.DINERO_INICIAL_V2
            self.estado.dinero_inicio_nivel = config.DINERO_INICIAL_V2
        self._seguridad_activada = False
        self._evento_disparado = False
        self._perdio_por_gasto = False
        self._otp_incidente = -1
        self._otp_codigo = ""
        self._cargar_nivel(self.niveles[0])

    # ============================================================
    # Seguridad
    # ============================================================

    def activar_seguridad(self):
        if self._seguridad_activada:
            return False
        self.estado.privacidad = min(100, self.estado.privacidad + 15)
        self._seguridad_activada = True
        if "activar_2fa" not in self.estado.historial_consejos:
            self.estado.historial_consejos.append("activar_2fa")
        return True

    # ============================================================
    # Estado global
    # ============================================================

    def _sin_dinero(self):
        """Saldo en 0 = derrota, salvo el Viernes con la matrícula ya pagada:
        pagarla puede dejarte exactamente en $0 y eso no debe hacerte perder
        (era lo único que había que lograr con ese dinero)."""
        if self.estado.dinero > 0:
            return False
        return not (self.nivel.id == 4 and self.estado.matricula_pagada)

    def estado_estado(self):
        if (self.estado.privacidad <= 0
                or self._sin_dinero()
                or self.estado.reputacion <= 0):
            return "derrota"
        return "jugando"

    def chequear_derrota(self):
        if self._perdio_por_gasto:
            return True
        return self.estado_estado() == "derrota"

    def puede_pasar_n4(self):
        return (self.estado.privacidad > 30
                and self.estado.reputacion > 30
                and self.estado.dinero > 100)

    def recursos_bajos(self):
        e = self.estado
        return (e.privacidad < 30 or e.reputacion < 30 or e.dinero < 100)

    def resultado_final(self):
        if config.ECONOMIA_V2 and not self.estado.matricula_pagada:
            return "sin_matricula"
        if self.estado.xp >= config.UMBRAL_CERTIF:
            return "certificado"
        return "parcial"

    def resultado_nivel(self):
        if self.nivel.id == 4:
            return self.resultado_final()
        if self.nivel.id == 3 and not self.puede_pasar_n4():
            return "repetir_n3"
        return "continuar"

    # ============================================================
    # Economía
    # ============================================================

    def aplicar_gastos_dia(self):
        if not config.ECONOMIA_V2:
            return None
        if self.nivel.id not in config.GASTOS_DIARIOS:
            return None
        if self.nivel.id in self.estado.gastos_pagados:
            return None
        return config.GASTOS_DIARIOS[self.nivel.id]

    def pagar_gasto_obligatorio(self):
        gasto = self.aplicar_gastos_dia()
        if gasto is None:
            return True
        if self.estado.dinero < gasto["monto"]:
            self._perdio_por_gasto = True
            return False
        self.estado.dinero -= gasto["monto"]
        self.estado.dinero_inicio_nivel -= gasto["monto"]   # no se reembolsa al reiniciar
        self.estado.gastos_pagados.add(self.nivel.id)
        return True

    def pedir_prestamo_mama(self, monto):
        if monto <= 0 or monto > config.PRESTAMO_MAX:
            return {"aprobado": False, "razon": "monto_invalido"}
        if self.estado.prestamo_pedido:
            return {"aprobado": False, "razon": "ya_pediste"}
        self.estado.prestamo_pedido = True
        if monto <= config.PRESTAMO_SEGURO_HASTA:
            self.estado.dinero += monto
            self.estado.dinero_inicio_nivel += monto        # no se pierde al reiniciar
            return {"aprobado": True, "razon": "seguro", "monto": monto}
        if random.random() < config.PRESTAMO_PROB_RECHAZO:
            self.estado.prestamo_negado = True
            return {"aprobado": False, "razon": "rechazo"}
        self.estado.dinero += monto
        self.estado.dinero_inicio_nivel += monto
        return {"aprobado": True, "razon": "aprobado", "monto": monto}

    def pagar_matricula(self):
        if self.nivel.id != 4:
            return {"ok": False, "razon": "no_es_viernes"}
        if self.estado.matricula_pagada:
            return {"ok": False, "razon": "ya_pagada"}
        if self.estado.dinero < config.MATRICULA:
            return {"ok": False, "razon": "sin_dinero"}
        self.estado.dinero -= config.MATRICULA
        self.estado.dinero_inicio_nivel -= config.MATRICULA  # no se reembolsa al reiniciar
        self.estado.matricula_pagada = True
        return {"ok": True}

    def necesita_pagar_matricula(self):
        if not config.ECONOMIA_V2:
            return False
        return self.nivel.id == 4 and not self.estado.matricula_pagada

    def puede_pagar_matricula(self):
        return self.estado.dinero >= config.MATRICULA

    # ============================================================
    # Eventos aleatorios
    # ============================================================

    def intentar_evento_aleatorio(self):
        if not config.EVENTO_ACTIVO or not config.ECONOMIA_V2:
            return None
        if self._evento_disparado:
            return None
        if self.nivel.id == 0:
            return None
        if len(self.estado.indices_respondidos) == 0:
            return None
        
        # Fix: No disparar si faltan muy pocos incidentes normales por responder
        normales_pendientes = sum(
            1 for i, inc in self.incidentes_en_nivel()
            if not inc.es_evento and not self.esta_respondido(i)
        )
        if normales_pendientes <= 1:
            return None

        if random.random() > config.EVENTO_CHANCE:
            return None
        ev = random.choice(config.EVENTOS_DISPONIBLES)
        self._evento_disparado = True

        inc = Incidente(
            id=f"evento_{ev['id']}",
            nivel=self.nivel.id,
            dia=self.nivel.dia,
            tipo="whatsapp",
            categoria="legitimo",
            remitente=Remitente(
                nombre=ev["parentesco"],
                numero="+57 3XX XXX XXXX",
                en_contactos=True,
                cuenta_dias=9999,
                reportes=0,
                verificado=True,
                pista="Contacto familiar real.",
            ),
            texto=f"Necesito ${ev['monto']}. ¿Me puedes ayudar?",
            enlace=None,
            requiere_urgencia=True,
            respuesta_correcta="CONFIAR",
            respuestas_aceptables=["CONFIAR"],
            impacto=Impacto(dinero=0, privacidad=0, reputacion=-15, xp=0),
            feedback_ok=(f"Le enviaste ${ev['monto']} a {ev.get('quien', ev['parentesco'])}. "
                         "Ayudar a tu familia te devuelve un poco de respeto, "
                         "pero ese dinero ya no está para la matrícula."),
            feedback_err=(f"No ayudaste a {ev.get('quien', ev['parentesco'])}. Tu familia lo "
                          "nota y pierdes respeto."),
            consejo=None,
            # Ayudar = transferencia por el monto exacto (cuesta dinero)
            interaccion="transferencia",
            es_familiar=True,
            es_evento=True,
            monto_solicitado=ev["monto"],
            cuenta_destino=ev.get("cuenta", ""),
            titular_destino=f"{ev['parentesco']} (verificado)",
        )
        self.nivel.incidentes.append(inc)
        self.estado.eventos_activos.append(len(self.nivel.incidentes) - 1)
        return inc

    def fue_evento_disparado(self):
        return self._evento_disparado

    # ============================================================
    # OTP / Transferencia
    # ============================================================

    def generar_otp(self, idx):
        if idx != self._otp_incidente:
            self._otp_codigo = "".join(random.choices("0123456789", k=6))
            self._otp_incidente = idx
        return self._otp_codigo

    def enviar_otp(self, idx):
        inc = self.incidente_por_indice(idx)
        if inc is None or self.esta_respondido(idx):
            return None
        impacto_aplicado = self._aplicar_impacto(inc.impacto)
        self.estado.indices_respondidos.append(idx)
        self.estado.timer_activo = False
        self.estado.timer_indice = -1
        consejo = None
        if inc.consejo:
            consejo = self.consejos.get(inc.consejo)
            if consejo and consejo.key not in self.estado.historial_consejos:
                self.estado.historial_consejos.append(consejo.key)
        return {
            "idx": idx, "accion": "CONFIAR", "correcta": False,
            "puntos": 0,
            "herramienta_usada": self.herramienta_usada_en(idx),
            "feedback": inc.feedback_err,
            "consejo": consejo,
            "impacto_aplicado": impacto_aplicado,
            "estado_post": self.estado_estado(),
            "auto_por_timer": False,
            "via_banco": "otp",
        }

    def _saldo_alcanza(self, inc, monto):
        """Un evento no puede dejarte en $0 (eso sería una derrota)."""
        if inc.es_evento:
            return self.estado.dinero > monto
        return self.estado.dinero >= monto

    def saldo_alcanza_para(self, idx):
        """¿Te alcanza el saldo para pagar lo que piden en este incidente?"""
        inc = self.incidente_por_indice(idx)
        if inc is None:
            return False
        if inc.monto_solicitado <= 0:
            return self.estado.dinero > 0
        return self._saldo_alcanza(inc, inc.monto_solicitado)

    def motivo_monto_invalido(self, idx, monto):
        """None si `monto` es válido para esta transferencia; si no, el motivo:
        'monto_invalido' (no entero positivo), 'monto_incorrecto' (distinto a
        lo que piden: ni más ni menos) o 'saldo_insuficiente'."""
        inc = self.incidente_por_indice(idx)
        if inc is None or self.esta_respondido(idx):
            return "monto_invalido"
        if isinstance(monto, bool) or not isinstance(monto, int) or monto <= 0:
            return "monto_invalido"
        if inc.monto_solicitado > 0 and monto != inc.monto_solicitado:
            return "monto_incorrecto"
        if not self._saldo_alcanza(inc, monto):
            return "saldo_insuficiente"
        return None

    def confirmar_transferencia(self, idx, monto):
        inc = self.incidente_por_indice(idx)
        if inc is None or self.esta_respondido(idx):
            return None
        # Solo enteros, exactamente lo pedido (ni más ni menos) y con saldo.
        if self.motivo_monto_invalido(idx, monto) is not None:
            return None
        self.estado.dinero -= monto
        correcta = (inc.categoria == "legitimo"
                    and "CONFIAR" in inc.respuestas_aceptables)
        impacto_aplicado = {"dinero": -monto}
        if inc.categoria == "fraude":
            extra = Impacto(
                privacidad=inc.impacto.privacidad,
                dinero=0,
                reputacion=inc.impacto.reputacion,
                xp=0,
            )
            impacto_aplicado.update(self._aplicar_impacto(extra))
        if correcta and inc.es_evento:
            # Ayudar a un familiar devuelve un poco de reputación (tope 100)
            antes = self.estado.reputacion
            self.estado.reputacion = min(
                100, antes + config.EVENTO_REP_AYUDA)
            impacto_aplicado["reputacion"] = self.estado.reputacion - antes
        puntos = 0
        if correcta and not inc.es_evento:
            base = config.PTS_BASE_LEGIT
            if self.herramienta_usada_en(idx):
                base += config.PTS_HERRAMIENTA
            self.estado.xp += base
            puntos = base
        self.estado.indices_respondidos.append(idx)
        self.estado.timer_activo = False
        self.estado.timer_indice = -1
        consejo = None
        if inc.consejo and not correcta:
            consejo = self.consejos.get(inc.consejo)
            if consejo and consejo.key not in self.estado.historial_consejos:
                self.estado.historial_consejos.append(consejo.key)
        return {
            "idx": idx, "accion": "CONFIAR", "correcta": correcta,
            "puntos": puntos,
            "herramienta_usada": self.herramienta_usada_en(idx),
            "feedback": inc.feedback_ok if correcta else inc.feedback_err,
            "consejo": consejo,
            "impacto_aplicado": impacto_aplicado,
            "estado_post": self.estado_estado(),
            "auto_por_timer": False,
            "via_banco": "transferencia",
        }

    # ============================================================
    # Temporizador agotado
    # ============================================================

    def resolver_por_tiempo(self, idx):
        """Se agotó el temporizador: Camilo 'confía' automáticamente.
        En un incidente con OTP o transferencia completa la interacción
        (envía el código / paga exactamente lo pedido). Si no tiene saldo
        para pagar, la estafa o la ayuda falla sin mover dinero."""
        inc = self.incidente_por_indice(idx)
        if inc is None or self.esta_respondido(idx):
            return None
        if config.INTERACCION_ACTIVA and inc.interaccion == "otp":
            res = self.enviar_otp(idx)
        elif config.INTERACCION_ACTIVA and inc.interaccion == "transferencia":
            if self.motivo_monto_invalido(idx, inc.monto_solicitado) is None:
                res = self.confirmar_transferencia(idx, inc.monto_solicitado)
            else:
                res = self._resultado_sin_pago(idx, inc)
        else:
            res = self.evaluar_decision_en(idx, "CONFIAR", auto_por_timer=True)
        if res is not None:
            res["auto_por_timer"] = True
        return res

    def _resultado_sin_pago(self, idx, inc):
        """Respuesta incorrecta de una transferencia que no se pudo pagar:
        aplica el daño del mensaje, pero no se mueve dinero."""
        imp = inc.impacto
        if inc.categoria == "fraude":
            imp = Impacto(privacidad=imp.privacidad, dinero=0,
                          reputacion=imp.reputacion, xp=0)
        impacto_aplicado = self._aplicar_impacto(imp)
        consejo = None
        if inc.consejo:
            consejo = self.consejos.get(inc.consejo)
            if consejo and consejo.key not in self.estado.historial_consejos:
                self.estado.historial_consejos.append(consejo.key)
        self.estado.indices_respondidos.append(idx)
        self.estado.timer_activo = False
        self.estado.timer_indice = -1
        return {
            "idx": idx, "accion": "CONFIAR", "correcta": False, "puntos": 0,
            "herramienta_usada": self.herramienta_usada_en(idx),
            "feedback": inc.feedback_err,
            "consejo": consejo,
            "impacto_aplicado": impacto_aplicado,
            "estado_post": self.estado_estado(),
            "auto_por_timer": False,
            "via_banco": "sin_fondos",
        }

    # ============================================================
    # Motivo de la derrota
    # ============================================================

    def motivo_derrota(self):
        """'gasto' | 'privacidad' | 'dinero' | 'reputacion' | None."""
        if self._perdio_por_gasto:
            return "gasto"
        e = self.estado
        if e.privacidad <= 0:
            return "privacidad"
        if self._sin_dinero():
            return "dinero"
        if e.reputacion <= 0:
            return "reputacion"
        return None

    def info_derrota(self):
        """Datos para explicarle al jugador por qué perdió. Si no pudo pagar
        el gasto del día, repetir el nivel no sirve (mismo saldo): no se ofrece."""
        motivo = self.motivo_derrota()
        info = {"motivo": motivo, "puede_repetir": motivo != "gasto",
                "dinero": self.estado.dinero}
        if motivo == "gasto":
            gasto = config.GASTOS_DIARIOS.get(self.nivel.id, {})
            info["concepto"] = gasto.get("concepto", "los gastos del día")
            info["monto"] = gasto.get("monto", 0)
        return info

    # ============================================================
    # Utilidades
    # ============================================================

    def puntaje_maximo(self):
        total = 0
        for nv in self.niveles:
            for inc in nv.incidentes:
                if inc.es_evento or inc.es_tutorial:
                    continue
                if inc.categoria == "fraude":
                    base = config.PTS_BASE_FRAUDE + config.PTS_HERRAMIENTA
                    if inc.nivel >= 3 and inc.respuesta_correcta == "REPORTAR":
                        base += config.PTS_REPORTAR
                    total += base
                else:
                    total += config.PTS_BASE_LEGIT + config.PTS_HERRAMIENTA
        return total

    def puntaje_maximo_correcta(self):
        return self.puntaje_maximo()

    # ============================================================
    # Compatibilidad tests
    # ============================================================

    def incidente_en_curso(self):
        return self.incidente_por_indice(self.estado.incidente_actual)

    def usar_herramienta(self, nombre, idx=None):
        if idx is None:
            idx = self.estado.incidente_actual
        return self.usar_herramienta_en(idx, nombre)

    def herramienta_usada(self):
        return self.herramienta_usada_en(self.estado.incidente_actual)

    def evaluar_decision(self, accion, auto_por_timer=False, idx=None):
        if idx is None:
            idx = self.estado.incidente_actual
        return self.evaluar_decision_en(idx, accion, auto_por_timer)

    def siguiente_incidente(self):
        self.estado.incidente_actual += 1
        if self.estado.incidente_actual >= len(self.nivel.incidentes):
            return "fin_nivel"
        return "siguiente"