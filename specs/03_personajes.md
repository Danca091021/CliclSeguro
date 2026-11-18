# Spec 03 — Personajes

## Camilo (protagonista)
- Estudiante de 18 años, primer semestre de Ingeniería de Sistemas.
- Aparece como avatar flat en: pantalla de inicio (pequeño), resumen
  del día, informe final.
- Estilo: círculo de color, cabello simple, sin rasgos faciales
  detallados (estilo Headspace).

## Personajes legítimos
| Nombre       | Rol                        | Canal           | Avatar              |
|--------------|----------------------------|-----------------|---------------------|
| Mamá         | Contacto real              | WhatsApp        | Círculo coral       |
| Valentina    | Mejor amiga                | WhatsApp/IG     | Círculo violeta     |
| Universidad  | Institución                | Correo/WhatsApp | Escudo azul         |
| CAI Virtual  | Canal de denuncia          | App             | Escudo rojo         |

## Estafadores — REGLA CLAVE
**Imitan al legítimo.** No tienen íconos genéricos. La señal está en
los detalles del remitente, no en el logo.

| Suplantan a      | Se ve como        | Señal detectable                              |
|------------------|-------------------|-----------------------------------------------|
| Soporte WhatsApp | Ícono verde +95% oficial | +1 555 (internacional), cuenta 2 días, no verificado |
| Banco Nacional   | Logo azul de banco       | Número no coincide con canal oficial          |
| Valentina        | Su foto real             | Cuenta creada hace horas (visible al llamar)  |
| Tienda de ofertas| Foto atractiva           | Dominio con typo (`banc0lombia.com`)          |
| Perfil anónimo   | Avatar genérico          | Único caso donde la sospecha es visible       |

## Expresiones de Camilo (para pantalla de resultados)
- **Contento:** ojos curvos, boca sonriente.
- **Neutral:** ojos rectos, boca recta.
- **Preocupado:** cejas juntas, boca curva hacia abajo.

## Criterios de aceptación
- [ ] Ningún incidente de fraude usa un ícono "obviamente falso".
- [ ] La diferencia entre legítimo y fraude siempre es detectable con
      al menos una herramienta.
- [ ] Los personajes se dibujan con primitivas Pygame (no PNGs externos).