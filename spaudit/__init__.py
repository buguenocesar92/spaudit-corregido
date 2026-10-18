"""spaudit — auditoría de cumplimiento y ciberseguridad.

Audita lo que el Manual de Procedimientos de Saint Patrick School declara
contra lo que realmente se puede verificar, y contrasta el resultado con el
marco legal chileno aplicable (Ley 21.719, Ley 19.886 / Directiva 44/2026).

Uso mínimo:
    python auditar.py
"""

__version__ = "1.0.0"
__all__ = ["catalogo", "evidencia", "checks", "red", "reporte", "motor"]