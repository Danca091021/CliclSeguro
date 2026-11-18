# Spec 08 — Diagramas de arquitectura

Este archivo centraliza los diagramas que sustentan la solución algorítmica
del proyecto. Se usa como fuente de verdad visual y como base para la
sustentación ante el profesor.

## A. Arquitectura de alto nivel (módulos)

```
                     main.py
                       │
                       ▼
                   game.py (EstadoJuego)
                       │
       ┌───────────────┼───────────────┬──────────────────┐
       ▼               ▼               ▼                  ▼
    modelos.py      datos.py     audio_manager.py       ui.py
   (dataclasses)   (niveles,    (SFX, música, voz)   (dibujo con pygame)
                    incidentes,
                    consejos)
                       │                                   │
                       └────────────┬──────────────────────┘
                                    ▼
                               config.py
                        (constantes globales)
```

**Regla de dependencia:**
- `main.py` conoce a `game.py`.
- `game.py` conoce a `modelos.py`, `datos.py`, `audio_manager.py` y `ui.py`.
- `modelos.py`, `datos.py` y `config.py` **no importan pygame**.
- `ui.py` y `audio_manager.py` **sí importan pygame**.
- Ningún módulo de lógica importa `ui.py`.

Esto permite testear la lógica sin ventana.

## B. Bucle principal (E-P-S global)

```
INICIO
  │
  ├─ pygame.init()
  ├─ AudioManager.inicializar()
  ├─ cargar datos (NIVELES, CONSEJOS)
  ├─ ventana(400 × 700)
  ├─ estado ← MENU
  │
  ▼
┌──────────────────── BUCLE (60 FPS) ────────────────────┐
│                                                         │
│  1. ENTRADA                                             │
│     eventos = pygame.event.get()                        │
│     ├─ QUIT → salir                                     │
│     └─ MOUSEBUTTONDOWN → handler según estado           │
│                                                         │
│  2. PROCESO                                             │
│     actualizar_segun_estado(estado)                     │
│     ├─ MENU / JUEGO / CHAT / MODAL / FEEDBACK           │
│     └─ PANEL / RESUMEN / DERROTA / CERTIFICADO          │
│                                                         │
│  3. SALIDA                                              │
│     renderizar_segun_estado(estado)                     │
│                                                         │
│  4. AUDIO                                               │
│     audio.actualizar()  # crossfade, cola de voz        │
│                                                         │
│  5. clock.tick(60)                                      │
│                                                         │
└─────────────────────────────────────────────────────────┘
  │
  ▼
pygame.quit()
FIN
```

## C. Máquina de estados de pantallas

```
     ┌──────────┐
     │   MENU   │
     └────┬─────┘
          │
          ▼
     ┌──────────┐      ┌──────────┐
     │   JUEGO  │◄────►│  CHAT    │
     │  (home)  │      └────┬─────┘
     └──────────┘           │
                            ├─► MODAL ─► CHAT
                            │
                            ▼
                       ┌──────────┐
                       │ FEEDBACK │
                       └────┬─────┘
                            │
                            ├─► PANEL ─► CHAT
                            │
                            ▼
                       ┌──────────┐
                       │ RESUMEN  │
                       └────┬─────┘
                            │
              ┌─────────────┼─────────────┐
              ▼             ▼             ▼
         ┌──────────┐  ┌──────────┐  ┌──────────────┐
         │ DERRROTA │  │ siguiente│  │ CERTIFICADO  │
         │          │  │  JUEGO   │  │  (nivel 4)   │
         └────┬─────┘  └──────────┘  └──────┬───────┘
              │                             │
              └──► JUEGO (mismo nivel)      └──► MENU
```

## D. Ciclo de un incidente (corazón del juego)

