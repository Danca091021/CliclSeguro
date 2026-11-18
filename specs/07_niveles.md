# Spec 07 — Progresión de niveles

## Nivel 1 — Lunes: "Bienvenida universitaria"
- Objetivo: aprender acciones y herramientas sin perder recursos.
- Incidentes: **6** (3 legítimos, 3 fraude).
- Tipos: aviso universidad, mensaje de mamá, mensaje de Valentina,
  sorteo falso, correo con errores, oferta de premio con link.
- Tutorial: sí. Se resaltan las señales de alerta.
- Temporizador: no.

## Nivel 2 — Miércoles: "La llamada del pánico"
- Objetivo: resistir urgencia, no dar códigos ni datos.
- Incidentes: **8** (3 legítimos, 5 fraude).
- Tipos: soporte falso WhatsApp (OTP), falso banco, multa falsa,
  aviso universidad, mensaje legítimo amigo, promo legítima banco,
  doble intento de estafa.
- Tutorial: no. Temporizador: **sí** (20 s).
- Se desbloquean Ajustes de seguridad (2FA + perfil privado → +15 Privacidad).

## Nivel 3 — Jueves: "Círculo cercano vulnerado"
- Objetivo: gestionar ataques relacionales y acoso.
- Incidentes: **8** (4 legítimos, 4 fraude).
- Tipos: Valentina suplantada pide dinero, perfil falso acosador,
  foto editada, mensajes legítimos mezclados.
- Mecánica nueva: "Llamar a Valentina" para verificar por voz.
- Se desbloquea CAI Virtual (reportar con evidencia = +10 extra).

## Nivel 4 — Viernes: "Examen final"
- Objetivo: aplicar todo sin pistas.
- Incidentes: **10** (5 legítimos, 5 fraude).
- Tipos: todos los anteriores, mezclados, sin señales resaltadas.
- Temporizador: sí, en todos los críticos.
- Al terminar: informe final (#13).

## Desbloqueo entre niveles
- Nivel 2 disponible si Nivel 1 terminado con 3 barras > 0.
- Nivel 3 disponible si Nivel 2 terminado con 3 barras > 0.
- **Nivel 4 solo si Nivel 3 terminó con las 3 barras > 30.**

## Criterios de aceptación
- [ ] Cada nivel tiene al menos 3 mensajes legítimos.
- [ ] Los 4 tipos de ataque del GDD están representados.
- [ ] El Nivel 4 nunca muestra pistas amarillas.
- [ ] Al terminar cada nivel se muestra el resumen (#10).