# Spec 09 — Mapa de pantallas y transiciones

> Actualizado en el Bloque F al estado real del código (`main.py` + `ui.py`).
> Los mockups `specs/mockups/01…13` son el diseño original; las pantallas
> añadidas en los Bloques D–F no tienen mockup (marcadas con —).

## Pantallas (estados de `main.py`)

| Estado                     | Función en `ui.py`        | Mockup | Tipo              |
|----------------------------|---------------------------|--------|-------------------|
| MENU                       | `draw_menu`               | 01     | Pantalla completa |
| CINEMATICA                 | `draw_cinematica`         | —      | Pantalla completa (spec 10) |
| ANIMACION                  | `escenas.draw_animacion`  | —      | Pantalla completa (spec 15) |
| DIA_INTRO                  | `draw_dia_intro`          | —      | Pantalla completa (spec 13) |
| GASTOS_DIA                 | `draw_gastos_dia`         | —      | Pantalla completa |
| HOME                       | `draw_home`               | 02     | Pantalla completa |
| MATRICULA_PAGO             | `draw_matricula_pago`     | —      | Pantalla completa |
| MODAL_APP (ajustes, banco…)| `draw_modal_app`          | 06     | Modal             |
| MESSAGE_LIST               | `draw_message_list`       | —      | Pantalla completa (scroll) |
| CHAT                       | `draw_chat`               | 03     | Pantalla completa |
| MODAL (remitente/enlace/contactos) | `draw_modal`      | 04, 05 | Modal             |
| VERIFICACION               | `draw_verificacion`       | —      | Pantalla completa |
| BANCO_OTP                  | `draw_banco_otp`          | —      | Pantalla completa |
| BANCO_TRANSFERENCIA        | `draw_banco_transferencia`| —      | Pantalla completa |
| FEEDBACK (ok / error)      | `draw_feedback`           | 07, 08 | Overlay           |
| PANEL                      | `draw_panel`              | 09     | Pantalla completa |
| RESUMEN                    | `draw_resumen`            | 10     | Pantalla completa |
| DERROTA                    | `draw_derrota`            | 11     | Pantalla completa |
| INSTRUCCIONES              | `draw_instrucciones`      | 12     | Pantalla completa (scroll) |
| APRENDIZAJES               | `draw_aprendizajes`       | —      | Pantalla completa (scroll) |
| CREDITOS                   | `draw_creditos`           | —      | Pantalla completa |
| FIN_SEMANA_SIN_MATRICULA / FIN_SEMANA_PARCIAL | `draw_fin_semana` | — | Pantalla completa |
| CERTIFICADO                | `draw_certificado`        | 13     | Pantalla completa |

Los mockups 04 y 05 (remitente / enlace) y las apps del home (06) se
implementan como modales; la lógica de qué mostrar vive en `game.py`.

## Flujo principal

```
MENU ─Jugar─► ANIMACION* ─► CINEMATICA* ─► DIA_INTRO ─► [GASTOS_DIA**] ─► HOME
                                                 │
        ┌──────────────── Mensajes ──────────────┤── apps ──► MODAL_APP ─► HOME
        ▼                                        └── viernes ► MATRICULA_PAGO ─► HOME
   MESSAGE_LIST ──abrir──► CHAT ──herramienta──► MODAL ─► CHAT
        ▲                    │ ──Verificar────► VERIFICACION ─► CHAT
        │                    │ ──Confiar (OTP)► BANCO_OTP ──┐
        │                    │ ──Confiar (transf.)► BANCO_TRANSFERENCIA ──┤
        │                    │ ──otra acción──┐                           │
        │                    ▼                ▼                           ▼
        │                 (derrota?)──sí──► DERROTA              FEEDBACK
        │                                                          │
        │                                                  ¿consejo? ─sí─► PANEL
        └────────── quedan incidentes ◄────────────────────────────┴───────┘
                              │ nivel completado
                              ▼
                          RESUMEN ─► DIA_INTRO (siguiente nivel) │ CERTIFICADO (nivel 4)
                                  └► FIN_SEMANA_SIN_MATRICULA / FIN_SEMANA_PARCIAL

 * solo la primera partida de la sesión y si SKIP_INTRO = False (spec 10)
** si el nivel tiene gasto diario (config.GASTOS_DIARIOS); sin fondos → DERROTA
```

## Transiciones

