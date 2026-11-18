# Spec 14 — Tutorial guiado (Bloque K)

## Problema
El tutorial anterior era solo una animación con textos y un pulso en los botones del
chat: no obligaba a hacer nada, no explicaba el porqué y no contaba la historia.

## Qué es ahora
Un tutorial **como el de un videojuego**: primero la historia y el objetivo, y luego una
práctica sobre las pantallas reales donde el juego **oscurece todo, señala qué tocar,
explica por qué y no deja pulsar otra cosa**.

### 1. La historia (6 pantallas, con voz y texto que se escribe)
Ver spec 10. Cuenta quién eres, tu dinero y la matrícula, **el peligro**, los **tres
recursos** y la **misión**, y termina con "Te enseñaré cómo se juega, paso a paso".

### 2. La práctica guiada (19 pasos en el Domingo)
Cada paso sucede sobre la pantalla real (Home → Mensajes → Chat → herramientas →
resultado), con: pantalla oscurecida salvo el elemento resaltado (con esquinas redondeadas),
un anillo azul que late, un globo con el texto, una flecha hacia el elemento, el contador
"Paso 7 de 19" y una voz que lo lee.

| # | Pantalla | Tipo | Qué resalta | Qué dice |
|---|----------|------|-------------|----------|
| 1 | Home | info | Tu semana | Hoy es domingo; el viernes vence la matrícula |
| 2 | Home | info | Banco | Tienes $800 y el viernes debes pagar $500 |
| 3 | Home | **clic** | Mensajes | Te llegó un mensaje: tócalo |
| 4 | Lista | info | Barras de recursos | Privacidad, Dinero y Reputación; a cero pierdes |
| 5 | Lista | **clic** | Mensaje de mamá | Es de tu mamá: ábrelo |
| 6 | Chat | info | El mensaje | Mira quién escribe y qué te pide |
| 7 | Chat | **clic** | Remitente | Investiga primero (suma puntos) |
| 8 | Modal | **clic** | Cerrar | Está en tus contactos y el número coincide |
| 9 | Chat | **clic** | Confiar | Es tu mamá y todo coincide |
| 10 | Resultado | **clic** | Siguiente | Acertar suma puntos; errar cuesta recursos |
| 11 | Lista | **clic** | Mensaje sospechoso | Es de práctica: equivocarte no cuesta nada |
| 12 | Chat | info | El mensaje | Premio que no pediste, con prisa y un enlace |
| 13 | Chat | **clic** | Enlace | ¿A dónde lleva en realidad? |
| 14 | Modal | **clic** | Cerrar | Imita a la universidad pero no es el dominio oficial |
| 15 | Chat | info | Verificar | Si dudas: llamada, canal oficial o búsqueda |
| 16 | Chat | **clic** | Reportar | Es una estafa: avisa y protege a otros |
| 17 | Resultado | **clic** | Siguiente | Ante un fraude, reportar es lo más seguro |
| 18 | Consejo | **clic** | Entendido | Se guarda en Mis aprendizajes |
| 19 | Resumen | info | — | "Mañana empieza la semana de verdad" |

- **Paso "info"**: solo existe el botón *Siguiente* (o Espacio/Enter). Ningún botón del
  juego responde.
- **Paso "clic"**: solo se puede pulsar el botón resaltado. Cualquier otro clic se ignora.
- **Salida de emergencia:** "Saltar tutorial" (arriba a la derecha) siempre está a la
  vista; el juego sigue normal (y vuelve el pulso suave del Nivel 0).
- **Nunca se atasca:** si el juego está en una pantalla distinta a la del paso, o el botón
  no está a la vista, el tutorial se pausa y el juego queda libre.

### El mensaje de práctica (`n0_02`, "Premios Campus")
Segundo mensaje del Domingo, una estafa de beca con enlace a `beca-campus-premios.com`,
cuenta nueva, número internacional y muchos reportes. Es un incidente `es_tutorial`:
- **no da XP** (`puntos = 0`) y **no cuenta para el máximo** (sigue en 800 y el umbral en 560);
- **no penaliza** (`impacto` en cero): equivocarse no cuesta nada;
- sí desbloquea el consejo *typosquatting* al reportarlo, y su error tiene voz.

El Domingo suma 25 XP (el mensaje de mamá con una herramienta).

## Arquitectura
- `tutorial.py` — motor **sin pygame**: `Tutorial(pasos)` con `paso_en(estado)`,
  `permite(estado, boton)`, `click(...)`, `siguiente()`, `saltar()`. Es lo que decide qué
  clics valen y cuándo se avanza; se prueba sin ventana.
- `datos.TUTORIAL_PASOS` — los pasos como **datos** (id, pantalla, tipo, foco, texto, voz).
  Para cambiar el tutorial basta editar esa lista.
- `ui.draw_tutorial(...)` — la capa visual. Las pantallas declaran **zonas** no clicables
  (`btns["_zonas"]`: `semana`, `hud`, `mensaje`) para poder resaltar cosas que no son
  botones; van en un diccionario aparte para que nunca intercepten clics.
- `main.py` — dibuja la pantalla normal, **luego** la capa del tutorial, reemplaza
  `last_buttons` por solo lo permitido, y reenvía al tutorial cada clic ejecutado.
- `voces.py` — cada paso tiene su audio `tut_<id>`; las cifras van en palabras en `voz`.
- `config.TUTORIAL_ACTIVO = True` lo activa (con `False` el juego va directo al Domingo).

## Cómo cambiar el tutorial
1. Edita `datos.TUTORIAL_PASOS` (texto, orden, qué resaltar) o `n0_02`.
2. Si el foco es un elemento nuevo que no es botón, declara su zona en la pantalla
   correspondiente de `ui.py`.
3. `python generar_voces.py` regenera solo las voces que cambiaron.
4. `python _test_game.py` falla si un paso apunta a algo que no existe en su pantalla.
5. `python _capturas.py 1.25` guarda una imagen de cada paso (`tutorial_<id>.png`).

## Pruebas
- Test 29: datos de los pasos, reglas del motor (info vs clic, clic equivocado, "Siguiente"
  que no salta un clic, pausa en otra pantalla, saltar), el Nivel 0 cuadra con los pasos
  y la práctica no puntúa ni penaliza.
- Test 30: los 19 pasos se dibujan con su foco; "Siguiente" solo en los informativos.
- Test 25 comprueba que los botones del tutorial no cambian con la escala.
- Corrida de `main.py` real: recorre los 19 pasos, verifica que en los pasos de clic solo
  existe el botón resaltado y en los informativos solo los del tutorial, que termina en el
  Resumen con 25 XP y el consejo desbloqueado, y que "Saltar" devuelve el juego libre.

## Criterios de aceptación
- [x] La historia cuenta quién eres, el dinero, el peligro, los recursos y la misión.
- [x] El tutorial **obliga** a pulsar donde se indica (los demás clics no existen).
- [x] Explica el porqué de cada elemento, paso a paso, con voz.
- [x] Practica las herramientas, el riesgo (estafa con enlace) y reportar.
- [x] La práctica no puntúa, no penaliza y no cambia el balance (800 / 560).
- [x] Se puede saltar en cualquier momento; nunca deja el juego atascado.
- [ ] Prueba con jugadores reales (¿se entiende sin ayuda?) — pendiente.
- [ ] Animación explicativa estilo anuncio educativo (siguiente bloque).

## Ideas pendientes
- Repetir el tutorial desde el menú ("Tutorial") sin empezar partida.
- Pasos opcionales para el temporizador y la verificación (Nivel 2) y para el banco
  (OTP/transferencias): hoy se descubren jugando, con el consejo al fallar.
