"""Comprobaciones en vivo: DNS, TLS, cabeceras HTTP y puertos de la LAN.

Son consultas de sólo lectura y sin carga. Todo se cachea en
`salida/evidencia_viva.json` para que una segunda corrida no vuelva a tocar la
red y para que el informe guarde la evidencia aunque se ejecute sin red.
"""

import json
import os
import socket
import ssl
import sys
import time

try:
    from urllib.request import Request, urlopen
    from urllib.error import HTTPError, URLError
except ImportError:  # pragma: no cover - Python 2 no está soportado
    sys.exit("spaudit necesita Python 3.8 o superior")

import ssl as _ssl  # noqa: F401  (usado abajo)

USER_AGENT = "spaudit/1.0 (auditoria de cumplimiento Saint Patrick School)"
RESOLVEDORES = [
    ("Google", "https://dns.google/resolve"),
    ("Cloudflare", "https://cloudflare-dns.com/dns-query"),
]

CABECERAS_SEGURIDAD = [
    ("strict-transport-security", "HSTS"),
    ("content-security-policy", "CSP"),
    ("x-content-type-options", "X-Content-Type-Options"),
    ("x-frame-options", "X-Frame-Options"),
    ("referrer-policy", "Referrer-Policy"),
]

# Puertos típicos de gestión de grabadores de video (DVR/NVR).
PUERTOS_DVR = [80, 443, 554, 37777, 8000, 34567, 9000]


