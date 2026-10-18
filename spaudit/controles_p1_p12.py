"""Controles del Manual de Procedimientos Saint Patrick 2026-II — Procedimientos 1 a 12."""

from .controles_comunes import D

CONTROLES = [
    # ------------------------------------------------------------------ P.1
    D("SP-01-01", 1, 4, "Acceso físico", "medio", "organizacional",
      "Las áreas limitadas tendrán relación del personal con acceso, firmada por el "
      "máximo directivo y plasmada en la puerta del local.",
      brecha="No se fija periodicidad de actualización ni responsable de revocarla. "
             "La lista en la puerta queda desactualizada sin que nadie lo detecte.",
      ref="CIS Control 6.x (control de acceso físico)",
      fix="Revisar la relación de accesos cada 6 meses y después de cada cambio de "
          "personal; versionarla con fecha y firma.",
      verificacion="Pedir la relación de cada área y su fecha de última actualización."),

    D("SP-01-02", 1, 4, "Acceso físico", "medio", "organizacional",
      "Personal ajeno ingresa siempre en presencia de una persona con acceso autorizado.",
      brecha="No hay registro de quién acompaña ni de qué se accedió. La regla depende "
             "de la buena memoria del acompañante.",
      ref="ISO 27001 A.7.2 (registro de acceso)",
      fix="Usar el libro de incidencias o un registro simple: fecha, hora, visitante, "
          "acompañante, equipo intervenido."),

    D("SP-01-03", 1, 4, "Acceso físico", "medio", "organizacional",
      "El nochero comprueba después de las 18:00 la seguridad de locales y puertas "
      "laterales/traseras, registrándolo en un libro de incidencias.",
      brecha="El control es 100% manual y en papel: no deja rastro digital, no se puede "
             "auditar si se hizo todos los días ni si hubo omisiones.",
      ref="ISO 27001 A.7.2",
      fix="Digitalizar el registro (hoja de cálculo con fecha obligatoria) y definir que "
          "toda anomalía genera un ticket, no solo una nota."),

    D("SP-01-04", 1, 4, "Acceso físico", "medio", "organizacional",
      "Las salas y locales permanecen cerrados y sellados al término de la jornada y del aseo.",
      brecha="No hay control cruzado con el inventario de llaves ni verificación posterior.",
      ref="ISO 27001 A.7.2",
      fix="Inventario de llaves por local, con entrega y devolución registradas."),

    D("SP-01-05", 1, 4, "Acceso físico", "bajo", "documental",
      "A toda persona ajena se le entrega en portería un solapín que identifica el propósito.",
      brecha="El solapín identifica el propósito pero no hay verificación de identidad, "
             "ni registro de entrega/devolución, ni caducidad. Un solapín puede circular.",
      ref="CIS Control 6.5",
      fix="Vincular el solapín a un registro con nombre, documento, ingreso y salida; "
          "devolución obligatoria al salir."),

    D("SP-01-06", 1, 16, "Llaves", "alto", "organizacional",
      "Instructivo: si quien solicita la sala se atrasa, debe acercarse a Gerencia a "
      "buscar la llave.",
      brecha="No existe inventario de llaves, ni registro de a quién se entrega, ni "
             "devolución obligatoria. La llave de la sala de computación y de los "
             "gabinetes de red circula sin trazabilidad.",
      ref="CIS Control 6.x; CISA guidance on physical security",
      fix="Contar y numerar las llaves críticas (sala de computación, gabinete de red, "
          "oficina), con registro de entrega, devolución y responsable de custodia."),

    D("SP-01-07", 1, 15, "Acceso físico", "medio", "documental",
      "El laboratorio se mantiene disponible de 8:15 a 16:20 con registro de acceso y "
      "reglamento escolar.",
      brecha="El registro no está digitalizado y no se indica quién lo revisa ni con qué "
             "frecuencia.",
      ref="ISO 27001 A.7.2",
      fix="Registro en formato digital con responsable de revisión semanal."),

    # ------------------------------------------------------------------ P.2
    D("SP-02-01", 2, 5, "Inventario", "medio", "documental",
      "Los medios informáticos se clasifican en Activos Fijos Tangibles, Partes y Piezas, "
      "Útiles y Materiales.",
      brecha="La clasificación del propio manual es contradictoria: «Equipos de sonido» "
             "aparece en Activos Fijos Tangibles (pág. 5) y otra vez en Partes y Piezas "
             "(subwoofer, pág. 6); «Mouse» y «ratones» están duplicados en Materiales "
             "(pág. 6). Mientras el criterio esté ambiguo el inventario no es auditable.",
      ref="Coherencia interna del manual, págs. 5-6",
      fix="Corregir la tabla: cada categoría debe ser excluyente. Eliminar duplicados y "
          "decidir en qué categoría entran los equipos de sonido.",
      verificacion="Cotejar la tabla de equipamiento con el inventario real y detectar "
                   "elementos en más de una categoría.",
      evidencia=["inventario.csv"],
      check={"tipo": "csv_columnas",
             "params": {"archivo": "inventario.csv", "requeridas": ["id", "tipo", "categoria", "serial", "ubicacion"]}}),

    D("SP-02-02", 2, 10, "Inventario", "alto", "documental",
      "Debe existir correspondencia exacta entre la Tabla de Equipamiento Informático y los "
      "activos fijos registrados en contabilidad.",
      brecha="No hay mecanismo de conciliación: se declara la correspondencia pero nada la "
             "comprueba periódicamente. Los equipos que no son activos (tablets, "
             "equipos de sala) quedan fuera del control patrimonial.",
      ref="Manual págs. 10-11",
      fix="Exportar ambos listados (Informática y Contabilidad) y conciliarlos trimestralmente; "
          "dejar el acta firmada.",
      verificacion="Conciliación Tabla de Equipamiento vs. Activos Fijos.",
      evidencia=["inventario.csv"]),

    D("SP-02-03", 2, 10, "Inventario", "medio", "documental",
      "Existe un Expediente técnico digital por configuración, mantenido desde la "
      "adquisición hasta la baja, con acceso restringido al Departamento Informático.",
      brecha="«Expediente técnico digital» no define dónde vive, con qué permisos, ni si "
             "tiene copia de seguridad. Si vive en un_share o en el buzón del jefe, el "
             "único respaldo documental del colegio es frágil.",
      ref="ISO 27001 A.12.3; A.5.3",
      fix="Definir ubicación, permisos (solo el grupo Informática), y respaldo del propio "
          "expediente. Registrar la política en el manual."),

    D("SP-02-04", 2, 11, "Inventario", "medio", "documental",
      "Los datos del expediente deben corresponder con la situación real del equipo y "
      "ser certificados por el jefe del departamento.",
      brecha="La certificación es una declaración, no una verificación. Nada comprueba que "
             "el serial del expediente sea el del equipo instalado.",
      ref="",
      fix="Automatizar: escanear el serial/etiqueta de cada equipo al menos una vez al año y "
          "compararlo con el expediente."),

    D("SP-02-05", 2, 9, "Mantenimiento", "medio", "documental",
      "El mantenimiento no puede exceder 12 meses: se debe dar al menos 1 mantenimiento "
      "por equipo al año.",
      brecha="No hay evidencia de ejecución real ni fecha por equipo. Es un compromiso "
             "escrito sin control de cumplimiento, y es además la puerta de entrada del "
             "software desactualizado (parcheo).",
      ref="CIS Control 7.1 (gestión de vulnerabilidades)",
      fix="Plan anual de mantenimiento con fecha por equipo y registro firmado; reportar "
          "ejecución a Gerencia.",
      verificacion="Contar equipos con mantenimiento fechado en los últimos 12 meses.",
      evidencia=["mantenimiento.csv"]),

    D("SP-02-06", 2, 8, "Reparaciones", "bajo", "documental",
      "La reparación capital sólo se admite si su costo es ≤ al de un equipo nuevo "
      "similarly; se informa a Gerencia y Contabilidad.",
      brecha="Control financiero, no de seguridad. Se mantiene porque evidencia criterio "
             "de gasto, pero no aporta a la ciberseguridad.",
      ref="", fix="Dejarlo como está."),

    D("SP-02-07", 2, 7, "Reparaciones", "medio", "documental",
      "La chatarra electrónica se entrega a empresa especializada con documento firmado "
      "por ambas partes y aprobado por Gerencia.",
      brecha="Sin plazo máximo para la entrega: los discos duros viejos con datos de alumnos "
             "pueden quedar almacenados indefinidamente en el depósito.",
      ref="Ley 20.296 (residuos peligrosos); Ley 19.628",
      fix="Fijar plazo (máx. 30 días) y certificado de destrucción/desintegración de "
          "medios que contuvieron datos personales."),

    D("SP-02-08", 2, 8, "Reparaciones", "bajo", "documental",
      "Todo registro de reparación debe quedar en el Expediente técnico digital o en el "
      "Libro de Control de Reparaciones.",
      brecha="El «Libro de Control de Reparaciones» no existe como documento con "
             "campos definidos; queda absorbido por el expediente.",
      ref="", fix="Definir campos mínimos (fecha, equipo, falla, acción, responsable)."),

    D("SP-02-09", 2, 12, "Movimientos", "medio", "documental",
      "Todo cambio de ubicación de un medio informático es autorizado por Gerencia y "
      "coordinado con Informática para actualizar el expediente.",
      brecha="No hay control sobre el traslado de equipos fuera del colegio, que es el "
             "caso con más exposición de datos (robo en la calle, equipo en el auto).",
      ref="", fix="Exigir autorización también para salida temporal y registro de "
                   "portátil/notebook fuera del recinto."),

    D("SP-02-10", 2, 13, "Bajas", "medio", "documental",
      "El Expediente de Baja requiere relación de equipos, modelo de baja y dictamen "
      "técnico, más certificación de Informática, grupo directivo y Gerencia.",
      brecha="No se exige certificación de destrucción segura del disco del equipo dado de "
             "baja (ver SP-02-07).",
      ref="", fix="Agregar certificado de destrucción de datos al expediente de baja."),

    # ------------------------------------------------------------------ P.3
    D("SP-03-01", 3, 14, "Uso de equipos", "medio", "organizacional",
      "Las solicitudes de tecnología deben hacerse por la plataforma Microsoft Bookings "
      "(URL publicada en el manual).",
      brecha="La URL de Bookings es pública y muestra el dominio del tenant de Microsoft "
             "365 (saintpatricktemuco.cl) y, según la configuración, los nombres de los "
             "usuarios que organizan las reservas. Es enumeration de cuentas y un punto de "
             "entrada para phishing dirigido al personal.",
      ref="OWASP; enumeración de usuarios en servicios publicados",
      fix="Usar Bookings con acceso restringido a la cuenta del colegio y desactivar la "
          "exposición pública del nombre de los anfitriones; alternativamente usar un "
          "formulario interno.",
      verificacion="Revisar en vivo la página de reservas.",
      evidencia=["live_web.json"],
      check={"tipo": "http_headers", "params": {"url": "https://bookings.cloud.microsoft/book/SolicituddeTecnologias@saintpatricktemuco.cl/"}}),

    D("SP-03-02", 3, 14, "Uso de equipos", "medio", "organizacional",
      "La entrega de equipos se hace directamente al docente; bajo ningún concepto un "
      "alumno puede recibir la tecnología.",
      brecha="Correcto como norma, pero no hay control técnico que impida a un alumno "
             "acceder a un equipo que quedó abierto (ver SP-03-04: los notebooks deben "
             "quedar encendidos y desbloqueados).",
      ref="", fix="Bloqueo de sesión automático y pantalla de bloqueo en los equipos de sala."),

    D("SP-03-04", 3, 17, "Gestión remota", "critico", "tecnico",
      "«Dejar abierto y encendido el notebook (remotamente se actualizará, por lo cual no "
      "debe ser apagado)».",
      brecha="El manual revela que existe una herramienta de gestión remota sobre los "
             "equipos de sala, pero NO define: qué herramienta, quién accede, con qué "
             "credencial, si hay MFA, si las sesiones quedan registradas, ni qué datos son "
             "accesibles. Es el mayor punto ciego del documento: acceso remoto total a los "
             "equipos de los docentes, con la sesión abierta.",
      ref="CIS Control 8.5 (access management); CISA remote access guidance",
      fix="Documentar la herramienta de gestión remota; exigir MFA; cuenta de servicio "
          "dedicada (no la del profesor); registro y retención de sesiones; bloqueo de "
          "pantalla; aviso al usuario en cada conexión.",
      verificacion="Identificar la herramienta en uso y revisar sus controles de acceso.",
      evidencia=["gestion_remota.txt"]),

    D("SP-03-05", 3, 15, "Uso de equipos", "medio", "documental",
      "Los equipos se revisan al término de cada curso y se lleva un registro por tecnología.",
      brecha="Control manual sin verificación; no registra estado de seguridad (parches, "
             "antivirus) sino sólo el estado físico.",
      ref="", fix="Agregar al registro columnas de estado de seguridad y que la revisión "
                   "incluya verificación de parches."),

    D("SP-03-06", 3, 16, "Responsabilidad", "alto", "legal",
      "«Es responsabilidad de quien recibe tecnologías la reposición del medio en caso de "
      "falla por fuerza mayor o externa (Ej: daños físicos, software o extravío)» "
      "(repetido en el instructivo de sala).",
      brecha="Traslada al trabajador la reposición por fallas de software, es decir por "
             "causas que no controla, sin distinguir negligencia de falla técnica. Es un "
             "punto de conflicto laboral y una excusa para no reportar incidentes: quien "
             "pierde el equipo calla. Debe revisarse con asesoría legal/laboral.",
      ref="Código del Trabajo, arts. 7 y 160",
      fix="Reformular: aviso obligatorio e inmediato de cualquier falla; el Colegio asume "
          "el costo del defecto técnico; responsabilidad del usuario sólo ante daño "
          "intencional o negligencia acreditada.",
      verificacion="Revisión jurídica del texto antes de la próxima revisión del manual."),

    D("SP-03-07", 3, 15, "Uso de equipos", "bajo", "organizacional",
      "Las tecnologías se entregan por número de lista y el docente las retira y almacena "
      "al finalizar el turno; tablets numeradas del 01 al 35.",
      brecha="La entrega por número es un control trazable y bueno; falta la devolución "
             "registrada y con firma (queda implícita pero no documentada).",
      ref="", fix="Agregar hoja de entrega y devolución por número."),

    # ------------------------------------------------------------------ P.4
    D("SP-04-01", 4, 18, "Acceso físico", "medio", "organizacional",
      "Todas las computadoras se sellan; todo cambio de sello se refleja en el expediente "
      "con las razones.",
      brecha="No hay control de los números de serie de los sellos ni registro de sellos "
             "rotos o destruidos; no cubre tablets ni otros dispositivos (que sí llevan "
             "etiqueta de identificación).",
      ref="", fix="Inventario de sellos por número de serie, con registro de destrucción."),

    # ------------------------------------------------------------------ P.5
    D("SP-05-01", 5, 19, "Medios extraíbles", "bajo", "documental",
      "Los pendrives se entregan sólo a directivos y administrativos, con acta y "
      "aprobación de Gerencia; Contabilidad los registra.",
      brecha="El alcance es correcto (reduce superficie), pero no exige cifrado ni prohíbe "
             "el uso de medios propios por el resto del personal. En la práctica, quién "
             "conecta qué no es verificable.",
      ref="CIS Control 12.3; CISA guidance on USB",
      fix="Exigir cifrado nativo en todo medio institucional; bloquear USB por GPO con "
          "excepciones documentadas (el manual ya lo pide en el P.20, pero no lo conecta "
          "con este procedimiento)."),

    # ------------------------------------------------------------------ P.6
    D("SP-06-01", 6, 20, "Incidentes", "alto", "legal",
      "Ante pérdida o extravío: el usuario avisa a Informática, que avisa a Gerencia; "
      "Informática actualiza el expediente.",
      brecha="No hay plazo (debe ser inmediato), no hay borrado remoto del equipo, no hay "
             "cambio de claves ni revocación de sesiones, y —lo más importante— no hay "
             "evaluación de si la pérdida también expuso datos personales. Bajo la Ley 21.719 "
             "(vigente desde el 01-12-2026, art. 14 sexies) una pérdida de equipo con "
             "datos de menores obliga a comunicar sin dilaciones indebidas y a informar a "
             "los titulares.",
      ref="Ley 21.719, arts. 14 sexies y 15 ter (vigencia 01-12-2026)",
      fix="Reescribir el procedimiento con: aviso inmediato, bloqueo remoto y borrado, "
          "rotación de credenciales, y evaluación de brecha de datos con comunicación a "
          "familias cuando corresponda.",
      verificacion="Leer el procedimiento vigente y contrastarlo con el art. 14 sexies."),

    # ------------------------------------------------------------------ P.7
    D("SP-07-01", 7, 21, "Identidad", "medio", "tecnico",
      "Active Directory se mantiene actualizado con altas y traslados; existen OUs por "
      "área y grupos por departamento.",
      brecha="Bien planteado. Falta la revisión periódica: nada obliga a comprobar que las "
             "OUs y grupos siguen reflejando la organización real.",
      ref="CIS Control 5.2 (account management)",
      fix="Revisar trimestralmente las unidades organizativas y grupos contra el organigrama "
          "vigente, y dar de baja las cuentas que no correspondan a nadie.",
      verificacion="Exportar usuarios, grupos y UO y revisar cuentas huérfanas.",
      evidencia=["usuarios_ad.csv", "grupos_ad.csv"],
      check={"tipo": "csv_columnas",
             "params": {"archivo": "usuarios_ad.csv",
                        "requeridas": ["SamAccountName", "Department", "Enabled"]}}),

    D("SP-07-02", 7, 21, "Identidad", "alto", "organizacional",
      "RR.HH. avisa con no menos de 72 horas de anticipación la baja o traslado de un "
      "trabajador; Informática cierra la cuenta e inhabilita permisos.",
      brecha="72 horas de anticipación es insuficiente para el caso típico: el aviso suele "
             "coincidir con el último día, cuando el colaborador ya está fuera. Además no "
             "exige: cerrar sesión, revocar tokens, desactivar buzones compartidos, ni "
             "traspasar la propiedad de archivos.",
      ref="CIS Control 6.5 (revocation);",
      fix="Checklist de baja con 15 pasos: cerrar sesión, bloquear dispositivo, revocar "
          "tokens y sesiones M365, rotar claves compartidas, traspasar archivos, desactivar "
          "en cada plataforma (ver P.26), y devolver llaves/equipos con firma.",
      verificacion="Pedir el último caso de baja ejecutada y contrastarlo con el checklist."),

    D("SP-07-03", 7, 21, "Identidad", "medio", "organizacional",
      "El encargo de Recursos Humanos incorpora a las responsabilidades laborales las "
      "funciones y responsabilidades de seguridad informática.",
      brecha="La responsabilidad queda en el papel de funciones, sin documento firmado por "
             "el trabajador ni con consequences claras más allá de la sanción del P.8.",
      ref="", fix="Firmar un «Compromiso de confidencialidad y uso adecuado de sistemas» "
                   "con cada trabajador (ver SP-16-03)."),

    D("SP-07-04", 7, 21, "Identidad", "medio", "organizacional",
      "El Administrador de Red crea la cuenta y habilita los derechos concedidos por el "
      "jefe de departamento con aprobación de Gerencia.",
      brecha="«Derechos concedidos por el jefe de departamento» sin un perfil de privilege "
             "por rol documentado: el criterio queda en la discreción del jefe, lo que en la "
             "práctica deriva en acumulación de permisos.",
      ref="CIS Control 6.1; NIST SP 800-53 AC-6",
      fix="Definir 4-5 perfiles de acceso (docente, administrativo, dirección, informática) "
          "y asignar por perfil, no caso a caso."),

    # ------------------------------------------------------------------ P.8
    D("SP-08-01", 8, 22, "Acceso lógico", "medio", "organizacional",
      "El acceso a las tecnologíasinstalled se autoriza por Gerencia; técnicos "
      "externos trabajan en presencia de persona autorizada; hay sanción para el acceso no "
      "autorizado.",
      brecha="El control es correcto pero la «sanción» sin un procedimiento de auditoría "
             "previo: sin registro de accesos fallidos y sin revisión, la sanción es "
             "discrecional.",
      ref="", fix="Revisar mensualmente eventos 4625/4771 y accesos no autorizados."),

    D("SP-08-02", 8, 23, "Claves", "critico", "organizacional",
      "«Las claves de los controladores de dominio y red, wifi y bluehost serán de acceso "
      "limitado al Departamento Informático [...] tendrá un respaldo de todas las "
      "contraseñas debidamente actualizado».",
      brecha="El manual ordena mantener un respaldo de TODAS las contraseñas administrativas. "
             "Un «respaldo de contraseñas» sin indicar dónde, cifrado ni control de acceso "
             "es, en la práctica, una planilla o un documento con la clave del controlador "
             "de dominio, del firewall, del wifi y del hosting. Si ese archivo se filtra, "
             "se pierde la red completa. Contradice el propio deber de confidencialidad que "
             "el manual impone al P.16.",
      ref="CIS Control 5.4; OWASP Secrets Management; NIST SP 800-63B",
      fix="Sustituir «respaldo de contraseñas» por un gestor de claves corporativo con "
          "cifrado y auditoría (Vaultwarden/KeePassXC en servidor, o el gestor del "
          "organismo), acceso con MFA, y registro de quién abre qué secreto.",
      verificacion="Pedir que muestren dónde están las claves administrativas y quién "
                   "puede leerlas.",
      evidencia=["gestor_claves.txt"]),

    D("SP-08-03", 8, 23, "Claves", "critico", "organizacional",
      "«El Departamento Informático mantendrá actualizado el registro de contraseñas, "
      "modificando las mismas según se requiera».",
      brecha="Un «registro de contraseñas» es exactamente el patrón que la ISO 27001 y "
             "CIS prohíben: almacenamiento de secretos en texto legible. Debe eliminarse "
             "del procedimiento.",
      ref="ISO/IEC 27001 A.5.17 (authentication information); CIS Control 5.4",
      fix="Eliminar el registro de contraseñas; sustituir por un gestor de claves con "
          "rotación programada y auditoría."),

    D("SP-08-04", 8, 23, "Claves", "medio", "organizacional",
      "Las claves de sesión y de correo son personales e intransferibles.",
      brecha="Regla escrita pero sin respaldo técnico: nada impide compartir la clave de "
             "correo entre dos professors, y no hay firma ni registro del compromiso.",
      ref="CIS Control 5.2",
      fix="Exigir MFA en correo, que hace inútil compartir la clave, y firmado del "
          "compromiso (ver SP-16-03)."),

    D("SP-08-05", 8, 23, "Identidad", "critico", "tecnico",
      "En ningún punto del manual se exige autenticación multifactor (MFA/2FA).",
      brecha="Ausencia total de MFA: ni Active Directory, ni correo, ni VPN, ni firewall "
             "Meraki, ni cuentas de administración, ni Microsoft 365, ni plataformas "
             "digitales. Todo el control de acceso descansa en un solo factor (contraseña), "
             "en un colegio con datos de menores. Es la brecha número uno del manual.",
      ref="CIS Control 5.3 (MFA); NIST SP 800-63B (AAL2); CISA MFA guidance",
      fix="Implantar MFA en el orden de riesgo: (1) cuentas administrativas y dominio, "
          "(2) correo Microsoft 365, (3) VPN y firewall, (4)NAS y servidores, "
          "(5) plataformas del P.26 y redes sociales.",
      verificacion="Revisar en cada sistema si MFA está activo y cuántos usuarios lo tienen.",
      evidencia=["m365_mfa.csv"],
      check={"tipo": "csv_booleano", "params": {"archivo": "m365_mfa.csv", "columna": "MFA"}}),

    D("SP-08-06", 8, 23, "Acceso lógico", "medio", "organizacional",
      "La Gerencia determina qué usuarios acceden a cada aplicación y con qué nivel de "
      "permiso; Informática mantiene esa determinación actualizada.",
      brecha="«Mantener actualizado» sin frecuencia declarada ni evidencia de revisión.",
      ref="CIS Control 5.2",
      fix="Revisión trimestral de permisos por aplicación, firmada y archivada."),

    D("SP-08-07", 8, 23, "Claves", "medio", "organizacional",
      "«El Usuario cambiará su contraseña cada vez que estime conveniente».",
      brecha="Rotación opcional. Contradice el P.13, que fija edad máxima de 180 días: "
             "hay dos reglas incompatibles en el mismo manual y el usuario puede seguir "
             "la que entienda.",
      ref="CIS Control 5.2 (verificar ambos criterios)",
      fix="Unificar: rotación obligatoria por política del dominio (o mejor, sin rotación "
          "forzosa pero con MFA y bloqueos, según CIS/NIST) y eliminar el «cada vez que "
          "estime conveniente»."),

    D("SP-08-08", 8, 22, "Acceso lógico", "medio", "organizacional",
      "El acceso del personal técnico especializado a la tecnología se autoriza por "
      "Informática y se realiza en presencia de persona autorizada.",
      brecha="No cubre al personal propio de Informática, que accede sin acompañante y "
             "sin que nadie registre qué hizo.",
      ref="", fix="Definir que toda intervención de Informática queda registrada con "
                   "fecha, motivo y usuario afectado."),

    # ------------------------------------------------------------------ P.9
    D("SP-09-01", 9, 24, "Incidentes", "medio", "organizacional",
      "Detectada una violación de seguridad, se comunica al jefe de área y de inmediato a "
      "Gerencia; Informática preserva trazas, previene recurrencia, retira acceso a los "
      "involucrados y pone en cuarentena los equipos dañados.",
      brecha="El procedimiento es correcto en su flujo pero no tiene: clasificación de "
             "severidad, tiempos de respuesta, responsable por turno, ni formato de "
             "acta/post-mortem. Y —crítico— no contempla la obligación legal de evaluar y "
             "notificar una brecha de datos personales (Ley 21.719, art. 14 sexies, desde "
             "el 01-12-2026).",
      ref="Ley 21.719 art. 14 sexies; ISO 27001 A.5.24-28",
      fix="Añadir al P.9: matriz de severidad, plazos, bitácora de incidentes, y un "
          "punto explícito de «¿esto es una brecha de datos personales? → comunicar sin "
          "dilaciones indebidas y, con datos de menores, a las familias».",
      verificacion="Revisar el procedimiento vigente contra la Ley 21.719 antes del "
                   "01-12-2026.",
      evidencia=["bitacora_incidentes.csv"]),

    D("SP-09-02", 9, 24, "Incidentes", "alto", "tecnico",
      "El jefe de informática recolecta y preserva las trazas del incidente.",
      brecha="Ningún procedimiento del manual define la retención de registros (event logs, "
             "firewall, DHCP, VPN, acceso a archivos). Sin retención definida, a los 30-60 "
             "días los logs se sobrescriben y no hay forma de investigar nada.",
      ref="CIS Control 8.2 (audit log retention)",
      fix="Definir retención mínima (mínimo 6-12 meses), dónde se archivan los logs y quién "
          "tiene acceso. Esto es condición de posibilidad de cualquier investigación.",
      verificacion="Consultar la política de retención de logs del firewall y de los servidores."),

    D("SP-09-03", 9, 24, "Incidentes", "alto", "organizacional",
      "Los equipos con daño quedan en cuarentena y el hecho se anota en el registro de "
      "incidencia de la tecnología afectada.",
      brecha="No hay procedimiento de «contención y preservación forense»: la cuarentena "
             "puede implicar apagar el equipo y perder la evidencia en memoria.",
      ref="NIST SP 800-61 (incident handling)",
      fix="Definir: no apagar sin fotografiar, aislar la red antes que apagar, preservar "
          "disco/volátil y dejar acta."),

    # ----------------------------------------------------------------- P.10
    D("SP-10-01", 10, 25, "Monitoreo", "medio", "tecnico",
      "El Administrador de red usa herramientas de monitoreo autorizadas por Gerencia para "
      "detectar fallas y corregir las vulnerabilidades encontradas.",
      brecha="No se nombra ninguna herramienta, ni periodicidad de revisión, ni destinatario "
             "de las alertas, ni retención de logs. Un «monitoreo» sin dueño ni calendario "
             "no detecta nada: si el administrador no mira, no hay monitoreo.",
      ref="CIS Control 8.1; NIST SP 800-61",
      fix="Declarar la herramienta (Meraki Security Center, Wazuh, Defender for Endpoint), "
          "la periodicidad (mín. mensual), quién ve las alertas y qué se hace con ellas."),

    D("SP-10-02", 10, 25, "Monitoreo", "medio", "tecnico",
      "Los programas de monitoreo se usan para el mejoramiento continuo de la red.",
      brecha="No hay registro de vulnerabilidades detectadas ni de su cierre. Se pierde la "
             "trazabilidad de qué se encontró y qué se corrigió.",
      ref="CIS Control 7.1",
      fix="Bitácora de vulnerabilidades: hallazgo, severidad, responsable, fecha objetivo "
          "de cierre."),

    # ----------------------------------------------------------------- P.11
    D("SP-11-01", 11, 26, "Software", "medio", "organizacional",
      "Las aplicaciones se evalúan por el jefe de informática, se aprueban por Gerencia y "
      "se instalan sólo por el área de Informática.",
      brecha="No hay una lista de software permitido (allowlist/denylist) ni un proceso de "
             "retiro del software no autorizado o vulnerable. «Se instala lo que aprueba "
             "Informática» sin criterio documentado es discrecionalidad.",
      ref="CIS Control 2.3; Application allowlisting",
      fix="Publicar la lista de software autorizado; definir tiempo máximo de retiro "
          "(p. ej. 30 días) de lo que no esté en la lista."),

    D("SP-11-02", 11, 26, "Software", "medio", "organizacional",
      "Las aplicaciones que estén desactualizadas se eliminan por versiones posteriores.",
      brecha="«Desactualizada» sin criterio verificable (ni umbral de versión ni de "
             "soporte del fabricante).",
      ref="", fix="Definir el criterio: sin soporte del fabricante o sin parche crítico por "
                   "más de 6 meses → retiro obligatorio."),

    # ----------------------------------------------------------------- P.12
    D("SP-12-01", 12, 27, "Acceso lógico", "alto", "tecnico",
      "Las carpetas se comparten con accesos restringidos según clasificación de grupos y "
      "se eliminan los accesos «cuando corresponda».",
      brecha="«Cuando corresponda» es indeterminación: no hay periodicidad de revisión de "
             "permisos. Las carpetas de personal que se va acumulan permisos y quedan "
             "abiertas a ex compañeros. Es una de las vías más comunes de fuga de datos en "
             "colegios.",
      ref="CIS Control 6.1; OWASP Authorization",
      fix="Revisión trimestral de permisos de todos los recursos compartidos, con "
          "responsable y acta; eliminar permisos de quienes ya no pertenecen.",
      verificacion="Exportar permisos de los shares y buscar cuentas de personal que no "
                   "trabaja en el colegio.",
      evidencia=["permisos_comparticiones.csv"],
      check={"tipo": "csv_columnas",
             "params": {"archivo": "permisos_comparticiones.csv",
                        "requeridas": ["Nombre", "Ruta", "Acceso"]}}),

    D("SP-12-02", 12, 27, "Acceso lógico", "medio", "organizacional",
      "La información compartida sólo es para fines de trabajo; los estudiantes comparten "
      "sólo a través de los sistemas que establezca Informática.",
      brecha="No hay definición de clasificación de la información, que es la base que el "
             "propio procedimiento invoca («según clasificación de grupos») sin existir.",
      ref="ISO 27001 A.8.2 (classification)",
      fix="Definir 3 niveles (pública / interna / restringida: notas de conducta, salud, "
          "antecedentes de conducta) y asociarlos a dónde puede guardarse y quién accede."),
]