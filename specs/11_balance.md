# Spec 11 — Balance y simulación (Bloques G y H)

## Objetivo
Comprobar con datos —no a ojo— que el juego no es imposible ni trivial, y
dejar documentadas las decisiones de balance del equipo.

## Método
`_simular_balance.py` juega partidas completas contra la lógica real de
`game.py` (sin Pygame) con jugadores automáticos definidos por dos números:
probabilidad de acertar cada mensaje y probabilidad de usar la herramienta
"Remitente" (+5). Supuestos del jugador simulado:

- Responde en el orden de la lista; si se equivoca, cae en la estafa (fraude)
  o rechaza al legítimo. En una transferencia envía el monto **exacto** que piden.
- **Eventos familiares:** los ayuda (cuesta dinero, +5 reputación) con probabilidad
  igual a su tasa de aciertos; si no, los ignora (−15 reputación). Si no le
  alcanza el saldo, no puede ayudar.
- El viernes paga la matrícula en cuanto puede (si no, pide el préstamo de mamá).
- Si pierde un nivel, lo repite (máx. 5 intentos).
- **No aprende entre intentos** y **no se modela el temporizador**: ambas cosas
  hacen que los perfiles débiles se vean peor que un humano real (que memoriza
  las respuestas al repetir). Tampoco decide *no* ayudar para proteger la
  matrícula, como podría hacer un humano estratégico.

```bash
python _simular_balance.py        # 2000 partidas por perfil
python _simular_balance.py 500    # más rápido
```

## Decisiones de balance del equipo
| Decisión | Valor | Por qué |
|----------|-------|---------|
| Umbral del certificado | **560 XP = 70% del máximo (800)** | Es el 70% que decía el spec original (había sido calculado sobre un máximo de 885, por eso se había quedado en 620 = 77,5%). Con 620 un jugador con 80% de aciertos certificaba solo el 34%. |
| Reputación al empezar un día nuevo | **+10** (`REP_NUEVO_DIA`, tope 100) | La reputación era lo que más derrotas causaba y nunca se recuperaba. |
| Eventos familiares | Cuestan dinero (+5 reputación al ayudar, −15 al no hacerlo) | Dilema: ayudar puede poner en riesgo la matrícula. |
| Monto de transferencias | Exacto, ni más ni menos | Evita pérdidas de $1 en fraudes y pagos incorrectos. |

La meta anterior de "partida experta ~15% sobre el umbral" se reemplazó al
adoptar el 70%: ahora la experta queda +28%.

## Resultados (2000 partidas por perfil, umbral 560 XP)

_Recalculado tras añadir el mensaje de práctica del Nivel 0 (spec 14), que no puntúa ni penaliza: el balance no cambia; las diferencias de ±2 puntos son ruido de la simulación._

| Perfil   | Aciertos | Usa herram. | Certificado | Parcial | Sin matrícula | Atascada* | XP prom. | vs umbral | $ final |
|----------|---------:|------------:|------------:|--------:|--------------:|----------:|---------:|----------:|--------:|
| Perfecta |     100% |        100% |      100,0% |    0,0% |          0,0% |      0,0% |      800 |    +42,9% |     $33 |
| Experta  |     100% |         50% |      100,0% |    0,0% |          0,0% |      0,0% |      718 |    +28,1% |     $33 |
| Buena    |      90% |         70% |       98,2% |    0,4% |          1,1% |      0,4% |      676 |    +20,7% |     $41 |
| Media    |      75% |         50% |       45,1% |   46,0% |          1,8% |      7,0% |      530 |     −5,4% |     $82 |
| Mala     |      40% |         20% |        0,0% |    4,0% |          0,4% |     95,7% |      135 |    −75,9% |       — |

\* "Atascada": no supera un nivel en 5 intentos (ver límites del modelo arriba).

### Sensibilidad al umbral (simulado antes del +10 de reputación diario)
Porcentaje que certifica según los aciertos del jugador (1000 partidas c/u):

| Umbral | % del máx. | 100% (con herram. 50%) | 90% | 80% | 70% | 75% |
|-------:|-----------:|-----------------------:|----:|----:|----:|----:|
| 540 | 68% | 100% | 98,8% | 86,4% | 43,8% | 63,1% |
| **560** | **70%** | 100% | 98,8% | 77,8% | 30,1% | 47,9% |
| 600 | 75% | 100% | 96,4% | 50,9% | 9,9% | 22,1% |
| 620 | 77,5% | 100% | 90,8% | 34,1% | 4,3% | 12,0% |
| 650 | 81% | 100% | 76,6% | 16,2% | 0,8% | 3,7% |

