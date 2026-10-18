"""Comprueba que todos los módulos compilan y que los paréntesis balancean.

Uso:  python herramientas/comprobar.py
"""
import ast
import io
import os
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main():
    objetivos = []
    for carpeta in ("spaudit", "herramientas"):
        base = os.path.join(RAIZ, carpeta)
        for nombre in sorted(os.listdir(base)):
            if nombre.endswith(".py"):
                objetivos.append(os.path.join(base, nombre))
    objetivos.append(os.path.join(RAIZ, "auditar.py"))

    fallos = 0
    for ruta in objetivos:
        nombre = os.path.relpath(ruta, RAIZ)
        try:
            with io.open(ruta, encoding="utf-8") as fh:
                ast.parse(fh.read(), filename=ruta)
            print("[OK ] %s" % nombre)
        except SyntaxError as exc:
            fallos += 1
            print("[ERR] %s  linea %s: %s" % (nombre, exc.lineno, exc.msg))
            if exc.text:
                print("      " + exc.text.strip().encode("cp1252", "replace").decode("cp1252"))
    print("")
    print("%d módulo(s) con error de sintaxis." % fallos)
    return 1 if fallos else 0


if __name__ == "__main__":
    sys.exit(main())