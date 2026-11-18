# Clic Seguro

Videojuego educativo en **Python + Pygame** que enseña ciberseguridad
preventiva (phishing, suplantación, códigos OTP, transferencias falsas,
acoso) a jóvenes de 15 a 25 años. Proyecto de aula de **Programación III**
(Ingeniería de Sistemas).

Eres Camilo, estudiante de primer semestre. Tienes **$800** para el semestre
y el viernes debes pagar **$500** de matrícula. Durante la semana te llegan
mensajes: algunos son legítimos y otros son estafas. Investiga antes de
decidir: cada clic tiene consecuencias.

## Requisitos
- Python 3.12
- Pygame 2.6.1
- pyttsx3 (opcional, solo para la voz "robot")

```bash
pip install pygame pyttsx3
```

## Cómo jugar
```bash
python main.py
```

- Eres **Camilo**, estudiante de primer semestre. Pulsa **Jugar** (o Enter).
- La primera vez, una **animación de ~1 minuto con voz** explica de qué trata el juego ("Ver animación" en el menú la repite; "Saltar" la omite).
- Luego el juego te cuenta la historia y te enseña a jugar **paso a paso**: oscurece la pantalla,
  señala dónde tocar y solo deja pulsar eso. "Saltar tutorial" siempre está disponible.
- **Intro:** clic, Espacio o Enter avanzan; "Saltar intro" o Esc la omiten.
- Cada día empieza con una pantalla que dice el día de la semana y su objetivo.
- Abre **Mensajes**, toca un mensaje y decide: **Confiar, Verificar, Ignorar,
  Bloquear o Reportar**. Antes puedes usar las herramientas (Remitente, Enlace,
  Contactos): dan +5 puntos.
- A partir del Miércoles los mensajes urgentes tienen cuenta regresiva de 20 s;
  **Verificar la pausa**.
- Las transferencias aceptan **solo el monto exacto** que te piden.
- A veces un familiar te pide dinero (evento): **ayudar cuesta dinero** y devuelve
  un poco de reputación; no ayudar resta reputación. Ayudar puede ponerte en
  riesgo de no pagar la matrícula.
- Si un recurso (Privacidad, Dinero, Reputación) llega a 0, repites el nivel.
  Si no puedes pagar el gasto del día, pierdes la partida y la pantalla te
  explica por qué (repetir no cambiaría tu saldo).
- **Certificado:** terminar el viernes con la matrícula pagada y al menos
  **560 puntos** (el 70% del máximo).
- Cada día nuevo recuperas **+10 de reputación**.

**Pantalla nítida:** la interfaz es de 400×700 "lógicos", pero el juego se declara
compatible con la escala de Windows y abre la ventana al tamaño real (por ejemplo
500×875 con escala 125%), dibujando a esa resolución con suavizado. Si la ventana te
queda muy grande o pequeña, fija `UI_ESCALA` en `config.py` (por ejemplo `1.0` o `1.5`).
No usa `pygame.SCALED` a propósito: con escala > 100% desfasaba los clics.

## Voz
El juego habla: la intro, el día de la semana, los consejos y —lo más importante— una
voz que **explica qué hiciste mal** cada vez que fallas (y por qué perdiste el nivel).
Son 95 frases (animación, historia, tutorial, días, consejos, errores); la lista completa está en `voces.py`.

Los audios ya vienen generados en `assets/audio/voz/grabado/` con la voz en español de
Windows (Microsoft Helena). Si cambias un texto en `datos.py`, regénera:

```bash
python generar_voces.py --verificar   # ¿hay audios desactualizados o faltantes?
python generar_voces.py               # genera solo los que faltan o cambiaron
python generar_voces.py --listar      # muestra todas las frases
```

`config.py` → `MODO_VOZ`:

