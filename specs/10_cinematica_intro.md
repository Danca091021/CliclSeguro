# Spec 10 — La historia de la intro (6 pantallas narrativas)

> Reemplaza la versión anterior (mano + zoom + "Lunes 6:55") y se amplió en el
> Bloque K: ahora cuenta la historia, el peligro, los recursos y la misión antes de
> la práctica guiada (spec 14).

> Va **después** de la animación explicativa (spec 15) en la primera partida.

## Secuencia
Fondo negro, sin teléfono. Seis pantallas con título (fade-in) y texto con efecto
*typewriter* (`TYPEWRITER_CPS`), centrados, cada una con su voz. Contenido en
`datos.INTRO_PAGINAS`:

| # | Título                | Texto                                                        |
|---|-----------------------|--------------------------------------------------------------|
| 1 | Domingo, 6:00 PM      | Casa de Camilo. Último día antes de la universidad.          |
| 2 | Tu primer celular     | Tus padres te dieron tu primer celular y $800 para el semestre. El viernes debes pagar $500 de matrícula. |
| 3 | Pero hay un peligro   | Hay gente que usa mensajes falsos para robarte datos, dinero y reputación. |
| 4 | Tus tres recursos     | Cuida tu Privacidad, tu Dinero y tu Reputación. Si alguno llega a cero, pierdes el nivel. |
| 5 | Tu misión             | Llega al viernes, paga la matrícula y aprende a detectar los engaños. |
| 6 | Practica primero      | Llegan tus primeros mensajes. Te enseñaré cómo se juega, paso a paso. |

`$800` y `$500` salen de `config.DINERO_INICIAL_V2` y `config.MATRICULA`
(marcadores `{dinero}` y `{matricula}`).

## Interacción
- **Clic / Espacio / Enter, texto escribiéndose:** muestra el texto completo.
- **Clic / Espacio / Enter, texto completo:** siguiente pantalla.
- **Tras la pantalla 5:** muestra la pantalla del día de Domingo (spec 13) y luego
  entra al Nivel 0 (Home) con la práctica guiada (spec 14).
- **"Saltar intro" / Esc:** salta toda la secuencia al Nivel 0.
- Puntos de progreso abajo; la pista "Click para continuar" solo aparece
  cuando el texto está completo.

## Voz
Cada pantalla llama a `audio.hablar(key_voz, voz)` con `intro_p1`…`intro_p6`.
Según `config.MODO_VOZ`: `silencio` (nada), `robot` (pyttsx3) o `grabado`
(`assets/audio/voz/grabado/intro_pN.wav` u `.ogg`, con fallback a robot).
Al cambiar de pantalla o saltar se corta la voz (`audio.detener_voz()`).

## Cuándo se muestra
- Solo al empezar una partida nueva por primera vez en la sesión
  (no en reinicios de nivel ni al volver al menú).
- `SKIP_INTRO = True` la omite por completo (demos cortas).

## Criterios de aceptación
- [x] Se puede saltar con botón, Esc, o avanzar con clic/Espacio/Enter.
- [x] Primer clic completa el texto; segundo avanza.
- [x] No se reproduce al reiniciar nivel.
- [x] Funciona con `SKIP_INTRO = True` (no se ve nada).
- [x] Al terminar, el jugador pasa por la pantalla del día y queda en el Nivel 0.
