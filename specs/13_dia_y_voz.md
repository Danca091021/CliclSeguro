# Spec 13 — Nombre, día de la semana, fundidos y voz de errores (Bloque J)

## 1. Nombre del jugador
**Antes:** el menú pedía un nombre, pero la historia es de Camilo ("Eres Camilo",
"¿Qué hace Camilo?", "El consejo de Camilo"…). El nombre solo servía para el saludo
del Home, así que no aportaba y contradecía la historia.

**Ahora:** el protagonista es siempre **Camilo** (`config.NOMBRE_JUGADOR`). El menú ya
no tiene campo de texto; **Enter o Espacio** inician la partida. El saludo del Home
depende del día (`config.SALUDO_POR_NIVEL`): el Domingo (6 PM) dice "Buenas tardes,"
y los demás días "Buenos días,".

## 2. Pantalla del día de la semana (estado `DIA_INTRO`)
Al empezar la partida y al avanzar de día se muestra una pantalla propia:

```
      D ──── L ──── X ──── J ──── V        el marcador viaja del día anterior
      ●      ●      ◎                       al actual (los pasados en verde)

                MIÉRCOLES                   nombre del día (color propio)
                ─────────
          La llamada del pánico             título del nivel
   Resistir la urgencia: no dar códigos…    objetivo del nivel

            Toca para empezar el día
```

- Datos: `Nivel.dia`, `titulo` y `objetivo` de `datos.NIVELES` (nada nuevo que mantener).
- Color de acento por día: `config.COLOR_DIA` (el mismo del widget "Tu semana").
- Animación: la semana y el nombre entran con fundido, el marcador viaja (~0,9 s), y
  luego aparecen título y objetivo. Pasados `DIA_INTRO_LISTO_MS` (2 s) aparece la
  pista. **Primer toque/Espacio:** salta la animación; **segundo:** empieza el día.
- Voz: dice el día y el título ("Miércoles. La llamada del pánico.").
- **Cuándo se muestra:** tras la intro (Domingo), al terminar un nivel y pulsar
  "Continuar al siguiente día", y al empezar partida con `SKIP_INTRO = True`.
  **No** al repetir un nivel (derrota, "Repetir este día", fin de semana).
- Después va al cobro del gasto del día (si lo hay) y al Home.

## 3. Fundidos entre pantallas completas (spec 09, regla 3)
Fundido de entrada de `FADE_MS` = 200 ms (de negro a la pantalla) al entrar a: menú,
día, gastos, resumen, derrota, certificado, fin de semana, instrucciones, créditos y
aprendizajes; y al llegar al Home desde la pantalla del día, los gastos o la intro.
No hay fundido al ir y venir entre apps, mensajes, chat, modales y feedback (sería
molesto en la navegación frecuente).

## 4. Voz que explica los errores
Cuando el jugador falla suena una voz que dice **qué hizo mal, por qué y qué señal debió
notar**. Los textos son más largos que los de pantalla (`feedback_err` eran frases de
cuatro palabras como "Era tu mamá.") y están escritos para ser hablados.

Ejemplo (`n2_05`, estafa del código):
> «Fallaste. Entregaste tu código de verificación. Ese código es la llave de tu cuenta:
> nunca lo compartas, ni con alguien que diga ser de soporte.»

| Cuándo | Qué se dice | Clave |
|--------|-------------|-------|
| Respuesta incorrecta | Explicación de ese mensaje | `err_<id>` (33) |
| No ayudar en un evento | "No ayudaste a tu mamá…" | `err_evento_<id>` (4) |
| Se agotó el temporizador | Aviso, **y luego** la explicación | `err_tiempo` + `err_<id>` |
| No cayó, pero había algo mejor | Qué era lo ideal | `parcial_<acción>` (4) |
| Derrota del nivel | Por qué se perdió | `derrota_<motivo>` (4) |
| Consejo desbloqueado | El consejo (ya existía) | `consejo_*` (9) |
| Intro / día nuevo | Narración y día | `intro_p1..6`, `dia_0..4` |
| Tutorial guiado | Cada paso (spec 14) | `tut_<paso>` (19) |
| Animación explicativa | Una narración por escena (spec 15) | `anim_<escena>` (9) |

**Corte:** la voz se interrumpe al pulsar *Siguiente* (y entonces habla el consejo, si
lo hay), al salir de la derrota y al saltar la pantalla del día.

### Dónde viven los textos
- `datos.VOZ_ERRORES` (un texto por mensaje (34, incluido el de práctica)), `VOZ_ERROR_TIEMPO`, `VOZ_DERROTA`.
  `datos._validar()` exige un texto por cada incidente.
- `voces.manifest()` reúne **las 95 frases** del juego en un diccionario clave → texto.
- Regla de estilo (la verifica el test 26): empiezan con "Fallaste.", ≤ 330 caracteres y
  **sin cifras ni monedas** ("$40") para que suenen bien con cualquier voz.

### Cómo se generan los audios
```bash
python generar_voces.py              # genera los que faltan o cambiaron
python generar_voces.py --listar     # ver las 95 frases
python generar_voces.py --verificar  # ¿faltan o están desactualizados?
python generar_voces.py --forzar     # regenerar todos
```
Usa la voz en español de Windows (**Microsoft Helena**) por PowerShell: sin internet,
sin ffmpeg. Crea `assets/audio/voz/grabado/<clave>.wav` y un `manifest.json` con una
huella del texto de cada audio: si cambias un texto, `--verificar` lo detecta y el
script regenera solo ese. Estado actual: **95 audios, ~13 min, ~34 MB** (incluye la historia, el tutorial, la animación y los errores).

### Reemplazar por voces mejores
Los audios son archivos con el nombre de la clave: se reemplazan por grabaciones
propias (`.wav` u `.ogg`) sin tocar código. El juego prefiere `.ogg` si existe.
`MODO_VOZ` en `config.py`: `"grabado"` (por defecto), `"robot"` (voz en vivo con
pyttsx3) o `"silencio"`. Si falta un audio en modo grabado, cae a `"robot"`.

### Bug corregido: el modo "robot" hablaba en inglés
`audio_manager` buscaba `"es"` dentro del *id* de la voz. En Windows el id es una ruta
del registro (`…\Speech\Voices\Tokens\TTS_MS_EN-US_ZIRA_11.0`) que contiene la palabra
"v**oic**es", así que **todas** las voces coincidían y ganaba la última (Zira, inglés).
`voces.elegir_voz()` mira el idioma y el nombre del token, y prefiere es-MX/es-CO/es-US.

## Pruebas
- Test 26: manifiesto completo, estilo de los textos, elección de la voz española y
  audios al día. Test 27: reproducción y corte (con el mezclador sin ventana).
  Test 28: menú sin nombre, saludo y pantalla del día de los 5 niveles.
- Corrida de `main.py` real: voz de la intro, del día, de un error OTP, del consejo tras
  *Siguiente*, del temporizador agotado y de la derrota; corte al salir.

## Criterios de aceptación
- [x] El menú no pide nombre; el protagonista es Camilo.
- [x] Cada nivel empieza con su día, la semana y su objetivo, con voz.
- [x] Fundido de 200 ms entre pantallas completas.
- [x] Una voz explica cada error, el tiempo agotado y la derrota.
- [x] La voz se corta al avanzar.
- [x] El modo "robot" elige la voz en español.
- [ ] Revisión con ventana y altavoces reales (pendiente).
- [ ] Voces grabadas o neuronales para mayor naturalidad (opcional).
