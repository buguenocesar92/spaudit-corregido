"""Controles de los procedimientos 23 a 27, coherencia del documento y marco legal.

Este módulo separa tres cosas que conviene no mezclar en el informe:

  SP-23..SP-27  lo que dicen los procedimientos restantes del manual
  DOC-01..      la calidad del propio documento (índices, firmas, numeración)
  LEY-*         obligaciones que la ley impone y el manual no menciona
  D44-*         la Directiva 44/2026, aplicable según el caso
"""

from .controles_comunes import D

DOMINIO = "saintpatricktemuco.cl"

# Equipos declarados en el procedimiento 23 y en el procedimiento 24.
EQUIPOS_RED = [
    ("192.168.254.1", "CORESW", "Servidor de núcleo (core switch)"),
    ("192.168.254.2", "SWPS02", "Switch de preescolar / sala 2"),
    ("192.168.254.3", "SWRECTORIA", "Switch de rectoría"),
    ("192.168.254.4", "SWPS01", "Switch sala 1"),
    ("192.168.254.5", "SWGIMNASIO", "Switch gimnasio"),
    ("192.168.254.6", "SWPREBASICA", "Switch prebásica"),
    ("192.168.254.7", "SWS.INF", "Switch sala de informática"),
]

DVR = [
    ("192.168.92.2", "32 puertos", "Cámaras de salas"),
    ("192.168.92.3", "16 puertos", "Cámaras exteriores y espacios comunes"),
    ("192.168.92.4", "32 puertos", "Cámaras exteriores y espacios comunes"),
]

