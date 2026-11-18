# Spec 15 — Animación explicativa (Bloque L)

## Qué es
Un video corto **dentro del juego** que explica de qué trata Clic Seguro, al estilo de los
anuncios y programas educativos de televisión: gráficos planos y brillantes que se mueven
con rebote, un rótulo de color por escena, una **voz que narra** y **subtítulos que se
iluminan palabra por palabra** al ritmo de la voz. Dura **62,7 s** con los audios actuales.

No es un archivo de video: son escenas vectoriales dibujadas en vivo con `gfx`, así que
son nítidas a cualquier escala, pesan casi nada y se sincronizan con los audios aunque
cambies un texto o la voz.

## Cuándo se ve
- **Al empezar la primera partida de la sesión**, antes de la historia:
  `Jugar → animación → historia (6 pantallas) → día → tutorial guiado`.
- **Cuando quieras**, con el botón **"Ver animación"** del menú (al terminar vuelve al menú).
- Siempre se puede saltar: botón **Saltar ›** arriba a la derecha, o Esc/Espacio/Enter.
- `config.ANIMACION_ACTIVA = False` la quita del arranque (el botón del menú sigue).

## Guion (9 escenas)
| # | Escena | Rótulo | Narración | Imagen |
|---|--------|--------|-----------|--------|
| 1 | mensajes (4,6 s) | TU CELULAR | "Cada día recibes decenas de mensajes en tu celular." | Un celular rodeado de notificaciones que llegan; el contador sube hasta 37 |
| 2 | trampa (8,6 s) | LA TRAMPA | "Pero algunos no son lo que parecen. Son trampas para robar tus datos, tu dinero o tu reputación." | Un mensaje "¡Ganaste una beca!"; un **anzuelo** baja y lo atrapa; las barras de Privacidad, Dinero y Reputación se vacían |
| 3 | habitos (3,6 s) | — | "Tres hábitos te protegen." | Un gran **3** con tres íconos: lupa, escudo, candado |
| 4 | investiga (7,2 s) | 1 · INVESTIGA | "Uno: investiga antes de actuar. Mira quién escribe y a dónde lleva el enlace." | Una **lupa** recorre un correo falso y marca el dominio "univers1dad…" como ¡Dominio falso! |
| 5 | verifica (9,0 s) | 2 · VERIFICA | "Dos: verifica por un canal oficial. Llama al número que ya conoces, no al que viene en el mensaje." | Un mensaje con un número dudoso (tachado) y el contacto oficial con escudo verde; un auricular suena |
| 6 | codigos (7,2 s) | 3 · NO COMPARTAS CÓDIGOS | "Tres: nunca compartas tus códigos, ni siquiera con alguien que diga ser del banco." | El código 4 8 2 9 1 5; llega "Soy del banco. Dame tu código." y un **sello rojo de prohibido** cae encima |
| 7 | prisa (8,3 s) | LA PRISA | "Y desconfía de la prisa: los estafadores te apuran para que no pienses. Detente y verifica." | "¡ÚLTIMO AVISO!" con una **cuenta regresiva** 00:20 → 00:00; aparece un **ALTO** |
| 8 | mision (8,9 s) | TU MISIÓN | "Tu misión: llegar al viernes, pagar tu matrícula y proteger tu privacidad, tu dinero y tu reputación." | La semana D·L·X·J·V con un marcador que viaja hasta el viernes; la matrícula $500 con ✓; los tres recursos |
| 9 | cierre (5,5 s) | — | "Clic Seguro. Cada clic tiene consecuencias." | El logo con destellos y el lema |

Cada escena dura **lo que dura su audio + 0,7 s de pausa** (o su `min_ms` si es mayor).

## Arquitectura
- `datos.ANIMACION_ESCENAS` — el guion como **datos**: `id`, `etiqueta`, `color`, `voz`
  (la narración, que también son los subtítulos) y `min_ms`.
- `animacion.py` — la **línea de tiempo** (sin pygame): `Animacion(escenas, duraciones_de_voz)`
  calcula cuándo empieza cada escena, `escena_en(t)` dice cuál toca y `progreso_voz` cuánto de
  la frase ya se dijo.
- `voces.duracion_ms(clave)` — lee lo que dura cada audio (`.wav`); sin audio estima por el texto.
- `escenas.py` — el **dibujo** de las 9 escenas y el cuadro completo (`draw_animacion`): fondo
  con círculos flotantes, rótulo, barra de progreso, subtítulos y botón Saltar. Cada escena es
  `f(screen, t, d)` con `t` = ms desde que empezó.
- `main.py` — estado `ANIMACION`: avanza el reloj, y al cambiar de escena corta la voz anterior
  y dice la nueva (`anim_<id>`).
- `voces.py` / `generar_voces.py` — las 9 narraciones son parte del manifiesto (`anim_<id>`).

## Cómo cambiarla
1. Texto, orden o colores: edita `datos.ANIMACION_ESCENAS`.
2. Regenera las voces que cambiaron: `python generar_voces.py` (las duraciones se ajustan solas).
3. Una escena nueva: agrega su entrada en la lista y una función `_escena_<id>(screen, t, d)` en
   `escenas.py` registrada en `ESCENAS`. El test falla si una escena no tiene dibujo.
4. Ver todas las escenas sin jugar: `python _capturas.py 1.25` guarda `anim_<id>_a/b/c.png`
   (al 30%, 65% y 97% de cada escena).

## Detalles técnicos
- **Nitidez y rendimiento:** todo con `gfx` (suavizado, escala de Windows). ~2 ms por cuadro.
- **Subtítulos:** las palabras se miden con la fuente con que se dibujan (÷ escala). Medirlas con
  la de tamaño lógico las hacía ~5 % más anchas de lo previsto y salían pegadas ("algunosno").
  `escenas._disponer_subtitulo` lo calcula y un test lo comprueba a escala 1,0 / 1,25 / 1,5.
- **Fundido** de entrada de 200 ms al abrir la animación (spec 13).

## Pruebas
- Test 31: línea de tiempo (voz + pausa, mínimos, encadenado, límites, "pasado el final"),
  datos del guion, duraciones leídas de los `.wav`, duración total entre 35 y 100 s.
- Test 32: cada escena se dibuja en 7 instantes, **se anima** (probada sin el fondo, que siempre se
  mueve) y no termina vacía, el botón Saltar cabe en pantalla, y los subtítulos no se pisan.
- Test 25: los botones no cambian con la escala (incluye 27 cuadros de la animación).
- Corrida de `main.py` real: Jugar → animación con la voz de la escena 1; cambio de escena habla la
  nueva; Saltar → historia; la 2.ª partida no la repite; "Ver animación" vuelve al menú.

## Criterios de aceptación
- [x] Explica el objetivo del juego con voz, al estilo de un anuncio educativo.
- [x] Subtítulos sincronizados con la voz.
- [x] Se puede saltar en cualquier momento y repetir desde el menú.
- [x] Voz y dibujo siempre sincronizados (la duración sale del audio).
- [x] Nítida a cualquier escala y sin consumir apenas CPU.
- [ ] Ver y oír la animación con ventana y altavoces reales (pendiente).
- [ ] Música de fondo propia para la animación y voz más natural (opcional; ver spec 13).

## Ideas pendientes
- Pequeños efectos de sonido sincronizados (notificaciones, "ding" del anzuelo, sello).
- Voz masculina o grabada por el equipo: se reemplazan los `anim_*.wav` sin tocar código.
- Una versión corta (~20 s) para repetir sin cansar.
