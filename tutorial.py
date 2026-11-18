"""tutorial.py — Motor del tutorial guiado (sin pygame). Ver specs/14_tutorial.md.

El tutorial recorre una lista de PASOS (datos.TUTORIAL_PASOS) sobre las pantallas
reales del juego. Cada paso dice en qué pantalla (estado de main.py) ocurre, qué
elemento se resalta (un botón o una "zona" que ui.py declara) y de qué tipo es:

  "info"  explica algo; solo se puede pulsar "Siguiente".
  "click" obliga a pulsar EL botón resaltado (`foco`); cualquier otro clic se ignora.

Este módulo solo decide qué clics se permiten y cuándo se avanza; dibujar el
resaltado y el globo de texto es trabajo de ui.draw_tutorial.

Seguridad contra atascos: si el juego está en una pantalla distinta a la que el
paso espera, el tutorial se "pausa" (paso_en() devuelve None) y el juego queda libre.
"""


class Tutorial:
    def __init__(self, pasos):
        self.pasos = list(pasos)
        self.indice = 0
        self.terminado = not self.pasos

    @property
    def total(self):
        return len(self.pasos)

    @property
    def paso(self):
        """El paso actual, o None si ya terminó."""
        return None if self.terminado else self.pasos[self.indice]

    def paso_en(self, estado):
        """El paso actual SOLO si corresponde a la pantalla `estado`."""
        p = self.paso
        return p if (p is not None and p["estado"] == estado) else None

    def permite(self, estado, boton):
        """¿Se permite pulsar `boton` ahora? Si el tutorial no está activo en esta
        pantalla, el juego es libre."""
        p = self.paso_en(estado)
        if p is None:
            return True
        return p["tipo"] == "click" and boton == p["foco"]

    def click(self, estado, boton):
        """Registra un clic ya ejecutado por el juego. Si era el botón que el paso
        pedía, avanza y devuelve True."""
        if not self.permite(estado, boton):
            return False
        p = self.paso_en(estado)
        if p is None or p["tipo"] != "click":
            return False
        self._avanzar()
        return True

    def siguiente(self):
        """Pulsó "Siguiente" en un paso informativo."""
        p = self.paso
        if p is not None and p["tipo"] == "info":
            self._avanzar()

    def saltar(self):
        self.terminado = True

    def _avanzar(self):
        self.indice += 1
        if self.indice >= len(self.pasos):
            self.terminado = True
