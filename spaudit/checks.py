"""Verificadores: cada uno toma un control y devuelve un veredicto con evidencia.

Firmas de todos los verificadores:

    fn(contexto) -> (estado, detalle, evidencia)

`estado` es una de las constantes de controles_comunes. Si falta la evidencia,
el resultado SIEMPRE es NO_VERIFICADO con el nombre del archivo que falta: nunca
se infiere cumplimiento.
"""

import datetime
import json
import re

from .controles_comunes import (
    CUMPLE, NO_CUMPLE, PARCIAL, NO_VERIFICADO, NO_APLICA,
)

HOY = datetime.date.today()


# --------------------------------------------------------------------- utils
def _falta(contexto, archivo, que):
    return (NO_VERIFICADO,
            "No hay evidencia para verificar %s. Falta el archivo `%s`." % (que, archivo),
            "")


def _csv(contexto, archivo):
    return contexto.evidencia.csv(archivo)


def _booleano(valor):
    """Interpreta las formas habituales de un booleano en un CSV."""
    if valor is None:
        return None
    v = str(valor).strip().lower()
    if v in ("true", "sí", "si", "yes", "1", "verdadero", "habilitado", "on"):
        return True
    if v in ("false", "no", "0", "falso", "deshabilitado", "off"):
        return False
    return None


def _entero(valor):
    if valor is None:
        return None
    m = re.search(r"-?\d+", str(valor))
    return int(m.group(0)) if m else None


def _fecha(valor):
    if not valor:
        return None
    texto = str(valor).strip()
    for formato in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%d/%m/%Y"):
        try:
            return datetime.datetime.strptime(texto[:19], formato).date()
        except ValueError:
            continue
    return None


# ------------------------------------------------------- política de dominio
CLAVES_NET_ACCOUNTS = {
    "history": ["contraseñas memorizadas", "password history"],
    "max_password_age": ["duración máxima de la contraseña", "maximum password age"],
    "min_password_age": ["duración mínima de la contraseña", "minimum password age"],
    "min_len": ["longitud mínima de la contraseña", "minimum password length"],
    "complexity": ["requisitos de complejidad", "complexity requirements",
                   "cumplir los requisitos"],
    "lockout_threshold": ["umbral de bloqueo de cuenta", "account lockout threshold"],
    "lockout_minutes": ["duración del bloqueo de cuenta", "account lockout duration"],
}


def ad_password_policy(contexto, params):
    """Lee `net accounts` y compara con el valor que el manual declara."""
    archivo = params.get("archivo", "net_accounts.txt")
    texto = contexto.evidencia.texto(archivo)
    if texto is None:
        return _falta(contexto, archivo, "la política de contraseñas del dominio")

    clave = params["clave"]
    patrones = CLAVES_NET_ACCOUNTS.get(clave, [clave])
    valor = None
    linea_encontrada = None
    for linea in texto.splitlines():
        bajo = linea.lower()
        if any(p in bajo for p in patrones):
            partes = linea.split()
            if partes:
                valor = partes[-1].strip().rstrip(".")
                linea_encontrada = linea.strip()
            break

    if valor is None:
        return (NO_VERIFICADO,
                "Se encontró el archivo pero no la línea de '%s'. El formato de salida de "
                "`net accounts` puede haber cambiado." % clave,
                linea_encontrada or "")

    if "esperado" in params:
        real = _booleano(valor)
        if real is None:
            return (NO_VERIFICADO, "No se pudo interpretar el valor '%s'." % valor, linea_encontrada)
        if real == params["esperado"]:
            return (CUMPLE, "El manual declara %s y la configuración coincide." % linea_encontrada,
                    linea_encontrada)
        return (NO_CUMPLE,
                "El manual declara %s, pero la configuración real difiere." % linea_encontrada,
                linea_encontrada)

    real = _entero(valor)
    if real is None:
        if valor.lower() in ("nunca", "never"):
            real = 0
        else:
            return (NO_VERIFICADO, "No se pudo interpretar el valor '%s'." % valor, linea_encontrada)

    if "minimo" in params and real < params["minimo"]:
        return (NO_CUMPLE,
                "Valor actual %d; el estándar de referencia exige al menos %d. El manual "
                "declara un valor inferior." % (real, params["minimo"]),
                linea_encontrada)
    if "maximo" in params and real > params["maximo"]:
        return (NO_CUMPLE,
                "Valor actual %d; se admite un máximo de %d." % (real, params["maximo"]),
                linea_encontrada)
    return (CUMPLE, "Valor actual %d, dentro de lo esperado." % real, linea_encontrada)


def ad_audit_policy(contexto, params):
    """Verifica que las subcategorías de auditoría existan y registren los fallos."""
    archivo = params.get("archivo", "auditpol.txt")
    texto = contexto.evidencia.texto(archivo)
    if texto is None:
        return _falta(contexto, archivo, "la configuración de auditoría del servidor")

    pedidas = params.get("subcategorias", [])
    lineas = texto.splitlines()
    con_fallo, sin_fallo, ausentes = [], [], []
    for sub in pedidas:
        encontrada = None
        for linea in lineas:
            if sub.lower() in linea.lower():
                encontrada = linea.strip()
                break
        if encontrada is None:
            ausentes.append(sub)
        elif re.search(r"failure|fallo", encontrada, re.I):
            con_fallo.append(sub)
        else:
            sin_fallo.append(sub)

    evidencia = "Subcategorías con registro de fallos: %d/%d" % (len(con_fallo), len(pedidas))
    if ausentes and len(ausentes) == len(pedidas):
        return (NO_VERIFICADO,
                "El archivo no parece una salida de `auditpol`: no se encontró ninguna de "
                "las subcategorías buscadas. Verifique que el script lo haya generado con "
                "`auditpol /get /subcategory:*`.", evidencia)
    if not ausentes and not sin_fallo:
        return (CUMPLE, "Las %d subcategorías declaradas están configuradas y registran "
                        "éxitos y fallos." % len(pedidas), evidencia)
    problemas = []
    if sin_fallo:
        problemas.append("sin registrar fallos: %s" % ", ".join(sin_fallo))
    if ausentes:
        problemas.append("no configuradas: %s" % ", ".join(ausentes))
    return (PARCIAL, "Auditoría incompleta (%s). Sin registro de fallos no hay forma de "
                     "investigar un incidente." % "; ".join(problemas), evidencia)


