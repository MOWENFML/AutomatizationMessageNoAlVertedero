# test
# .venv\Scripts\Activate.ps1
import csv
from datetime import datetime
from pathlib import Path
import time
import pywhatkit as pwk


BASE_DIR = Path(__file__).resolve().parent.parent
CSV_PATH = BASE_DIR / "data" / "datos de prueba.csv"
LOG_PATH = BASE_DIR / "logs" / "registro_poc.csv"

# Ajustes para tu PoC
DRY_RUN = True          # True = simula el envío; False = llama a pywhatkit
PAUSA_SEGUNDOS = 8      # Pausa entre contactos para evitar ráfagas
WAIT_TIME = 15          # Segundos que pywhatkit espera antes de enviar
TAB_CLOSE = True
CLOSE_TIME = 3


def cargar_contactos(ruta_csv: Path) -> list[dict[str, str]]:
    """Lee el CSV y limpia espacios en encabezados y valores."""
    contactos: list[dict[str, str]] = []
    with ruta_csv.open(mode="r", encoding="utf-8", newline="") as archivo:
        lector = csv.DictReader(archivo)
        for fila in lector:
            limpia = {
                (clave or "").strip(): (valor or "").strip()
                for clave, valor in fila.items()
            }
            if limpia.get("Numero"):
                contactos.append(limpia)
    return contactos


def registrar_resultado(ruta_log: Path, registro: dict[str, str]) -> None:
    """Agrega una fila al archivo CSV de registro."""
    ruta_log.parent.mkdir(parents=True, exist_ok=True)
    archivo_existe = ruta_log.exists()
    campos = ["timestamp", "fila", "numero", "nombre", "correo", "estado", "detalle"]

    with ruta_log.open(mode="a", encoding="utf-8", newline="") as archivo:
        escritor = csv.DictWriter(archivo, fieldnames=campos)
        if not archivo_existe:
            escritor.writeheader()
        escritor.writerow(registro)


def construir_mensaje(nombre: str) -> str:
    return f"Hola {nombre}, este es un mensaje de prueba técnico para validar el flujo de PoC."


def ejecutar_poc() -> None:
    if not CSV_PATH.exists():
        raise FileNotFoundError(f"No se encontró el archivo de contactos en: {CSV_PATH}")

    contactos = cargar_contactos(CSV_PATH)
    total = len(contactos)
    print(f"Contactos cargados: {total} | DRY_RUN={DRY_RUN}")

    for indice, contacto in enumerate(contactos, start=1):
        numero = contacto.get("Numero", "")
        nombre = contacto.get("Nombre", "")
        correo = contacto.get("Correo", "")
        mensaje = construir_mensaje(nombre)
        timestamp = datetime.now().isoformat(timespec="seconds")

        print(f"[{indice}/{total}] Procesando a {nombre} ({numero})...")

        try:
            if DRY_RUN:
                time.sleep(3)
                estado = "SIMULADO_OK"
                detalle = "Modo prueba activo; no se abrió WhatsApp Web"
            else:
                pwk.sendwhatmsg_instantly(
                    phone_no=numero,
                    message=mensaje,
                    wait_time=WAIT_TIME,
                    tab_close=TAB_CLOSE,
                    close_time=CLOSE_TIME,
                )
                estado = "ENVIADO_INTENTO"
                detalle = "Función pywhatkit ejecutada sin excepciones"

        except Exception as exc:
            estado = "ERROR"
            detalle = f"{type(exc).__name__}: {exc}"

        registrar_resultado(
            LOG_PATH,
            {
                "timestamp": timestamp,
                "fila": str(indice),
                "numero": numero,
                "nombre": nombre,
                "correo": correo,
                "estado": estado,
                "detalle": detalle,
            },
        )
        print(f"   -> {estado}: {detalle}")

        if indice < total:
            print(f"   Esperando {PAUSA_SEGUNDOS}s antes del siguiente contacto...")
            time.sleep(PAUSA_SEGUNDOS)

    print(f"\nProceso terminado. Revisa el registro en: {LOG_PATH}")


if __name__ == "__main__":
    ejecutar_poc()