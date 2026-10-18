# -*- coding: utf-8 -*-
"""Que evidencia pide el catalogo y que archivos escribe realmente el recolector.

De los 32 controles automatizables, el recolector resuelve 21, spaudit resuelve
5 mas si se corre SIN `--sin-vivo`, y 6 no los resuelve nada de este paquete.
Ese numero es el que hay que pegarle al colegio cuando pregunte por que siguen
sin verificar.

    python herramientas\\que_evidence_falta.py
"""
import io
import os
import re
import sys
from collections import defaultdict

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if len(sys.argv) > 1:
    RAIZ = sys.argv[1]
sys.path.insert(0, RAIZ)

from spaudit import catalogo  # noqa: E402

PS1 = os.path.join(RAIZ, "powershell", "recolectar-evidencia.ps1")

# Archivos que genera el propio auditar.py cuando corre con red.
VIVOS = ("live_web.json", "live_dns.json", "live_red.json")


def archivos_del_recolector():
    with io.open(PS1, "r", encoding="utf-8") as fh:
        texto = fh.read()
    # Todo lo que se pasa por Join-Path $Salida "..."
    return set(re.findall(r'Join-Path\s+\$Salida\s+"([^"]+)"', texto))


def main():
    producidos = archivos_del_recolector()
    dependientes = defaultdict(list)
    for c in catalogo.CONTROLES:
        for a in (c.get("evidencia") or []):
            dependientes[a].append(c.get("id"))

    sin_productor = sorted(a for a in dependientes
                           if a not in producidos and a not in VIVOS)
    con_red = sorted(a for a in dependientes
                     if a not in producidos and a in VIVOS)

    automatizables = [c for c in catalogo.CONTROLES if c.get("automatizable")]

    def sin_resolver(de_archivos):
        fuera = set()
        for a in de_archivos:
            for cid in dependientes[a]:
                c = catalogo.por_id(cid)
                if c and c.get("automatizable"):
                    fuera.add(cid)
        return fuera

    n_rec = len(sin_resolver([a for a in dependientes if a in producidos]))
    n_red = len(sin_resolver(con_red))
    n_nadie = len(sin_resolver(sin_productor))

    print("")
    print("  %d controles automatizables en el catalogo" % len(automatizables))
    print("    %2d  los resuelve recolectar-evidencia.ps1" % n_rec)
    print("    %2d  los resuelve auditar.py, pero solo SIN --sin-vivo" % n_red)
    print("    %2d  no los resuelve nada de este paquete" % n_nadie)
    print("")
    print("  ARCHIVOS QUE NADIE PRODUCE (%d)" % len(sin_productor))
    for a in sin_productor:
        print("    %-34s %2d controles: %s"
              % (a, len(dependientes[a]), ", ".join(sorted(dependientes[a]))))
    print("")
    print("  Lo que sale sin red (%d): %s"
          % (len(con_red), ", ".join(con_red)))
    print("")


if __name__ == "__main__":
    main()