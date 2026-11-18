# Spec 01 — Mecánicas y balance

## Ciclo de juego
notificación → investigar (opcional) → acción → consecuencia → siguiente

## Recursos
| Recurso     | Inicial | Rango      | Baja por                     | Sube por                          |
|-------------|---------|------------|------------------------------|-----------------------------------|
| Privacidad  | 100     | 0–100      | Dar código/datos, abrir link | Ajustes (2FA+perfil privado) +15  |
| Saldo       | $800    | 0–sin tope | Gastos diarios, matrícula, estafas | Préstamo de mamá ($50 / $100) |
| Reputación  | 100     | 0–100      | Cuenta robada, callar acoso, no ayudar a un familiar (−15) | Ayudar en un evento familiar (+5); cada día nuevo (+10) |
| XP          | 0       | sin tope   | (nunca baja)                 | Decisiones correctas              |

## Sistema de puntos (opción D)

| Tipo de incidente | Base | +Herramienta | +Reportar | Máximo por incidente |
|-------------------|------|--------------|-----------|----------------------|
| Fraude (15)       | 15   | +5           | +10 (N3 y N4, si REPORTAR es la correcta) | **30** |
| Legítimo (18)     | 20   | +5           | No aplica | **25**               |

- Máximo teórico: **800** (lo calcula `Game.puntaje_maximo()`; no incluye eventos,
  que no dan XP). Sin usar ninguna herramienta el máximo es 635.
- Certificado (victoria): ≥ **560 puntos (70% del máximo)** **y matrícula pagada**.
- "Solo herramienta usada" cuenta como +5 una vez por incidente.
- Las herramientas son opcionales: sin usar ninguna, la partida perfecta suma 635
  (+13% sobre el umbral, unos 3–4 errores de margen). Ver spec 11.

## Nivel 0 (Domingo): práctica guiada
Dos mensajes: el de mamá (puntúa: 20 + 5 por herramienta) y uno de **práctica** (`es_tutorial`) que
**no da XP, no penaliza y no cuenta para el máximo** (sigue en 800). Ver spec 14.

## Acciones y cuándo son correctas
| Acción    | Correcta cuando                                  |
|-----------|--------------------------------------------------|
| Confiar   | Mensaje legítimo verificado                      |
| Verificar | Siempre es segura; ideal ante duda               |
| Ignorar   | Spam/oferta falsa sin acoso ni suplantación      |
| Bloquear  | Remitente insiste, acosa, o ya fue identificado  |
| Reportar  | Suplantación, acoso, estafa confirmada           |

## Qué cuesta cada respuesta (regla corregida en el Bloque N)
Antes, cualquier respuesta fuera de la lista de aceptadas aplicaba el **daño completo de la
estafa** aunque el jugador no hubiera enviado nada (p. ej. bloquear a la "Valentina hackeada"
descontaba los $50 de una transferencia que nunca hizo). Ahora:

| Situación | Resultado |
|-----------|-----------|
| **Confiar** en una estafa (o el temporizador confía por ti) | Caíste: aplica el daño del mensaje (privacidad, dinero, reputación) |
| **Ignorar / Bloquear / Reportar** una estafa y era una respuesta aceptada | Correcto: puntos, sin pérdidas |
| Ignorar / Bloquear una estafa **sin ser la mejor respuesta** (p. ej. no verificaste a un familiar suplantado) | **"No caíste, pero…"**: no pierdes nada, no sumas puntos, se desbloquea el consejo y se explica qué era lo ideal |
| **Verificar primero** (llamada, canal oficial o búsqueda) y luego ignorar, bloquear o reportar una estafa | Correcto: ya sabes que es falso |
| Ignorar a una **persona real** (mensaje legítimo) | Error: pierdes reputación (rechazaste a alguien real) |
| **Acoso** (`penaliza_ignorar`): ignorar | Error: callar *es* el error (−25 reputación); bloquear o reportar son correctos; verificar no justifica callar |

Reportar un fraude cuenta siempre como correcto. En el Jueves y el Viernes suma +10 solo si
reportar era la respuesta diseñada (acoso, sorteos).

## Herramientas (gratis, antes de decidir)
1. **Inspeccionar remitente** → muestra 4 señales (contacto, antigüedad, reportes, verificado).
2. **Analizar enlace** → descompone URL y compara con dominio oficial.
3. **Contactos / Llamar** → confirma voz o compara con agenda.

Usar cualquiera antes de acertar = +5 pts. Las herramientas **no consumen turno**.

## Temporizador de urgencia (Nivel 2+)
- Duración: **20 s** en incidentes críticos.
- Al agotarse: se aplica `CONFIAR` automáticamente.
- `VERIFICAR` **detiene** el temporizador (la pausa es la lección).

## Condiciones de victoria/derrota
- **Victoria total:** terminar N4 con 3 recursos > 0, matrícula pagada y ≥ 560 pts.
- **Victoria parcial** ("Casi lo logras"): matrícula pagada pero < 560 pts.
- **Sin matrícula** (regaño de mamá): llegar al viernes sin poder pagar los $500.
- **Derrota de nivel:** cualquier recurso = 0 → repite el nivel. Excepción: el
  Viernes con la matrícula ya pagada, quedar en $0 no es derrota.
- **No poder pagar el gasto del día** también es derrota, pero **no se ofrece
  repetir** (el saldo sería el mismo): la pantalla explica qué faltó y solo
  permite empezar una partida nueva.
- **La pantalla de derrota explica el motivo** (privacidad, saldo, reputación o gasto).
- **Al repetir un nivel** se restauran Privacidad, Reputación, Saldo **y XP** a
  como estaban al empezarlo (así repetir no permite sumar puntos dos veces).
- **Transacciones persistentes:** el gasto diario, la matrícula y el préstamo
  ajustan ese punto de partida al ocurrir; repetir el nivel **no los reembolsa
  ni los cobra otra vez**. Los eventos aleatorios se descartan al repetir.

## Transferencias y eventos familiares
- **Monto exacto:** toda transferencia (legítima o fraudulenta) acepta solo el monto
  que piden, ni más ni menos. La pantalla del banco muestra "Te piden $X".
- **Evento familiar** (máx. 1 por nivel, 60%, nunca en el Nivel 0): un familiar pide
  dinero (`monto_solicitado`, $30–$80). **Ayudar cuesta ese dinero** y devuelve +5 de
  reputación (tope 100); no da XP. **No ayudar resta 15 de reputación.** Sin saldo
  no se puede ayudar, y un evento nunca puede dejarte en $0. Ayudar puede poner en
  riesgo la matrícula: es la decisión del jugador.
- **Temporizador agotado:** Camilo "confía". En OTP envía el código; en una
  transferencia paga lo pedido; si no alcanza el saldo, falla sin mover dinero.

## Criterios de aceptación
- [ ] La suma de puntos de un nivel coincide con el desglose mostrado.
- [x] Repetir un nivel restaura saldo y XP sin reembolsar gastos (`_test_game.py`, test 17).
- [ ] El temporizador nunca se muestra en Nivel 1.
- [ ] Ningún incidente tiene dos acciones como respuesta correcta única
      (puede tener varias aceptables, pero la "correcta" es una).