| De                 | A                              | Trigger |
|--------------------|--------------------------------|---------|
| MENU               | ANIMACION → CINEMATICA / DIA_INTRO | "Jugar" (o Enter/Espacio); animación e historia solo la primera vez |
| MENU               | ANIMACION → MENU               | "Ver animación" |
| MENU               | INSTRUCCIONES / CREDITOS       | Botones del menú |
| INSTRUCCIONES      | APRENDIZAJES                   | "Ver mis aprendizajes" |
| CINEMATICA         | DIA_INTRO (Domingo)            | Tras la pantalla 5, "Saltar intro" o Esc |
| DIA_INTRO          | GASTOS_DIA / HOME              | Tocar (1.º salta la animación, 2.º empieza el día) |
| GASTOS_DIA         | HOME / DERROTA                 | Pagar gasto / saldo insuficiente |
| HOME               | MESSAGE_LIST                   | App Mensajes |
| HOME               | MODAL_APP                      | Cualquier otra app |
| HOME               | MATRICULA_PAGO                 | "Pedir préstamo" (viernes, sin $500) |
| MESSAGE_LIST       | CHAT / HOME                    | Abrir mensaje / botón ⌂ |
| CHAT               | MODAL / VERIFICACION           | Herramienta / Verificar |
| CHAT               | BANCO_OTP / BANCO_TRANSFERENCIA| Confiar en incidente con esa interacción |
| CHAT               | FEEDBACK                       | Confiar/Ignorar/Bloquear/Reportar |
| CHAT               | DERROTA                        | Un recurso llegó a 0 (**la derrota gana**) |
| BANCO_*            | CHAT / FEEDBACK / DERROTA      | Cancelar / enviar o confirmar |
| FEEDBACK           | PANEL                          | Si hay consejo desbloqueado |
| FEEDBACK / PANEL   | MESSAGE_LIST / RESUMEN         | Quedan incidentes normales / nivel completo (los eventos son opcionales) |
| RESUMEN            | DIA_INTRO / CERTIFICADO        | Siguiente nivel / nivel 4 superado |
| RESUMEN            | FIN_SEMANA_*                   | Sin matrícula o XP < umbral (spec 06) |
| DERROTA, FIN_SEMANA_*, RESUMEN | HOME o GASTOS_DIA (mismo nivel) | "Repetir" (restaura priv/rep/dinero/XP del inicio del nivel). **DERROTA por no poder pagar el gasto no ofrece "Repetir"**: solo "Empezar de nuevo" |
| CHAT | FEEDBACK / DERROTA | Temporizador agotado (N2+): resolución automática ("Camilo confía"), también en OTP y transferencias |
| DERROTA, FIN_SEMANA_*, RESUMEN, CERTIFICADO | MENU | "Menú" (reinicia la partida) |

## Reglas de navegación

1. **Modal bloquea el chat:** con un modal abierto, las acciones y herramientas no responden.
2. **Los modales no abren otros modales.**
3. **El feedback siempre precede al siguiente incidente.**
4. **Derrota siempre gana:** si una acción llevaría a RESUMEN pero un recurso llegó a 0, va a DERROTA.
5. **El timer (N2+) solo corre en CHAT;** Verificar y los flujos bancarios lo pausan.
6. **Dibujar antes de procesar eventos** (`last_buttons` siempre coincide con lo que se ve).
7. **Listas con scroll:** `gfx.clip(viewport)` + blit simple de una superficie **opaca**; nunca `blit(..., area=)`.
8. **Hover:** `ui.set_mouse()` una vez por frame (posición ya en coordenadas lógicas); `_btn` dibuja borde azul al pasar el mouse.
9. **Tutorial guiado (spec 14):** es una *capa*, no un estado: se dibuja sobre la pantalla real y reemplaza los botones activos por solo el resaltado (más "Siguiente" y "Saltar tutorial").
10. **Dibujo y escala:** `ui.py` dibuja en coordenadas lógicas 400×700 con `gfx`; la ventana mide 400·S × 700·S píxeles reales y el ratón se convierte con `gfx.a_logico`. Ver spec 12.

## Criterios de aceptación

- [x] El jugador nunca queda atrapado en una pantalla sin salida (verificado por flujo).
- [x] Ningún modal abre otro modal.
- [x] El feedback precede al siguiente incidente.
- [x] La derrota tiene prioridad sobre el resumen.
- [ ] "Volver al menú" a ≤1 clic desde cualquier pantalla completa: **no se cumple hoy**;
      desde CHAT/HOME hay que llegar a RESUMEN, DERROTA o FIN_SEMANA. Pendiente de decidir.
- [x] Fundido de 200 ms al entrar a pantallas completas (spec 13).