class Red(object):
    """Cliente de comprobaciones de red con caché en disco."""

    def __init__(self, timeout=8.0, cache_path=None):
        self.timeout = timeout
        self.cache_path = cache_path
        self.resultados = {}
        self.errores = []
        if cache_path and os.path.isfile(cache_path):
            try:
                with open(cache_path, "r", encoding="utf-8") as fh:
                    self.resultados = json.load(fh).get("consultas", {})
            except (ValueError, OSError):
                self.resultados = {}

    # -------------------------------------------------------------- helpers
    def _guardar(self):
        if not self.cache_path:
            return
        carpeta = os.path.dirname(self.cache_path)
        if carpeta and not os.path.isdir(carpeta):
            os.makedirs(carpeta, exist_ok=True)
        with open(self.cache_path, "w", encoding="utf-8") as fh:
            json.dump({"generado": time.strftime("%Y-%m-%d %H:%M:%S"),
                       "consultas": self.resultados}, fh, indent=2, ensure_ascii=False)

    def _cache(self, clave):
        return self.resultados.get(clave)

    # ----------------------------------------------------------------- DNS
    def dns(self, nombre, tipo="TXT"):
        """Consulta DNS sobre HTTPS (no necesita librerías externas)."""
        clave = "dns:%s:%s" % (nombre.lower(), tipo)
        if clave in self.resultados:
            return self.resultados[clave]

        salida = {"ok": False, "tipo": tipo, "nombre": nombre, "respuestas": [],
                  "error": None}
        for etiqueta, base in RESOLVEDORES:
            url = "%s?name=%s&type=%s" % (base, nombre, tipo)
            cabeceras = {"User-Agent": USER_AGENT, "Accept": "application/dns-json"}
            if "cloudflare" in base:
                cabeceras["Accept"] = "application/dns-json"
            try:
                peticion = Request(url, headers=cabeceras)
                with urlopen(peticion, timeout=self.timeout) as respuesta:
                    cuerpo = json.loads(respuesta.read().decode("utf-8", "replace"))
                salida["ok"] = True
                salida["resolutor"] = etiqueta
                salida["respuestas"] = [a.get("data", "") for a in cuerpo.get("Answer", [])]
                salida["codigo"] = cuerpo.get("Status")
                break
            except (HTTPError, URLError, ValueError, socket.timeout, OSError) as exc:
                salida["error"] = "%s: %s" % (etiqueta, exc)
        else:
            self.errores.append("DNS %s %s: %s" % (tipo, nombre, salida["error"]))

        self.resultados[clave] = salida
        return salida

    def texto_dns(self, nombre, tipo="TXT"):
        """Devuelve los registros como lista de cadenas, o None si falla la consulta."""
        r = self.dns(nombre, tipo)
        if not r.get("ok"):
            return None
        return r.get("respuestas") or []

    # ----------------------------------------------------------------- TLS
    def tls(self, host, puerto=443):
        """Negociación TLS: versión, cifrado y vigencia del certificado."""
        clave = "tls:%s:%s" % (host, puerto)
        if clave in self.resultados:
            return self.resultados[clave]

        salida = {"ok": False, "host": host, "puerto": puerto, "error": None}
        contexto = ssl.create_default_context()
        try:
            with socket.create_connection((host, puerto), timeout=self.timeout) as crudo:
                with contexto.wrap_socket(crudo, server_hostname=host) as tls:
                    cert = tls.getpeercert()
                    salida.update({
                        "ok": True,
                        "version": tls.version(),
                        "cifrado": (tls.cipher() or (None,))[0],
                        "emisor": dict(x[0] for x in cert.get("issuer", ())).get("organizationName"),
                        "sujeto": dict(x[0] for x in cert.get("subject", ())).get("commonName"),
                        "vigente_desde": cert.get("notBefore"),
                        "vigente_hasta": cert.get("notAfter"),
                        "dns_names": [v for k, v in cert.get("subjectAltName", ())
                                      if k == "DNS"],
                    })
        except (ssl.SSLError, socket.timeout, OSError) as exc:
            salida["error"] = "%s: %s" % (type(exc).__name__, exc)
            self.errores.append("TLS %s:%s -> %s" % (host, puerto, salida["error"]))

        self.resultados[clave] = salida
        return salida

    # ---------------------------------------------------------------- HTTP
    def http(self, url, metodo="GET", max_bytes=200000):
        """Petición HTTP; devuelve estado, cabeceras, redirecciones y cuerpo parcial."""
        clave = "http:%s:%s" % (url, metodo)
        if clave in self.resultados:
            return self.resultados[clave]

        salida = {"ok": False, "url": url, "estado": None, "cabeceras": {},
                  "redireccion": None, "cuerpo": "", "error": None}

        def peticion(destino, restantes=0):
            req = Request(destino, method=metodo,
                          headers={"User-Agent": USER_AGENT,
                                   "Accept": "text/html,application/json,*/*"})
            urlopen_request = req
            try:
                with urlopen(urlopen_request, timeout=self.timeout) as resp:
                    salida["estado"] = resp.status
                    salida["url_final"] = resp.url
                    salida["cabeceras"] = {k.lower(): v for k, v in resp.headers.items()}
                    cuerpo = resp.read(max_bytes)
                    salida["cuerpo"] = cuerpo.decode("utf-8", "replace")
                    salida["ok"] = True
            except HTTPError as exc:
                salida["estado"] = exc.code
                salida["url_final"] = exc.url if hasattr(exc, "url") else destino
                salida["cabeceras"] = {k.lower(): v for k, v in exc.headers.items()}
                try:
                    salida["cuerpo"] = exc.read(max_bytes).decode("utf-8", "replace")
                except Exception:
                    salida["cuerpo"] = ""
                salida["ok"] = True  # un 4xx/5xx es un resultado válido, no un error
            except (URLError, socket.timeout, OSError) as exc:
                salida["error"] = "%s: %s" % (type(exc).__name__, exc)

        peticion(url)
        self.resultados[clave] = salida
        return salida

    # ----------------------------------------------------------------- TCP
    def tcp(self, host, puerto, timeout=None):
        """Comprueba si un puerto TCP acepta conexiones desde donde corre la auditoría."""
        clave = "tcp:%s:%s" % (host, puerto)
        if clave in self.resultados:
            return self.resultados[clave]

        salida = {"ok": False, "host": host, "puerto": puerto, "abierto": False,
                  "error": None, "tiempo_ms": None}
        inicio = time.time()
        try:
            conexion = socket.create_connection((host, puerto),
                                                timeout=timeout or min(self.timeout, 3.0))
            conexion.close()
            salida.update({"ok": True, "abierto": True})
        except (socket.timeout, OSError) as exc:
            salida["error"] = "%s: %s" % (type(exc).__name__, exc)
        salida["tiempo_ms"] = int((time.time() - inicio) * 1000)
        self.resultados[clave] = salida
        return salida

    # --------------------------------------------------------------- utils
    def comprobar_cabeceras(self, url):
        """Evalúa las cabeceras de seguridad de una URL. Devuelve (ok, detalle, datos)."""
        r = self.http(url)
        if not r.get("ok"):
            return False, "No se pudo consultar %s (%s)" % (url, r.get("error")), r
        cabeceras = r.get("cabeceras", {})
        presentes, ausentes = [], []
        for clave, nombre in CABECERAS_SEGURIDAD:
            (presentes if clave in cabeceras else ausentes).append(nombre)
        if not _es_https(url):
            ausentes.append("HTTPS (la comprobación se hizo por HTTP)")
        if not ausentes:
            return True, "El sitio envía todas las cabeceras de seguridad evaluadas.", r
        return (False,
                "El sitio no envía %s." % _enumerar(ausentes), r)

    def guardar(self):
        self._guardar()


def _es_https(url):
    return url.lower().startswith("https://")


def _enumerar(items):
    """'a', 'a y b', 'a, b y c'."""
    if not items:
        return ""
    if len(items) == 1:
        return items[0]
    return "%s y %s" % (", ".join(items[:-1]), items[-1])