# Spec 12 — Apartado visual: pantalla nítida (Bloque I)

## Problema
Todo se veía pixelado y de baja resolución: textos, íconos y formas. Agrandar la
ventana no lo arreglaba.

## Causa (medida en el equipo del desarrollador)
- Windows tenía la escala de pantalla en **125%** (escritorio de 1536×864 lógicos
  sobre 1920×1080 reales).
- El proceso de Python era **"no consciente de DPI"**: Windows tomaba la ventana de
  400×700 píxeles y la **estiraba 25%** como una imagen. Por eso era borrosa, y
  agrandarla no ayudaba: el dibujo seguía siendo de 400×700.
- Además, `pygame.font.SysFont("segoeui")` cargaba **Segoe UI Light**
  (`segoeuil.ttf`), una tipografía finísima que a 9–13 px se ve débil.
- Las formas (círculos, esquinas redondeadas, íconos) se dibujaban sin suavizado, y
  los emojis (📞 🏛 🔎) y símbolos (⚠ ✕ ⌂) salían como cuadros.

## Solución
1. **Compatible con la escala de Windows.** `gfx.calcular_escala()` declara el
   proceso "System DPI aware" **antes** de crear la ventana y lee la escala real
   (1,25 en este equipo). La ventana se abre a **400·S × 700·S píxeles reales**
   (500×875 a 125%) y Windows ya no la estira. Sin `pygame.SCALED` (desfasaba clics).
2. **Todo se dibuja a la resolución real.** `ui.py` sigue en coordenadas lógicas
   400×700; el módulo nuevo `gfx.py` las multiplica por la escala `S`:
   - formas con **suavizado** (supersampling ×2–×4 y reducción) guardadas en
     **caché**: rectángulos redondeados, círculos, elipses, polígonos y líneas
     inclinadas; rectas y líneas horizontales/verticales se dibujan directas;
   - firmas iguales a `pygame.draw` (`rect, circle, ellipse, line, lines, polygon`),
     así que el cambio en `ui.py` fue mecánico (172 llamadas);
   - texto a tamaño real (`tamaño · S`), pero **medido con las fuentes de tamaño
     lógico**: los saltos de línea y recortes son los mismos a cualquier escala.
3. **El ratón** se convierte a lógico (`gfx.a_logico`); los botones que devuelve
   `ui.py` siguen en coordenadas lógicas, así que `main.py` no cambió su lógica.
4. **Tipografía:** Segoe UI normal/negrita cargadas por ruta (`segoeui.ttf`,
   `segoeuib.ttf`); si no existen (otro sistema) se usa `SysFont`.
5. **Símbolos:** si Segoe UI no trae un carácter (⚠ ✕ ⌂ ✓ ⌫), se dibuja con
   *Segoe UI Symbol*. La detección compara el dibujo contra el cuadro vacío
   (`font.metrics()` no sirve: devuelve las medidas del cuadro). Los emojis fuera del
   plano básico se descartan (pygame no puede dibujarlos).
6. **Íconos** de la pantalla de verificación (auricular, edificio, lupa) dibujados
   con vectores en lugar de emojis.
7. **HUD:** las barras de Privacidad/Dinero/Reputación se acortaron para que no
   pisen el número de la derecha.

## Pantallas de información rediseñadas (Bloque N)
**Cómo jugar** y **Créditos** se rehicieron con el mismo lenguaje visual que la animación:
banda azul superior, tarjetas redondeadas y **íconos vectoriales de color** por acción.
- *Cómo jugar* (con scroll): quién eres, las 5 acciones (cada una con su ícono y color), las
  herramientas, los 3 recursos, el tiempo y los gastos, la barra del certificado (560 de 800) y
  los aprendizajes. Los números salen de `config`, no están escritos a mano.
- *Créditos*: banda con degradado y logo, tarjetas del equipo con sus iniciales, el proyecto,
  los tres ODS con sus colores oficiales y las versiones reales de Python y Pygame.
- Los íconos viven en `iconos.py` y los comparten la animación, Instrucciones y Créditos.

## Configuración (`config.py`)
`UI_ESCALA = "auto"` usa la escala de Windows (limitada para que la ventana quepa
en el escritorio, mínimo 0,75). Un número (`1.0`, `1.5`, `2.0`) la fuerza tal cual.

## Reglas para el código nuevo
- Dibujar siempre con `gfx.*` y texto con `ui._t()`; **no** usar `pygame.draw`,
  `screen.blit(font.render(...))` ni `pygame.Surface` directos en `ui.py`.
- Superficies auxiliares con `gfx.surface(ancho, alto[, fondo])`, recortes con
  `gfx.clip`, oscurecer el fondo con `gfx.overlay`.
- Las superficies de scroll son **opacas** (`fondo=`), no transparentes: mezclar
  bordes suavizados sobre transparente deja halos oscuros.
- Cualquier cadena de texto puede llevar símbolos BMP; los emojis no se verán.
- Dimensiones y posiciones **siempre lógicas**; nunca multiplicar por `gfx.S` en `ui.py`
  (la excepción son los pocos sitios que blitean una superficie de texto ya dibujada).

## Herramienta: `_capturas.py`
`python _capturas.py [escala] [carpeta]` renderiza ~70 pantallas en distintos estados
(menú, home de cada día, apps, lista con scroll y evento cayendo, chat con temporizador,
banco, derrotas…) a PNG y guarda `rects.json` con todos los botones. Sirve para revisar
el aspecto sin jugar y para comprobar que un cambio no mueve ningún botón.

## Resultados medidos
- **Botones idénticos** a escala 1,0, 1,25, 1,5 y 2,0 en las 70 pantallas, y
  idénticos al código anterior al refactor (comparación pantalla por pantalla).
- **Rendimiento** (caché caliente): 0,8–1,8 ms por cuadro a escala 1,0; 1,3–2,8 ms a
  1,25; máx. 5 ms a 2,0 (presupuesto a 60 FPS: 16,7 ms). El primer cuadro de cada
  pantalla tarda 5–55 ms mientras se llena la caché.
- **Clics** probados con `main.py` real a escala 1,0, 1,25 y 1,5: el clic en píxeles
  reales activa el botón correcto y un clic a 4 px fuera no lo activa.

## Criterios de aceptación
- [x] Ventana al tamaño real (400·S × 700·S) y proceso compatible con la escala.
- [x] Texto, círculos, esquinas e íconos suavizados.
- [x] ⚠ ✕ ⌂ ✓ se ven (ya no cuadros); sin emojis rotos.
- [x] Botones idénticos a cualquier escala (`_test_game.py`, test 25).
- [x] Conversión de escala y ratón, suavizado y caché (test 24).
- [ ] Prueba visual con ventana real en el equipo del desarrollador (pendiente).

## Pendiente / ideas
- Tamaño mínimo del texto "tiny" (9 px lógicos): sigue pequeño; subirlo a 10–11 px
  cambia los saltos de línea y requiere revisar pantallas.
- Pantallas en monitores con escalas distintas: se usa "System DPI aware" (la escala
  se fija al abrir); al arrastrar la ventana a otro monitor Windows la estira.
