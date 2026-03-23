import os
import urllib.request
import urllib.error

# ── Constantes ────────────────────────────────────────────────────────────────
CLOUD_METADATA_URL  = "http://169.254.169.254/metadata/instance?api-version=2021-02-01"
VALID_VENDORS       = {"AuthenticAMD", "GenuineIntel"}
VALID_MODEL_KEYWORDS = {"AMD", "Intel"}
QEMU_PROCESS_NAME   = "qemu-guest-agent"


def _check_cloud_metadata() -> bool:
    """Detecta proveedor cloud intentando acceder al endpoint de metadatos."""
    try:
        req = urllib.request.Request(CLOUD_METADATA_URL)
        with urllib.request.urlopen(req, timeout=2) as resp:
            return resp.status == 200
    except Exception:
        return False


def _check_cpuinfo() -> bool:
    """
    Lee /proc/cpuinfo. Si vendor_id o model name NO son AMD/Intel → VM detectada.
    """
    try:
        with open("/proc/cpuinfo", "r") as f:
            content = f.read()

        vendor_ok = False
        model_ok  = False

        for line in content.splitlines():
            if line.startswith("vendor_id"):
                value = line.split(":", 1)[-1].strip()
                if value in VALID_VENDORS:
                    vendor_ok = True
            elif line.startswith("model name"):
                value = line.split(":", 1)[-1].strip()
                if any(kw in value for kw in VALID_MODEL_KEYWORDS):
                    model_ok = True

        # Si alguno no cuadra con AMD/Intel → asumimos VM
        return not (vendor_ok and model_ok)
    except Exception:
        return True  # Fail-safe


def _check_qemu_agent() -> bool:
    """
    Escanea /proc/*/cmdline buscando qemu-guest-agent.
    No usa subprocess ni librerías externas: puro acceso a /proc.
    """
    try:
        for entry in os.listdir("/proc"):
            if not entry.isdigit():
                continue
            cmdline_path = os.path.join("/proc", entry, "cmdline")
            try:
                with open(cmdline_path, "rb") as f:
                    # Los argumentos en cmdline están separados por '\x00'
                    cmdline = f.read().decode("utf-8", errors="replace")
                if QEMU_PROCESS_NAME in cmdline:
                    return True
            except (PermissionError, FileNotFoundError):
                continue
    except Exception:
        pass
    return False


def is_vm() -> bool:
    """Devuelve True si CUALQUIER técnica detecta un entorno virtualizado."""
    if _check_cloud_metadata():
        return True
    if _check_cpuinfo():
        return True
    if _check_qemu_agent():
        return True
    return False
