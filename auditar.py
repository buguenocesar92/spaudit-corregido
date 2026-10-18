#!/usr/bin/env python3
"""spaudit — auditoría de cumplimiento del manual y de ciberseguridad real.

Uso típico:
    python auditar.py                      auditoría completa (documental + en vivo)
    python auditar.py --sin-vivo          sólo con la evidencia local
    python auditar.py --dominio ejemplo.cl
    python auditar.py --id SP-13-04        ver un control concreto
    python auditar.py --recolectar         recordatorio de qué evidencia falta
"""

import os
import sys

RAIZ = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, RAIZ)

from spaudit import catalogo, motor, reporte  # noqa: E402
from spaudit.controles_comunes import (  # noqa: E402
    CUMPLE, NO_CUMPLE, PARCIAL, NO_VERIFICADO, COLOR_ESTADO, RIESGO_ORDEN,
)
from spaudit.evidencia import Evidencia  # noqa: E402
from spaudit.red import Red  # noqa: E402


def _seguro(texto):
    """La consola de Windows usa cp1252: sustituimos lo que no cabe."""
    return texto.encode("cp1252", "replace").decode("cp1252")


def parsear(argv):
    opciones = {
        "evidencia": os.path.join(RAIZ, "evidencia"),
        "salida": os.path.join(RAIZ, "salida"),
        "dominio": "saintpatricktemuco.cl",
        "vivo": True,
        "timeout": 8.0,
        "id": None,
        "recolectar": False,
        "verbose": False,
    }
    i = 0
    while i < len(argv):
        arg = argv[i]
        if arg in ("--evidencia", "--salida", "--dominio", "--id", "--timeout"):
            i += 1
            if i >= len(argv):
                return None, "falta el valor de %s" % arg
            valor = argv[i]
            if arg == "--evidencia":
                opciones["evidencia"] = valor
            elif arg == "--salida":
                opciones["salida"] = valor
            elif arg == "--dominio":
                opciones["dominio"] = valor
            elif arg == "--id":
                opciones["id"] = valor
            else:
                opciones["timeout"] = float(valor)
        elif arg in ("--sin-vivo", "--no-live"):
            opciones["vivo"] = False
        elif arg == "--recolectar":
            opciones["recolectar"] = True
        elif arg in ("-v", "--verbose"):
            opciones["verbose"] = True
        elif arg in ("-h", "--help"):
            return None, None
        else:
            return None, "opción desconocida: %s" % arg
        i += 1
    return opciones, None


def ayuda():
    print(__doc__)
    print("Opciones:")
    print("  --evidencia RUTA   carpeta con los archivos de evidencia")
    print("  --salida RUTA      carpeta donde se escriben los informes")
    print("  --dominio DOMINIO  dominio del colegio (por defecto saintpatricktemuco.cl)")
    print("  --sin-vivo         no hace consultas de red (DNS, TLS, sitio, puertos)")
    print("  --timeout SEG      segundos de espera por consulta (por defecto 8)")
    print("  --id CONTROL       muestra un control del catálogo y sale")
    print("  --recolectar       lista qué evidencia falta para evaluar más controles")
    print("  -v, --verbose     muestra cada control mientras se evalúa")


def mostrar_control(cid):
    control = catalogo.por_id(cid)
    if not control:
        print("No existe el control '%s'." % cid)
        print("Controles disponibles: %s ..." % ", ".join(
            c["id"] for c in catalogo.CONTROLES[:6]))
        return 1
    print("=" * 88)
    print("%s   [%s]   riesgo=%s   tipo=%s   categoría=%s" % (
        control["id"], "verificable automáticamente" if control["automatizable"]
        else "revisión humana",
        control["riesgo"], control["tipo"], control["categoria"]))
    origen = ("Manual de Procedimientos, procedimiento %s, página %s"
              % (control["proc"], control["pagina"])) if control["proc"] else \
             "Marco legal o calidad del documento (sin página)"
    print("origen:      %s" % origen)
    print("dice:        %s" % _seguro(control["enunciado"]))
    print("brecha:      %s" % _seguro(control["brecha"]))
    print("verificar:   %s" % _seguro(control["verificacion"]))
    print("acción:      %s" % _seguro(control["fix"]))
    print("referencia:  %s" % _seguro(control["ref"]))
    if control["evidencia"]:
        print("evidencia:   %s" % ", ".join(control["evidencia"]))
    if control["check"]:
        print("verificador: %s" % control["check"]["tipo"])
    return 0


