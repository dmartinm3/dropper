import requests

KILLSWITCH_STRING = "QUIETO PARAO"

def check_killswitch(url: str) -> bool:
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            return KILLSWITCH_STRING in response.text
        return True  # Código HTTP distinto de 200 lo para
    except Exception:
        return True  # Cualquier excepción lo parar
