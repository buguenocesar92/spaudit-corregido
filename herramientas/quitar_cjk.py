"""Elimina secuencias CJK concretas que quedaron pegadas en el catálogo.

Cada entrada es (secuencia_literal, texto_en_espanol). Se aplica una sola vez.

AVISO, PARA QUIEN ABRA ESTE ARCHIVO Y SE PREGUNTE POR QUÉ HAY CARACTERES
CHINOS AQUÍ: son las `SECUENCIAS`, y están a propósito. Guardan el texto roto
y su corrección. Ya se aplicaron: el catálogo está limpio.

No es parte del auditor: `auditar.py` no la importa.

Uso:  python herramientas/quitar_cjk.py <archivo.py> [...]
"""
import io
import sys

SECUENCIAS = [
    ("、重庆", " acogerse "),
    ("价值和", " y valoran a "),
    ("switch de氧 de", "switch de"),
    ("America/Santiago统一", "America/Santiago"),
    ("升级 a una versión", "actualización a una versión"),
]


def main(rutas):
    total = 0
    for ruta in rutas:
        with io.open(ruta, encoding="utf-8") as fh:
            texto = fh.read()
        original = texto
        for viejo, nuevo in SECUENCIAS:
            texto = texto.replace(viejo, nuevo)
        if texto != original:
            with io.open(ruta, "w", encoding="utf-8", newline="\n") as fh:
                fh.write(texto)
            print("%s: corregido" % ruta.rsplit("\\", 1)[-1])
            total += 1
    print("archivos corregidos: %d" % total)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))