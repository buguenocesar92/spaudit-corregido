"""Catálogo consolidado de controles y utilidades para consultarlo."""

from .controles_comunes import (
    D, CUMPLE, NO_CUMPLE, PARCIAL, NO_VERIFICADO, NO_APLICA,
    ESTADOS, RIESGOS, COLOR_ESTADO, RIESGO_ORDEN,
)
from .controles_p1_p12 import CONTROLES as _P1
from .controles_p13_p22 import CONTROLES as _P2
from .controles_p23_legal import CONTROLES as _P3

CONTROLES = list(_P1) + list(_P2) + list(_P3)

#: Orden canónico de los identificadores por familia.
def _orden(control):
    fam = control["id"].split("-")[0]
    peso = {"SP": 0, "DOC": 1, "LEY": 2, "D44": 3}.get(fam, 9)
    numero = control["id"]
    return (peso, numero)


CONTROLES.sort(key=_orden)


def por_id(cid):
    for control in CONTROLES:
        if control["id"] == cid:
            return control
    return None


def por_procedimiento(proc):
    """Controles del manual que pertenecen a un procedimiento (1..27)."""
    return [c for c in CONTROLES if c["proc"] == proc]


def por_riesgo(riesgo):
    return [c for c in CONTROLES if c["riesgo"] == riesgo]


def automatizables():
    """Controles que el motor puede verificar sin intervención humana."""
    return [c for c in CONTROLES if c["automatizable"]]


def resumen():
    """Cuentas por riesgo, tipo y automatizabilidad."""
    por_r = {}
    por_t = {}
    automatica = 0
    for c in CONTROLES:
        por_r[c["riesgo"]] = por_r.get(c["riesgo"], 0) + 1
        por_t[c["tipo"]] = por_t.get(c["tipo"], 0) + 1
        if c["automatizable"]:
            automatica += 1
    return {
        "total": len(CONTROLES),
        "por_riesgo": por_r,
        "por_tipo": por_t,
        "automatizables": automatica,
        "revision_humana": len(CONTROLES) - automatica,
    }