## Conclusiones
1. **Ni trivial ni imposible:** azar puro (40%) nunca certifica; 90% de aciertos
   certifica el 98%; 75% certifica el 43% y casi la mitad llega al "Casi lo logras".
2. **El +10 de reputación diario funciona:** en el perfil de 75% las derrotas por
   reputación bajaron de 256 a 48 por cada 500 partidas, los atascados de 12% a
   7% y las repeticiones de 1,33 a 0,65 por partida. Los perfiles buenos casi no
   cambian (la reputación no era su problema).
3. **Las herramientas dejan de ser obligatorias.** Sin usar ninguna, la partida
   perfecta suma 635: +13% sobre el umbral, unos 3–4 errores de margen. (Con 620
   quedaba a solo 15 puntos.) Siguen dando +5 por incidente.
4. **La matrícula está en juego.** Un jugador perfecto que ayuda a todos llega al
   viernes con ~$33 de sobra, y "sin matrícula" aparece en 1–2% de quienes
   fallan. El préstamo de mamá evita que una partida perfecta falle.
5. **Pendiente para la prueba con humanos:** el modelo no incluye el temporizador
   ni el aprendizaje entre intentos; conviene validar con jugadores reales si 560
   se siente justo.

## Bugs encontrados y corregidos
| Bug | Efecto | Corrección |
|-----|--------|------------|
| `reiniciar_nivel` no restauraba el XP | Repetir un nivel permitía sumar puntos dos veces | `xp_inicio_nivel` |
| El dinero se restauraba a *antes* del gasto diario y el gasto no se recobraba | Reembolso gratis de $20–$30 al repetir | El pago ajusta `dinero_inicio_nivel` |
| Lo mismo con la matrícula | **Reembolso de $500** al repetir el viernes | Ídem |
| Lo mismo con el préstamo | El jugador perdía el préstamo | Ídem |
| Los eventos quedaban en la lista al repetir | Tarjetas viejas y eventos duplicados | Se descartan en `reiniciar_nivel` |
| `confirmar_transferencia` aceptaba decimales | Montos como 50.5 | Solo enteros positivos |
| **Cierre del juego:** si el temporizador de 20 s vencía en un mensaje con OTP o transferencia, `main.py` fallaba con `KeyError: 'consejo'` | El juego se cerraba | `Game.resolver_por_tiempo()` completa la interacción |
| **Pagar la matrícula con exactamente $500 dejaba $0 = derrota**, y al repetir se restauraba el mismo saldo | Partida perfecta atascada (3,4% con eventos que cuestan) | Saldo $0 no es derrota el viernes con la matrícula pagada |

## Reglas de economía y eventos (Bloque H)
1. **Los eventos familiares cuestan dinero.** Ayudar = transferencia por el monto
   exacto ($30–$80) y devuelve +5 de reputación (`EVENTO_REP_AYUDA`). No ayudar
   resta 15. Sin saldo no se puede ayudar, y un evento no puede dejarte en $0.
2. **Toda transferencia acepta solo el monto exacto que piden** (ni más ni menos),
   legítima o fraudulenta. En un fraude la pérdida es exactamente lo que piden.
3. **Reputación:** +5 al ayudar en un evento y +10 al empezar cada día nuevo (tope 100).
4. **Sin dinero para el gasto del día = derrota sin repetir.** Repetir dejaría el
   mismo saldo, así que no se ofrece; la pantalla explica qué faltó y cuánto, y
   solo permite empezar de nuevo.
5. **Temporizador agotado = "Camilo confía":** en OTP envía el código; en una
   transferencia paga lo pedido; si no alcanza el saldo, falla sin mover dinero.

## Criterios de aceptación
- [x] Umbral = 70% del máximo teórico (`_test_game.py`, test 18).
- [x] Partida perfecta = 800 XP, certificado, 0 derrotas (test 18).
- [x] Experta con margen +22%–+35% sobre el umbral (test 18).
- [x] Más habilidad → más certificados; azar puro → 0 (test 18).
- [x] Ayudar en un evento cuesta dinero y da reputación (test 19).
- [x] Temporizador agotado no rompe el juego (test 20).
- [x] La derrota explica su motivo y no ofrece repetir si no sirve (test 21).
- [x] Pagar la matrícula quedando en $0 no es derrota (test 22).
- [x] +10 de reputación al avanzar de día, con tope, incluido al repetir (test 23).