CONTROLES = [
    # ----------------------------------------------------------------- P.23
    D("SP-23-01", 23, 42, "Red", "medio", "documental",
      "Topología de red estrella, con el Meraki como salida a Internet y un switch central "
      "(CORESW) al que se conectan los switches de sala, rectoría, gimnasio, prebásica e "
      "informática.",
      brecha="La topología está bien descrita pero no hay diagrama vigente, ni criterio de "
             "diseño, ni responsable de mantenerlo al día. Un documento de topología que no "
             "se actualiza deja de describir la red real en pocos meses.",
      ref="ISO 27001 A.7.1 (network diagrams)",
      fix="Mantener un diagrama versionado con fecha, y actualizarlo cada vez que cambie un "
          "equipo o un enlace."),

    D("SP-23-02", 23, 42, "Red", "critico", "tecnico",
      "Plan de direccionamiento: todos los switches en la VLAN 254 (192.168.254.0/24), "
      "cámaras en 192.168.92.0/24.",
      brecha="La tabla del P.23 contradice al P.14 (que exige crear VLAN para segmentar). "
             "Con todo en VLAN 254 no hay segmentación: un alumno con un notebook en una "
             "sala alcanza los puertos de administración de los switches y de los equipos de "
             "las otras salas. Y la red de cámaras, que es la que registra a todos los "
             "alumnos, aparece en otra subred sin ninguna regla de firewall declarada que "
             "diga si es accesible desde la red de aulas.",
      ref="CIS Control 12.x; NIST SP 800-125B",
      fix="Decidir y documentar el plan de VLANs (aulas, administración, servidores, "
          "cámaras, invitados) y las reglas de Allowed entre ellas; y corregir el manual "
          "para que el P.14 y el P.23 digan lo mismo.",
      verificacion="Comparar la tabla del manual con la configuración real del Meraki y "
                   "con los VLAN configurados en los switches.",
      evidencia=["meraki.json"],
      check={"tipo": "meraki_segmentacion", "params": {"archivo": "meraki.json"}}),

    D("SP-23-03", 23, 42, "Red", "alto", "tecnico",
      "Direcciones IP fijas documentadas para cada switch de la red.",
      brecha="El manual documenta las IP de los switches, no de los servidores, la NAS, los "
             "DVR ni los equipos. Sin un inventario de direccionamiento completo no se puede "
             "saber qué equipos existen ni qué está expuesto dentro de la red.",
      ref="", 
      fix="Inventario de direccionamiento: cada IP, qué equipo es, dónde está, quién lo "
          "administra y qué puerto expone."),

    D("SP-23-04", 23, 42, "Red", "medio", "tecnico",
      "El manual no documenta los puntos de acceso inalámbricos ni las redes wifi.",
      brecha="El P.8 menciona claves wifi y el P.14 segmenta por VLAN, pero ningún "
             "procedimiento documenta cuántas redes wifi existen, cuáles separan y con qué "
             "cifrado. Es imposible auditar la red inalámbrica a partir de este manual.",
      ref="CIS Control 12.4; Wi-Fi Alliance WPA3",
      fix="Documentar SSID, VLAN, cifrado (WPA3-Enterprise o WPA2), y confirmar que la red "
          "de invitados está aislada de la interna."),

    D("SP-23-05", 23, 42, "Red", "medio", "tecnico",
      "El manual no define sincronización horaria (NTP) de los equipos.",
      brecha="Sin NTP, los registros de los distintos equipos no son comparables: un "
             "incidente que cruza el firewall, el servidor y el portátil no se puede "
             "reconstruir. Y los errores de hora rompen la evidencia forense.",
      ref="ISO 27001 A.8.15 (logging); CIS Control 8.2",
      fix="Todos los equipos sincronizados contra una fuente externa (o el Meraki como "
          "servidor NTP), con zona horaria America/Santiago."),

    # ----------------------------------------------------------------- P.24
    D("SP-24-01", 24, 45, "Videovigilancia", "critico", "tecnico",
      "Composición del sistema de cámaras: tres DVR, en 192.168.92.2, 192.168.92.3 y "
      "192.168.92.4.",
      brecha="El manual documenta las IP de los grabadores pero no dice si son "
             "accesibles desde Internet, ni con qué contraseña, ni desde qué equipos se "
             "ven. Un DVR expuesto a Internet es una fuga de imágenes de menores y una "
             "puerta de entrada al resto de la red. Es uno de los chequeos más concretos "
             "que se pueden hacer desde la LAN.",
      ref="CIS Control 12.x; ANPD videovigilancia",
      fix="Verificar que los puertos de gestión de los DVR no están accesibles desde la red "
          "de aulas ni desde Internet; cambiar las contraseñas predeterminadas; exigir "
          "MFA en la aplicación; y documentar quién puede ver las grabaciones.",
      verificacion="Comprobación de puertos de los DVR desde un equipo de la LAN.",
      evidencia=["live_red.json"],
      check={"tipo": "puertos_dvr", "params": {"objetivos": [
          "192.168.92.2:80", "192.168.92.2:554", "192.168.92.2:37777", "192.168.92.2:8000",
          "192.168.92.3:80", "192.168.92.3:554", "192.168.92.3:37777",
          "192.168.92.4:80", "192.168.92.4:554", "192.168.92.4:37777"]}}),

    D("SP-24-02", 24, 45, "Videovigilancia", "critico", "legal",
      "El manual no contiene ninguna política de videovigilancia.",
      brecha="Se instala una cámara en cada sala (procedimiento 24) y se graban a menores "
             "de forma sistemática. No hay: plazo de retención, quién accede y con qué "
             "registro, aviso a la comunidad, consentimiento, ni criterios para analizar "
             "una queja por/images de alumnos. Desde el 01-12-2026 la Ley 21.719 exige "
             "evaluación de impacto para el monitoreo sistemático de zonas de acceso "
             "público y para el tratamiento masivo de datos.",
      ref="Ley 21.719 art. 15 ter; Ley 19.628; Código Civil arts. 234 y ss.",
      fix="Redactar una política de videovigilancia: finalidad, base legal, retención "
          "(días), acceso y auditoría de accesos, aviso a apoderados, procedimiento de "
          "solicitud de imagen por un titular, y prohibiciones de difusión.",
      verificacion="Revisar si existe política de videovigilancia antes del 01-12-2026.",
      evidencia=["politica_videovigilancia.pdf"]),

    D("SP-24-03", 24, 45, "Videovigilancia", "alto", "organizacional",
      "Mantenimiento preventivo de las cámaras en las vacaciones de verano; reparación o "
      "sustitución autorizada por Gerencia; inventario vigente.",
      brecha="Los tres DVR están en 192.168.92.x, una red separada del resto. Si esa red no "
             "tiene salida a Internet y está aislada, la segmentación funciona; si el "
             "Meraki enruta entre ambas subredes sin filtro, los DVR quedan alcanzables "
             "desde cualquier aula.",
      ref="", 
      fix="Documentar y probar el aislamiento entre la red de cámaras y la red de aulas; "
          "verificar que los DVR no tienen salida a Internet."),

    D("SP-24-04", 24, 45, "Videovigilancia", "medio", "tecnico",
      "Mantener el sistema de cámaras inventariado y apto para cumplir su función.",
      brecha="No se indica si los DVR tienen alimentación interrumpida (UPS). Un corte de "
             "luz en el colegio borra la evidencia y deja el sistema fuera de servicio "
             "justo cuando más falta hace.",
      ref="",
      fix="UPS para DVR, switches y NVR; y verificar en el mantenimiento de verano que las "
          "baterías están sanas."),

    # ----------------------------------------------------------------- P.25
    D("SP-25-01", 25, 47, "Inventario", "bajo", "documental",
      "Equipos de sonido: entrega con registro de control, parlantes portátiles para "
      "docentes, almacenamiento en el gimnasio con acceso restringido, inventario y "
      "mantenimiento preventivo en verano.",
      brecha="El mismo manual clasifica los «equipos de sonido» como activo fijo tangible "
             "(pág. 5) y como parte y pieza (subwoofer, pág. 6). Dos criterios para el "
             "mismo activo rompen la trazabilidad del inventario (ver SP-02-01).",
      ref="Coherencia interna del manual",
      fix="Corregir la clasificación en el P.2 y usar una sola categoría."),

    D("SP-25-02", 25, 47, "Hardware", "bajo", "organizacional",
      "En eventos generales en el gimnasio, un técnico de informática y un profesor de "
      "música operan los equipos de sonido.",
      brecha="Buena separación de funciones. Sin observación.",
      ref="", fix="Sin cambios."),

    # ----------------------------------------------------------------- P.26
    D("SP-26-01", 48, 48, "Plataformas", "alto", "organizacional",
      "El administrador de la plataforma crea usuarios según perfil y permisos; monitorea el "
      "uso; agrega, desactiva y elimina usuarios; capacita a la comunidad y facilita los "
      "enlaces de acceso.",
      brecha="El procedimiento gobierna «la plataforma» en singular, pero el colegio usa "
             "varias: Microsoft 365, Microsoft Bookings, plataformas educativas, redes "
             "sociales, intranet. Sin inventario de plataformas, cuentas y permisos, esta "
             "sección es inaplicable.",
      ref="CIS Control 5.2; ISO 27001 A.5.9",
      fix="Inventario de aplicaciones y cuentas con sistema, responsable, número de "
          "cuentas, MFA activada y fecha de la última revisión de permisos."),

    D("SP-26-02", 48, 48, "Plataformas", "critico", "organizacional",
      "El procedimiento no exige MFA ni revisión periódica de permisos en las plataformas.",
      brecha="Sin MFA en las cuentas de plataforma, un robo de contraseña de un docente "
             "(phishing) da acceso inmediato a grupos, archivos y correo compartido. Y sin "
             "revisión de permisos, las cuentas de quienes se fueron siguen activas.",
      ref="CIS Control 5.3",
      fix="MFA en toda cuenta institucional; revisión trimestral de permisos y de cuentas "
          "de ex trabajadores; y baja de cuentas dentro del plazo del P.7.",
      verificacion="Revisar MFA activa por usuario en cada plataforma.",
      evidencia=["m365_mfa.csv"],
      check={"tipo": "csv_booleano", "params": {"archivo": "m365_mfa.csv", "columna": "MFA"}}),

    D("SP-26-03", 48, 48, "Datos personales", "alto", "legal",
      "Las plataformas externas tratan datos de estudiantes, apoderados y docentes.",
      brecha="El procedimiento no menciona en ningún punto que un proveedor externo trata "
             "datos personales del colegio. Bajo la Ley 21.719 eso obliga a un contrato de "
             "tratamiento por mandato (encargo), con instrucciones documentadas y "
             "obligación de devolver o suprimir los datos al terminar. Bluehost, Microsoft y "
             "las plataformas de redes sociales tratan datos del colegio sin que el manual "
             "lo refleje.",
      ref="Ley 21.719 (régimen de tratamiento por mandato); Directiva 44/2026, cláusula "
          "de tratamiento de datos por mandato",
      fix="Inventario de proveedores que tratan datos personales, con contrato de encargo y "
          "compromiso de no usar los datos para entrenar modelos (ver D44-03).",
      verificacion="Listar los proveedores y verificar si existe contrato de tratamiento "
                   "con cada uno.",
      evidencia=["contratos_proveedores/"]),

    # ----------------------------------------------------------------- P.27
    D(
      "SP-27-01", 49, 53, "Redes sociales", "alto", "organizacional",
      "Todo contenido debe revisarse por los encargados de la actividad y aprobarse por el "
      "Encargado del Departamento TICs; la Dirección aprueba lo de relevancia institucional.",
      brecha="Se menciona «una herramienta institucional» para verificar la trazabilidad "
             "del material desde su creación hasta la aprobación, pero la herramienta no se "
             "identifica en todo el protocolo. Un proceso de aprobación cuyo rastro no se "
             "puede mostrar no es auditable.",
      ref="ISO 27001 A.5.3; Ley 20.285 (si aplica a fondos)",
      fix="Nombrar la herramienta y definir quién la usa, qué se guarda y por cuánto tiempo."),

    D("SP-27-02", 51, 51, "Datos personales", "critico", "legal",
      "Las imágenes de estudiantes deben estar autorizadas en el contrato de matrícula "
      "firmado por padres o tutores, especificando el uso que se dará a la información.",
      brecha="«Autorización en el contrato de matrícula» es una autorización genérica. Para "
             "difundir imágenes de menores en redes sociales e internet, la autorización "
             "debe ser específica, expresa, informada y separable: la autorización "
             "para diagnosticar no habilita automáticamente la difusión pública. Y si el "
             "alumno deja de asistir, la autorización sigue vigente.",
      ref="Código Civil arts. 234 y ss. (derecho a la propia imagen); Ley 21.719 (vigencia "
          "01-12-2026); criterio de la Agencia de Protección de Datos",
      fix="Autorización específica, informada y revocable, con opción clara de no "
          "difusión de imagen; y procedimiento de baja que revise las publicaciones "
          "anteriores.",
      verificacion="Revisar el texto del contrato de matrícula vigente y compararlo con lo "
                   "que el colegio publica efectivamente.",
      evidencia=["autorizacion_imagenes.pdf"]),

    D("SP-27-03", 51, 52, "Datos personales", "medio", "organizacional",
      "Evitar mencionar nombres completos de estudiantes en publicaciones; usar iniciales o "
      "referencias generales.",
      brecha="Correcto, pero el riesgo real no es el nombre: es la imagen. Un niño "
             "identificable en una foto del colegio junto a su nombre completo, o con su "
             "uniforme y su curso, es identificable aunque se use la inicial. Y las "
             "publicaciones en redes sociales son públicas y permanentes aunque se "
             "borren después.",
      ref="Ley 21.719; Código Civil arts. 234 y ss.",
      fix="Criterio de anonimización más estricto: sin nombre completo, sin curso visible "
          "cuando pueda identificar, y revisión de la foto antes de publicar."),

    D("SP-27-04", 51, 52, "Propiedad intelectual", "medio", "legal",
      "El contenido publicado debe contar con derechos de autor adecuados: material propio "
      "o con licencia, con créditos.",
      brecha="El protocolo no nombra un banco de música ni un inventario de licencias, que "
             "es donde en la práctica aparece el problema (música de fondo en videos de "
             "eventos).",
      ref="Ley 17.336 (Derechos de Autor)",
      fix="Banco de música con licencia verificada para uso en redes sociales y "
          "publicidad institucional."),

    D(
      "SP-27-05", 54, 54, "Identidad", "critico", "organizacional",
      "Las credenciales de acceso a las cuentas oficiales están bajo control del Departamento "
      "de Transformación Digital y el acceso debe ser restringido.",
      brecha="Ninguna de las cuentas de Instagram, LinkedIn, YouTube ni del sitio tiene "
             "exigido MFA. Una cuenta oficial tomada por un atacante permite publicar en "
             "nombre del colegio: es un riesgo reputacional y, si se difunden datos de "
             "alumnos, también de datos personales.",
      ref="CIS Control 5.3; Meta/Google/LinkedIn requieren 2FA",
      fix="MFA obligatoria en las cuatro cuentas; claves en el gestor de claves; "
          "revisión trimestral de los usuarios con acceso; y procedimiento de recuperación "
          "de cuenta."),

    D("SP-27-06", 54, 54, "Respaldo", "medio", "organizacional",
      "Copias de seguridad semanales de todo el contenido digital publicado, alojadas en "
      "servidores dentro del colegio.",
      brecha="Es una buena medida y correctamente pensada. Le falta el paso complementario: "
             "que esas copias se prueben y que se documente qué se guarda y por cuánto "
             "tiempo (los alumnos que se van siguen en las fotos publicadas).",
      ref="ISO 27001 A.12.3",
      fix="Definir retención de las copias, verificación periódica y un procedimiento de "
          "retirada de imágenes cuando el titular lo solicite."),

    D("SP-27-07", 55, 55, "Marco legal", "alto", "legal",
      "El protocolo cita «la Ley N° 19.628 sobre Protección de la Vida Privada (Chile) y la "
      "Ley General de Protección de Datos Personales».",
      brecha="«Ley General de Protección de Datos Personales» no es el nombre de ninguna ley: "
             "es la Ley 21.719, que modifica la 19.628 y entra en vigor el 01-12-2026. El "
             "manual debe citar la norma correcta con su número y fecha, y anticipar el "
             "cambio de régimen:=newa agencia, inventario obligatorio de tratamientos y "
             "evaluaciones de impacto obligatorias.",
      ref="Ley 21.719 (vigencia 01-12-2026); Ley 19.628",
      fix="Corregir la cita en el P.27 y transversalmente en todo el manual antes de la "
          "próxima revisión."),

    D("SP-27-08", 55, 55, "Marco legal", "medio", "legal",
      "El protocolo de redes sociales se revisa de forma anual o ante cambios "
      "significativos.",
      brecha="Correcto, pero no hay fecha de la última revisión ni responsable de "
             "convocarla. Un protocolo que dice «se revisa anualmente» y nunca se revisó "
             "está peor que uno sin cláusula.",
      ref="",
      fix="Registrar fecha de última revisión, próxima revisión y responsable."),

    # ------------------------------------------------- calidad del documento
    D("DOC-01", 0, 2, "Documento", "medio", "documental",
      "El índice del manual lista los procedimientos 1 a 27.",
      brecha="El índice salta del procedimiento 16 al 18: el procedimiento 17 (normativa de "
             "instalación y uso de software, hardware y soporte) sí existe en el cuerpo del "
             "documento, en la página 32, pero no aparece en el índice. Un manual sin índice "
             "fiable se cites mal.",
      ref="Coherencia interna del manual, págs. 2 y 32",
      fix="Incorporar el procedimiento 17 al índice en la próxima revisión."),

    D("DOC-02", 0, 3, "Documento", "medio", "documental",
      "La portada registra revisiones con fecha (15/04/2024, 28/04/2026, 12/05/2026) y "
      "firmas deJEfe de Informática, Osmani Fernández, y de la Presidente de Fundación, "
      "Lorena Cerna.",
      brecha="Los bloques de firma están vacíos y las fechas de revisión no indican cuántas "
             "páginas se revisaron en cada una (sólo la primera dice 45, cuando el documento "
             "tiene 56 páginas). Sin firma, una revisión no es una revisión: es un "
             "borrador. Y el documento no tiene número de versión ni de revisión.",
      ref="Buenas prácticas de control documental; Ley 19.846",
      fix="Completar firmas, indicar páginas revisadas por versión, y asignar número de "
          "revisión y fecha de vigencia."),

    D("DOC-03", 0, 32, "Documento", "medio", "documental",
      "El manual utiliza nombres de cargo cambiantes: Departamento Informático, Encargado de "
      "la Actividad Informática, Administrador de la Red, Dirección de Informática y "
      "Tecnología, Departamento TICs, Departamento de Transformación Digital.",
      brecha="Al menos seis nombres para lo que parece ser una o dos personas. Sin "
             "definición de roles y responsabilidades, no hay a quién exigir nada: nadie "
             "es responsable de un control porque todos pueden ser \"el área de informática\". "
             "Es la causa raíz de que muchos controles del manual no se puedan auditar.",
      ref="CIS Control 5.2; ISO 27001 A.5.2",
      fix="Una tabla de roles y responsabilidades: rol, persona, respaldo, qué autoriza y "
          "qué debe cumplir. Y usar esos nombres de forma uniforme en los 27 "
          "procedimientos."),

    D("DOC-04", 0, 32, "Documento", "bajo", "documental",
      "El procedimiento 17 se titula «Normativa de la instalación, configuración, uso de "
      "software, hardware y servicio de soporte a computadores y notebooks… Normativa de "
      "seguridad de la información y acceso a sistemas».",
      brecha="El título está pegado: son dos títulos distintos unidos por puntos "
             "suspendidos dentro de la misma entrada. Evidencia de que dos procedimientos se "
             "fusionaron sin editarlos.",
      ref="", fix="Separar en dos procedimientos y agregarlos al índice."),

    D("DOC-05", 0, 28, "Documento", "medio", "documental",
      "El manual no define la periodicidad de revisión propia, ni su relación con la "
      "actualización de los sistemas.",
      brecha="El protocolo de redes sociales (P.27) sí dice «se revisa de forma anual», pero "
             "el manual completo no. Y no hay ninguna cláusula de «revisión tras un "
             "incidente o un cambio de infraestructura».",
      ref="ISO 27001 A.5.2",
      fix="Declarar revisión anual del manual completo y revisión extraordinaria tras "
          "incidentes, cambios de equipo o nuevas obligaciones legales."),

    # ---------------------------------------------- Ley 21.719 (obligatorio)
    D("LEY-01", 0, 0, "Datos personales", "critico", "legal",
      "OBLIGACIÓN LEGAL NO CUBIERTA POR EL MANUAL: inventario de las operaciones de "
      "tratamiento de datos personales (qué datos se tratan, con qué finalidad, sobre "
      "quién y con qué base legal).",
      brecha="El manual de TICs no menciona la ley de datos personales ni una sola vez. La "
             "obligación no es opcional: aplica a toda organización que trate datos "
             "personales en Chile, sea pública o privada. El colegio trata fichas de "
             "alumnos, datos de salud, de conducta, imágenes y videovigilancia.",
      ref="Ley 21.719, que modifica la Ley 19.628; vigencia 01-12-2026",
      fix="Levantar el inventario de tratamientos antes del 01-12-2026. Es la base de todo "
          "lo demás: sin inventario no hay evaluación de impacto posible.",
      verificacion="Solicitar el inventario de tratamientos y su fecha de elaboración.",
      evidencia=["rat.csv"]),

    D(
      "LEY-02", 0, 0, "Datos personales", "critico", "legal",
      "OBLIGACIÓN LEGAL NO CUBIERTA POR EL MANUAL: evaluación de impacto en protección de "
      "datos (EIPD) previa al inicio de tratamientos de alto riesgo.",
      brecha="La ley la exige siempre en varios casos concretos, y el colegio cae en varios "
             "a la vez: (a) videovigilancia sistemática de todas las salas y espacios "
             "comunes, con más de 50 cámaras; (b) tratamiento masivo de datos de más de "
             "400 alumnos y apoderados; (c) datos sensibles y especialmente protegidos de "
             "menores (salud, conducta) fuera de la base del consentimiento. Y ninguno de "
             "los 27 procedimientos exige una evaluación de impacto.",
      ref="Ley 21.719, art. 15 ter, incisos a), b), c) y d)",
      fix="Realizar como mínimo tres EIPD antes del 01-12-2026: videovigilancia, fichas y "
          "datos sensibles de alumnos, y redes sociales. La metodología puede ser la de la "
          "Plataforma Algoritmos Públicos o la del artículo 35 de la ley.",
      verificacion="Solicitar la EIPD de videovigilancia y de datos de alumnos.",
      evidencia=["eipd_videovigilancia.pdf", "eipd_alumnos.pdf"]),

    D("LEY-03", 0, 0, "Datos personales", "critico", "legal",
      "OBLIGACIÓN LEGAL NO CUBIERTA POR EL MANUAL: comunicar las vulneraciones de seguridad "
      "que afecten datos personales.",
      brecha="El procedimiento 9 (incidentes) termina en «anotar el hecho en el registro». "
             "No hay ninguna mención a comunicar la brecha. La ley exige informar a la "
             "Agencia de Protección de Datos Personales sin dilaciones indebidas, "
             "describiendo la naturaleza de la vulneración, sus efectos, las categorías de "
             "datos y el número aproximado de titulares afectados, y además comunicar a los "
             "titulares cuando se trate de datos sensibles o de menores de 14 años: en un "
             "colegio, casi siempre.",
      ref="Ley 21.719, art. 14 sexies",
      fix="Incorporar al P.9 un punto obligatorio de evaluación y comunicación de brecha, con "
          "el plazo interno de decisión (por ejemplo 24 horas para evaluar y 72 horas para "
          "comunicar) y la persona responsable de decidir.",
      verificacion="Revisar si el procedimiento de incidentes incluye el paso de "
                   "comunicación antes del 01-12-2026."),

    D("LEY-04", 0, 0, "Datos personales", "alto", "legal",
      "OBLIGACIÓN LEGAL NO CUBIERTA: contrato de tratamiento de datos por mandato con cada "
      "proveedor que trate datos del colegio.",
      brecha="Bluehost (hosting), Microsoft 365 (correo, archivos, agenda), las plataformas "
             "educativas y las redes sociales tratan datos personales y de menores. El "
             "manual no exige contrato con ninguno, ni condiciones de seguridad, ni derecho "
             "a auditar, ni plazo de devolución o supresión de datos al terminar.",
      ref="Ley 21.719 (régimen de tratamiento por mandato); Directiva 44/2026, cláusula tipo "
          "de tratamiento de datos por mandato",
      fix="Modelo de contrato de encargo con cada proveedor, con cláusulas de seguridad, "
          "subcontratación prohibida sin autorización, y devolución o supresión al término "
          "del servicio."),

    D("LEY-05", 0, 0, "Datos personales", "alto", "legal",
      "OBLIGACIÓN LEGAL NO CUBIERTA: medidas de seguridad y su documentación demostrable.",
      brecha="La ley establece el deber de adoptive medidas adecuadas para proteger los datos "
             "y, desde 2026, que el cumplimiento debe poder demostrarse. El manual tiene "
             "medidas, pero no tiene el respaldo de ejecución que permite demostrarlas: sin "
             "registros, sin evidencia de ejecución y sin responsable, las medidas "
             "escritas no prueban nada.",
      ref="Ley 21.719 (deber de seguridad y carga de la prueba)",
      fix="Este informe y los registros que lo alimentan son justamente la evidencia de "
          "cumplimiento: es la forma más directa de construirla."),

    D("LEY-06", 0, 0, "Datos personales", "alto", "legal",
      "Uso de inteligencia artificial generativa con datos de alumnos.",
      brecha="Ninguno de los 27 procedimientos menciona la IA generativa. Si el colegio usa "
             "asistentes de IA para redactar, resumir o calificar tareas de alumnos, pueden "
             "estar saliendo datos personales y sensibles (nombres, Conducta, salud) hacia "
             "un servicio externo que los usa para entrenar. La Directiva 44/2026 exige, en "
             "contratos de este tipo,prohibir expresamente el uso de los datos para "
             "entrenar modelos.",
      ref="Directiva 44/2026 (cláusula de confidencialidad y de no entrenamiento)",
      fix="Política de uso de IA generativa: qué usos se permiten, qué datos pueden "
          "introducirse (idealmente ninguno), qué queda prohibido, y revisión de las "
          "herramientas que ya se usan.",
      verificacion="Preguntar al equipo qué herramientas de IA usa el colegio y con qué "
                   "datos.",
      evidencia=["politica_ia.pdf"]),

    # ------------------------------------ Directiva 44/2026 (alcance a definir)
    D("D44-01", 0, 0, "Marco legal", "alto", "legal",
      "ALCANCE DE LA LEY DE COMPRAS PÚBLICAS: verificar si el colegio queda sujeto a la "
      "Ley 19.886 y, por tanto, a la Directiva 44/2026.",
      brecha="La Directiva 44/2026 rige a los órganos públicos, y un colegio privado no lo es "
             "automáticamente. Pero la propia Ley 19.886 (art. 1) extiende su aplicación a "
             "las fundaciones y asociaciones en las que participe un organismo de la "
             "Administración del Estado en su administración o dirección y que reciban "
             "transferencias de fondos públicos por 1.500 UTM o más mensuales al año "
             "(a octubre de 2026, unas 18.000 UTM anuales), así como a las personas "
             "jurídicas receptoras de fondos públicos en los casos que defina el "
             "reglamento. Además, la ley permite acogerse arse voluntariamente mediante un "
             "convenio con ChileCompra.",
      ref="Ley 19.886 art. 1; Decreto 661/2024; Directiva 44/2026 (Resolución Exenta de "
          "12-03-2026, que deja sin efecto la de 2015)",
      fix="Confirmar con la asesoría jurídica del colegio (y con el sostenedor, si lo hay) "
          "si la entidad recibe fondos públicos, quién administra el colegio y si procede "
          "un convenio voluntario con ChileCompra. La respuesta define si las cláusulas de "
          "la Directiva son obligatorias o sólo una buena práctica.",
      verificacion="Solicitar el monto anual de fondos públicos recibidos, la composición "
                   "del directorio y el convenio con el sostenedor o el contrato vigente con el municipio."),

    D("D44-02", 0, 0, "Marco legal", "alto", "legal",
      "Si la Ley 19.886 aplica: usar las cláusulas tipo de la Directiva 44/2026 en todo "
      "contrato de TI, software o IA.",
      brecha="La Directiva trae cláusulas redactadas y listas para copiar: seguridad de la "
             "información, notificación de incidentes en 2 horas, evaluación de impacto en "
             "protección de datos, tratamiento de datos por mandato, no uso de los datos "
             "para entrenar modelos, entrega del código fuente, auditoría algorítmica, "
             "confidencialidad y fichas de transparencia. Ninguna de ellas está hoy en los "
             "contratos del colegio.",
      ref="Directiva 44/2026, sección «Cláusulas sugeridas en la elaboración del "
          "requerimiento de compra, bases de licitación y/o contrato»",
      fix="Incorporar las cláusulas como modelo tipo del departamento de Tinteligencia y "
          "usarlas en el próximo contrato, con ayuda externa: adaptarlas al realidad del "
          "colegio."),

    D("D44-03", 0, 0, "Marco legal", "medio", "legal",
      "Si aplica a la Ley 19.886: los procedimientos de compra de tecnología deben incluir "
      "el análisis ético y de privacidad que la directiva describe.",
      brecha="La directiva define un flujo de 3 fases (investigación del problema, propuesta "
             "de solución, gestión del contrato) con puntos de control, y herramientas "
             "gratuitas para la evaluación de impacto algorítmico y la ficha de "
             "transparencia. Para un colegio, el equivalente práctico es más simple: antes "
             "de comprar o desarrollar software que trate datos de alumnos, preguntar qué "
             "datos toca, dónde quedan y quién puede verlos.",
      ref="Directiva 44/2026, fases 1 a 3; Plataforma Algoritmos Públicos",
      fix="Usar la evaluación de impacto de la Plataforma Algoritmos Públicos (gratuita) "
          "como checklist de privacidad para las herramientas nuevas."),

    D(
      "D44-04", 0, 0, "Marco legal", "medio", "documental",
      "Vigencia de la referencia: la Directiva 44/2026 fue aprobada por Resolución Exenta "
      "del 12 de marzo de 2026 y deja sin efecto la Resolución Exenta 583-B de 2015.",
      brecha="Si algún contrato o procedimiento del colegio se apoya en la directiva de "
             "2015, está usando un texto derogado desde marzo de 2026.",
      ref="Directiva 44/2026, resoluciones 1 y 2",
      fix="Verificar que ningún documento del colegio cite la directiva de 2015."),

    D("D44-05", 0, 0, "Marco legal", "bajo", "documental",
      "Marco general aplicable a la contratación pública de tecnología con IA.",
      brecha="La directiva está dirigida a organismos públicos y su aplicación al "
             "colegio depende de D44-01. Aun así, sus cláusulas son el estándar de mercado "
             "más detallado que existe en el país para contratar tecnología con datos "
             "personales: usarlas como referencia mejora la posición de negociación del "
             "colegio con cualquier proveedor.",
      ref="Directiva 44/2026",
      fix="Mantener la referencia como estándar interno de compra de tecnología."),

    D("D44-06", 0, 0, "Marco legal", "medio", "legal",
      "Marco de ciberseguridad y de infraestructura crítica.",
      brecha="La Ley 21.663 (Ley Marco de Ciberseguridad), el Decreto 273/2022 de "
             "notificación de incidentes al CSIRT y el Decreto 83/2004 de seguridad de "
             "documentos electrónicos se aplican a los órganos del Estado, no a un colegio "
             "privado. No corresponde exigirse su cumplimiento, pero sí su práctica: son el "
             "estándar técnico que usan las empresas privadas que y valoran a Proveedores del "
             "Estado.",
      ref="Ley 21.663; Decreto 273/2022; Decreto 83/2004",
      fix="Adoptarlos voluntariamente como referencia técnica interna; el único plazo de "
          "notificación de 2 horas que hoy importa es el del contrato con los proveedores."),
]