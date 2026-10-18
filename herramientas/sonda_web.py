"""Sonda puntual del sitio: compruebaWordPress y xmlrpc.php desde el exterior.

Uso:  python herramientas/sonda_web.py <dominio>
"""
import io
import os
import re
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

from spaudit.red import Red  # noqa: E402


def main(dominio):
    red = Red(timeout=12, cache_path=None)

    inicio = red.http("https://%s/" % dominio)
    print("INICIO https://%s/ -> HTTP %s" % (dominio, inicio.get("estado")))
    generador = re.search(r'<meta name="generator" content="([^"]+)"', inicio.get("cuerpo", ""))
    print("  meta generator: %s" % (generador.group(1) if generador else "no declarado"))
    print("  server: %s" % inicio.get("cabeceras", {}).get("server"))
    print("  enlaces a xmlrpc: %s" % bool(re.search(r"xmlrpc\.php", inicio.get("cuerpo", ""))))
    cookie = inicio.get("cabeceras", {}).get("set-cookie", "")
    print("  cookie: %s" % (cookie[:120] if cookie else "ninguna"))

    xmlrpc = red.http("https://%s/xmlrpc.php" % dominio, metodo="POST")
    print("")
    print("XMLRPC https://%s/xmlrpc.php (POST) -> HTTP %s" % (dominio, xmlrpc.get("estado")))
    cuerpo = xmlrpc.get("cuerpo", "")[:300].replace("\n", " ")
    print("  respuesta: %s" % cuerpo)

    listado = red.http("https://%s/xmlrpc.php?rsd" % dominio)
    print("XMLRPC ?rsd -> HTTP %s" % listado.get("estado"))

    http_plano = red.http("http://%s/" % dominio)
    print("")
    print("HTTP plano http://%s/ -> HTTP %s (url final %s)"
          % (dominio, http_plano.get("estado"), http_plano.get("url_final")))

    robots = red.http("https://%s/robots.txt" % dominio)
    print("")
    print("robots.txt -> HTTP %s" % robots.get("estado"))
    if robots.get("estado") == 200:
        mapa = re.findall(r"^Sitemap:\s*(\S+)", robots.get("cuerpo", ""), re.M)
        print("  sitemaps: %s" % (", ".join(mapa[:5]) if mapa else "ninguno declarado"))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "saintpatricktemuco.cl")