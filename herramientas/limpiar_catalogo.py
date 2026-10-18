"""Limpieza puntual del catálogo: quita ramas muertas y reporta residuos.

Es una herramienta de un solo uso, escrita para dejar el catálogo en verde.
No modifica el significado de los controles, sólo elimina artefactos de formato.

AVISO, PARA QUIEN ABRA ESTE ARCHIVO Y SE PREGUNTE POR QUÉ HAY CARACTERES
CHINOS Y JAPONESES AQUÍ: son los SECUENCIAS DE `SUSTITUCIONES`, y están a
propósito. Guardan, literalmente, el texto roto que había y su corrección en
español. Es el registro de qué se corrigió, y por eso el paquete lo lleva.

Ya se aplicó: el catálogo está limpio (0 caracteres CJK o cirílicos). Volver a
correrla sobre un archivo ya corregido no cambia nada. No es parte del
auditor: `auditar.py` no la importa.

Uso:  python herramientas/limpiar_catalogo.py <archivo.py>
"""
import io
import re
import sys

# Ramas muertas del estilo:  D(...) if False else D(
RAMA_MUERTA = re.compile(
    r'    D\("(?:SP|LEY|D44|DOC)-[0-9A-Za-z\-]+",[^\n]*\n(?:      "[^\n]*\n)+      '
    r'breach_="", brecha="", ref="", fix=""\) if False else D\(\n'
)

# Residuos detectados: texto en otro idioma pegado dentro del español.
SUSTITUCIONES = [
    ("otros guests锡 Enable in AD", "otras cuentas de invitado habilitadas en AD"),
    ("SID终结-500", "SID-500"),
    ("la forma más común de无损 llegada del ransomware",
     "la vía más común de entrada del ransomware"),
    ("NTLMv2のみ", "NTLMv2 solamente"),
    ("planear el升级 a una versión", "planear la actualización a una versión"),
    ("con记录 de cada cambio", "con registro de cada cambio"),
    ("con記録 de cada cambio", "con registro de cada cambio"),
    ("es el acceso deDynnta a la red", "es la puerta de entrada permanente a la red"),
    ("tres personas BIT y sin gestor", "tres personas y sin gestor"),
    ("dejarla撑 como norma de uso", "dejarla sólo como norma de uso"),
    ("y prohibiting el acceso", "y prohibiendo el acceso"),
    ("sin(finalidad) definida", "sin finalidad definida"),
    ("dejarla撑 como norma de uso", "dejarla sólo como norma de uso"),
    # --- residuos del bloque de red, videovigilancia, redes sociales y marco legal
    ("switch de氧 de preescolar", "switch de preescolar"),
    ("America/Santiago统一", "America/Santiago"),
    ("la，温 autorización", "la autorización"),
    ("=:newa agencia, inventario", ": nueva agencia, inventario"),
    ("etingir expresamente", "prohibir expresamente"),
    ("con Independent助力: adaptarlas", "con ayuda externa: adaptarlas"),
    ("Vigencia y，一张一张 aplicación", "Vigencia y aplicación"),
    ("que价值和Proveedores del Estado", "y a los proveedores del Estado"),
    ("Adoptarlos voluntarily como referencia técnica interna",
     "Adoptarlos voluntariamente como referencia técnica interna"),
    ("con el sostenedor, si lo hay", "con el sostenedor, si lo hay"),
    ("el convenio con el sostenedor o la璨“六selecta",
     "el convenio con el sostenedor o el contrato vigente con el municipio"),
    ("es admittedly dirigida", "está dirigida"),
    ("(régimen de-treatment por mandato)", "(régimen de tratamiento por mandato)"),
]

# Palabras que no pertenecen al español del documento (heurística de revisión).
SOSPECHOSO = re.compile(r"\b(enable|prohibiting|payload|hosting|Websites?|websites)\b")


def main(ruta):
    with io.open(ruta, encoding="utf-8") as fh:
        original = fh.read()

    texto = RAMA_MUERTA.sub("    D(\n", original)
    aplicadas = []
    for viejo, nuevo in SUSTITUCIONES:
        if viejo in texto:
            texto = texto.replace(viejo, nuevo)
            aplicadas.append(viejo)

    if texto != original:
        with io.open(ruta, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(texto)

    print("ramas muertas eliminadas: %d" % (len(RAMA_MUERTA.findall(original))))
    print("sustituciones aplicadas: %d" % len(aplicadas))
    for a in aplicadas:
        print("   - %s" % a.encode("cp1252", "replace").decode("cp1252"))

    # Revisión manual pendiente: palabras extrañas que no se corrigieron solos.
    for i, linea in enumerate(texto.split("\n"), 1):
        if SOSPECHOSO.search(linea):
            print("   REVISAR línea %d: %s" % (i, linea.strip().encode(
                "cp1252", "replace").decode("cp1252")))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))