| Valor        | Qué hace |
|--------------|----------|
| `"grabado"`  | (por defecto) Reproduce `assets/audio/voz/grabado/<clave>.wav` o `.ogg`. Si falta un archivo, cae a `robot`. |
| `"robot"`    | Voz en español de Windows en vivo (pyttsx3). |
| `"silencio"` | Sin voz. |

**Para usar voces propias o mejores:** reemplaza cualquier archivo por una grabación con
el mismo nombre (`.wav` u `.ogg`) y no uses `--forzar`. Detalles en `specs/13_dia_y_voz.md`.

## Configuración rápida (`config.py`)
| Constante | Para qué |
|-----------|----------|
| `SKIP_INTRO` | `True` omite la cinemática (demos). |
| `UMBRAL_CERTIF` | Puntos para el certificado (560 = 70% del máximo). |
| `REP_NUEVO_DIA` | Reputación que se recupera al empezar cada día (10). |
| `ANIMACION_ACTIVA` | `False` quita la animación explicativa del arranque. |
| `TUTORIAL_ACTIVO` | `False` omite la práctica guiada del Domingo. |
| `UI_ESCALA` | `"auto"` (escala de Windows) o un número para forzar el tamaño de la ventana. |
| `EVENTO_CHANCE` | Probabilidad del evento aleatorio por nivel (0.60). |
| `TIEMPO_URGENCIA` | Segundos del temporizador (20). |
| `DINERO_INICIAL_V2`, `MATRICULA`, `GASTOS_DIARIOS` | Economía. |

## Pruebas y balance
```bash
python _test_game.py          # 34 tests (lógica, dibujo, voz, tutorial y animación), sin abrir ventana
python _simular_balance.py    # simula partidas de 5 perfiles de jugador
python _capturas.py 1.25      # guarda ~70 pantallas como PNG en capturas/ (revisión visual)
```

`_test_game.py` cubre niveles, economía (gastos, matrícula, préstamo),
verificación, OTP, transferencias, eventos aleatorios (que cuestan dinero),
temporizador agotado, derrota explicada, final de la semana, reinicio de
nivel, balance, dibujo a distintas escalas y voz. Los resultados del balance están en
[`specs/11_balance.md`](specs/11_balance.md).

## Arquitectura
```
main.py           máquina de estados + bucle principal + clics
config.py         constantes globales
modelos.py        dataclasses (Incidente, Nivel, Consejo, EstadoJugador...)
datos.py          contenido: consejos, 33 incidentes, 5 niveles, intro
game.py           lógica pura (SIN pygame)  ← testeable sin ventana
ui.py             dibujo de pantallas y modales (en coordenadas lógicas 400×700)
gfx.py            capa de dibujo: escala, suavizado y escala de pantalla de Windows
audio_manager.py  SFX sintetizados + música procedural + voz
tutorial.py       motor del tutorial guiado (sin pygame)
animacion.py      línea de tiempo de la animación explicativa (sin pygame)
escenas.py        dibujo de las 9 escenas de la animación (vectorial)
iconos.py         íconos vectoriales compartidos (animación, instrucciones, créditos)
voces.py          qué se dice en voz alta (95 frases) y dónde están sus audios
generar_voces.py  crea los audios con la voz en español de Windows
```

Regla de dependencia: `game.py`, `modelos.py` y `datos.py` **no importan
pygame**; solo `ui.py`, `gfx.py` y `audio_manager.py` lo hacen. Por eso la lógica se
prueba y se simula sin abrir una ventana.

El proyecto se desarrolló con **Spec-Driven Development**: los documentos de
`specs/` son la fuente de verdad y se actualizan junto con el código
(visión, mecánicas, personajes, audio, modelo de datos, niveles, diagramas,
pantallas, cinemática, balance, apartado visual, día y voz, tutorial y animación). Los mockups están en `specs/mockups/` y
los diagramas de arquitectura en `Diagramas/`.

## Créditos
José David Saza Montero · Daniel Calderón
Programación III — Ingeniería de Sistemas — Cali, Colombia, 2026
Alineado con los ODS 4, 9 y 16.
