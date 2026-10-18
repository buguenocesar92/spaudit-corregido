"""Encuentra la línea con paréntesis desbalanceados (ignorando cadenas)."""
import io
import sys


def main(ruta):
    with io.open(ruta, encoding="utf-8") as fh:
        lineas = fh.readlines()
    nivel = 0
    for i, linea in enumerate(lineas, 1):
        dentro = None
        profundidad = 0
        for ch in linea:
            if dentro:
                if ch == "\\":
                    continue
                if ch == dentro:
                    dentro = None
                continue
            if ch in "\"'":
                dentro = ch
            elif ch == "#":
                break
            elif ch == "(":
                profundidad += 1
            elif ch == ")":
                profundidad -= 1
        antes = nivel
        nivel += profundidad
        if nivel < 0:
            print("línea %d: nivel de paréntesis negativo -> %s"
                  % (i, linea.rstrip().encode("ascii", "replace").decode()))
            print("   (nivel antes: %d, cambio: %d)" % (antes, profundidad))
            return 1
    print("balance final: %d" % nivel)
    return 0 if nivel == 0 else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))