def listar_pendientes(contexto):
    """Muestra qué archivos de evidencia habilitarían más controles."""
    faltantes = {}
    for control in catalogo.CONTROLES:
        for archivo in control["evidencia"]:
            if contexto.evidencia.existe(archivo):
                continue
            faltantes.setdefault(archivo, []).append(control["id"])

    print("Controles pendientes por evidencia (%d archivos):\n" % len(faltantes))
    for archivo in sorted(faltantes):
        ids = faltantes[archivo]
        print("  %-34s %2d control(es): %s" % (
            archivo, len(ids), ", ".join(sorted(ids)[:6]) +
            ("..." if len(ids) > 6 else "")))
    print("\nLos archivos marcados 'docs/' y carpetas deben copiarse a mano desde el")
    print("colegio; los que empiezan con 'red/' los genera")
    print("powershell\\recolectar-evidencia.ps1")
    return 0


def resumen_consola(resultados, tablero_):
    e = tablero_["estados"]
    print("")
    print("=" * 88)
    print("RESUMEN DE LA AUDITORÍA — %s" % tablero_["generado"])
    print("=" * 88)
    for estado in (NO_CUMPLE, PARCIAL, NO_VERIFICADO, CUMPLE):
        print("  %-16s %4d" % (estado, e.get(estado, 0)))
    print("  %-16s %4d controles en total" % ("TOTAL", tablero_["total"]))
    print("")
    print("Cobertura de verificación automática: %d/%d controles verificables (%d%%)"
          % (tablero_["evaluados"], tablero_["verificables"], tablero_["evaluados_pct"]))

    hallazgos = sorted([r for r in resultados if r.es_hallazgo],
                       key=lambda r: (RIESGO_ORDEN.get(r.control["riesgo"], 9), r.control["id"]))
    if hallazgos:
        print("")
        print("HALLAZGOS (los primeros 25):")
        for r in hallazgos[:25]:
            print("  [%-6s] %-10s %s" % (r.control["riesgo"], r.control["id"],
                                        _seguro(r.detalle)[:88]))
    print("")


def main(argv):
    opciones, error = parsear(argv)
    if error:
        print("Error: %s" % error)
        ayuda()
        return 2
    if opciones is None:
        ayuda()
        return 0

    if opciones["id"]:
        return mostrar_control(opciones["id"])

    evidencia = Evidencia(opciones["evidencia"])
    contexto = motor.Contexto(evidencia, dominio=opciones["dominio"])

    if opciones["vivo"]:
        print("Realizando comprobaciones en vivo contra %s ..." % opciones["dominio"])
        contexto.red = Red(timeout=opciones["timeout"],
                           cache_path=os.path.join(opciones["salida"], "evidencia_viva.json"))
    else:
        print("Comprobaciones en vivo desactivadas (--sin-vivo).")

    if evidencia.archivos():
        print("Evidencia encontrada: %d archivo(s) en %s"
              % (len(evidencia.archivos()), evidencia.carpeta))
    else:
        print("No hay evidencia en %s: los controles técnicos quedarán sin verificar."
              % evidencia.carpeta)

    if opciones["recolectar"]:
        return listar_pendientes(contexto)

    if opciones["verbose"]:
        print("")
        print("Evaluando controles:")
    resultados = motor.ejecutar(contexto, verbose=opciones["verbose"])

    if contexto.red:
        contexto.red.guardar()

    tablero_ = motor.tablero(resultados)
    rutas = reporte.escribir(resultados, tablero_, contexto, opciones["salida"])

    resumen_consola(resultados, tablero_)
    print("Informes escritos en:")
    for clave in ("html", "json", "md"):
        print("  %-5s %s" % (clave.upper(), rutas[clave]))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))