# -------------------------------------------------------------------- CSV
def csv_columnas(contexto, params):
    archivo = params["archivo"]
    cabecera, filas = _csv(contexto, archivo)
    if cabecera is None:
        return _falta(contexto, archivo, "el archivo de datos")
    faltantes = [c for c in params.get("requeridas", []) if c not in cabecera]
    minimo = params.get("minimo_filas", 1)
    if faltantes:
        return (NO_VERIFICADO,
                "El archivo existe pero no tiene las columnas esperadas (%s). Columnas "
                "encontradas: %s." % (", ".join(faltantes), ", ".join(cabecera)),
                "%d columnas, %d filas" % (len(cabecera), len(filas)))
    if len(filas) < minimo:
        return (PARCIAL,
                "El archivo tiene las columnas correctas pero sólo %d filas (se esperaban "
                "al menos %d). ¿Está la extracción completa?" % (len(filas), minimo),
                "%d filas" % len(filas))
    return (CUMPLE, "El archivo tiene las columnas esperadas y %d filas." % len(filas),
            "%d filas" % len(filas))


def csv_booleano(contexto, params):
    """Revisa que una columna booleana esté activa en todas las filas."""
    archivo = params["archivo"]
    cabecera, filas = _csv(contexto, archivo)
    if cabecera is None:
        return _falta(contexto, archivo, "el estado de activación")
    columna = params["columna"]
    if columna not in cabecera:
        return (NO_VERIFICADO,
                "El archivo no tiene la columna '%s'. Columnas: %s."
                % (columna, ", ".join(cabecera)), "")
    valores = [_booleano(f.get(columna)) for f in filas]
    activos = sum(1 for v in valores if v is True)
    inactivos = [f for f, v in zip(filas, valores) if v is False]
    desconocidos = sum(1 for v in valores if v is None)
    pct = int(100.0 * activos / len(valores)) if valores else 0
    evidencia = "%d de %d activos (%d%%)" % (activos, len(valores), pct)
    if not filas:
        return (NO_VERIFICADO, "El archivo no tiene filas.", "")
    if inactivos:
        nombres = ", ".join(str(f.get("User") or f.get("Equipo") or f.get("Nombre") or "?")
                            for f in inactivos[:8])
        extra = "..." if len(inactivos) > 8 else ""
        return (NO_CUMPLE,
                "%s. Sin activarlo en: %s%s." % (evidencia, nombres, extra), evidencia)
    if desconocidos:
        return (PARCIAL, "%s, pero %d filas tienen un valor no interpretable." % (evidencia, desconocidos),
                evidencia)
    return (CUMPLE, "Todos los registros tienen '%s' activo. %s." % (columna, evidencia), evidencia)


def csv_sin_filas(contexto, params):
    """Verifica que NO exista ninguna fila que cumpla un patrón (control negativo).

    `col_booleano_esperado` es el valor que esa columna **debería** tener para
    que la fila esté bien. La fila es un incumplimiento cuando tiene el valor
    contrario.

    POR QUÉ ESTÁ EXPLICADO TANTO. La versión anterior filtraba por
    `_booleano(...) == esperado`, o sea, conservaba las filas que estaban como
    debían y descartaba las que estaban mal. El resultado era el inverso del
    que dice el control: una cuenta Guest **habilitada** pasaba como
    cumplimiento, y una Guest correctamente deshabilitada se reportaba como
    incumplimiento. Dos controles de identidad con CUMPLE y el problema
    presente.

    Un valor que no se puede interpretar no es un incumplimiento: es
    ilegible, y sale como NO VERIFICADO.
    """
    archivo = params["archivo"]
    cabecera, filas = _csv(contexto, archivo)
    if cabecera is None:
        return _falta(contexto, archivo, "el listado de cuentas")
    columna = params["columna"]
    if columna not in cabecera:
        return (NO_VERIFICADO,
                "El archivo no tiene la columna '%s'. Columnas: %s."
                % (columna, ", ".join(cabecera)), "")
    patron = re.compile(params["patron"], re.I)
    if not filas:
        # Un control negativo sobre una lista vacía no se cumple: no hay nada
        # que revisar. "No hay cuentas Guest" sacado de un archivo sin cuentas no
        # es un cumplimiento: es una afirmación que nadie puede sostener.
        return (NO_VERIFICADO,
                "El archivo `%s` no tiene filas, así que no hay nada que revisar. "
                "Esto NO es un cumplimiento: es una lista vacía." % archivo,
                "0 filas")
    candidatas = [f for f in filas if patron.search(str(f.get(columna) or ""))]
    ilegibles = []
    col_bool = params.get("col_booleano")
    if col_bool and col_bool in cabecera:
        esperado = _booleano(params.get("col_booleano_esperado", "False"))
        valor_inesperado = []
        for f in candidatas:
            valor = _booleano(f.get(col_bool))
            if valor is None:
                ilegibles.append(f)
            elif valor != esperado:
                valor_inesperado.append(f)
        candidatas = valor_inesperado

    if candidatas:
        nombres = ", ".join(str(f.get(columna)) for f in candidatas[:10])
        return (NO_CUMPLE,
                "Se encontraron %d registros que no deberían existir: %s."
                % (len(candidatas), nombres), nombres)
    if ilegibles:
        nombres = ", ".join(str(f.get(columna)) for f in ilegibles[:10])
        return (NO_VERIFICADO,
                "%d registro(s) coinciden con el patrón pero su valor de '%s' no se pudo "
                "interpretar: %s. No se afirma que estén bien ni que estén mal."
                % (len(ilegibles), col_bool, nombres), "")
    return (CUMPLE, "No hay registros que incumplan el patrón esperado (%d filas revisadas)."
                    % len(filas), "%d filas revisadas" % len(filas))


