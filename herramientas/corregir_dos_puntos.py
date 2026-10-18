"""Convierte `clave:` en `clave=` donde corresponde a un argumento con nombre.

Los controles usan la forma `fix="..."`; un `fix:` es un error de tipeo que el
parser de Python reporta de forma confusa. Esta herramienta lo corrige.

Uso:  python herramientas/corregir_dos_puntos.py <archivo.py> [...]
"""
import io
import re
import sys

# Sólo las claves que existen en la firma de D(...)
CLAVES = "brecha|ref|fix|verificacion|evidencia|check|nota|automatizable"
# La clave puede empezar la línea o ir tras otra llamada al mismo argumento.
PATRON = re.compile(r'(?<=[\s,])(' + "|".join(CLAVES.split("|")) + r'):(?=[^:=])')


def corregir(ruta):
    with io.open(ruta, encoding="utf-8") as fh:
        lineas = fh.readlines()

    cambios = 0
    for i, linea in enumerate(lineas):
        nueva = PATRON.sub(lambda m: "%s=" % m.group(1),
                           linea.rstrip("\n"))
        # No tocar dicts dentro de los propios controles (usan "tipo": ..., "params": ...)
        if nueva != linea.rstrip("\n"):
            cambios += 1
            lineas[i] = nueva + "\n"

    if cambios:
        with io.open(ruta, "w", encoding="utf-8", newline="\n") as fh:
            fh.writelines(lineas)
    return cambios


def main(rutas):
    total = 0
    for ruta in rutas:
        n = corregir(ruta)
        total += n
        print("%-34s %d correcciones" % (ruta.rsplit("\\", 1)[-1], n))
    print("total: %d" % total)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))