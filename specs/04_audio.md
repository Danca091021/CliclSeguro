# Spec 04 — Audio

## Arquitectura

Un solo `AudioManager`, instanciado una vez en `main.py`. Tiene 3 canales:

| Canal | Uso       | Concurrencia     | Bloquea |
|-------|-----------|------------------|---------|
| 0     | SFX       | Múltiples a la vez | No    |
| 1     | Música    | 1 pista a la vez  | No      |
| 2     | Voz (TTS) | 1 frase a la vez  | No (hilo) |

## SFX — sintetizados con numpy + wave

Todos se generan en código al arrancar el juego. **Ningún SFX se descarga.**

| Key           | Duración máx | Forma                            |
|---------------|--------------|----------------------------------|
| `click`       | 200 ms       | Seno 440 Hz, envelope ADSR corta |
| `hover`       | 150 ms       | Seno 660 Hz, 30% volumen         |
| `notificacion`| 800 ms       | Dos tonos ascendentes 660→880 Hz |
| `exito`       | 1200 ms      | Arpegio mayor ascendente         |
| `error`       | 900 ms       | Dos tonos descendentes 440→330 Hz|
| `alerta`      | 1000 ms      | Pulso repetido 880 Hz, 4 veces   |
| `dinero`      | 700 ms       | Ruido filtrado + ping 1200 Hz    |

### Regla de límite de duración

Cada SFX tiene un `duracion_max_ms` en `config.LIMITES_SFX_MS`. Al reproducir:

1. Se verifica si el archivo cargado excede el límite.
2. Si lo excede, se reproduce y se programa un `.stop()` exacto al cumplirse el límite.
3. Si el archivo es más corto, se reproduce completo.

Esto permite cambiar un SFX por otro más largo sin tocar código: el límite se respeta solo.

## Música

Dos pistas en crossfade:

| Pista            | Cuándo                                           |
|------------------|--------------------------------------------------|
| `musica_segura`  | Por defecto durante el juego                     |
| `musica_tension` | Cuando `min(priv, dinero, rep) < 30`             |

- Crossfade: 800 ms.
- Al volver a estado seguro: crossfade de vuelta.
- En el menú principal: `musica_segura` con volumen reducido.

**Ubicación de archivos:** `assets/audio/musica/*.ogg`. Si no existen, el juego corre en silencio sin romperse.

## Voz (TTS)

### Motor
`pyttsx3` corriendo en un **hilo separado** para no bloquear el game loop.

### Idioma
- Configurado en `config.TTS_IDIOMA = "es-MX"`.
- Al inicializar, se busca la primera voz cuyo `id` o `name` contenga "es-MX".
- Fallback: primera voz que contenga "es".
- Si no hay ninguna voz en español: se usa la voz por defecto del SO.

### Modo
`config.MODO_VOZ = "robot"` (por defecto) o `"grabado"`.

### Catálogo de frases
Archivo `assets/audio/voz/catalogo.json`:

```json
{
  "consejo_otp":      {"texto_fallback": "El código OTP nunca se comparte."},
  "consejo_urgencia": {"texto_fallback": "La urgencia es la táctica del estafador."},
  "consejo_typo":     {"texto_fallback": "Un carácter puede cambiar todo."},
  "consejo_llamar":   {"texto_fallback": "Ante un conocido que pide dinero, llama."},
  "consejo_acoso":    {"texto_fallback": "Callar deja libre al agresor."},
  "consejo_banco":    {"texto_fallback": "El banco no pide datos por llamada."},
  "consejo_2fa":      {"texto_fallback": "El 2FA es tu mejor escudo."}
}
```

### Función pública `hablar(key, texto)`

Pseudocódigo:

```
FUNCIÓN hablar(key, texto):
    detener_voz_actual()

    SI MODO_VOZ == "grabado":
        ruta = assets/audio/voz/grabado/{key}.ogg
        SI existe(ruta):
            reproducir_en_canal_2(ruta)
            RETORNAR

    # Fallback a TTS
    encolar_en_hilo_tts(texto)
```

**El resto del código NUNCA llama a `pyttsx3` directamente.** Solo llama `audio.hablar(...)`.

### Detener voz
`audio.detener_voz()` corta la reproducción actual (sea grabada o TTS) y limpia la cola.

## API pública del AudioManager

```python
class AudioManager:
    def inicializar(self): ...
    def reproducir_sfx(self, key: str): ...
    def cambiar_musica(self, pista: str, fade_ms: int = 800): ...
    def hablar(self, key: str, texto: str): ...
    def detener_voz(self): ...
    def actualizar(self): ...   # llamar cada frame
    def cerrar(self): ...
```

## Criterios de aceptación

- [ ] Cambiar `MODO_VOZ = "grabado"` en `config.py` no rompe nada.
- [ ] Un SFX nunca dura más que su límite declarado.
- [ ] La voz no bloquea el game loop (corre en hilo).
- [ ] Si `pyttsx3` falla, el juego sigue funcionando sin voz.
- [ ] Si faltan archivos de música, no hay error fatal.
- [ ] El crossfade entre pistas dura exactamente 800 ms.