def csv_minimo_admin(contexto, params):
    """Revisa el tamaño y composición de los grupos privilegiados."""
    archivo = params.get("archivo", "grupos_ad.csv")
    cabecera, filas = _csv(contexto, archivo)
    if cabecera is None:
        return _falta(contexto, archivo, "la composición de los grupos privilegiados")
    grupo_col = "Grupo" if "Grupo" in cabecera else (cabecera[0] if cabecera else None)
    miembro_col = "Miembro" if "Miembro" in cabecera else (
        cabecera[1] if len(cabecera) > 1 else None)
    if not grupo_col or not miembro_col:
        return (NO_VERIFICADO,
                "El archivo necesita columnas 'Grupo' y 'Miembro'. Encontradas: %s."
                % ", ".join(cabecera), "")

    privilegiados = ("domain admins", "enterprise admins", "schema admins",
                     "administradores", "domain admins")
    resumen = []
    problemas = []
    Contingencia = []
    for fila in filas:
        grupo = str(fila.get(grupo_col) or "")
        miembro = str(fila.get(miembro_col) or "")
        if not any(p in grupo.lower() for p in privilegiados):
            continue
        resumen.append("%s: %s" % (grupo, miembro))
        if miembro.lower() in ("admin", "administrator", "administrador"):
            contingencia.append(miembro)
    if not resumen:
        return (NO_VERIFICADO,
                "No se encontraron grupos privilegiados en el archivo. Revise que la "
                "extracción incluya Domain Admins y Enterprise Admins.", "")
    evidencia = "; ".join(resumen[:12])
    if contingencia:
        problemas.append("hay una cuenta de contingencia (ADMIN) dentro de un grupo "
                         "privilegiado: úsela sólo para emergencias y con alerta de uso")
    if len(resumen) > 6:
        problemas.append("hay %d cuentas en grupos privilegiados: en un colegio de este "
                         "tamaño lo razonable son 2 o 3" % len(resumen))
    if problemas:
        return (NO_CUMPLE if contingencia else PARCIAL,
                "; ".join(problemas).capitalize() + ".", evidencia)
    return (CUMPLE, "Composición de grupos privilegiados razonable (%d cuentas)." % len(resumen),
            evidencia)


def csv_bitlocker(contexto, params):
    archivo = params.get("archivo", "bitlocker.csv")
    cabecera, filas = _csv(contexto, archivo)
    if cabecera is None:
        return _falta(contexto, archivo, "el estado de cifrado de disco")
    col = None
    for candidata in ("ProtectionStatus", "EstadoProteccion", "Estado"):
        if candidata in cabecera:
            col = candidata
            break
    if col is None:
        return (NO_VERIFICADO,
                "El archivo no tiene una columna de estado de protección. Columnas: %s."
                % ", ".join(cabecera), "")
    protegidos = [f for f in filas if "on" in str(f.get(col) or "").lower()
                  or "activado" in str(f.get(col) or "").lower()]
    sin_cifrar = [f for f in filas if f not in protegidos]
    evidencia = "%d de %d volúmenes con cifrado activo" % (len(protegidos), len(filas))
    if sin_cifrar:
        nombres = ", ".join(str(f.get("Equipo") or f.get("MountPoint") or "?")
                            for f in sin_cifrar[:8])
        return (NO_CUMPLE,
                "%s. Sin cifrar en: %s. El manual no exige cifrado de disco en ningún punto."
                % (evidencia, nombres), evidencia)
    return (CUMPLE, evidencia + ".", evidencia)


