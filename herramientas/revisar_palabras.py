"""Detecta palabras pegadas (minúscula seguida de mayúscula) dentro de cadenas.

Permite cazar residuos como "elContaminación" o "sinPurpose". No distingue entre
un error real y un nombre propio en camelCase, así que la salida es una lista
para revisar a ojo.

Uso:  python herramientas/revisar_palabras.py <archivo.py> [...]
"""
import io
import re
import sys

# CamelCase interno: minúscula pegada a mayúscula, dentro de una cadena de texto.
PATRON = re.compile(r"[a-záéíóúñ][A-ZÁÉÍÓÚ][a-záéíóúñ]+")

# Palabras que sí son legítimas (nombres de technologies, siglas, etc.)
PERMITIDAS = {
    "MerakiHome", "PowerShell", "ActiveDirectory", "LdapPolicy",
    "WinServer", "MacBook", "WindowsUpdate", "OneNoteOneDrive",
    "BluetoothAudio", "AntivirusAntimalware",
}


def revisar(ruta):
    with io.open(ruta, encoding="utf-8") as fh:
        lineas = fh.readlines()

    hallazgos = 0
    for i, linea in enumerate(lineas, 1):
        limpio = linea.encode("ascii", "replace").decode()
        for palabra in PATRON.findall(limpio):
            if palabra in PERMITIDAS:
                continue
            print("  %s:%d  %s" % (ruta.rsplit("\\", 1)[-1], i, palabra))
            hallazgos += 1
    return hallazgos


def main(rutas):
    total = sum(revisar(r) for r in rutas)
    print("total: %d" % total)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))