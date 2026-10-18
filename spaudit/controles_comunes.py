"""Definición común del catálogo de controles de spaudit.

Un control = lo que el manual (o la normativa) exige  +  cómo se verifica  +
qué evidencia se necesita  +  qué brecha quedaría si no se cumple.

Los controles son datos, no código: se pueden editar, filtrar o extender sin
tocar el motor.
"""

# Estados posibles de una evaluación
CUMPLE = "CUMPLE"
NO_CUMPLE = "NO_CUMPLE"
PARCIAL = "PARCIAL"
NO_VERIFICADO = "NO VERIFICADO"
NO_APLICA = "NO APLICA"

ESTADOS = [CUMPLE, NO_CUMPLE, PARCIAL, NO_VERIFICADO, NO_APLICA]

# Orden de severidad para ordenar el plan de acción
RIESGOS = ["critico", "alto", "medio", "bajo"]

COLOR_ESTADO = {
    CUMPLE: "#0f9d58",
    PARCIAL: "#e8a33d",
    NO_CUMPLE: "#d93025",
    NO_VERIFICADO: "#8a8a8a",
    NO_APLICA: "#5f6368",
}

RIESGO_ORDEN = {r: i for i, r in enumerate(RIESGOS)}


def D(cid, proc, pagina, categoria, riesgo, tipo, enunciado, *,
      brecha, ref, fix, verificacion=None, evidencia=(), check=None,
      automatizable=False, nota=None):
    """Construye un control del catálogo.

    cid        identificador estable (SP-13-03, LEY-02, D44-01...)
    proc       número de procedimiento del manual (0 si no aplica)
    pagina     página del PDF del manual donde está escrito
    categoria  área temática (Identidad, Red, Respaldo...)
    riesgo     critico | alto | medio | bajo
    tipo       tecnico | organizacional | documental | legal
    enunciado  lo que el manual dice (para cotejar contra la realidad)
    brecha     lo que falta o por qué lo escrito no basta
    ref        referencia externa que respalda la brecha
    fix        acción concreta para cerrar la brecha
    check      spec del verificador automático (tipo + params), o None
    """
    return {
        "id": cid,
        "proc": proc,
        "pagina": pagina,
        "categoria": categoria,
        "riesgo": riesgo,
        "tipo": tipo,
        "enunciado": enunciado,
        "brecha": brecha,
        "ref": ref,
        "fix": fix,
        "verificacion": verificacion or "Revisión humana del documento y/o del sistema.",
        "evidencia": list(evidencia),
        "check": check,
        "automatizable": bool(check),
        "nota": nota,
    }