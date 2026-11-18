"""
audio_manager.py — SFX sintetizados + música procedural + voz (pyttsx3 / .ogg).

Modo de voz (config.MODO_VOZ):
  "silencio"  → no hace nada
  "robot"     → pyttsx3 en hilo separado (requiere `pip install pyttsx3`)
  "grabado"   → busca assets/audio/voz/grabado/{key}.wav (o .ogg);
                si no existe, hace fallback a "robot"
                (los audios se crean con `python generar_voces.py`)
"""
import os
import math
import struct
import queue
import threading
import pygame
import config
import voces


class AudioManager:
    def __init__(self):
        self.activo = False
        self.sonidos = {}
        self.musica_segura = None
        self.musica_tension = None
        self.canal_segura = None
        self.canal_tension = None
        self.canal_voz = None
        self._fade = None
        self._pista_actual = None
        self._ultimo_hablado = None

        # Voz / TTS
        self._cola_voz = queue.Queue()
        self._tts_hilo = None
        self._tts_engine = None
        self._tts_disponible = False

        try:
            if pygame.mixer.get_init() is None:
                pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
            init = pygame.mixer.get_init()
            if init is None:
                print("[AUDIO] mixer no disponible")
                return
            self.sr, _, self._canales = init
            pygame.mixer.set_num_channels(8)
            pygame.mixer.set_reserved(3)
            self.canal_segura = pygame.mixer.Channel(0)
            self.canal_tension = pygame.mixer.Channel(1)
            self.canal_voz = pygame.mixer.Channel(2)
            self.activo = True
            print(f"[AUDIO] mixer OK · sr={self.sr} canales={self._canales}")
        except pygame.error as e:
            print(f"[AUDIO] mixer FALLÓ: {e}")
            return

        # SFX base
        self._gen_sfx("click", 880, 40, 0.15)
        self._gen_sfx("ok", 990, 120, 0.25)
        self._gen_sfx("err", 220, 180, 0.25)
        self._gen_sfx("notif", 660, 90, 0.18)
        self._gen_ding()
        self._gen_otp_ready()
        self._gen_cash()

        # Música
        self.musica_segura = self._gen_musica("segura")
        self.musica_tension = self._gen_musica("tension")

        dur = {k: round(s.get_length(), 3) for k, s in self.sonidos.items()}
        print(f"[AUDIO] sonidos generados (seg): {dur}")

        # Iniciar hilo de voz si aplica
        if config.MODO_VOZ in ("robot", "grabado"):
            self._iniciar_tts()

    # ============================================================
    # SFX
    # ============================================================

    def _gen_sfx(self, key, freq, ms, vol):
        sr = self.sr
        n = int(sr * ms / 1000)
        ataque = max(1, int(n * 0.05))
        buf = bytearray()
        for i in range(n):
            if i < ataque:
                env = i / ataque
            elif i > n - ataque:
                env = (n - i) / ataque
            else:
                env = 1.0
            v = int(vol * 32767 * math.sin(2 * math.pi * freq * i / sr) * env)
            buf += struct.pack("<hh", v, v)
        self.sonidos[key] = pygame.mixer.Sound(buffer=bytes(buf))

    def _gen_ding(self):
        """Chime de 3 notas (A5, C#6, E6) para abrir el panel pedagógico."""
        sr = self.sr
        ms = 700
        n = int(sr * ms / 1000)
        buf = bytearray()
        notas = [(880.0, 0.0), (1108.73, 0.10), (1318.51, 0.20)]
        for i in range(n):
            t = i / sr
            v = 0.0
            for freq, offset in notas:
                t_local = t - offset
                if 0 <= t_local < 0.5:
                    env = math.exp(-3 * t_local)
                    if t_local < 0.01:
                        env *= t_local / 0.01
                    v += math.sin(2 * math.pi * freq * t_local) * env
            v = int(max(-1.0, min(1.0, v * 0.55)) * 32767)
            buf += struct.pack("<hh", v, v)
        self.sonidos["ding"] = pygame.mixer.Sound(buffer=bytes(buf))

    def _gen_otp_ready(self):
        """Dos bleeps ascendentes, tono robótico. Para OTP generado."""
        sr = self.sr
        ms = 450
        n = int(sr * ms / 1000)
        buf = bytearray()
        for i in range(n):
            t = i / sr
            if t < 0.15:
                f = 1200.0
                env = 1.0 if t < 0.13 else max(0.0, (0.15 - t) / 0.02)
            elif t < 0.20:
                env = 0.0
                f = 1200.0
            else:
                f = 1600.0
                tt = t - 0.20
                env = 1.0 if tt < 0.13 else max(0.0, (0.25 - tt) / 0.02)
            v = int(max(-1.0, min(1.0, math.sin(2 * math.pi * f * t) * env * 0.30)) * 32767)
            buf += struct.pack("<hh", v, v)
        self.sonidos["otp_ready"] = pygame.mixer.Sound(buffer=bytes(buf))

    def _gen_cash(self):
        """Bling de caja registradora. Para confirmación de transferencia."""
        sr = self.sr
        ms = 550
        n = int(sr * ms / 1000)
        buf = bytearray()
        for i in range(n):
            t = i / sr
            # Mezcla de dos tonos altos con decaimiento
            v = (math.sin(2 * math.pi * 1800 * t) * math.exp(-8 * t) * 0.25 +
                 math.sin(2 * math.pi * 2400 * t) * math.exp(-12 * t) * 0.20)
            v = int(max(-1.0, min(1.0, v)) * 32767)
            buf += struct.pack("<hh", v, v)
        self.sonidos["cash"] = pygame.mixer.Sound(buffer=bytes(buf))

    def play(self, key):
        if not self.activo:
            return
        s = self.sonidos.get(key)
        if s:
            s.play()
        else:
            print(f"[AUDIO] ⚠️ sonido inexistente: '{key}'")

    # ============================================================
    # Música
    # ============================================================

    def _gen_musica(self, tipo):
        sr = self.sr
        dur = 4.0
        n = int(sr * dur)
        buf = bytearray()

        if tipo == "segura":
            notas = [261.63, 329.63, 392.00, 523.25]
            vol_nota = 0.12
            vol_pad = 0.05
            pad_freq = 130.81
        else:
            notas = [220.00, 261.63, 277.18, 311.13]
            vol_nota = 0.10
            vol_pad = 0.04
            pad_freq = 110.00

        dur_nota = dur / len(notas)
        for i in range(n):
            t = i / sr
            v = 0.0
            for j, f in enumerate(notas):
                t_local = t - j * dur_nota
                if 0 <= t_local < dur_nota:
                    env = 1.0
                    ataque = 0.08
                    release = 0.15
                    if t_local < ataque:
                        env = t_local / ataque
                    elif t_local > dur_nota - release:
                        env = max(0.0, (dur_nota - t_local) / release)
                    v += vol_nota * env * math.sin(2 * math.pi * f * t)
            v += vol_pad * math.sin(2 * math.pi * pad_freq * t)
            v = int(max(-1.0, min(1.0, v)) * 32767)
            buf += struct.pack("<hh", v, v)

        return pygame.mixer.Sound(buffer=bytes(buf))

    def cambiar_musica(self, pista, fade_ms=None):
        if not self.activo or pista == self._pista_actual:
            return
        fade_ms = fade_ms or config.MUSICA_FADE_MS

        if self._pista_actual is None:
            canal = self._canal_de(pista)
            canal.set_volume(self._vol_de(pista))
            canal.play(self._sonido_de(pista), loops=-1)
            self._pista_actual = pista
            return

        self._fade = {
            "desde": self._pista_actual,
            "hacia": pista,
            "progreso": 0.0,
            "total": fade_ms,
            "iniciado": False,
        }
        self._pista_actual = pista

    def _canal_de(self, pista):
        return self.canal_segura if pista == "segura" else self.canal_tension

    def _sonido_de(self, pista):
        return self.musica_segura if pista == "segura" else self.musica_tension

    def _vol_de(self, pista):
        return (config.VOL_MUSICA_SEGURA if pista == "segura"
                else config.VOL_MUSICA_TENSION)

    def actualizar(self, dt_ms):
        if not self.activo or self._fade is None:
            return
        self._fade["progreso"] += dt_ms
        p = min(1.0, self._fade["progreso"] / self._fade["total"])

        if not self._fade["iniciado"]:
            canal = self._canal_de(self._fade["hacia"])
            canal.set_volume(0.0)
            canal.play(self._sonido_de(self._fade["hacia"]), loops=-1)
            self._fade["iniciado"] = True

        v_old = (1 - p) * self._vol_de(self._fade["desde"])
        v_new = p * self._vol_de(self._fade["hacia"])
        self._canal_de(self._fade["desde"]).set_volume(v_old)
        self._canal_de(self._fade["hacia"]).set_volume(v_new)

        if p >= 1.0:
            self._canal_de(self._fade["desde"]).stop()
            self._fade = None

    def detener_musica(self):
        if not self.activo:
            return
        if self.canal_segura:
            self.canal_segura.stop()
        if self.canal_tension:
            self.canal_tension.stop()
        self._pista_actual = None
        self._fade = None

    # ============================================================
    # Voz (TTS / grabado)
    # ============================================================

    def _iniciar_tts(self):
        try:
            import pyttsx3
        except ImportError:
            print("[AUDIO] pyttsx3 no instalado (pip install pyttsx3)")
            return
        try:
            self._tts_engine = pyttsx3.init()
            # Antes se buscaba "es" dentro del id, que en Windows es una ruta del
            # registro con la palabra "voices": coincidía con todas y ganaba la
            # última voz (en inglés). Ver voces.es_voz_espanola.
            voz = voces.elegir_voz(self._tts_engine.getProperty("voices"))
            if voz is not None:
                self._tts_engine.setProperty("voice", voz.id)
            else:
                print("[AUDIO] No hay voz en español instalada: la voz 'robot' "
                      "sonará en otro idioma")
            self._tts_engine.setProperty("rate", 150)
            self._tts_hilo = threading.Thread(target=self._tts_worker, daemon=True)
            self._tts_hilo.start()
            self._tts_disponible = True
            print(f"[AUDIO] pyttsx3 iniciado")
        except Exception as e:
            print(f"[AUDIO] pyttsx3 falló: {e}")

    def _tts_worker(self):
        while True:
            try:
                item = self._cola_voz.get(timeout=1.0)
            except queue.Empty:
                continue
            if item is None:
                break
            texto = item
            try:
                self._tts_engine.say(texto)
                self._tts_engine.runAndWait()
            except Exception:
                pass

    def hablar(self, key, texto):
        """Reproduce una frase. Según config.MODO_VOZ."""
        self._ultimo_hablado = (key, texto)
        if config.MODO_VOZ == "silencio":
            return

        if config.MODO_VOZ == "grabado":
            ruta = voces.ruta_audio(key)
            if ruta and self.canal_voz is not None:
                try:
                    self.canal_voz.play(pygame.mixer.Sound(ruta))
                    return
                except pygame.error:
                    pass
            # fallback a robot

        if self._tts_disponible and self._tts_hilo is not None:
            self._cola_voz.put(texto)

    def hablar_varios(self, items):
        """Dice varias frases una tras otra: [(clave, texto), ...].
        Interrumpe lo que esté sonando."""
        self.detener_voz()
        if not items:
            return
        self._ultimo_hablado = items[-1]
        if config.MODO_VOZ == "silencio":
            return
        for i, (key, texto) in enumerate(items):
            ruta = voces.ruta_audio(key) if config.MODO_VOZ == "grabado" else None
            if ruta and self.canal_voz is not None:
                try:
                    sonido = pygame.mixer.Sound(ruta)
                    if i == 0 or not self.canal_voz.get_busy():
                        self.canal_voz.play(sonido)
                    else:
                        self.canal_voz.queue(sonido)
                    continue
                except pygame.error:
                    pass
            if self._tts_disponible and self._tts_hilo is not None:
                self._cola_voz.put(texto)

    def detener_voz(self):
        """Vacía la cola de TTS y detiene la reproducción de grabaciones."""
        while not self._cola_voz.empty():
            try:
                self._cola_voz.get_nowait()
            except queue.Empty:
                break
        if self.canal_voz:
            self.canal_voz.stop()