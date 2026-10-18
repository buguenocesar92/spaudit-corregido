"""Valida el catálogo: sintaxis, IDs únicos y caracteres no permitidos.

Uso:  python herramientas/validar_catalogo.py
"""
import ast
import io
import os
import re
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAQUETE = os.path.join(RAIZ, "spaudit")

# Rangos de caracteres que no deberían aparecer en un catálogo en español.
SOSPECHOSOS = {
    0x2E80: 0x9FFF,    # CJK
    0xAC00: 0xD7AF,    # Hangul
    0x3040: 0x30FF,    # Kana
    0x0400: 0x04FF,    # Cirílico
    0x200E: 0x200F,    # marcas de dirección LTR/RTL
    0x202A: 0x202E,    # marcas de incrustación bidireccional
    0x2066: 0x2069,    # aisladores bidireccionales
    0xFEFF: 0xFEFF,    # BOM interno
}


def _seguro(texto):
    """Sustituye lo que la consola cp1252 no puede imprimir."""
    return texto.encode("cp1252", "replace").decode("cp1252")


REQUERIDOS = {"brecha", "ref", "fix"}
POSICIONALES_OBLIGATORIOS = 7  # cid, proc, pagina, categoria, riesgo, tipo, enunciado


def revisar_estructura(texto):
    """Detecta llamadas D(...) sin argumentos con nombre obligatorios."""
    problemas = []
    arbol = ast.parse(texto)
    for nodo in ast.walk(arbol):
        if not isinstance(nodo, ast.Call) or not isinstance(nodo.func, ast.Name):
            continue
        if nodo.func.id != "D":
            continue
        con_nombre = {kw.arg for kw in nodo.keywords if kw.arg}
        faltantes = REQUERIDOS - con_nombre
        if len(nodo.args) < POSICIONALES_OBLIGATORIOS:
            problemas.append("línea %d: D() con %d posicionales (se requieren %d)"
                             % (nodo.lineno, len(nodo.args), POSICIONALES_OBLIGATORIOS))
        if faltantes:
            problemas.append("línea %d: D() sin %s" % (nodo.lineno, ", ".join(sorted(faltantes))))
    return problemas


def revisar(archivo):
    problemas = []
    with io.open(archivo, encoding="utf-8") as fh:
        texto = fh.read()
    try:
        ast.parse(texto)
    except SyntaxError as exc:
        problemas.append("sintaxis: %s (línea %s)" % (exc.msg, exc.lineno))
        return problemas, texto

    for i, char in enumerate(texto):
        for ini, fin in SOSPECHOSOS.items():
            if ini <= ord(char) <= fin:
                problemas.append(
                    "carácter extraño U+%04X en offset %d (línea %d)"
                    % (ord(char), i, texto.count("\n", 0, i) + 1))
                break
    problemas.extend(revisar_estructura(texto))
    return problemas, texto


def main():
    modulos = sorted(f for f in os.listdir(PAQUETE)
                     if f.startswith("controles_") and f.endswith(".py"))
    total_ids = []
    salida = 0
    for nombre in modulos:
        ruta = os.path.join(PAQUETE, nombre)
        problemas, texto = revisar(ruta)
        ids = re.findall(
            r'D\(\s*"(SP-[0-9A-Za-z\-]+|LEY-[0-9A-Za-z\-]+|D44-[0-9A-Za-z\-]+|DOC-[0-9A-Za-z\-]+)"',
            texto)
        total_ids += ids
        estado = "OK " if not problemas else "ERR"
        print("[%s] %-26s %3d controles" % (estado, nombre, len(ids)))
        for p in problemas:
            print("      - %s" % _seguro(p))
            salida = 1

    duplicados = sorted({i for i in total_ids if total_ids.count(i) > 1})
    if duplicados:
        print("[ERR] IDs duplicados: %s" % ", ".join(duplicados))
        salida = 1
    else:
        print("[OK ] %d IDs únicos en total" % len(total_ids))

    return salida


if __name__ == "__main__":
    sys.exit(main())