def csv_antiguedad_parche(contexto, params):
    """Revisa versión del sistema operativo y antigüedad del último parche."""
    archivo = params.get("archivo", "sistema.csv")
    cabecera, filas = _csv(contexto, archivo)
    if cabecera is None:
        return _falta(contexto, archivo, "la versión y el estado de parcheo de los equipos")
    col_so = "SO" if "SO" in cabecera else ("OS" if "OS" in cabecera else None)
    col_version = "Version" if "Version" in cabecera else ("Build" if "Build" in cabecera else None)
    col_fecha = None
    for candidata in ("UltimaActualizacion", "UltimoParche", "LastPatched", "FechaParche"):
        if candidata in cabecera:
            col_fecha = candidata
            break
    if not col_so:
        return (NO_VERIFICADO,
                "El archivo necesita una columna de sistema operativo. Columnas: %s."
                % ", ".join(cabecera), "")

    # Versiones fuera de soporte (Microsoft Lifecycle).
    SIN_SOPORTE = [
        (r"2003|2008|2008\s*r2", "Windows Server 2008 (R2)"),
        (r"2012(\s*r2)?\b", "Windows Server 2012 / 2012 R2"),
        (r"windows\s*7\b", "Windows 7"),
        (r"windows\s*8(\.1)?\b", "Windows 8 / 8.1"),
    ]

    problemas, avisos, detalles = [], [], []
    for fila in filas:
        equipo = str(fila.get("Equipo") or fila.get("Nombre") or "?")
        so = str(fila.get(col_so) or "")
        version = str(fila.get(col_version) or "") if col_version else ""
        texto = ("%s %s" % (so, version)).lower()
        detalles.append("%s -> %s %s" % (equipo, so, version))

        for patron, nombre in SIN_SOPORTE:
            if re.search(patron, texto):
                problemas.append("%s tiene %s, fuera de soporte" % (equipo, nombre))

        if col_fecha and fila.get(col_fecha):
            fecha = _fecha(fila.get(col_fecha))
            if fecha:
                dias = (HOY - fecha).days
                if dias > 120:
                    problemas.append("%s: último parche hace %d días" % (equipo, dias))
                elif dias > 45:
                    avisos.append("%s: último parche hace %d días" % (equipo, dias))
                else:
                    detalles.append("  %s parcheado hace %d días" % (equipo, dias))
            else:
                avisos.append("%s: no se pudo leer la fecha del último parche" % equipo)

    evidencia = "; ".join(detalles[:10])
    if problemas:
        return (NO_CUMPLE,
                "Gestión de parches insuficiente: %s. El manual no define ninguna "
                "política de actualización." % "; ".join(problemas), evidencia)
    if avisos:
        return (PARCIAL, "Revisar: %s." % "; ".join(avisos), evidencia)
    return (CUMPLE, "Todos los equipos reportados están con soporte vigente y parcheados "
                    "recientemente.", evidencia)


def respaldo_trabajos(contexto, params):
    """Revisa el historial de tareas de respaldo: fallos y antigüedad."""
    archivo = params.get("archivo", "respaldo_trabajos.csv")
    cabecera, filas = _csv(contexto, archivo)
    if cabecera is None:
        return _falta(contexto, archivo, "el historial de tareas de respaldo")
    col_fecha = None
    for candidata in ("UltimaEjecucion", "UltimaEjecucionExitosa", "Fecha"):
        if candidata in cabecera:
            col_fecha = candidata
            break
    col_ok = None
    for candidata in ("Exito", "Resultado", "Estado"):
        if candidata in cabecera:
            col_ok = candidata
            break

    fallos, antiguos, detalles = [], [], []
    for fila in filas:
        trabajo = str(fila.get("Trabajo") or fila.get("Nombre") or "?")
        if col_ok and _booleano(fila.get(col_ok)) is False:
            fallos.append(trabajo)
        if col_fecha and fila.get(col_fecha):
            fecha = _fecha(fila.get(col_fecha))
            if fecha:
                dias = (HOY - fecha).days
                detalles.append("%s: %d días" % (trabajo, dias))
                if dias > 3:
                    antiguos.append("%s (%d días)" % (trabajo, dias))
            else:
                antiguos.append("%s (fecha ilegible)" % trabajo)
        else:
            antiguos.append("%s (sin fecha de última ejecución)" % trabajo)

    evidencia = "; ".join(detalles[:12])
    if fallos:
        return (NO_CUMPLE,
                "Hay %d tareas de respaldo con error en la última ejecución: %s. Un "
                "respaldo que falla en silencio no es un respaldo." % (len(fallos), ", ".join(fallos[:8])),
                evidencia)
    if antiguos:
        return (PARCIAL,
                "%d tareas sin ejecución reciente (más de 3 días o sin fecha): %s."
                % (len(antiguos), ", ".join(antiguos[:8])), evidencia)
    return (CUMPLE, "Todas las tareas reportadas se ejecutaron correctamente en los últimos "
                    "3 días.", evidencia)


# ------------------------------------------------------------ texto simple
# Dos clases de marcador que el recolector escribe, y que NO son lo mismo:
#
#   <no definido>  -> se consultó la clave y no existe. Es EVIDENCIA, y para
#                     estos controles que falte es justamente el incumplimiento.
#   <sin permiso de lectura>, <no informado>, "N/A: ..." -> se intentó y no se
#                     pudo. Eso NO es evidencia de nada, y contarlo como
#                     incumplimiento convierte ignorancia en hallazgo falso.
#
# Medido contra el recolector real: Get-ItemProperty lanza
# ItemNotFoundException o PSArgumentException cuando la clave o la propiedad no
# existen, y SecurityException cuando el acceso se deniega. Get-MpPreference
# devuelve el literal "N/A: Must be an administrator to view ..." cuando el
# proceso no es administrador. Son tres hechos distintos y el recolector ahora
# los escribe por separado.
#
# Los archivos recolectados con la versión anterior usan el literal combinado
# "<no definido o sin permiso>", que sigue cayendo en NO_DEFINIDO: no cambia el
# comportamiento de evidencia ya recogida, solo el de la nueva.
SIN_LECTURA = re.compile(r"<\s*sin permiso|<\s*no informado|N/?A\s*:|access denied|"
                         r"must be an administrator|"
                         r"se requiere el modulo de Active Directory", re.I)
NO_DEFINIDO = re.compile(r"<\s*no definido", re.I)


