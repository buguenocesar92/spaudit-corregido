# -*- coding: utf-8 -*-
"""Comprueba que un marcador de "no se pudo leer" NO se reporte como incumplimiento.

Se escribe evidencia sintetica en una carpeta temporal y se corre el verificador
real de spaudit. La pregunta no es si el texto cambio, sino si cambia el
veredicto: antes, "sin permiso" caia en NO_DEFINIDO y producia NO_CUMPLE.

    python herramientas\\probar_marcadores.py
"""
import io
import os
import shutil
import sys
import tempfile

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

from spaudit import checks
from spaudit.evidencia import Evidencia


class Contexto(object):
    def __init__(self, carpeta):
        self.evidencia = Evidencia(carpeta)


def correr(carpeta, verificador, params, archivo):
    p = dict(params)
    p.setdefault("archivo", os.path.basename(archivo))
    return verificador(Contexto(carpeta), p)


CASOS = [
    # (nombre, archivo, contenido, verificador, params, estado esperado)
    ("clave ausente = incumplimiento real",
     "registry_seguridad.txt",
     "HKLM:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\LAPS :: "
     "ConfigureLAPSRootKey = <no definido>",
     checks.texto_presente,
     {"patron": "LAPS|ManagedPassword"},
     checks.NO_CUMPLE),

    ("sin permiso NO es incumplimiento",
     "registry_seguridad.txt",
     "HKLM:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\LAPS :: "
     "ConfigureLAPSRootKey = <sin permiso de lectura>",
     checks.texto_presente,
     {"patron": "LAPS|ManagedPassword"},
     checks.NO_VERIFICADO),

    ("N/A de Defender NO es incumplimiento",
     "registry_seguridad.txt",
     "HKLM:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\LAPS :: "
     "ConfigureLAPSRootKey = N/A: Must be an administrator to view it",
     checks.texto_presente,
     {"patron": "LAPS|ManagedPassword"},
     checks.NO_VERIFICADO),

    ("si hay evidencia de ausencia, manda la ausencia",
     "registry_seguridad.txt",
     "HKLM:\\...\\LAPS :: A = <sin permiso de lectura>\n"
     "HKLM:\\...\\LAPS :: B = <no definido>",
     checks.texto_presente,
     {"patron": "LAPS|ManagedPassword"},
     checks.NO_CUMPLE),

    ("valor real = cumple",
     "registry_seguridad.txt",
     "HKLM:\\...\\LAPS :: ConfigureLAPSRootKey = 1",
     checks.texto_presente,
     {"patron": "LAPS|ManagedPassword"},
     checks.CUMPLE),

    ("literal antiguo se mantiene retrocompatible",
     "registry_seguridad.txt",
     "HKLM:\\...\\LAPS :: ConfigureLAPSRootKey = <no definido o sin permiso>",
     checks.texto_presente,
     {"patron": "LAPS|ManagedPassword"},
     checks.NO_CUMPLE),

    ("Defender: preferencia no informada no es incumplimiento",
     "defender_preferencias.txt",
     "DisableRemovableMediaExecution = <no informado>\n"
     "RemovableMediaScan = <no informado>",
     checks.config_valores,
     {"valores": [{"clave": "DisableRemovableMediaExecution",
                   "operador": "activo"},
                  {"clave": "RemovableMediaScan",
                   "operador": "activo"}]},
     checks.NO_VERIFICADO),

    ("Defender: las tres protecciones encendidas = cumple",
     "defender_preferencias.txt",
     "DisableRealtimeMonitoring = False\n"
     "DisableBehaviorMonitoring = False\n"
     "DisableScriptScanning = False",
     checks.config_valores,
     {"valores": [{"clave": "DisableRealtimeMonitoring",
                   "operador": "desactivado"},
                  {"clave": "DisableBehaviorMonitoring",
                   "operador": "desactivado"},
                  {"clave": "DisableScriptScanning",
                   "operador": "desactivado"}]},
     checks.CUMPLE),

    ("Defender: proteccion apagada SI es incumplimiento",
     "defender_preferencias.txt",
     "DisableRealtimeMonitoring = True\n"
     "DisableBehaviorMonitoring = True\n"
     "DisableScriptScanning = True",
     checks.config_valores,
     {"valores": [{"clave": "DisableRealtimeMonitoring",
                   "operador": "desactivado"},
                  {"clave": "DisableBehaviorMonitoring",
                   "operador": "desactivado"},
                  {"clave": "DisableScriptScanning",
                   "operador": "desactivado"}]},
     checks.NO_CUMPLE),

    ("Defender: lo ilegible manda sobre lo evaluado",
     # Criterio del motor: si alguna regla del control no se pudo leer, NO se
     # pronuncia veredicto, ni siquiera parcial. Un PARCIAL implicaria que ya se
     # miro todo lo que habia que mirar.
     "defender_preferencias.txt",
     "DisableRealtimeMonitoring = False\n"
     "DisableBehaviorMonitoring = <no informado>",
     checks.config_valores,
     {"valores": [{"clave": "DisableRealtimeMonitoring",
                   "operador": "desactivado"},
                  {"clave": "DisableBehaviorMonitoring",
                   "operador": "desactivado"}]},
     checks.NO_VERIFICADO),

    # --- Un control negativo sobre una lista vacía ----------------------------
    #
    # "No hay cuentas Guest" sacado de un archivo SIN CUENTAS no es un
    # cumplimiento: es una afirmación vacía. El recolector ahora escribe la
    # cabecera aunque no haya filas, y sin esta guarda ese caso salía CUMPLE.

    ("lista vacía NO es cumplimiento (control negativo)",
     "usuarios_ad.csv",
     '"SamAccountName","Enabled"\n',
     checks.csv_sin_filas,
     {"columna": "SamAccountName", "patron": "^(guest|invitado)$",
      "col_booleano": "Enabled", "col_booleano_esperado": "False"},
     checks.NO_VERIFICADO),

    ("lista con filas y ninguna coincide = cumplimiento",
     "usuarios_ad.csv",
     '"SamAccountName","Enabled"\n"jperez","True"\n"mlopez","True"\n',
     checks.csv_sin_filas,
     {"columna": "SamAccountName", "patron": "^(guest|invitado)$",
      "col_booleano": "Enabled", "col_booleano_esperado": "False"},
     checks.CUMPLE),

    ("lista con una fila que coincide = incumplimiento",
     "usuarios_ad.csv",
     '"SamAccountName","Enabled"\n"jperez","True"\n"invitado","True"\n',
     checks.csv_sin_filas,
     {"columna": "SamAccountName", "patron": "^(guest|invitado)$",
      "col_booleano": "Enabled", "col_booleano_esperado": "False"},
     checks.NO_CUMPLE),

    ("lista con una fila bien deshabilitada = cumplimiento",
     # La mitad del bug anterior: esta fila está como debe, y salía
     # reportada como incumplimiento.
     "usuarios_ad.csv",
     '"SamAccountName","Enabled"\n"jperez","True"\n"invitado","False"\n',
     checks.csv_sin_filas,
     {"columna": "SamAccountName", "patron": "^(guest|invitado)$",
      "col_booleano": "Enabled", "col_booleano_esperado": "False"},
     checks.CUMPLE),

    ("boolean que no se puede interpretar no es veredicto",
     "usuarios_ad.csv",
     '"SamAccountName","Enabled"\n"invitado","?"\n',
     checks.csv_sin_filas,
     {"columna": "SamAccountName", "patron": "^(guest|invitado)$",
      "col_booleano": "Enabled", "col_booleano_esperado": "False"},
     checks.NO_VERIFICADO),
]


def main():
    tmp = tempfile.mkdtemp(prefix="spaudit-marcadores-")
    fallos = []
    try:
        print("")
        print("  caso                                             esperado     obtenido")
        print("  " + "-" * 84)
        for nombre, archivo, contenido, verif, params, esperado in CASOS:
            ruta = os.path.join(tmp, archivo)
            with io.open(ruta, "w", encoding="utf-8") as fh:
                fh.write(contenido)
            estado, _motivo, _ev = correr(tmp, verif, params, ruta)
            ok = estado == esperado
            if not ok:
                fallos.append((nombre, esperado, estado))
            print("  %-48s %-12s %-12s %s"
                  % (nombre[:48], esperado, estado, "OK" if ok else "FALLA"))

        print("")
        if fallos:
            print("  %d CASO(S) CON RESULTADO INESPERADO" % len(fallos))
            for nombre, esperado, estado in fallos:
                print("    %s: se esperaba %s, salio %s" % (nombre, esperado, estado))
            return 1
        print("  %d/%d casos correctos" % (len(CASOS), len(CASOS)))
        return 0
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())