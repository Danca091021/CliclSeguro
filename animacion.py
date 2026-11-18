"""animacion.py — Línea de tiempo de la animación explicativa (sin pygame).
Ver specs/15_animacion.md.

La animación es una secuencia de ESCENAS (datos.ANIMACION_ESCENAS). Cada escena
tiene una frase de narración con su audio, y dura lo que dura ese audio más una
pausa (PAD_MS), o su `min_ms` si es mayor: así el dibujo y la voz quedan
sincronizados aunque cambies un texto o la voz.

Este módulo solo calcula tiempos; dibujar las escenas es trabajo de escenas.py.
"""


class Animacion:
    PAD_MS = 700          # pausa tras terminar de hablar, antes de la siguiente escena

    def __init__(self, escenas, duraciones_voz_ms):
        """escenas: lista de dicts (id, voz, min_ms…);
        duraciones_voz_ms: lo que dura el audio de cada escena, en ms."""
        assert len(escenas) == len(duraciones_voz_ms)
        self.escenas = list(escenas)
        self.voz_ms = [int(v) for v in duraciones_voz_ms]
        self.duraciones = [max(int(e.get("min_ms", 0)), v + self.PAD_MS)
                           for e, v in zip(self.escenas, self.voz_ms)]
        self.inicios = []
        t = 0
        for d in self.duraciones:
            self.inicios.append(t)
            t += d
        self.total = t

    def escena_en(self, t_ms):
        """-> (indice, t_local_ms, duracion_ms) de la escena que corresponde a t_ms.
        Pasado el final se queda en el último instante de la última escena."""
        if not self.escenas:
            return (0, 0, 0)
        if t_ms >= self.total:
            i = len(self.escenas) - 1
            return (i, self.duraciones[i], self.duraciones[i])
        t_ms = max(0, t_ms)
        for i in range(len(self.escenas) - 1, -1, -1):
            if t_ms >= self.inicios[i]:
                return (i, t_ms - self.inicios[i], self.duraciones[i])
        return (0, 0, self.duraciones[0])

    def terminada(self, t_ms):
        return t_ms >= self.total

    def progreso_voz(self, i, t_local_ms):
        """0..1: cuánto de la frase ya se dijo (ilumina los subtítulos)."""
        v = self.voz_ms[i]
        return 1.0 if v <= 0 else max(0.0, min(1.0, t_local_ms / v))