def texto_presente(contexto, params):
    archivo = params["archivo"]
    texto = contexto.evidencia.texto(archivo)
    if texto is None:
        return _falta(contexto, archivo, "este parámetro de configuración")

    patron = params["patron"]
    lineas = [l.strip() for l in texto.splitlines() if l.strip()]
    coincidencias = [l for l in lineas if re.search(patron, l, re.I)]
    validas = [l for l in coincidencias
               if not (SIN_LECTURA.search(l) or NO_DEFINIDO.search(l))]
    ausentes = [l for l in coincidencias if NO_DEFINIDO.search(l)]
    ilegibles = [l for l in coincidencias if SIN_LECTURA.search(l)]

    if validas:
        return (CUMPLE, "Encontrado: %s" % validas[0][:300], validas[0][:300])

    if ausentes:
        return (NO_CUMPLE,
                "La clave aparece en el archivo pero NO está definida (%d coincidencias): %s. "
                "Para estos controles, que la clave no exista es justamente el incumplimiento."
                % (len(ausentes), ausentes[0][:200]), ausentes[0][:300])

    if ilegibles:
        return (NO_VERIFICADO,
                "El valor no se pudo leer (%d coincidencias): %s. Esto NO es evidencia de que "
                "falte: la recolección no pudo acceder al valor. Hay que volver a correr "
                "`powershell\\recolectar-evidencia.ps1` como administrador y auditar de nuevo."
                % (len(ilegibles), ilegibles[0][:200]), ilegibles[0][:300])

    return (NO_CUMPLE,
            "No se encontró el patrón '%s' en `%s` (%d líneas revisadas)."
            % (patron, archivo, len(lineas)), "")


# ------------------------------------------------------------------ Meraki
def _cargar_json(contexto, archivo):
    texto = contexto.evidencia.texto(archivo)
    if texto is None:
        return None, _falta(contexto, archivo, "la configuración del firewall")
    try:
        return json.loads(texto), None
    except ValueError as exc:
        return None, (NO_VERIFICADO,
                      "El archivo no es un JSON válido (%s). La exportación del Meraki "
                      "debe guardarse sin modificación." % exc, "")


def _buscar_lista(datos, claves):
    """Busca la primera lista cuyo nombre coincida con alguno de los candidatos."""
    if isinstance(datos, list):
        for elemento in datos:
            if isinstance(elemento, dict):
                for clave in claves:
                    if clave in elemento and isinstance(elemento[clave], list):
                        return elemento[clave]
        return datos if datos and all(not isinstance(x, dict) for x in datos) else None
    if isinstance(datos, dict):
        for clave in claves:
            if clave in datos and isinstance(datos[clave], list):
                return datos[clave]
        for valor in datos.values():
            if isinstance(valor, (dict, list)):
                encontrado = _buscar_lista(valor, claves)
                if encontrado is not None:
                    return encontrado
    return None


def meraki_segmentacion(contexto, params):
    archivo = params.get("archivo", "meraki.json")
    datos, error = _cargar_json(contexto, archivo)
    if error:
        return error
    vlans = _buscar_lista(datos, ["vlans", "networkVlans", "vlanIds"]) or []
    ids = set()
    for vlan in vlans:
        if isinstance(vlan, dict):
            for campo in ("id", "vlanId", "networkId"):
                if campo in vlan:
                    ids.add(str(vlan[campo]))
    nombres = [str(v.get("name", "?")) for v in vlans if isinstance(v, dict)]
    evidencia = "%d VLAN(s): %s" % (len(ids), ", ".join(nombres) if nombres else "sin nombres")
    if not vlans:
        return (NO_VERIFICADO,
                "No se encontró una lista de VLAN en el JSON. Verifique que la "
                "exportación incluya la configuración de VLAN del Meraki.", evidencia)
    if len(ids) <= 1:
        return (NO_CUMPLE,
                "La configuración muestra %d sola VLAN. El procedimiento 14 exige segmentar "
                "y el procedimiento 23 documenta todos los equipos en VLAN 254: la "
                "segmentación no está implementada." % len(ids), evidencia)
    return (PARCIAL,
            "Hay %d VLAN configuradas, lo que es consistente con un segmento de "
            "segmentación parcial. Falta comprobar las reglas de firewall entre ellas."
            % len(ids), evidencia)


def meraki_reglas(contexto, params):
    archivo = params.get("archivo", "meraki.json")
    datos, error = _cargar_json(contexto, archivo)
    if error:
        return error
    reglas = _buscar_lista(datos, ["firewallRules", "l3FirewallRules", "rules"]) or []
    if not reglas:
        return (NO_VERIFICADO,
                "No se encontró una lista de reglas de firewall en el JSON.", "")
    acciones = [str(r.get("comment", "")) + " " + str(r.get("policy", "")) + " " +
                str(r.get("action", "")) for r in reglas if isinstance(r, dict)]
    texto = " ".join(acciones).lower()
    tiene_allow = re.search(r"\ballow\b|permit", texto)
    tiene_deny = re.search(r"\bdeny\b|block|drop", texto)
    evidencia = "%d reglas; %s" % (len(reglas), ", ".join(
        str(r.get("comment") or r.get("policy") or "?") for r in reglas[:8]
        if isinstance(r, dict)))
    if tiene_allow and not tiene_deny:
        return (NO_CUMPLE,
                "Las %d reglas encontradas sólo permiten tráfico: no hay ninguna política de "
                "denegación explícita. Sin denegar por defecto, todo lo que no esté "
                "prohibido sale a Internet." % len(reglas), evidencia)
    if tiene_allow and tiene_deny:
        return (PARCIAL,
                "Hay %d reglas con permisos y denegaciones. Verificar que la política "
                "efectiva sea denegar en salida y que las reglas se revisen "
                "trimestralmente (no hay revisión definida en el manual)." % len(reglas),
                evidencia)
    return (NO_VERIFICADO,
            "No se pudo determinar la política efectiva de las %d reglas." % len(reglas),
            evidencia)