```
┌───────────────────────────────────────────────────────────┐
│                    LLEGA UN INCIDENTE                     │
└───────────────────────────┬───────────────────────────────┘
                            │
                            ▼
              ┌──────────────────────────────┐
              │ Renderizar notificación      │
              │ SFX: "notificacion"          │
              │ Música: cambiar si aplica    │
              │ (TTS NO en esta fase)        │
              └──────────────┬───────────────┘
                             │
                             ▼
        ┌──────────────────────────────────────────────┐
        │ ESPERAR INPUT                                │
        │                                              │
        │ a) Click "Remitente" → mostrar modal (#4)   │
        │    marcar herramienta_usada                  │
        │    volver a esperar input                    │
        │                                              │
        │ b) Click "Enlace" → mostrar modal (#5)      │
        │    marcar herramienta_usada                  │
        │    volver a esperar input                    │
        │                                              │
        │ c) Click "Contactos" → mostrar modal         │
        │    marcar herramienta_usada                  │
        │    volver a esperar input                    │
        │                                              │
        │ d) Click ACCIÓN → salir del loop             │
        └──────────────────────┬───────────────────────┘
                               │
                               ▼
              ┌────────────────────────────────┐
              │ EVALUAR DECISIÓN               │
              │ accion ∈ respuestas_aceptables?│
              └─────────┬──────────────┬───────┘
                        │ SÍ           │ NO
                        ▼              ▼
              ┌──────────────┐   ┌──────────────┐
              │ SFX "exito"  │   │ SFX "error"  │
              │ XP += puntos │   │ XP += 0      │
              │ impacto OK   │   │ impacto ✗    │
              │ TTS feedback │   │ TTS feedback │
              └──────┬───────┘   └──────┬───────┘
                     │                  │
                     │                  ▼
                     │           ┌──────────────┐
                     │           │ ¿consejo?    │
                     │           └──────┬───────┘
                     │                  │ sí
                     │                  ▼
                     │           ┌──────────────┐
                     │           │ PANEL        │
                     │           │ typewriter + │
                     │           │ TTS          │
                     │           └──────┬───────┘
                     │                  │
                     └──────┬───────────┘
                            ▼
              ┌────────────────────────────────┐
              │ Actualizar HUD y música        │
              │ (crossfade a tension si < 30%) │
              └────────────────┬───────────────┘
                               │
                               ▼
              ┌────────────────────────────────┐
              │ ¿Algún recurso = 0?            │
              │   SÍ → DERRROTA                │
              │   NO → ¿quedan incidentes?     │
              │         SÍ → siguiente CHAT    │
              │         NO → RESUMEN           │
              └────────────────────────────────┘
```

## E. Subsistema de audio

```
                     ┌───────────────────────┐
                     │     AudioManager      │
                     └───────────┬───────────┘
                                 │
        ┌────────────────────────┼───────────────────────┐
        │                        │                       │
        ▼                        ▼                       ▼
 ┌─────────────┐          ┌─────────────┐        ┌──────────────┐
 │   SFX       │          │   MÚSICA    │        │   VOZ        │
 │  canal 0    │          │  canal 1    │        │  canal 2     │
 └──────┬──────┘          └──────┬──────┘        └──────┬───────┘
        │                        │                      │
        │ numpy → .wav           │ 2 pistas             │ MODO_VOZ
        │ al arrancar            │ crossfade 800ms      │
        │                        │                      │
        ▼                        ▼                      ▼
 limites_sfx_ms[key]     musica_segura /        ¿robot?    ¿grabado?
 corta con .stop()       musica_tension          │          │
                                                 ▼          ▼
                                              pyttsx3    buscar .ogg
                                              (hilo)     si existe
                                                          └─ no → TTS
```

## F. Modelo de datos (entidades y relaciones)

```
┌──────────────────┐
│    EstadoJugador │
│  privacidad      │
│  dinero          │
│  reputacion      │
│  xp              │
│  nivel_actual    │
│  incidente_actual│
│  historial_cons. │
└────────┬─────────┘
         │
         │ usa
         ▼
┌──────────────────┐         ┌──────────────────┐
│      Nivel       │ 1..N    │    Incidente     │
│  id (1..4)       ├────────►│  id              │
│  dia             │         │  tipo            │
│  titulo          │         │  categoria       │
│  objetivo        │         │  remitente{}     │
│  tutorial        │         │  texto           │
└──────────────────┘         │  enlace{}|None   │
                             │  respuestas_ok[] │
                             │  impacto{}       │
                             │  consejo_key|None│
                             └────────┬─────────┘
                                      │
                                      │ referencia por key
                                      ▼
                             ┌──────────────────┐
                             │     Consejo      │
                             │  key             │
                             │  titulo          │
                             │  texto           │
                             │  tipo            │
                             │  key_voz         │
                             └──────────────────┘
```

## Criterios de aceptación

- [ ] Los 6 diagramas (A–F) están representados en el código final.
- [ ] Un desarrollador externo entiende el flujo leyendo solo este archivo.
- [ ] Los diagramas sirven como base para la sección de "solución algorítmica" de la sustentación.