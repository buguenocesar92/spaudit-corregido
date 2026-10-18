"""Imprime el catálogo: conteos y una muestra de controles legible en consola.

Sirve para revisar el texto de los controles sin abrir el informe HTML.

Uso:  python herramientas/ver_catalogo.py [--id SP-13-04]
"""
import io
import os
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

from spaudit import catalogo  # noqa: E402

ANCHO = 92


def _seguro(texto):
    return texto.encode("cp1252", "replace").decode("cp1252")


def mostrar(control):
    print("=" * ANCHO)
    print("%s  [%s]  riesgo=%s  tipo=%s  categoria=%s"
          % (control["id"], "auto" if control["automatizable"] else "revision",
             control["riesgo"], control["tipo"], control["categoria"]))
    origen = ("Procedimiento %s, pág. %s" % (control["proc"], control["pagina"])
              if control["proc"] else "sin página en el manual")
    print("origen:   %s" % origen)
    print("dice:     %s" % _seguro(control["enunciado"]))
    print("brecha:   %s" % _seguro(control["brecha"]))
    print("ref:      %s" % _seguro(control["ref"]))
    print("fix:      %s" % _seguro(control["fix"]))
    print("verif:    %s" % _seguro(control["verificacion"]))
    if control["evidencia"]:
        print("evidencia: %s" % ", ".join(control["evidencia"]))
    if control["check"]:
        print("check:    %s %s" % (control["check"]["tipo"], control["check"]["params"]))


def main(argv):
    if len(argv) > 1 and not argv[1].startswith("--"):
        control = catalogo.por_id(argv[1])
        if not control:
            print("No existe el control %s" % argv[1])
            return 1
        mostrar(control)
        return 0

    info = catalogo.resumen()
    print("Catálogo: %d controles (%d verificables automáticamente, %d de revisión humana)"
          % (info["total"], info["automatizables"], info["revision_humana"]))
    print("por riesgo: %s" % ", ".join(
        "%s=%d" % (r, info["por_riesgo"].get(r, 0)) for r in catalogo.RIESGOS))
    print("por tipo:   %s" % ", ".join(
        "%s=%d" % (t, info["por_tipo"].get(t, 0)) for t in sorted(info["por_tipo"])))
    print()

    for control in catalogo.CONTROLES:
        print("  %-10s p%-3s %-18s %-8s %s" % (
            control["id"], control["pagina"] or "-", control["categoria"],
            control["riesgo"], _seguro(control["enunciado"])[:64]))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))