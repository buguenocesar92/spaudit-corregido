"""Ejecuta el catálogo sobre la evidencia y devuelve resultados.

Reglas del motor:
  1. Un control sin verificador automático nunca se marca como cumplido: queda
     como NO VERIFICADO, que es información, no un fallo.
  2. Un verificador sin evidencia devuelve NO VERIFICADO, nunca CUMPLE.
  3. Ningún control se da por satisfactorio por defecto.
"""

import datetime

from . import catalogo, checks
from .controles_comunes import (
    CUMPLE, NO_CUMPLE, PARCIAL, NO_VERIFICADO, NO_APLICA,
    COLOR_ESTADO, RIESGO_ORDEN,
)


class Contexto(object):
    """Lo que los verificadores necesitan saber para trabajar."""

    def __init__(self, evidencia, red=None, dominio="saintpatricktemuco.cl"):
        self.evidencia = evidencia
        self.red = red
        self.dominio = dominio


class Resultado(object):
    def __init__(self, control, estado, detalle, evidencia="", error=None):
        self.control = control
        self.estado = estado
        self.detalle = detalle
        self.evidencia = evidencia
        self.error = error

    def a_dict(self):
        c = self.control
        return {
            "id": c["id"],
            "procedimiento": c["proc"],
            "pagina": c["pagina"],
            "categoria": c["categoria"],
            "riesgo": c["riesgo"],
            "tipo": c["tipo"],
            "estado": self.estado,
            "enunciado": c["enunciado"],
            "brecha": c["brecha"],
            "referencia": c["ref"],
            "verificacion": c["verificacion"],
            "remediacion": c["fix"],
            "detalle": self.detalle,
            "evidencia": self.evidencia,
            "automatizable": c["automatizable"],
            "error": self.error,
        }

    @property
    def id(self):
        return self.control["id"]

    @property
    def es_hallazgo(self):
        """Un hallazgo es algo que no está bien hoy: incumplimiento o vacío."""
        return self.estado in (NO_CUMPLE, PARCIAL)


def ejecutar(contexto, controles=None, verbose=False):
    """Evalúa cada control y devuelve la lista de resultados."""
    controles = controles if controles is not None else catalogo.CONTROLES
    resultados = []
    for control in controles:
        resultados.append(_evaluar(contexto, control, verbose))
    return resultados


def _evaluar(contexto, control, verbose=False):
    if not control["check"]:
        return Resultado(
            control, NO_VERIFICADO,
            "Control no automatizable: requiere revisión humana y documental.",
            "Pendiente de revisión (%s)." % control["tipo"])

    tipo = control["check"]["tipo"]
    params = control["check"].get("params", {})
    verificador = checks.VERIFICADORES.get(tipo)
    if verificador is None:
        return Resultado(control, NO_VERIFICADO,
                         "No hay verificador implementado para '%s'." % tipo,
                         "", error="verificador-missing")

    try:
        estado, detalle, evidencia = verificador(contexto, params)
    except Exception as exc:  # un verificador roto no debe tumbar la auditoría
        return Resultado(control, NO_VERIFICADO,
                         "El verificador falló al evaluar: %s: %s"
                         % (type(exc).__name__, exc), "", error="excepcion")

    if verbose:
        print("  %-10s %-14s %s" % (control["id"], estado, detalle[:70]))
    return Resultado(control, estado, detalle, evidencia)


def ordenar_hallazgos(resultados):
    """Ordena por riesgo y luego por familia de control."""
    def clave(r):
        c = r.control
        return (RIESGO_ORDEN.get(c["riesgo"], 9), c["proc"], c["id"])
    return sorted([r for r in resultados if r.es_hallazgo], key=clave)


def tablero(resultados):
    """Conteos por estado y por riesgo, para el resumen del informe."""
    estados = {CUMPLE: 0, NO_CUMPLE: 0, PARCIAL: 0, NO_VERIFICADO: 0, NO_APLICA: 0}
    riesgos = {}
    for r in resultados:
        estados[r.estado] = estados.get(r.estado, 0) + 1
        riesgos.setdefault(r.control["riesgo"], {CUMPLE: 0, NO_CUMPLE: 0,
                                                 PARCIAL: 0, NO_VERIFICADO: 0})
        riesgos[r.control["riesgo"]][r.estado] = riesgos[r.control["riesgo"]].get(r.estado, 0) + 1
    total = len(resultados)
    verificables = sum(1 for r in resultados if r.control["automatizable"])
    evaluados = sum(1 for r in resultados
                    if r.control["automatizable"] and r.estado != NO_VERIFICADO)
    return {
        "total": total,
        "estados": estados,
        "riesgos": riesgos,
        "verificables": verificables,
        "evaluados": evaluados,
        "evaluados_pct": int(100.0 * evaluados / verificables) if verificables else 0,
        "generado": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
    }


def color(estado):
    return COLOR_ESTADO.get(estado, "#5f6368")