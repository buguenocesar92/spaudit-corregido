"""Controles del Manual de Procedimientos Saint Patrick 2026-II — Procedimientos 13 a 22.

Este bloque es el núcleo técnico: identidad, red, correo, respaldo y sitio web.
La mayoría de los controles tiene un verificador automático asociado, por eso la
evidencia se recoge con el script PowerShell y con los chequeos en vivo.
"""

from .controles_comunes import D

DOMINIO = "saintpatricktemuco.cl"

CONTROLES = [
    # ----------------------------------------------------------------- P.13
    D("SP-13-01", 13, 28, "Identidad", "medio", "tecnico",
      "Guardar en el histórico de las contraseñas: 6 contraseñas recordadas.",
      brecha="6 contraseñas es un valor bajo: con una política de 180 días de vigencia y "
             "contraseñas de 8 caracteres, un atacante con acceso a los hashes tiene "
             "material suficiente para predecir patrones.",
      ref="CIS Control 5.2 (5.2.2: 24 contraseñas)",
      fix="Subir a 24 contraseñas memorizadas.",
      verificacion="Leer 'net accounts' y el valor de 'Password history'.",
      evidencia=["net_accounts.txt"],
      check={"tipo": "ad_password_policy",
             "params": {"archivo": "net_accounts.txt", "clave": "history", "minimo": 24}}),

    D("SP-13-02", 13, 28, "Identidad", "medio", "tecnico",
      "La edad máxima de la cuenta es de 180 días.",
      brecha="CIS y NIST BESTrecommendan NO caducar la contraseña de forma periódica "
             "cuando ya hay MFA y bloqueos: la rotación forzada genera contraseñas "
             "predecibles («Otoño2026», «Saint2026») que se debilitan. Además contradice el "
             "P.8, donde el usuario «cambia cuando estima conveniente».",
      ref="NIST SP 800-63B; CIS Control 5.2",
      fix="Decidir una sola política. Lo recomendado: sin caducidad + MFA + bloqueo por "
          "intentos + detección de credenciales filtradas, y rotar sólo ante incidente.",
      verificacion="Leer 'net accounts' (edad máxima de la contraseña).",
      evidencia=["net_accounts.txt"],
      check={"tipo": "ad_password_policy",
             "params": {"archivo": "net_accounts.txt", "clave": "max_age"}}),

    D("SP-13-03", 13, 28, "Identidad", "medio", "tecnico",
      "La edad mínima de la cuenta es de 30 días.",
      brecha="Valor arbitrario sin justificación. 30 días es más restrictivo que el valor "
             "habitual de 1 día y sin sentido con una política de 180 días.",
      ref="CIS Control 5.2", fix="Ajustar a 1 día o eliminar el requisito."),

    D("SP-13-04", 13, 28, "Identidad", "alto", "tecnico",
      "Longitud mínima de la contraseña de 8 caracteres.",
      brecha="8 caracteres es el umbral de las guías de 2003. Con ese valor, una lista de "
             "contraseñas common o un diccionario la rompe en segundos. Es el valor que "
             "más directamente explica por qué el manual necesita MFA.",
      ref="CIS Control 5.2 (5.2.1: 14 caracteres); NIST SP 800-63B §3.1.1",
      fix="Subir a 14 caracteres como mínimo (sin caracteres especiales obligatorios ni "
          "reglas de periodicidad, que sólo empujan a contraseñas peores).",
      verificacion="Leer 'net accounts'.",
      evidencia=["net_accounts.txt"],
      check={"tipo": "ad_password_policy",
             "params": {"archivo": "net_accounts.txt", "clave": "min_len", "minimo": 14}}),

    D("SP-13-05", 13, 28, "Identidad", "bajo", "tecnico",
      "Habilitar que las contraseñas requieran nivel de complejidad.",
      brecha="Correcto. Complementar con 'Password must meet complexity' y, sobre todo, "
             "con bloqueo de contraseñas comunes.",
      ref="CIS Control 5.2",
      fix="Activar además el bloqueo de contraseñas usadas recientemente (Azure AD Protection "
          "o una GPO con lista de contraseñas prohibidas), que es más efectivo que los "
          "caracteres especiales.",
      verificacion="Leer 'net accounts'.",
      evidencia=["net_accounts.txt"],
      check={"tipo": "ad_password_policy",
             "params": {"archivo": "net_accounts.txt", "clave": "complexity", "esperado": True}}),

    D("SP-13-06", 13, 28, "Identidad", "medio", "tecnico",
      "Bloquear a 3 intentos inválidos y desbloquear la cuenta tras 30 minutos.",
      brecha="El bloqueo por 3 intentos es correcto, pero con 8 caracteres de contraseña y "
             "sin rate limiting en servicios como RDP/VPN/Exchange, permite denegación de "
             "servicio contra un usuario concreto (bloqueo selectivo).",
      ref="CIS Control 5.2; NIST SP 800-53 AC-7",
      fix="Mantener 3 intentos, y añadir excepciones explícitas para cuentas de servicio y "
          "contenedor de cuentas privilegiadas.",
      verificacion="Leer 'net accounts' (umbral y duración del bloqueo).",
      evidencia=["net_accounts.txt"],
      check={"tipo": "ad_password_policy",
             "params": {"archivo": "net_accounts.txt", "clave": "lockout_threshold", "maximo": 5}}),

    D("SP-13-07", 13, 28, "Registro", "medio", "tecnico",
      "Auditar el inicio de sesión, el manejo de cuentas, el acceso a servicios de "
      "directorios, el acceso a objetos, el cambio de política, el uso de privilegios y "
      "los eventos del sistema.",
      brecha="El manual no distingue entre «Directiva de auditoría» clásica y «Directiva de "
             "auditoría avanzada». En Windows Server 2019+ y Windows 10/11 la segunda "
             "reemplaza a la primera, y es la que genera los eventos que hoy permiten "
             "investigar (4624, 4625, 4672, 4768...). Sin subcategorías configuradas, la "
             "mayoría de estos eventos no se generan nunca.",
      ref="Microsoft «Advanced Audit Policy»; CIS Control 8.2",
      fix="Migrar a Directiva de auditoría avanzada con las subcategorías necesarias "
          "(logon/logoff, cambio de cuenta/grupo, acceso a objetos sensibles, uso de "
          "privilegios) y volcar los eventos a un servidor de registros.",
      verificacion="Revisar 'auditpol /get /subcategory:*' y confirmar que hay eventos 4624, "
                   "4625, 4672, 4688, 4768/4769/4771.",
      evidencia=["auditpol.txt"],
      check={"tipo": "ad_audit_policy",
             "params": {"archivo": "auditpol.txt", "subcategorias": [
                 "Logon", "Logoff", "Account Lockout", "Special Logon",
                 "Security Group Management", "Other Account Management Events",
                 "Audit Policy Change", "Audit Other Privileged Events",
                 "Security State Change", "Other System Events"]}}),

    D("SP-13-08", 13, 28, "Identidad", "medio", "tecnico",
      "Deshabilitar la cuenta de invitado.",
      brecha="Control correcto. Verificar además que no queden otras cuentas de invitado "
             "habilitadas en el directorio activo.",
      ref="CIS Control 5.2",
      fix="Deshabilitar Guest y cualquier cuenta temporal que quedara activa; revisarlo "
          "en cada alta y baja.",
      verificacion="Buscar cuentas Guest habilitadas en el dominio.",
      evidencia=["usuarios_ad.csv"],
      check={"tipo": "csv_sin_filas",
             "params": {"archivo": "usuarios_ad.csv", "columna": "SamAccountName",
                        "patron": "^(guest|invitado)$", "col_booleano": "Enabled",
                        "col_booleano_esperado": "False"}}),

    D("SP-13-09", 13, 28, "Identidad", "critico", "tecnico",
      "Renombrar la cuenta del administrador.",
      brecha="Renombrar la cuenta «Administrator» no es lo mismo que desactivar la cuenta "
             "integrada con SID-500, que sigue presente y es el objetivo predilecto de los "
             "ataques de movimiento lateral (pass-the-hash). El manual no pide "
             "deshabilitarla.",
      ref="CIS Control 5.2 (deshabilitar o renombrar cuentas integradas); MITRE ATT&CK T1078.003",
      fix="Renombrar Y deshabilitar la cuenta integrada Administrator (SID-500),uir "
          "excepciones de red con cuenta de emergencia (ver P.15) monitorizada.",
      verificacion="Confirmar que no existe una cuenta habilitada con el nombre original "
                   "ni con SID-500.",
      evidencia=["usuarios_ad.csv"],
      check={"tipo": "csv_sin_filas",
             "params": {"archivo": "usuarios_ad.csv", "columna": "SamAccountName",
                        "patron": "^(administrator|administrador)$",
                        "col_booleano": "Enabled", "col_booleano_esperado": "False"}}),

    D("SP-13-10", 13, 28, "Identidad", "critico", "tecnico",
      "Cuentas de administración separadas para contingencia (ver P.15).",
      brecha="No hay política de cuentas privilegiadas: no se define cuántas cuentas "
             "administrativas existen, quién las usa, ni si hay una por persona. Una cuenta "
             "administrativa compartida es la vía más común de entrada del ransomware.",
      ref="CIS Control 5.4; MITRE ATT&CK T1078, T1550.003 (pass-the-hash)",
      fix="Una cuenta administrativa nominal por persona (nunca compartida), con "
          "distinción de funciones: administración de dominio, administración de "
          "servidores y soporte de escritorio.",
      verificacion="Listar los miembros de Domain Admins / Enterprise Admins.",
      evidencia=["grupos_ad.csv"],
      check={"tipo": "csv_minimo_admin",
             "params": {"archivo": "grupos_ad.csv"}}),

    D("SP-13-11", 13, 28, "Identidad", "critico", "tecnico",
      "Protección de credenciales administrativas locales (LAPS).",
      brecha="Ausente. El manual no menciona LAPS ni Windows LAPS: cada cuenta "
             "administrativa comparte la misma contraseña local en todos los equipos, lo que "
             "permite obtener privileged desde cualquier estación.",
      ref="Microsoft Windows LAPS; CIS Control 5.2 (LAPS)",
      fix="Activar Windows LAPS en el dominio y migrar las cuentas locales protegidas "
          "(aleatorizadas por máquina).",
      verificacion="Confirmar que Get-LAPSPolicy está configurado en el dominio.",
      evidencia=["registry_seguridad.txt"],
      check={"tipo": "texto_presente",
             "params": {"archivo": "registry_seguridad.txt", "patron": "LAPS|ManagedPassword"}}),

    D("SP-13-12", 13, 28, "Sistema", "critico", "tecnico",
      "Endurecimiento del controlador de dominio (firma SMB, NTLM, LDAP).",
      brecha="El manual define qué servicios usa el DC (DNS, AD, «Netsupport») pero no exige "
             "endurecimiento alguno: sin firma SMB obligatoria, sin nivel mínimo de NTLM, "
             "sin firma LDAP. Sin estos controles, un atacante de la LAN puede interceptar "
             "o capturar credenciales.",
      ref="CIS Microsoft Windows Server Benchmark (secciones Account Use, SMB, LDAP)",
      fix="Aplicar el benchmark CIS al DC: SMB signing obligatorio, "
          "LmCompatibilityLevel = 5 (NTLMv2 solamente), LDAP signing, deshabilitar NTLM y "
          "deshabilitar las cuentas con SID Well-Known duplicadas.",
      verificacion="Revisar el registro del servidor en busca de RequireSecurityMode, "
                   "LmCompatibilityLevel y RestrictAnonymous.",
      evidencia=["registry_seguridad.txt"],
      check={"tipo": "texto_presente",
             "params": {"archivo": "registry_seguridad.txt", "patron": "RequireSecurityMode|RequireSecurityModeReplace"}}),

    D("SP-13-13", 13, 28, "Sistema", "critico", "tecnico",
      "Versión del Windows Server del controlador de dominio.",
      brecha="El manual dice «Windows server (actualizar versión según necesidad)». Si el DC "
             "corre Windows Server 2012 R2 o 2016 está fuera de soporte desde octubre de 2023 "
             "y no recibe parches de seguridad: es el activo más expuesto de la red y el "
             "objetivo de cualquier ransomware.",
      ref="Microsoft Lifecycle; CIS Control 7.1",
      fix="Verificar la versión y el último parche instalado; planificar la actualización a una versión "
          "con soporte (Server 2022 o superior).",
      verificacion="Revisar la versión del SO y la fecha del último parche en todos los "
                   "servidores.",
      evidencia=["sistema.csv"],
      check={"tipo": "csv_antiguedad_parche",
             "params": {"archivo": "sistema.csv"}}),

    D("SP-13-14", 13, 28, "Sistema", "alto", "tecnico",
      "Cifrado de disco (BitLocker) en servidores y equipos con datos.",
      brecha="Ausente. Sin BitLocker, un equipo robado entrega los datos sin esfuerzo.",
      ref="CIS Control 3.6; ANPD Buenas Prácticas de Cifrado",
      fix="Activar BitLocker en el DC, el NAS y los equipos que contengan datos de alumnos; "
          "guardar las claves de recuperación en el AD (o en el gestor de claves) y "
          "respaldar la clave de recuperación fuera del equipo.",
      verificacion="Estado de BitLocker por volumen.",
      evidencia=["bitlocker.csv"],
      check={"tipo": "csv_bitlocker", "params": {"archivo": "bitlocker.csv"}}),

    D("SP-13-15", 13, 28, "Red", "medio", "tecnico",
      "Configurar servidor DNS y servidor DHCP (en el firewall Meraki).",
      brecha="No se define: el DNS interno responde sólo por nombres internos; sin "
             "hardening, un servidor DNS abierto puede usarse para amplificación de "
             "ataques y envenenamiento de caché.",
      ref="CISA DNS security; CIS Control 1.4",
      fix="Documentar los servidores DNS y asegurar que no resuelven recursivamente desde "
          "Internet; desactivar respuestas a consultas de zona externa."),

    # ----------------------------------------------------------------- P.14
    D("SP-14-01", 14, 29, "Red", "critico", "tecnico",
      "Crear VLAN para segmentación de las diferentes redes.",
      brecha="Contradice directamente al P.23: la topología documentada muestra TODOS los "
             "switches y el core en VLAN 254 (192.168.254.0/24) y las cámaras en otra "
             "subred sin reglas documentadas. Si eso es lo que hay implementado, la "
             "segmentación no existe:forceable por dispositivo, las aulas, la "
             "administración y los servidores están en el mismo dominio de difusión y el "
             "mismo segmento, y cualquier alumno con un notebook en la red llega a todos "
             "los puertos de todos los equipos.",
      ref="CIS Control 1.x; NIST SP 800-125B (segmentación)",
      fix="Implementar la segmentación que el procedimiento exige: VLAN de algebraic "
          "docentes, VLAN de administración, VLAN de servidores, VLAN de cámaras, "
          "VLAN de invitados y VLAN de unmanaged. Con reglas de firewall entre ellas.",
      verificacion="Exportar la configuración de VLAN del Meraki y las reglas de firewall, "
                   "y compararla con la tabla del P.23.",
      evidencia=["meraki.json"],
      check={"tipo": "meraki_segmentacion", "params": {"archivo": "meraki.json"}}),

    D("SP-14-02", 14, 29, "Red", "bajo", "tecnico",
      "Distribuir equitativamente el ancho de banda.",
      brecha="Control de rendimiento, no de seguridad. Se mantiene.",
      ref="", fix="Sin cambios."),

    D("SP-14-03", 14, 29, "Red", "bajo", "tecnico",
      "Configurar DHCP para distribución de IP internas.",
      brecha="Verificar que el DHCP no entrega direcciones de gateway, DNS o WINS "
             "manipulados; y que sólo el Meraki entrega IPs.",
      ref="", fix="Confirmar que los switches no tienen DHCP habilitado."),

    D("SP-14-04", 14, 29, "Red", "critico", "tecnico",
      "Implementar políticas y reglas generales en el firewall.",
      brecha="No hay ni una sola regla escrita. No se sabe qué puede salir a Internet, "
             "qué puertos están abiertos, ni si existe una política de «por defecto negar» "
             "en salida. Sin esto, la red del colegio es una red abierta a todo.",
      ref="CIS Control 13.x; NIST SP 800-125B",
      fix="Documentar y versionar todas las reglas: denegar por defecto en salida, "
          "permitir sólo lo necesario, y revisar trimestralmente. Sin regla escrita no hay "
          "control que se pueda auditar.",
      verificacion="Exportar las reglas de firewall (archivo JSON) y revisar la política "
                   "efectiva.",
      evidencia=["meraki.json"],
      check={"tipo": "meraki_reglas", "params": {"archivo": "meraki.json"}}),

    D("SP-14-05", 14, 29, "Identidad", "critico", "tecnico",
      "Crear y administrar usuarios super admin (del firewall Meraki).",
      brecha="El manual no exige MFA ni límite de uso para la cuenta que administra la "
             "puerta de entrada de toda la red. Una sesión de Meraki sin MFA es un "
             "punto de control total de la red.",
      ref="CIS Control 5.3; CISA guidance on MFA",
      fix="Exigir MFA (la propia Meraki la ofrece de fábrica) en todas las cuentas de "
          "administrador del Meraki, y eliminar las cuentas de ejemplo que trae el "
          "equipamiento sin cambiar.",
      verificacion="Revisar los administradores de la organización Meraki.",
      evidencia=["meraki.json"]),

    D("SP-14-06", 14, 29, "Red", "medio", "tecnico",
      "Monitorear el comportamiento y uso de la red de datos.",
      brecha="Sin herramienta declarada ni periodicidad. El Meraki registra el tráfico en "
             "la nube de Cisco: conviene verificar que ese registro se consulte y que no "
             "dependa únicamente de una suscripción que caduque.",
      ref="CIS Control 8.1",
      fix="Activar y revisar mensualmente el Security Center / IDS del Meraki y documentar "
          "quién lo hace."),

    D("SP-14-07", 14, 29, "Red", "medio", "tecnico",
      "Restringir accesos a sitios vulnerables o con contenidos violentos y sexuales.",
      brecha="El filtrado de contenido está escrito, pero el manual no exige: bloqueo de "
             "categorías de amenazas (malware, phishing, C2), ni protección DNS contra "
             "suplantación, ni registro de las URL bloqueadas. Un filtro de contenido sin "
             "protección contra phishing es sólo de contenido inapropiado.",
      ref="CIS Control 13.6; CISA phishing guidance",
      fix="Verificar que están activas las categorías de seguridad (no sólo las de "
          "contenido), con bloqueo de DNS para phishing y malware, y una revisión mensual "
          "de los sitios bloqueados por los alumnos.",
      evidencia=["meraki.json"],
      check={"tipo": "meraki_filtrado", "params": {"archivo": "meraki.json"}}),

    D("SP-14-08", 14, 29, "Red", "bajo", "organizacional",
      "Actualizar las licencias de operatividad (Meraki).",
      brecha="Control financiero y de disponibilidad: si una licencia de seguridad caduca, "
             "la red sigue funcionando pero sin las protecciones. Enfatizar la alerta de "
             "vencimiento en el informe.",
      ref="", fix="Calendarizar la renovación y verificarla cada trimestre."),

    D("SP-14-09", 14, 29, "Acceso remoto", "critico", "tecnico",
      "Establecer los accesos VPN según corresponda.",
      brecha="«Según corresponda» no es un criterio: no define para quién, desde dónde, con "
             "qué condiciones, ni que el VPN de administración sólo permita llegar a los "
             "servidores. Combinado con la ausencia total de MFA (SP-08-05), el VPN es la "
             "puerta de entrada remota más probable de la red.",
      ref="CIS Control 12.4; NIST SP 800-124",
      fix="Definir dos VPNs separadas: (1) acceso remoto de usuarios, sólo con MFA y con "
          "túnel completo; (2) administración, sólo para el personal de Informática, sólo "
          "a los rangos de servidores, con MFA y registro de sesiones.",
      verificacion="Revisar la configuración de Client VPN del Meraki y la lista de usuarios "
                   "autorizados.",
      evidencia=["meraki.json"]),

    D("SP-14-10", 14, 29, "Red", "alto", "tecnico",
      "Otras configuraciones necesarias para reforzar la seguridad de la red.",
      brecha="La cláusula catch-all no cubre las carencias reales: sin IDS/IPS, sin "
             "registro de cambios de configuración del firewall, sin respaldo de la "
             "configuración (si se pierde el equipo, se pierde la red), sin filtrado de "
             "e-mail (SPF/DKIM/DMARC, ver SP-18-05) y sin monitoreo de puertos abiertos "
             "hacia Internet.",
      ref="CIS Control 13.x",
      fix="Activar IDS/IPS del Meraki, respaldar la configuración del firewall fuera del "
          "equipo y versionar los cambios."),

    # ----------------------------------------------------------------- P.15
    D("SP-15-01", 15, 30, "Identidad", "critico", "organizacional",
      "El Administrador de Red crea un usuario ADMIN para contingencia, distinto del "
      "administrador de la red.",
      brecha="Una cuenta de emergencia compartida sin MFA, sin alertas de uso y sin "
             "caducidad es la puerta de entrada permanente a la red. En la práctica, las cuentas de "
             "contingencia se usan como cuentas habituales y nadie sabe quién las usó.",
      ref="CIS Control 5.2 (emergency accounts); MITRE ATT&CK T1078.004",
      fix="Cuenta de emergencia con MFA, con alerta inmediata ante cada uso, con "
          "contraseña rotada tras cada activación, y con revisión trimestral de si se ha "
          "usado.",
      verificacion="Revisar si existe, quién la conoce y si hay registro de sus usos.",
      evidencia=["gestor_claves.txt"]),

    D("SP-15-02", 15, 30, "Identidad", "critico", "organizacional",
      "Las contraseñas de administración sólo son conocidas por el Administrador de Red, "
      "el jefe del área y Gerencia.",
      brecha="Con tres personas y sin gestor de claves, la contraseña del controlador "
             "de dominio vive en la cabeza o en el correo de tres personas. El manual "
             "prohíbe compartir claves de usuario, y en la práctica comparte la clave "
             "maestra de la infraestructura.",
      ref="ISO 27001 A.5.17; CIS Control 5.4",
      fix="Gestor de claves con acceso individual y auditado, copia de recuperación sellada "
          "y bajo custodia, y registro de cada lectura de un secreto administrativo."),

    D("SP-15-03", 15, 30, "Identidad", "medio", "organizacional",
      "Las contraseñas se actualizan por solicitud del jefe de informática o cuando la "
      "Gerencia lo determine.",
      brecha="No hay periodicidad máxima: las claves pueden no cambiarse nunca. Y el "
             "cambio manual de clave de dominio no se hace en el AD, se hace \"en el "
             "servidor\", lo que casi siempre implica cambiar la clave del cuenta del "
             "servidor sin rotar el secreto almacenado.",
      ref="",
      fix="Caducidad máxima definida (p. ej. 90 días) para cuentas de servicio y "
          "administración, con registro de cada cambio."),

    D("SP-15-04", 15, 30, "Identidad", "critico", "tecnico",
      "Restricción y actualización de las contraseñas de dominio, aplicaciones y hosting.",
      brecha="Sin criterio técnico: ¿dónde están almacenadas? ¿están cifradas? ¿quién las "
             "puede leer? Este procedimiento es el que legitima el «registro de "
             "contraseñas» del P.8.",
      ref="ISO/IEC 27001 A.5.17; OWASP Secrets Management Cheat Sheet",
      fix="Un único gestor de claves como fuente de verdad; prohibido el registro de "
          "contraseñas en texto legible; verificación automática de las claves del "
          "proveedor con escaneo de secretos."),

    # ----------------------------------------------------------------- P.16
    D("SP-16-01", 16, 31, "Legal", "medio", "organizacional",
      "Obligaciones del trabajador: cumplir políticas, confidencialidad, diligencia de "
      "claves.",
      brecha="El manual define obligaciones pero no exige su aceptación formal por escrito. "
             "Una obligación no firmada es difícil de hacer valer.",
      ref="Código del Trabajo, arts. 7 y 160",
      fix="Documento de «Compromiso de confidencialidad y uso adecuado de los sistemas» "
          "firmado por cada trabajador, incluido en elmanual de funciones.",
      verificacion="Pedir el documento firmado y el porcentaje del padrón que lo tiene.",
      evidencia=["compromiso_confidencialidad.pdf"]),

    D(
      "SP-16-02", 16, 31, "Legal", "alto", "organizacional",
      "Prohibiciones al trabajador: acceder sin autorización, vulnerar la seguridad o "
      "acceder a cuentas ajenas.",
      brecha="El manual no define ningún procedimiento de baja de un_worker que incumple: "
             "ni investigación, ni evidencia (registro de accesos fallidos), ni derecho a "
             "ser oído. La sanción queda sin base probatoria.",
      ref="Código del Trabajo, art. 154 bis",
      fix="Procedimiento de investigación interna con evidencia técnica, entrevista y "
          "acta; y coordinación con RR.HH. para la medida disciplinaria."),

    D("SP-16-03", 16, 31, "Datos personales", "critico", "legal",
      "El manual no menciona en ningún momento los datos personales de los alumnos como "
      "información sensible a proteger.",
      brecha="Es la brecha de fondo del documento: el colegio trata datos sensibles de "
             "menores (ficha escolar, salud, Conducta, imágenes, videovigilancia) y el "
             "manual de TICs no lo reconoce ni una sola vez. A partir del 01-12-2026 la "
             "Ley 21.719 obliga a inventariar los tratamientos, evaluar impacto en los "
             "casos de alto riesgo y comunicar las brechas. Ninguno de los 27 "
             "procedimientos lo contempla.",
      ref="Ley 21.719 (vigencia 01-12-2026); Ley 19.628; art. 19 Nº4 CPR",
      fix="Añadir un procedimiento de gestión de datos personales (o al menos un capítulo "
          "en el P.9 y en el P.24) que defina responsable, inventario de tratamientos, "
          "EIPD y comunicación de brechas. Ver controles LEY-01 a LEY-05.",
      verificacion="Revisar si existe inventario de tratamientos y evaluación de impacto "
                   "antes del 01-12-2026."),

    # ----------------------------------------------------------------- P.17
    D("SP-17-01", 17, 32, "Software", "medio", "organizacional",
      "Prohibido instalar software sin licencia, desinstalar, borrar archivos o cambiar "
      "configuraciones sin autorización de Informática.",
      brecha="Correcto, pero sin inventario de software instalado no se puede detectar la "
             "infracción. El manual sí pide inventario (P.17, punto b), así que la brecha "
             "está en ejecutar el inventario, no en el texto.",
      ref="CIS Control 2.3; Application control",
      fix="Automatizar el inventario de software instalado y contrastarlo mensualmente con "
          "la lista de software autorizado (ver SP-11-01).",
      evidencia=["inventario_software.csv"]),

    D("SP-17-02", 17, 32, "Software", "bajo", "organizacional",
      "Prohibido instalar software de TV/radio/música online y clientes P2P (Torrent, "
      "eMule, Kazza, Ares...).",
      brecha="La lista es de 2015. Los clientes P2P actuales no están nombrados, pero lo "
             "relevante es que el control técnico (bloqueo por categoría en el firewall) es "
             "el del P.14-07, no la lista.",
      ref="", fix="Mantener la norma y dejarla sólo como norma de uso; el bloqueo real es el "
                   "del P.14-07."),

    D("SP-17-03", 17, 33, "Software", "medio", "documental",
      "Soporte Técnico debe realizar inventario de computadores y del software instalado, "
      "accediendo a los equipos con software de recolección de información.",
      brecha="El acceso de Soporte Técnico a los equipos es total y silencioso. No hay "
             "consentimiento del usuario, ni aviso, ni registro de qué datos se recopilan.",
      ref="ISO 27001 A.5.1; Ley 19.628",
      fix="Inventario automatizado y agendado (no under demanda), con aviso al usuario y "
          "política de uso de la información recopilada."),

    D("SP-17-04", 17, 33, "Acceso remoto", "critico", "organizacional",
      "El soporte se entrega de manera presencial o \"utilizando herramientas de control o "
      "acceso remoto a los equipos\".",
      brecha="Autoriza el acceso remoto a cualquier equipo sin condiciones: sin MFA, sin "
             "registro de sesión, sin aviso al usuario, sin aprobación, sin límite de "
             "horario. Es el mismo punto ciego que SP-03-04.",
      ref="CIS Control 8.5; NIST SP 800-63B",
      fix="Política de acceso remoto: herramienta única, MFA, aprobación por el titular del "
          "equipo, aviso visible al usuario, registro de sesión, y prohibiendo el acceso a "
          "equipos sin el usuario presente salvo emergencia declarada."),

    D("SP-17-05", 17, 33, "Respaldo", "medio", "organizacional",
      "Los servicios de mantenimiento o cambio de equipo tienen \"considerado un respaldo de "
      "toda la información contenida\" en ellos.",
      brecha="«Toda la información» sin definir: sin indicar qué se respalda, dónde, con qué "
             "retención ni con qué verificación. Y si el respaldo va al mismo NAS del P.21 "
             "(que es un único punto de fallo), no protege de nada.",
      ref="CIS Control 11.1; CISA 3-2-1",
      fix="Definir el respaldo previo a intervención: qué datos, dónde (copia aislada), "
          "retención y una prueba de restauración registrada. Coordinar con el P.21."),

    # ----------------------------------------------------------------- P.18
    D("SP-18-01", 18, 34, "Correo", "medio", "organizacional",
      "Uso eficiente del buzón: eliminar mensajes antiguos; existe límite de espacio por "
      "casilla.",
      brecha="Correcto. Lo que falta es la retención y el archivo legal de la "
             "correspondencia oficial del colegio: los correos de la dirección son "
             "documentos de la institución y deben conservarse.",
      ref="ISO 27001 A.12.3",
      fix="Definir retención del correo institucional (p. ej. archivo de buzones "
          "departamentales)."),

    D("SP-18-02", 18, 34, "Correo", "alto", "organizacional",
      "Extenso listado de contenidos y usos prohibidos en el correo.",
      brecha="El listado es correcto y copiable de un manual tipo, pero no tiene ninguna "
             "consecuencia verificable: sin filtro de remitentes, sin clasificación de "
             "correo, sin bloqueo de archivos adjuntos ejecutables.",
      ref="ISO 27001 A.7.5",
      fix="Traducir cada prohibición a un control técnico en el filtro de correo "
          "(ver SP-18-03 y SP-20-02)."),

    D("SP-18-03", 18, 36, "Correo", "critico", "tecnico",
      "El manual no exige controles de autenticación de correo (SPF, DKIM, DMARC).",
      brecha="Sin SPF/DKIM/DMARC, el dominio del colegio puede ser usado para suplantar al "
             "director o a la administración en phishing, y los correos legítimos del "
             "colegio acabarán en la carpeta de correo no deseado de terceros. Es una "
             "puerta de entrada directa al personal y a las familias.",
      ref="RFC 7208 (SPF), RFC 6376 (DKIM), RFC 7489 (DMARC); CIS Control 5.9",
      fix="Publicar SPF con los emisores reales (incluido Microsoft 365), DKIM firmado y "
          "DMARC en política de rechazo (p=reject) tras verificar los subdominios.",
      verificacion="Consulta DNS en vivo del dominio.",
      evidencia=["live_dns.json"],
      check={"tipo": "dns_registro", "params": {"tipo": "SPF"}}),

    D("SP-18-04", 18, 35, "Correo", "critico", "organizacional",
      "El manual prohíbe enviar virus por correo, pero no exigeWARE protección antiphishing.",
      brecha="El phishing y elransomware son la vía de entrada real en un colegio (el "
             "fraude al apoderado). No hay ninguna mención a capacitación, ni a simulación, "
             "ni a procedimiento de reporte de phishing.",
      ref="CIS Control 14.2; CISA phishing guidance",
      fix="Campaña de capacitación corta y anual para personal y apoderados; botón de "
          "reporte de phishing; y regla en el filtro que bloquee remitentes nuevos con "
          "enlace."),

    D("SP-18-05", 18, 36, "Acceso lógico", "alto", "organizacional",
      "La institución se reserva el derecho de monitorear el uso de Internet e Intranet "
      "\"sin previo aviso\", incluida la revisión de archivos individuales no privados.",
      brecha="La reserva de monitoreo es válida, pero sin warnotificación, sin "
             "proporcionalidad y sin finalidad definida, es difícil de sostener si un "
             "trabajador la cuestiona. Y con las cámaras y el acceso remoto, lauzzles "
             "actualización de la LPD en 2026 obliga a documentar finalidad y base legal.",
      ref="Ley 19.628; Ley 21.719; Ley 20.606",
      fix="Documentar la finalidad, el alcance y la base legal del monitoreo; informar a "
          "los trabajadores; y limitarlo a lo necesario."),

    D("SP-18-06", 18, 36, "Red", "medio", "organizacional",
      "Prohibido el uso recreativo de internet, televisión y radio en línea por ancho de "
      "banda.",
      brecha="Correcto. Verificar que el bloqueo exista también en los equipos móviles "
             "(tablets), no sólo en el firewall de la red.",
      ref="", fix="Confirmar filtrado en la VLAN de aula y en los hotspots."),

    # ----------------------------------------------------------------- P.19
    D("SP-19-01", 19, 37, "Acceso remoto", "alto", "organizacional",
      "El usuario VPN declara que toda la información en sus equipos y en tránsito es "
      "propiedad del colegio y puede ser administrada o monitoreada.",
      brecha="La declaración de conducta es correcta, pero no hay ninguna condición "
             "técnica de acceso: sin MFA, sin lista de usuarios autorizados, sin "
             "restricción de dispositivos, sin registro de sesiones, sin revocación al "
             "término de la relación. Un VPN sin esas condiciones es un acceso permanente "
             "a la red interna.",
      ref="CIS Control 12.4",
      fix="Condiciones mínimas: MFA obligatorio, túnel completo, sólo usuarios autorizados "
          "por Gerencia, registro de conexiones, y baja automática al término de la "
          "relación laboral."),

    D("SP-19-02", 19, 37, "Acceso remoto", "medio", "organizacional",
      "El usuario se compromete a no divulgar información, no revelar su contraseña, no "
      "permitir su uso por terceros y desconectarse al terminar de usar el VPN.",
      brecha="No hay firma de este compromiso (ver SP-16-01) ni verificación técnica de que "
             "la sesión se cierra: un equipo con el VPN instalado mantiene el túnel "
             "disponible permanentemente.",
      ref="CIS Control 12.4",
      fix="Firmar el acuerdo; y política de desconexión automática (timeout de sesión) y "
          "del equipo (el VPN sólo se levanta al iniciar sesión del usuario)."),

    # ----------------------------------------------------------------- P.20
    D("SP-20-01", 20, 38, "Endpoint", "medio", "tecnico",
      "El administrador de redes instala los productos de antivirus en todas las áreas, "
      "con supervisión del encargado del área.",
      brecha="El manual habla de «productos de antivirus», un concepto de 2010. En Windows "
             "10/11 y Server 2016+ la protección real es Microsoft Defender Antivirus + "
             "EDR + protección contra ransomware + control de aplicaciones. Un antivirus "
             "sin EDR no detectacredential theft ni movimiento lateral, que es como "
             "operan los ransomware actuales.",
      ref="Microsoft Defender for Endpoint; CIS Control 10.x",
      fix="Verificar que la protección real está activa: Defender Antivirus, Protection "
          "History, Tamper Protection, Controlled Folder Access ypuerta de ransomware "
          "(vers SP-20-06).",
      verificacion="Estado de Defender por equipo.",
      evidencia=["defender_estado.csv"],
      check={"tipo": "defender_estado", "params": {"archivo": "defender_estado.csv"}}),

    D(
      "SP-20-02", 20, 38, "Correo", "alto", "tecnico",
      "Habilitar los filtros y programas detectores en el servidor de mensajería.",
      brecha="«Filtros» sin verificar que incluyan antiphishing, antimalware de adjuntos y "
             "listas de remitentes bloqueados. El filtro antispam de M365, por defecto, no "
             "bloquea adjuntos de ejecutables.",
      ref="CIS Control 14.2; Microsoft",
      fix="Verificar la configuración del filtro de M365: antiphishing, bloqueo de "
          "ejecutables y de archivos con macros, simulación de adjuntos."),

    D("SP-20-03", 20, 38, "Endpoint", "alto", "tecnico",
      "En el servidor de antivirus se habilita que se actualice sistemática y "
      "automáticamente.",
      brecha="El manual no fija una antigüedad máxima de las firmas. En la práctica, esto es "
             "lo que separa un antivirus de un placebo: hay equipos con firmas de hace "
             "semanas que siguen contando como «actualizado».",
      ref="CIS Control 10.1 (antivirus updated)",
      fix="Antigüedad máxima de firmas: 3 días; y alerta si algún equipo la supera.",
      verificacion="Edad de la firma de antivirus por equipo.",
      evidencia=["defender_estado.csv"],
      check={"tipo": "defender_estado",
             "params": {"archivo": "defender_estado.csv", "edad_firma_max": 3}}),

    D("SP-20-04", 20, 38, "Endpoint", "alto", "tecnico",
      "Se inhabilita en todas las computadoras la autoejecución de programas a través de "
      "soportes externos, puertos USB y lectores de discos.",
      brecha="Es el control más avanzado de todo el manual (equivale a CIS 8.4 y a la "
             "recomendación de CISA sobre USB), y se contradice con el P.5, que permite "
             "entregar pendrives a directivos sin exigir cifrado. Debe quedar explícito qué "
             "excepciones existen.",
      ref="CIS Control 8.4; CISA guidance on removable media",
      fix="Mantener el bloqueo por GPO con una lista corta y aprobada de excepciones, y "
          "exigir cifrado a todo medio institucional.",
      verificacion="Preferencias de Defender (ejecución desde medios extraíbles).",
      evidencia=["defender_preferencias.txt"],
      check={"tipo": "config_valores", "params": {
          "archivo": "defender_preferencias.txt",
          "valores": [
              {"clave": "DisableRemovableMediaExecution", "operador": "activo"},
              {"clave": "RemovableMediaScan", "operador": "activo"}]}}),

    D("SP-20-05", 20, 38, "Endpoint", "medio", "organizacional",
      "Los usuarios deben verificar que su puesto de trabajo tenga antivirus actualizado, "
      "revisar el disco no menos de una vez por semana y revisar todo pendrive, disco duro "
      "externo o medio portátil antes de conectarlo.",
      brecha="Encargar al usuario la verificación de seguridad es un control débil y no "
             "verificable: la condición humana no escala y casi nunca se cumple. Además, "
             "con el bloqueo de autoejecución del P.20-04, buena parte de este control es "
             "innecesaria: el USB ya no puede ejecutarse solo.",
      ref="CIS Control 10.3; CISA removable media",
      fix="Dejar la verificación al antivirus del servidor (escaneo automático de medios) y "
          "usar el control humano sólo para reportar incidentes."),

    D("SP-20-06", 20, 39, "Endpoint", "critico", "tecnico",
      "El manual no exige protección contra ransomware ni detección de comportamiento.",
      brecha="Sólo antivirus. Sin protección contra ransomware (control de carpetas "
             "protegidas, control de cmd.exe y PowerShell), sin "
             "detección de comportamiento y sin copias inmutables (ver SP-21-04), el "
             "ransomware que entra por un correo o un notebook se propaga al NAS sin "
             "obstáculo.",
      ref="Microsoft Defender for Endpoint (ransomware protection); CIS Control 10.7; "
          "CISA #3 Immutable Backups",
      fix="Activar ransomware protection y Controlled Folder Access, y configurar copias "
          "inmutables o aisladas del NAS (ver SP-21-04).",
      verificacion="Preferencias de Defender y estado de protección.",
      evidencia=["defender_preferencias.txt"],
      check={"tipo": "config_valores", "params": {
          "archivo": "defender_preferencias.txt",
          "valores": [
              {"clave": "DisableRealtimeMonitoring", "operador": "desactivado"},
              {"clave": "DisableBehaviorMonitoring", "operador": "desactivado"},
              {"clave": "DisableScriptScanning", "operador": "desactivado"},
              {"clave": "EnableControlledFolderAccess", "operador": "activo"},
              {"clave": "PUAProtection", "operador": "activo"}]}}),

    D("SP-20-07", 20, 39, "Endpoint", "medio", "organizacional",
      "Pasos a seguir ante la detección de un virus: tomar nota, apagar, comunicar a "
      "Informática, descontaminar.",
      brecha="«Apagar la computadora» como primer paso destruye la evidencia en memoria y "
             "no detiene la propagación: si el equipo está en la red, seguir conectado "
             "mientras se limpia propaga la contaminación.",
      ref="NIST SP 800-61; ISO 27001 A.5.24",
      fix="El primer paso debe ser aislar el equipo de la red (desconectar el cable / "
          "apagar el WiFi), no apagar. Sólo después preservar y escalar."),

    # ----------------------------------------------------------------- P.21
    D("SP-21-01", 21, 40, "Respaldo", "critico", "tecnico",
      "Los respaldos de los ordenadores: aplicación definida, frecuencia diaria/semanal/"
      "mensual, automática, replicados a servidores con carpetas por área, retención 5 "
      "años, fuente principal el NAS.",
      brecha="El diseño es 1-1: todo va al NAS, en el mismo recinto. Un ransomware, un "
             "incendio o un robo con las llaves del gabinete destruyen producción y copia "
             "a la vez. Tampoco se define RPO/RTO, ni se vigila que el respaldo haya "
             "terminado bien, ni hay copia de los servicios en la nube (M365, OneDrive, "
             "SharePoint, Bookings, NAS).",
      ref="CISA 3-2-1; CIS Control 11.1; ISO 27001 A.12.3",
      fix="Política 3-2-1-1-0: 3 copias, 2 medios, 1 copia fuera del sitio, 1 copia "
          "inmutable y verificación 0 errores. Copia de M365 (que es donde están los correos "
          "y archivos de hoy) y prueba de restauración documentada trimestral.",
      verificacion="Revisar la configuración del respaldo y el historial de tareas "
                   "exitosas y fallidas.",
      evidencia=["respaldo_trabajos.csv"],
      check={"tipo": "respaldo_trabajos", "params": {"archivo": "respaldo_trabajos.csv"}}),

    D("SP-21-02", 21, 40, "Respaldo", "alto", "documental",
      "Respaldo del servidor SQL: programado automático, frecuencia diaria, retención 5 "
      "años; sólo Informática y Contabilidad pueden modificar la programación.",
      brecha="Control de segregación de funciones bien planteado (es el control más "
             "maduro del manual). Le falta: verificación de que el respaldo termina bien y "
             "una prueba de restauración, que es lo que de verdad protege.",
      ref="CIS Control 11.1",
      fix="Alerta ante fallos de respaldo y prueba de restauración mensual documentada.",
      evidencia=["respaldo_trabajos.csv"]),

    D("SP-21-03", 21, 40, "Respaldo", "critico", "tecnico",
      "Respaldo del controlador de dominio mediante RAID espejo (disco espejo) o imagen "
      "del Windows Server.",
      brecha="RAID espejo no es un respaldo: protege de la falla de un disco, no de la "
             "eliminación maliciosa, del ransomware, del robo ni del incendio. Es la misma "
             "máquina, en el mismo lugar, con los mismos accesos. Una imagen del Windows "
             "Server tampoco protege la base de datos ni los datos de los perfiles.",
      ref="Microsoft «RAID is not a backup»; CISA #3 Immutable Backups; CIS Control 11.1",
      fix="Copias del DC fuera del equipo, inmutables y con una copia fuera del sitio "
          "(incluido el System Volume Shadow Copy y el backup completo del dominio, no sólo "
          "la imagen del SO).",
      verificacion="Confirmar existencia, ubicación y prueba de restauración de la copia "
                   "del dominio.",
      evidencia=["respaldo_trabajos.csv"]),

    D("SP-21-04", 21, 40, "Respaldo", "alto", "organizacional",
      "Periodicidad de retención del respaldo: 5 años.",
      brecha="Cinco años de retención de un respaldo de datos personales de alumnos es un "
             "plazo excesivo y una carga de protección de datos: si el colegio no puede "
             "aclarar para qué necesita 5 años de fichas de menores, el problema es de "
             "minimización, no de seguridad.",
      ref="Ley 21.719 (principio de finalidad); Ley 19.628",
      fix="Retención alineada a la finalidad (p. ej. 5 años lectiva + plazo legal de "
          "conservación de documentos escolares según normativa), y borrado documentado de "
          "lo que exceda."),

    # ----------------------------------------------------------------- P.22
    D("SP-22-01", 22, 41, "Web", "medio", "documental",
      "Mantener actualizadas las páginas del sitio; reparar errores de lógica; garantizar "
      "el funcionamiento óptimo.",
      brecha="El manual no nombra la tecnología del sitio ni el proveedor. \"Garantizar "
             "el funcionamiento óptimo\" no es un control de seguridad.",
      ref="",
      fix="Documentar el stack del sitio y quién es el responsable técnico."),

    D("SP-22-02", 22, 41, "Web", "critico", "tecnico",
      "«Implementar sistemas de seguridad» (sitio web e intranet).",
      brecha="La única línea de seguridad del procedimiento. Sin requisitos concretos no "
             "hay nada que auditar: nada de HTTPS obligatorio, nada de cabeceras de "
             "seguridad, nada de WAF, nada de MFA en el panel de administración, nada de "
             "respaldo del sitio, nada de parcheo del CMS. Como el sitio y el buzón "
             "comparten dominio, una toma de control del sitio es un vector directo contra "
             "el correo del colegio (ver SP-18-03).",
      ref="OWASP ASVS; CIS Control 16.x; MDN Security Headers",
      fix="HTTPS con TLS 1.2+ y HSTS; cabeceras (CSP, X-Content-Type-Options, "
          "Referrer-Policy); MFA en el hosting y en el registrador del dominio; parcheo "
          "del CMS y de sus extensiones; respaldo del sitio.",
      verificacion="Análisis externo en vivo del sitio.",
      evidencia=["live_web.json"],
      check={"tipo": "web_seguridad", "params": {}}),

    D("SP-22-04", 22, 41, "Web", "critico", "tecnico",
      "El sitio institucional está construido sobre WordPress, alojado en un hosting "
      "compartido.",
      brecha="Verificado desde Internet: el sitio declara su versión exacta de WordPress en "
             "el meta «generator», tiene XML-RPC activo en /xmlrpc.php y no emite "
             "cabeceras de seguridad. XML-RPC es el vector histórico de fuerza bruta contra "
             "cuentas de WordPress y no aporta nada a un sitio institucional.",
      ref="WordPress Codex (hardening); OWASP; CISA",
      fix="Desactivar XML-RPC (plugin de seguridad o bloqueo de /xmlrpc.php en el hosting), "
          "ocultar la versión en el meta generator y activar las cabeceras de seguridad.",
      verificacion="Comprobación externa automática en cada auditoría y manual en "
                   "https://saintpatricktemuco.cl/xmlrpc.php",
      evidencia=["live_web.json"],
      check={"tipo": "wordpress_exposicion", "params": {}}),

    D("SP-22-05", 22, 41, "Web", "alto", "tecnico",
      "Acceso al panel del sitio, al hosting y al registrador del dominio.",
      brecha="El manual no dice quién administra el sitio, si el panel exige MFA, ni si el "
             "registrador del dominio tiene autenticación de dos factores. Sin MFA, perder el "
             "correo del titular del dominio significa perder el sitio y el correo "
             "institucional a la vez, porque comparten dominio.",
      ref="CIS Control 16.x; OWASP ASVS",
      fix="MFA en el panel de WordPress, en el hosting y en el registrador del dominio; "
          "respaldos automáticos del sitio y de la base de datos; y una cuenta de correo de "
          "recuperación que no dependa del mismo dominio."),

    D(
      "SP-22-03", 22, 41, "Web", "alto", "tecnico",
      "La intranet maneja toda la información interna que circula a los funcionarios.",
      brecha="La intranet no tiene procedimiento propio: nada dice dónde está alojada, "
             "quién accede, con qué se autentican ni qué contiene. Es el sistema donde "
             "estarían las fichas de alumnos, las actas de conducta y las actas de reunión "
             "de dirección.",
      ref="ISO 27001 A.9.1",
      fix="Documentar la intranet: autenticación, perfil de acceso, contenido, respaldo y "
          "responsable. Si es SharePoint/OneDrive, aplicar la misma gestión que M365."),
]