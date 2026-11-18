# Spec 06 — Modelo de datos

## Entidad Incidente

| Campo                  | Tipo       | Descripción                                                    |
|------------------------|------------|----------------------------------------------------------------|
| `id`                   | str        | Único por nivel, formato `nX_YY`                                |
| `nivel`                | int        | 1–4                                                            |
| `dia`                  | str        | "Lunes" / "Miércoles" / "Jueves" / "Viernes"                   |
| `tipo`                 | str        | sms, whatsapp, llamada, email, instagram, banco                |
| `categoria`            | str        | fraude \| legitimo                                             |
| `remitente`            | dict       | {nombre, numero, en_contactos, cuenta_dias, reportes, verificado, pista} |
| `texto`                | str        | Cuerpo del mensaje                                             |
| `enlace`               | dict\|None | {url, oficial, pista}                                          |
| `requiere_urgencia`    | bool       | Activa temporizador si nivel ≥ 2                               |
| `respuesta_correcta`   | str        | CONFIAR \| VERIFICAR \| IGNORAR \| BLOQUEAR \| REPORTAR        |
| `respuestas_aceptables`| list       | Puede haber más de una acción válida                           |
| `impacto`              | dict       | {privacidad, dinero, reputacion, xp}                           |
| `feedback_ok`          | str        | Texto corto si acierta                                         |
| `feedback_err`         | str        | Texto corto si falla                                           |
| `consejo`              | str\|None  | Key del consejo (ej. "otp_nunca_se_comparte") o None           |

## Entidad Nivel

| Campo        | Tipo | Descripción                            |
|--------------|------|----------------------------------------|
| `id`         | int  | 1–4                                    |
| `dia`        | str  | Nombre del día                         |
| `titulo`     | str  | Título temático                        |
| `objetivo`   | str  | Objetivo pedagógico                    |
| `incidentes` | list | Lista ordenada de Incidentes           |
| `tutorial`   | bool | Solo Nivel 1                           |

## Entidad Consejo

| Campo     | Tipo | Descripción                                |
|-----------|------|--------------------------------------------|
| `key`     | str  | ID único (ej. "otp_nunca_se_comparte")     |
| `titulo`  | str  | Título corto                               |
| `texto`   | str  | Explicación (2–4 líneas)                   |
| `tipo`    | str  | urgencia \| otp \| enlace \| acoso \| banco |
| `key_voz` | str  | Archivo de voz grabado (vacío = TTS)       |

## Entidad EstadoJugador (runtime, no persistente)

```python
class EstadoJugador:
    privacidad: int = 100
    dinero: int = 800                # DINERO_INICIAL_V2 (la clase trae 500_000 legacy)
    reputacion: int = 100
    xp: int = 0
    nivel_actual: int = 1
    incidente_actual: int = 0
    indices_respondidos: list = []
    herramientas_por_incidente: dict = {}   # idx -> set de herramientas usadas
    historial_consejos: list = []
    # Punto de partida del nivel (para "Repetir nivel")
    priv_inicio_nivel: int; rep_inicio_nivel: int
    dinero_inicio_nivel: int; xp_inicio_nivel: int   # xp añadido en el Bloque G
    # Economía y eventos (Bloques A-D)
    matricula_pagada: bool = False
    gastos_pagados: set = set()
    verificados: set = set()          # idx de incidentes ya verificados
    eventos_activos: list = []
    prestamo_pedido: bool = False
    prestamo_negado: bool = False
    # Timer (N2+)
    timer_activo: bool; tiempo_restante: float; timer_indice: int
```

La definición completa y vigente está en `modelos.py`.

## Relaciones

```
Nivel (1..4)
  └── tiene muchos → Incidente
                        ├── tiene uno → Remitente (dict)
                        ├── tiene uno → Enlace (dict) o None
                        └── tiene uno → Consejo (lookup por key) o None

EstadoJugador
  ├── referencia al Nivel actual
  ├── referencia al Incidente actual
  └── acumula historial_consejos (lista de keys únicas)
```

## Criterios de aceptación

- [ ] Cargar un nuevo incidente no requiere tocar código del motor.
- [ ] Añadir un nivel nuevo solo requiere añadir datos a `datos.py`.
- [ ] Un incidente sin `consejo` no dispara el panel educativo.
- [ ] Los `id` son únicos en toda la base de datos.
- [ ] Cada `consejo` referenciado existe en `CONSEJOS`.