"""generar_voces.py — Crea los audios de voz del juego (una sola vez).

    python generar_voces.py              # genera los que faltan o cambiaron
    python generar_voces.py --forzar     # regenera todos
    python generar_voces.py --listar     # muestra qué se dice (sin generar)
    python generar_voces.py --verificar  # ¿faltan audios? (código de salida 1 si sí)
    python generar_voces.py --velocidad -2   # -10 (lento) .. 10 (rápido); por defecto -1

Usa la voz en español de Windows (por ejemplo "Microsoft Helena") vía PowerShell:
no necesita internet ni instalar nada. Crea un .wav por frase en
assets/audio/voz/grabado/ y un manifest.json que recuerda con qué texto se
generó cada uno: si cambias un texto en datos.py, vuelve a correr el script y solo
regenera ese audio.

Para usar grabaciones propias o una voz mejor: reemplaza cualquier archivo por
uno con el mismo nombre (.wav u .ogg) y no vuelvas a correr con --forzar.
La lista de frases está en voces.py.
"""
import argparse
import json
import os
import subprocess
import sys
import tempfile

import voces

_POWERSHELL = r"""
param([string]$Json, [int]$Velocidad = -1)
Add-Type -AssemblyName System.Speech
$s = New-Object System.Speech.Synthesis.SpeechSynthesizer
$voz = $s.GetInstalledVoices() | Where-Object { $_.Enabled -and $_.VoiceInfo.Culture.Name -like 'es-*' } | Select-Object -First 1
if (-not $voz) { Write-Error 'No hay una voz en espanol instalada en Windows'; exit 2 }
$s.SelectVoice($voz.VoiceInfo.Name)
$s.Rate = $Velocidad
Write-Output ('VOZ ' + $voz.VoiceInfo.Name)
$items = Get-Content -Raw -Encoding UTF8 $Json | ConvertFrom-Json
foreach ($it in $items) {
    $s.SetOutputToWaveFile($it.path)
    $s.Speak($it.text)
    $s.SetOutputToNull()
    Write-Output ('OK ' + $it.clave)
}
$s.Dispose()
"""


def main():
    ap = argparse.ArgumentParser(description="Genera los audios de voz del juego")
    ap.add_argument("--forzar", action="store_true", help="regenerar todos")
    ap.add_argument("--listar", action="store_true", help="solo mostrar las frases")
    ap.add_argument("--verificar", action="store_true", help="solo comprobar si faltan")
    ap.add_argument("--velocidad", type=int, default=-1, help="-10 .. 10")
    args = ap.parse_args()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    m = voces.manifest()
    if args.listar:
        for clave, texto in m.items():
            print(f"{clave:34} {texto}")
        print(f"\n{len(m)} frases")
        return 0

    faltan, obsoletos = voces.estado_audios()
    if args.verificar:
        print(f"{len(m) - len(faltan) - len(obsoletos)}/{len(m)} audios al día; "
              f"faltan {len(faltan)}, desactualizados {len(obsoletos)}")
        return 1 if (faltan or obsoletos) else 0

    pendientes = list(m) if args.forzar else faltan + obsoletos
    if not pendientes:
        print(f"Todo al día: {len(m)} audios en {voces.CARPETA}")
        return 0
    if sys.platform != "win32":
        print("Este script usa la voz de Windows. En otro sistema, graba los audios "
              "a mano con los nombres de `--listar` (.wav u .ogg).")
        return 2

    os.makedirs(voces.CARPETA, exist_ok=True)
    items = [{"clave": c, "text": m[c],
              "path": os.path.join(voces.CARPETA, c + ".wav")} for c in pendientes]
    with tempfile.TemporaryDirectory() as tmp:
        ps1 = os.path.join(tmp, "generar.ps1")
        js = os.path.join(tmp, "items.json")
        with open(ps1, "w", encoding="utf-8-sig") as f:     # BOM: PowerShell 5 lee UTF-8
            f.write(_POWERSHELL)
        with open(js, "w", encoding="utf-8") as f:
            json.dump(items, f, ensure_ascii=False)
        print(f"Generando {len(items)} audios...")
        r = subprocess.run(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass",
             "-File", ps1, "-Json", js, "-Velocidad", str(args.velocidad)],
            capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode != 0:
        print("Falló la generación:", (r.stderr or r.stdout).strip()[:400])
        return r.returncode

    voz = next((l[4:] for l in r.stdout.splitlines() if l.startswith("VOZ ")), "?")
    huellas = voces.leer_huellas()
    hechos = 0
    for it in items:
        if os.path.isfile(it["path"]) and os.path.getsize(it["path"]) > 1000:
            huellas[it["clave"]] = voces.huella(it["text"])
            hechos += 1
    with open(os.path.join(voces.CARPETA, voces.ARCHIVO_HUELLAS), "w",
              encoding="utf-8") as f:
        json.dump(huellas, f, indent=1, sort_keys=True)
    print(f"Listo: {hechos}/{len(items)} audios con la voz «{voz}» en {voces.CARPETA}")
    return 0 if hechos == len(items) else 1


if __name__ == "__main__":
    sys.exit(main())