def meraki_filtrado(contexto, params):
    archivo = params.get("archivo", "meraki.json")
    datos, error = _cargar_json(contexto, archivo)
    if error:
        return error
    filtrado = None
    if isinstance(datos, dict):
        filtrado = datos.get("contentFiltering") or datos.get("content_filtering")
    if not isinstance(filtrado, dict):
        filtrado = _buscar_lista(datos, ["contentFiltering", "contentFilter"])
        filtrado = filtrado if isinstance(filtrado, dict) else None
    if filtrado is None:
        return (NO_VERIFICADO,
                "No se encontró la sección de filtrado de contenido en el JSON.", "")
    habilitado = _booleano(filtrado.get("enabled"))
    categorias = filtrado.get("blockedUrlCategories") or filtrado.get("categories") or []
    texto_categorias = json.dumps(categorias, ensure_ascii=False).lower()
    evidencia = "enabled=%s, %d categorías bloqueadas" % (habilitado, len(categorias))
    if habilitado is False:
        return (NO_CUMPLE,
                "El filtrado de contenido está deshabilitado, pero el procedimiento 14 "
                "exige restringir contenidos.", evidencia)
    tiene_malware = "malware" in texto_categorias or "virus" in texto_categorias
    tiene_phishing = "phishing" in texto_categorias
    if tiene_malware and tiene_phishing:
        return (CUMPLE,
                "Filtrado activo con categorías de malware y phishing: el control del "
                "manual existe en la práctica.", evidencia)
    return (PARCIAL,
            "Filtrado activo (%s) pero sin categorías de malware o phishing en la "
            "configuración: sólo filtra contenido, no amenazas." % evidencia, evidencia)


# ------------------------------------------------------------- DNS y web
def dns_registro(contexto, params):
    if not contexto.red:
        return (NO_VERIFICADO,
                "La comprobación en vivo está desactivada (--sin-vivo).", "")
    dominio = contexto.dominio
    tipo = params.get("tipo", "TXT")
    nombre = dominio if tipo == "SPF" else "%s.%s" % (params.get("selector", ""), dominio)
    registros = contexto.red.texto_dns(nombre, tipo)
    if registros is None:
        return (NO_VERIFICADO,
                "No se pudo consultar DNS para %s (%s). Revise la conexión a Internet."
                % (nombre, tipo), "")
    if not registros:
        if tipo == "SPF":
            return (NO_CUMPLE,
                    "El dominio no publica registro SPF. Cualquiera puede enviar correo "
                    "usando la dirección del colegio y los phishing contra el personal "
                    "llegan indistinguibles.", "sin registros")
        return (NO_VERIFICADO, "No se encontró registro %s para %s." % (tipo, nombre), "")

    texto = " ".join(registros)
    evidencia = texto[:300]
    if tipo == "SPF":
        if "~all" in texto or "-all" in texto:
            politica = "rechazo estricto (-all)" if "-all" in texto else "rechazo suave (~all)"
            if re.search(r"\+all|\?all", texto):
                return (PARCIAL,
                        "SPF publicado con política %s, pero incluye «+all» o «?all», que "
                        "anulan el control." % politica, evidencia)
            if texto.count("include:") > 10:
                return (PARCIAL,
                        "SPF con %d inclusiones: seBROKE al límite de 10 Dust." %
                        texto.count("include:"), evidencia)
            return (CUMPLE, "SPF publicado con %s." % politica, evidencia)
        return (NO_CUMPLE,
                "SPF publicado sin política de rechazo: la consulta termina en «pass» y no "
                "protege contra suplantación.", evidencia)
    return (CUMPLE, "Registro %s encontrado." % tipo, evidencia)


def web_seguridad(contexto, params):
    if not contexto.red:
        return (NO_VERIFICADO, "La comprobación en vivo está desactivada (--sin-vivo).", "")
    url = params.get("url") or ("https://%s/" % contexto.dominio)
    hallazgos = []
    ok = True

    http = contexto.red.http(url)
    if not http.get("ok"):
        return (NO_VERIFICADO,
                "No se pudo consultar %s (%s)." % (url, http.get("error")), "")

    estado = http.get("estado")
    if estado and estado >= 400:
        ok = False
        hallazgos.append("el sitio responde HTTP %s" % estado)
    if not url.lower().startswith("https://"):
        ok = False
        hallazgos.append("la comprobación se hizo por HTTP sin cifrar")
    ok_cabeceras, detalle_cabeceras, http2 = contexto.red.comprobar_cabeceras(url)
    if not ok_cabeceras:
        ok = False
        if not detalle_cabeceras.startswith("No se pudo"):
            hallazgos.append(detalle_cabeceras)

    tls = contexto.red.tls(contexto.dominio, 443)
    if tls.get("ok"):
        version = tls.get("version", "")
        if version in ("TLSv1", "TLSv1.1", "SSLv3"):
            ok = False
            hallazgos.append("la conexión usa %s, obsoleto" % version)
        evidencia = "%s / %s, certificado válido hasta %s" % (
            version, tls.get("cifrado"), tls.get("vigente_hasta"))
    else:
        ok = False
        evidencia = "sin conexión TLS verificable: %s" % tls.get("error")
        hallazgos.append("no se pudo verificar el certificado TLS")

    if not ok:
        resumen = " ".join(h.rstrip(". ") + "." for h in hallazgos)
        return (NO_CUMPLE,
                "%s El procedimiento 22 sólo dice «implementar sistemas de seguridad», "
                "sin requisitos verificables." % resumen, evidencia)
    return (CUMPLE, "El sitio usa HTTPS con %s y presenta las cabeceras de seguridad "
                    "básicas." % version, evidencia)


