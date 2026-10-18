"""Carga de evidencia desde la carpeta `evidencia/`.

Regla de oro del motor: si no hay evidencia, el resultado es NO VERIFICADO,
nunca "cumple". Un control no verificado es una invitation a verificar, no un
control que pasa.
"""

import csv
import io
import os

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CARPETA_POR_DEFECTO = os.path.join(RAIZ, "evidencia")


class Evidencia(object):
    """Busca y lee los archivos de evidencia con tolerancia a formatos y carpetas.

    El control declara el archivo como `red/net_accounts.txt`, pero quien lo
    entrega puede haberlo dejado en la raíz de la carpeta. Por eso se indexa
    toda la carpeta y se acepta tanto la ruta relativa como el nombre de archivo,
    siempre que el nombre sea único dentro de la evidencia entregada.
    """

    def __init__(self, carpeta=None):
        self.carpeta = carpeta or CARPETA_POR_DEFECTO
        self._cache = {}
        self._indice = None
        self._por_nombre = {}

    # ---------------------------------------------------------------- rutas
    def _construir_indice(self):
        if self._indice is not None:
            return
        self._indice = {}
        self._por_nombre = {}
        if not os.path.isdir(self.carpeta):
            return
        for base, _dirs, files in os.walk(self.carpeta):
            for nombre in files:
                completa = os.path.join(base, nombre)
                rel = os.path.relpath(completa, self.carpeta).replace(os.sep, "/")
                self._indice[rel.lower()] = completa
                self._por_nombre.setdefault(nombre.lower(), []).append(completa)

    def ruta(self, nombre):
        """Resuelve un nombre de evidencia a una ruta real."""
        self._construir_indice()
        clave = nombre.replace("\\", "/").lower()
        if clave in self._indice:
            return self._indice[clave]
        base = nombre.rsplit("/", 1)[-1].lower()
        candidatos = self._por_nombre.get(base, [])
        if len(candidatos) == 1:
            return candidatos[0]
        return os.path.join(self.carpeta, *nombre.replace("/", os.sep).split("/"))

    def existe(self, nombre):
        self._construir_indice()
        clave = nombre.replace("\\", "/").lower()
        if clave in self._indice:
            return True
        base = nombre.rsplit("/", 1)[-1].lower()
        return len(self._por_nombre.get(base, [])) == 1

    def archivos(self, sufijo=None):
        """Lista los archivos presentes, para mostrar en el informe."""
        self._construir_indice()
        encontrados = []
        for clave, completa in sorted(self._indice.items()):
            nombre = os.path.basename(completa)
            if sufijo and not nombre.lower().endswith(sufijo):
                continue
            encontrados.append(clave)
        return encontrados

    # ------------------------------------------------------------- lectura
    def texto(self, nombre):
        """Devuelve el contenido como texto, o None si no existe o no se puede leer."""
        clave = ("texto", nombre)
        if clave in self._cache:
            return self._cache[clave]
        ruta = self.ruta(nombre)
        contenido = None
        if os.path.isfile(ruta):
            for codificacion in ("utf-8-sig", "cp1252", "latin-1"):
                try:
                    with io.open(ruta, "r", encoding=codificacion) as fh:
                        contenido = fh.read()
                    break
                except (UnicodeDecodeError, ValueError):
                    continue
            else:
                contenido = None
        self._cache[clave] = contenido
        return contenido

    def csv(self, nombre):
        """Devuelve (cabecera, filas) como listas de cadenas, o (None, None)."""
        clave = ("csv", nombre)
        if clave in self._cache:
            return self._cache[clave]
        texto = self.texto(nombre)
        resultado = (None, None)
        if texto:
            try:
                lector = csv.DictReader(io.StringIO(texto))
                filas = [dict((k or "", (v or "").strip()) for k, v in fila.items())
                         for fila in lector]
                resultado = ([c.strip() for c in (lector.fieldnames or [])], filas)
            except csv.Error:
                resultado = (None, None)
        self._cache[clave] = resultado
        return resultado

    def buscar(self, nombre, patron, ignorecase=True):
        """True si el patrón aparece en el texto del archivo."""
        texto = self.texto(nombre)
        if texto is None:
            return None
        return _buscar(texto, patron, ignorecase)

    def existe_patron(self, nombre, patron):
        """Como buscar(), pero devuelve False en vez de None si falta el archivo."""
        valor = self.buscar(nombre, patron)
        return bool(valor)


def _buscar(texto, patron, ignorecase=True):
    import re
    flags = re.IGNORECASE if ignorecase else 0
    return re.search(patron, texto, flags) is not None