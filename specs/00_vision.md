# Spec 00 — Visión del producto

## Qué es Clic Seguro
Simulador de celular en Python/Pygame donde el jugador es Camilo, un
universitario de primer semestre que debe distinguir mensajes reales
de intentos de fraude durante una semana.

## Para quién
Jóvenes de 15 a 25 años, especialmente estudiantes de primer semestre
universitario que estrenan celular y cuentas bancarias.

## Qué NO es
- No es un cuestionario disfrazado.
- No es un curso teórico con videos largos.
- No es un juego de acción ni de reflejos.
- No es un sitio web ni una app móvil real.

## Promesa pedagógica
Al terminar, el jugador debe poder:
1. Reconocer las 4 señales de alerta (urgencia, petición de código,
   enlace/número que no coincide, oferta demasiado buena).
2. Verificar por otro canal antes de actuar.
3. Aplicar el protocolo ante suplantación y acoso (evidencia, bloquear,
   reportar, contarle a alguien).
4. Configurar seguridad básica (2FA, perfil privado, dispositivos).

## Criterios de aceptación
- [ ] Una partida completa dura entre 20 y 30 minutos.
- [ ] El jugador puede terminar el juego sin haber leído instrucciones
      previas (gracias al tutorial del Nivel 1).
- [ ] El 100% de los incidentes corresponde a un tipo real de ataque
      documentado en la problemática (no inventados).
- [ ] El juego corre offline, en Windows, sin instalación adicional
      más allá de Python + Pygame.