def http_headers(contexto, params):
    if not contexto.red:
        return (NO_VERIFICADO, "La comprobación en vivo está desactivada (--sin-vivo).", "")
    url = params["url"]
    http = contexto.red.http(url)
    if not http.get("ok"):
        return (NO_VERIFICADO,
                "No se pudo abrir %s (%s). Si la página requiere sesión, esto es normal: "
                "revise el resultado desde un equipo autorizado." % (url, http.get("error")), "")

    correos = set(re.findall(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}",
                             http.get("cuerpo", "") + " " + " ".join(http.get("cabeceras", {}).values())))
    nombres = sorted(c for c in correos if not c.lower().endswith(
        ("microsoftonline.com", "microsoft.com", "windows.net", "outlook.com",
         "live.com", "office.com", "microsoftonline-p.com")))
    estado = http.get("estado")
    evidencia = "HTTP %s, %d correo(s) visible(s) en la página" % (estado, len(nombres))
    if estado and estado >= 400:
        return (NO_VERIFICADO,
                "La página respondió HTTP %s, así que no se pudo inspeccionar su contenido "
                "para evaluar la exposición de datos. Si requiere sesión, revise el resultado "
                "desde un equipo autorizado." % estado, evidencia)
    if nombres:
        return (PARCIAL,
                "La página de reservas es accesible y expone %d dirección(es) de correo "
                "del tenant: sirve para enumerar a quién se puede atacar con phishing. "
                "Revisar si debe ser pública." % len(nombres),
                evidencia + ": " + ", ".join(nombres[:6]))
    return (CUMPLE, "La página responde correctamente y no expone direcciones de correo.", evidencia)


def puertos_dvr(contexto, params):
    """Comprueba la exposición de los grabadores de video desde esta red."""
    if not contexto.red:
        return (NO_VERIFICADO,
                "La comprobación en red local está desactivada (ejecute la auditoría desde "
                "un equipo de la LAN del colegio).", "")
    objetivos = params.get("objetivos", [])
    abiertos, cerrados, inaccesibles = [], [], []
    for objetivo in objetivos:
        host, _, puerto = objetivo.rpartition(":")
        if not host:
            host, puerto = objetivo, "80"
        resultado = contexto.red.tcp(host, int(puerto))
        etiqueta = "%s:%s" % (host, puerto)
        if not resultado.get("ok"):
            inaccesibles.append(etiqueta)
        elif resultado.get("abierto"):
            abiertos.append(etiqueta)
        else:
            cerrados.append(etiqueta)

    evidencia = "abiertos: %s | cerrados: %s | sin respuesta: %s" % (
        ", ".join(abiertos) or "-", ", ".join(cerrados) or "-",
        ", ".join(inaccesibles) or "-")
    if not objetivos:
        return (NO_VERIFICADO, "No se definieron objetivos de puerto.", "")

    if inaccesibles and len(inaccesibles) == len(objetivos):
        return (NO_VERIFICADO,
                "No se obtuvo respuesta de ningún grabador desde esta posición de red. "
                "Ejecute la auditoría desde un equipo del segmento 192.168.92.x o desde un "
                "equipo de sala.", evidencia)

    if abiertos:
        return (PARCIAL,
                "%d puerto(s) de gestión responden desde esta posición de red: %s. Si la "
                "auditoría se ejecutó desde un equipo de aula, los grabadores de video están "
                "alcanzables desde los alumnos. Verifique además que no estén publicados en "
                "Internet." % (len(abiertos), ", ".join(abiertos)), evidencia)
    return (CUMPLE,
            "Ningún puerto de gestión respondió desde esta posición de red (%d "
            "comprobaciones)." % len(cerrados), evidencia)


def wordpress_exposicion(contexto, params):
    """Detecta WordPress y comprueba las dos exposiciones habituales: versión y XML-RPC."""
    if not contexto.red:
        return (NO_VERIFICADO, "La comprobación en vivo está desactivada (--sin-vivo).", "")
    dominio = contexto.dominio

    inicio = contexto.red.http("https://%s/" % dominio)
    if not inicio.get("ok"):
        return (NO_VERIFICADO,
                "No se pudo consultar el sitio (%s)." % inicio.get("error"), "")

    cabeceras = inicio.get("cabeceras", {})
    cuerpo = inicio.get("cuerpo", "")
    es_wordpress = bool(re.search(r"wp-content|wp-includes|wp-json", cuerpo)) or \
        "wordpress" in cabeceras.get("x-nginx-cache", "").lower() or \
        "wordpress" in cabeceras.get("x-powered-by", "").lower()
    version = ""
    generador = re.search(r'<meta name="generator" content="([^"]+)"', cuerpo)
    if generador:
        version = generador.group(1)

    if not es_wordpress and not version.lower().startswith("wordpress"):
        return (NO_APLICA,
                "El sitio no parece estar construido sobre WordPress: este control no aplica.",
                "cabeceras: %s" % ", ".join(sorted(cabeceras)[:8]))

    problemas = []
    if version:
        problemas.append("el sitio declara su versión en la página (%s), lo que permite "
                         "buscar fallos conocidos para esa versión exacta" % version)

    xmlrpc = contexto.red.http("https://%s/xmlrpc.php" % dominio)
    xmlrpc_activo = False
    if xmlrpc.get("ok") and xmlrpc.get("estado") in (200, 405):
        texto = (xmlrpc.get("cuerpo", "") or "").lower()
        if "xml-rpc" in texto or "xmlrpc" in texto or xmlrpc.get("estado") == 200:
            xmlrpc_activo = True
    if xmlrpc_activo:
        problemas.append("XML-RPC está activo (responde en /xmlrpc.php). Es el vector "
                         "histórico de fuerza bruta contra cuentas de WordPress y amplifica "
                         "los intentos de acceso desde cualquier parte del mundo.")
    problemas = [p.rstrip(". ") + "." for p in problemas]

    cookie = cabeceras.get("set-cookie", "")
    if cookie and "secure" not in cookie.lower():
        problemas.append("las cookies se emiten sin la marca Secure, por lo que pueden "
                         "viajar en claro si alguien fuerza una conexión sin cifrar")
    if cookie and "samesite" not in cookie.lower():
        problemas.append("las cookies se emiten sin SameSite, lo que facilita el envío "
                         "automático de sesión entre sitios (CSRF)")

    evidencia = "servidor=%s, version=%s, xmlrpc=%s" % (
        cabeceras.get("server", "?"), version or "no declarada",
        "activo" if xmlrpc_activo else "no detectado")

    if not problemas:
        return (CUMPLE,
                "WordPress sin exposición evidente de versión ni de XML-RPC.", evidencia)
    if xmlrpc_activo:
        return (NO_CUMPLE,
                "%s. El procedimiento 22 exige «implementar sistemas de seguridad» sin "
                "definir ninguno, y esta es la exposición más fácil de corregir."
                % "; ".join(problemas), evidencia)
    return (PARCIAL, "; ".join(problemas), evidencia)


