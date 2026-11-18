"""
modelos.py — Dataclasses del dominio del juego.
"""
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Remitente:
    nombre: str
    numero: str
    en_contactos: bool
    cuenta_dias: int
    reportes: int
    verificado: bool
    pista: str


@dataclass
class Enlace:
    url: str
    oficial: bool
    pista: str


@dataclass
class Consejo:
    key: str
    titulo: str
    texto: str
    tipo: str
    key_voz: str


@dataclass
class Impacto:
    privacidad: int = 0
    dinero: int = 0
    reputacion: int = 0
    xp: int = 0


@dataclass
class Incidente:
    id: str
    nivel: int
    dia: str
    tipo: str
    categoria: str
    remitente: Remitente
    texto: str
    enlace: Optional[Enlace]
    requiere_urgencia: bool
    respuesta_correcta: str
    respuestas_aceptables: list
    impacto: Impacto
    feedback_ok: str
    feedback_err: str
    consejo: Optional[str]
    verificacion_llamada: str = ""
    verificacion_oficial: str = ""
    verificacion_busqueda: str = ""
    interaccion: str = "ninguna"
    es_familiar: bool = False
    es_evento: bool = False
    es_tutorial: bool = False    # práctica guiada: no puntúa ni cuenta para el máximo
    # Acoso: aquí CALLAR (ignorar) ES el error y tiene su consecuencia. En el resto
    # de fraudes solo daña CONFIAR: ignorar/bloquear nunca quita recursos.
    penaliza_ignorar: bool = False
    # Campos para flujos bancarios (Bloque E)
    monto_solicitado: int = 0
    cuenta_destino: str = ""
    titular_destino: str = ""


@dataclass
class Nivel:
    id: int
    dia: str
    titulo: str
    objetivo: str
    incidentes: list
    tutorial: bool


@dataclass
class EstadoJugador:
    privacidad: int = 100
    dinero: int = 500_000
    reputacion: int = 100
    xp: int = 0
    nivel_actual: int = 1
    incidente_actual: int = 0
    indices_respondidos: list = field(default_factory=list)
    herramientas_por_incidente: dict = field(default_factory=dict)
    historial_consejos: list = field(default_factory=list)
    priv_inicio_nivel: int = 100
    rep_inicio_nivel: int = 100
    dinero_inicio_nivel: int = 500_000
    xp_inicio_nivel: int = 0
    timer_activo: bool = False
    tiempo_restante: float = 0.0
    timer_indice: int = -1
    matricula_pagada: bool = False
    gastos_pagados: set = field(default_factory=set)
    verificados: set = field(default_factory=set)
    eventos_activos: list = field(default_factory=list)
    prestamo_pedido: bool = False
    prestamo_negado: bool = False


def cargar_consejos(dict_consejos):
    return {
        k: Consejo(key=k, titulo=v["titulo"], texto=v["texto"],
                   tipo=v["tipo"], key_voz=v["key_voz"])
        for k, v in dict_consejos.items()
    }


def _incidente_desde_dict(d):
    return Incidente(
        id=d["id"], nivel=d["nivel"], dia=d["dia"], tipo=d["tipo"],
        categoria=d["categoria"],
        remitente=Remitente(**d["remitente"]),
        texto=d["texto"],
        enlace=Enlace(**d["enlace"]) if d["enlace"] else None,
        requiere_urgencia=d["requiere_urgencia"],
        respuesta_correcta=d["respuesta_correcta"],
        respuestas_aceptables=d["respuestas_aceptables"],
        impacto=Impacto(**d["impacto"]),
        feedback_ok=d["feedback_ok"],
        feedback_err=d["feedback_err"],
        consejo=d["consejo"],
        verificacion_llamada=d.get("verificacion_llamada", ""),
        verificacion_oficial=d.get("verificacion_oficial", ""),
        verificacion_busqueda=d.get("verificacion_busqueda", ""),
        interaccion=d.get("interaccion", "ninguna"),
        es_familiar=d.get("es_familiar", False),
        es_evento=d.get("es_evento", False),
        es_tutorial=d.get("es_tutorial", False),
        penaliza_ignorar=d.get("penaliza_ignorar", False),
        monto_solicitado=d.get("monto_solicitado", 0),
        cuenta_destino=d.get("cuenta_destino", ""),
        titular_destino=d.get("titular_destino", ""),
    )


def cargar_niveles(lista_niveles):
    return [
        Nivel(
            id=nv["id"], dia=nv["dia"], titulo=nv["titulo"],
            objetivo=nv["objetivo"],
            incidentes=[_incidente_desde_dict(i) for i in nv["incidentes"]],
            tutorial=nv["tutorial"],
        )
        for nv in lista_niveles
    ]