def config_valores(contexto, params):
    """Evalúa pares «clave = valor» con su SIGNIFICADO, no su simple presencia.

    Es la diferencia entre «la opción existe» y «la opción está activa». Un archivo
    que dice `EnableControlledFolderAccess = 0` tiene la clave presente y la
    protección desactivada: contarlo como cumplimiento sería mentir.
    """
    archivo = params.get("archivo", "defender_preferencias.txt")
    texto = contexto.evidencia.texto(archivo)
    if texto is None:
        return _falta(contexto, archivo, "esta configuración")

    valores = {}
    for linea in texto.splitlines():
        if "=" not in linea:
            continue
        clave, _, valor = linea.partition("=")
        valores[clave.strip()] = valor.strip()

    reglas = params.get("valores", [])
    cumplidas, falladas, ilegibles = [], [], []
    for regla in reglas:
        clave = regla["clave"]
        operador = regla.get("operador", "igual")
        esperado = regla.get("valor")
        if clave not in valores:
            ilegibles.append("%s (no aparece en el archivo)" % clave)
            continue
        real = valores[clave]
        # El valor está escrito pero no se pudo leer. No es "está mal", es
        # "no lo sé":(Get-MpPreference devuelve "N/A: Must be an administrator"
        # y $null cuando el proceso no es administrador).
        if SIN_LECTURA.search(real):
            ilegibles.append("%s = %s (sin permiso de lectura)" % (clave, real))
            continue
        if NO_DEFINIDO.search(real) or real == "":
            falladas.append("%s = %s" % (clave, real if real else "<vacio>"))
            continue

        if operador in ("activo", "desactivado"):
            activo = _booleano(real)
            es_activo = activo is True or str(real).strip() in ("1", "2", "3")
            if (operador == "activo") == es_activo:
                cumplidas.append("%s = %s" % (clave, real))
            else:
                falladas.append("%s = %s (se esperaba %s)" % (clave, real, operador))
        elif operador == "no_vacio":
            if real:
                cumplidas.append("%s = %s" % (clave, real))
            else:
                falladas.append("%s = <vacio>" % clave)
        elif operador == "no_presente":
            if clave in valores:
                falladas.append("%s está definida; el control pide que NO lo esté" % clave)
            else:
                cumplidas.append("%s no está definida (correcto)" % clave)
        else:
            if str(real).lower() == str(esperado).lower():
                cumplidas.append("%s = %s" % (clave, real))
            else:
                falladas.append("%s = %s (se esperaba %s)" % (clave, real, esperado))

    evidencia = " | ".join(cumplidas + falladas)[:400]
    if ilegibles:
        return (NO_VERIFICADO,
                "No se pudo determinar: %s. Puede que el equipo no tenga esta funcionalidad, "
                "o que la recolección se haya corrido sin permisos de administrador. Esto NO "
                "es un incumplimiento: es un control sin cobertura."
                % "; ".join(ilegibles), evidencia)
    if not falladas:
        return (CUMPLE, "Configuración correcta: %s." % "; ".join(cumplidas), evidencia)
    if cumplidas:
        return (PARCIAL,
                "Configuración incompleta. Correcto: %s. Incorrecto: %s."
                % ("; ".join(cumplidas), "; ".join(falladas)), evidencia)
    return (NO_CUMPLE,
            "Ninguna de las opciones esperadas está activa: %s." % "; ".join(falladas),
            evidencia)


# ------------------------------------------------------------- registro
VERIFICADORES = {
    "ad_password_policy": ad_password_policy,
    "ad_audit_policy": ad_audit_policy,
    "csv_columnas": csv_columnas,
    "csv_booleano": csv_booleano,
    "csv_sin_filas": csv_sin_filas,
    "csv_minimo_admin": csv_minimo_admin,
    "csv_bitlocker": csv_bitlocker,
    "csv_antiguedad_parche": csv_antiguedad_parche,
    "respaldo_trabajos": respaldo_trabajos,
    "texto_presente": texto_presente,
    "config_valores": config_valores,
    "meraki_segmentacion": meraki_segmentacion,
    "meraki_reglas": meraki_reglas,
    "meraki_filtrado": meraki_filtrado,
    "dns_registro": dns_registro,
    "web_seguridad": web_seguridad,
    "wordpress_exposicion": wordpress_exposicion,
    "http_headers": http_headers,
    "puertos_dvr": puertos_dvr,
}