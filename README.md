# spaudit — auditoría de cumplimiento y ciberseguridad

Audita lo que el **Manual de Procedimientos de Saint Patrick School 2026-II** declara
contra lo que se puede **comprobar realmente**, y lo contrasta con el marco legal
chileno aplicable.

La idea es simple: un manual dice «se hace», pero un manual no demuestra nada.
Esta herramienta compara las dos cosas y señala exactamente dónde difieren.

---

## Qué hace

1. **Extrae los controles** de los 27 procedimientos del manual, con la página exacta
   donde está escrito cada uno.
2. **Verifica automáticamente** lo que se puede verificar: política de contraseñas del
   dominio, auditoría de Windows, cuentas privilegiadas, Defender, parches, cifrado de
   disco, respaldos, configuración del firewall, sitio web, correo y puertos de la red.
3. **Comprueba en vivo, desde Internet**, lo que se puede comprobar sin acceso previo:
   SPF, TLS, cabeceras de seguridad, exposición de WordPress y XML-RPC.
4. **Detecta las contradicciones internas** del propio manual y sus lagunas legales
   más graves.
5. **Devuelve un informe** con los hallazgos ordenados por riesgo y una acción
   concreta para cada uno.

---

## Uso en 30 segundos

```powershell
# 1. Recoger evidencia en los equipos del colegio (sólo lectura)
powershell -ExecutionPolicy Bypass -File powershell\recolectar-evidencia.ps1

# 2. Auditar
python auditar.py

# 3. Abrir salida\informe-auditoria.html
```

No requiere instalar nada: sólo Python 3.8 o superior, sin dependencias externas.

### Lo que el recolector NO puede producir

Corriendo el recolector en cada equipo **no basta** para que los 147 controles
dejen de estar sin verificar. Hay evidencia que solo existe en un panel, en un
export o en un documento, y que alguien tiene que traer a mano.

Medido contra el catálogo, los **32 controles automatizables** se reparten así:

- **21** los resuelve `recolectar-evidencia.ps1` en cada equipo.
- **5** los resuelve el propio `auditar.py`, pero **solo sin `--sin-vivo`**
  (`SP-03-01`, `SP-18-03`, `SP-22-02`, `SP-22-04`, `SP-24-01`): son
  comprobaciones de red.
- **6** no los resuelve nada de este repositorio. Uno solo de esos archivos
  (`meraki.json`) desbloquea cuatro.

| Archivo que falta | De dónde sale | Controles |
|---|---|---|
| `meraki.json` | Dashboard de Meraki → **Organization → Settings → JSON**: firewall, VLANs y reglas. | 6 — `SP-14-01/04/05/07/09`, `SP-23-02` |
| `respaldo_trabajos.csv` | Historial de tareas de respaldo (Windows Backup, Veeam). El recolector no lo pide porque el nombre del producto no se puede adivinar. | 3 — `SP-21-01/02/03` |
| `m365_mfa.csv` | Portal de administración de M365: exportar MFA **por usuario**. No sirve el listado de usuarios: la columna que importa es si MFA está activo. | 2 — `SP-08-05`, `SP-26-02` |
| `inventario.csv` | Inventario de activos del colegio. No lo genera el recolector porque requiere conocer los activos, no sólo la máquina. | 2 — `SP-02-01/02` |
| `gestor_claves.txt` | Documento del gestor de contraseñas corporativo. | 2 — `SP-08-02`, `SP-15-01` |
| `inventario_software.csv` | Inventario de software con licencias. | 1 — `SP-17-01` |
| `mantenimiento.csv` | Plan de mantenimiento preventivo. | 1 — `SP-02-05` |
| `gestion_remota.txt` | Política de acceso remoto (VPN, AnyDesk, escritorio remoto). | 1 — `SP-03-04` |
| `bitacora_incidentes.csv` | Bitácora de incidentes de seguridad. | 1 — `SP-09-01` |

Los demás son PDF y documentos firmados (`rat.csv`, `eipd_*.pdf`,
`compromiso_confidencialidad.pdf`, `politica_*.pdf`, `autorizacion_imagenes.pdf`,
`contratos_proveedores/`) y **no son automatizables por naturaleza**: o existen
firmados o no existen.

Los controles de red viva (`live_web.json`, `live_dns.json`, `live_red.json`)
sí los resuelve spaudit, pero **solo sin `--sin-vivo`**, y por eso son 4 de los
cinco que no cubre el recolector.

Los **6 que no cubre ninguna herramienta** son `SP-02-01`, `SP-14-01`,
`SP-14-04`, `SP-14-07`, `SP-21-01` y `SP-23-02`: dependen de `inventario.csv`,
`meraki.json` (cuatro de ellos) y `respaldo_trabajos.csv`.

Copiar esos archivos a `evidencia\` antes de correr `auditar.py` es lo que
convierte los controles de "no verificado" en un veredicto.

Para ver esta misma lista contra tu instalación:

```powershell
python auditar.py --recolectar
```

### Correr el recolector como administrador

El recolector **funciona sin permisos**, y por eso conviene saber qué cambia:

- Las claves del registro que no existen se escriben como `<no definido>` y son
  evidencia real: el verificador las reporta como incumplimiento cuando el
  control las exige.
- Las claves y valores que **no pudo leer** se escriben como
  `<sin permiso de lectura>` o `<no informado>`, y NO se reportan como
  incumplimiento: quedan en `NO VERIFICADO`, que es un control sin cobertura y
  no un control incumplido.

Ejecutado sin permisos, el informe es menos completo pero **no inventa
incumplimientos**. Esa es la diferencia entre un informe parcial y uno falso.

Cuando algo no se puede leer por falta de permisos, el recolector lo dice con su
propio motivo en vez de un error genérico:

```
  [permiso] BitLocker: Acceso denegado
             No se escribió el archivo. El informe va a decir que falta la evidencia,
             que es verdad pero no es lo que pasó: pasó que no se pudo mirar.
             Vuelva a correr este script en una consola de ADMINISTRADOR.
```

### Un conjunto vacío también es un resultado

Si un equipo **no tiene** recursos compartidos, `comparticiones.csv` se escribe
igual, con su cabecera y cero filas. Antes no se escribía, y el informe decía
"Falta el archivo `comparticiones.csv`", que suena a que nadie miró.

Con la cabecera escrita, el archivo existe, se lee, y el control dice lo que
passó: `PARCIAL`, con las columnas correctas y cero filas.

El otro extremo: un control negativo —"que no haya ninguna cuenta Guest
habilitada"— sobre una lista vacía **no se cumple**. Sale `NO VERIFICADO` con
el motivo "no tiene filas, así que no hay nada que revisar". "No hay cuentas
Guest" sacado de un archivo sin cuentas es una afirmación que nadie puede
sostener.

### La política de ejecución puede impedir que corra

En equipos institucionales la política suele ser `RestrictedLanguage`,
`RemoteSigned` o `AllSigned`, y el doble clic o el `& .\recolectar-evidencia.ps1`
falla con *"la ejecución de scripts está deshabilitada en este sistema"*.

La salida es el bypass de **proceso**, que dura lo que dura la sesión y no toca
la máquina:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File powershell\recolectar-evidencia.ps1
```

No se pide `Set-ExecutionPolicy Unrestricted`, y no hace falta permiso de
administración para el bypass: hace falta para el resto del recolector.

### Probar las protecciones

```powershell
python herramientas\probar_marcadores.py
```

**15 casos**, escritos con evidencia a mano, que comprueban que lo que no se
sabe no se convierte en incumplimiento. Incluyen los cinco casos que se
confunden entre sí: clave ausente, sin permiso, `N/A` de Defender, lista vacía,
y un valor booleano que no se puede interpretar.

Para comprobar que esas pruebas sirven, hay que **romperlas**: dejar el filtro
de `csv_sin_filas` como estaba —comparando por igualdad en vez de por
desigualdad— hace fallar dos casos, uno en cada dirección.

### Opciones

| Opción | Qué hace |
|---|---|
| `--sin-vivo` | No hace consultas de red (útil sin Internet) |
| `--dominio X` | Audita otro dominio |
| `--evidencia RUTA` | Usa otra carpeta de evidencia |
| `--recolectar` | Lista qué evidencia falta y qué habilita |
| `--id SP-13-04` | Muestra un control concreto, con su brecha y su remediación |
| `-v` | Muestra cada control mientras se evalúa |

---

## Los cinco estados

| Estado | Significado |
|---|---|
| **Cumple** | Hay evidencia y la evidencia es correcta |
| **Parcial** | Hay evidencia, pero incompleta |
| **No cumple** | Hay evidencia y demuestra el incumplimiento |
| **Sin verificar** | No hay evidencia suficiente. **No es un fallo: es una tarea** |
| **No aplica** | El control no corresponde a esta organización |

La regla más importante del motor: **un control sin evidencia nunca se marca como
cumplido**. Por eso el informe sirve, además de para encontrar problemas, como
evidencia de gestión ante una auditoría externa.

---

## Qué encontró en la primera ejecución

Sobre los 147 controles del catálogo, y usando sólo lo que se puede comprobar
desde Internet y desde el propio documento:

**Contradicciones internas del manual**

- El procedimiento 14 exige segmentar en VLAN, pero el procedimiento 23 documenta
  **todos los equipos en la VLAN 254**. Una de las dos cosas no es cierta.
- La clasificación de bienes informáticos del procedimiento 2 es ambigua: los equipos de
  sonido aparecen como activo fijo y como parte y pieza a la vez.
- El índice no incluye el procedimiento 17, que sí existe en el cuerpo del documento.
- Los bloques de firma están vacíos y la portada declara 45 páginas revisadas cuando
  el documento tiene 56.
- Se usan al menos seis nombres distintos para lo que parece ser una o dos personas.

**Lagunas que el manual no menciona en ningún punto**

- **No existe MFA en ninguna parte del documento.** Ni dominio, ni correo, ni VPN,
  ni firewall, ni plataformas. Todo el acceso depende de una sola contraseña.
- **El manual ordena mantener un «respaldo de todas las contraseñas» y un «registro de
  contraseñas»** (procedimientos 8 y 15). Guardar las claves del controlador de
  dominio, del firewall y del hosting en un documento es, en la práctica, la forma de
  perder la red completa.
- **No hay gestión de parches.** Ningún procedimiento define qué se actualiza, cada
  cuánto ni quién lo verifica.
- **RAID espejo se presenta como respaldo del controlador de dominio.** No lo es:
  protege de un disco, no de un ransomware ni de un incendio.
- **No se menciona la ley de datos personales ni una sola vez**, en un colegio que
  maneja fichas, salud, conducta, imágenes de menores y videovigilancia.

**Comprobado desde Internet** (`salida\evidencia_viva.json`)

- El dominio **no publica registro SPF**: cualquiera puede enviar correo a nombre
  del colegio.
- El sitio **no envía ninguna cabecera de seguridad** (HSTS, CSP, X-Content-Type-Options,
  X-Frame-Options, Referrer-Policy).
- El sitio **declara su versión de WordPress** y tiene **XML-RPC activo**, que es el
  vector histórico de fuerza bruta contra cuentas WordPress.
- El certificado TLS está vigente y la redirección de HTTP a HTTPS funciona: eso sí
  está bien.

---

## El dato legal que cambia los plazos

**La Ley 21.719 entra en vigor el 1 de diciembre de 2026.** A esa fecha:

| Obligación | Aplicabilidad |
|---|---|
| Inventario de tratamientos de datos | Obligatoria para cualquier organización, pública o privada |
| Evaluación de impacto (EIPD) | Obligatoria en varios casos, y el colegio cae en varios a la vez |
| Comunicar vulneraciones que afecten datos personales | Sin dilaciones indebidas; además hay que informar a las familias cuando hay datos de menores |
| Contratos de tratamiento por mandato | Obligatorios con cada proveedor: hosting, correo, plataformas, redes sociales |

La evaluación de impacto es obligatoria cuando hay **tratamiento masivo de datos**
(cientos de alumnos y apoderados), **vigilancia sistemática de zonas** (el
procedimiento 24 pone cámaras en todas las salas) o **datos sensibles de menores**.

Sobre la **Directiva 44/2026**: está dirigida a los órganos públicos, y un colegio
privado no lo es automáticamente. Pero el artículo 1 de la Ley 19.886 extiende su
aplicación a las fundaciones en las que participe un organismo del Estado en su
administración o dirección y que reciban fondos públicos por 1.500 UTM o más
mensuales, y a las personas jurídicas receptoras de fondos públicos en los casos
que defina el reglamento. **Eso hay que confirmarlo con la asesoría jurídica del
colegio y con el sostenedor, si lo hay.** El control `D44-01` existe justamente para
dejar la pregunta anotada y resolverla una vez.

Independientemente del alcance legal, las cláusulas tipo de la directiva son el
modelo más detallado que existe en el país para contratar tecnología con datos
personales: notificación de incidentes en 2 horas, prohibición de usar los datos
para entrenar modelos, entrega del código fuente y auditoría. Usarlas como
referencia mejora la negociación con cualquier proveedor.

---

## Estructura

```
auditoria-saint-patrick/
├── auditar.py                     punto de entrada
├── spaudit/
│   ├── controles_p1_p12.py        catálogo: procedimientos 1 a 12
│   ├── controles_p13_p22.py       catálogo: procedimientos 13 a 22
│   ├── controles_p23_legal.py     catálogo: 23 a 27, documento y marco legal
│   ├── controles_comunes.py       definición de un control
│   ├── catalogo.py                consolidación
│   ├── checks.py                  verificadores (uno por tipo de control)
│   ├── evidencia.py               carga de archivos de evidencia
│   ├── red.py                     comprobaciones en vivo (DNS, TLS, HTTP, TCP)
│   ├── motor.py                   ejecución y clasificación de resultados
│   └── reporte.py                 informes HTML, JSON y Markdown
├── powershell/
│   └── recolectar-evidencia.ps1   recolección de evidencia en Windows
├── evidencia/                     ← colocar aquí la evidencia del colegio
├── salida/                        ← informes generados
└── herramientas/                  utilidades de mantenimiento del catálogo
```

El catálogo son **datos, no código**: se edita `controles_*.py` para añadir,
ajustar o quitar controles sin tocar el motor.

---

## Cómo mantener el catálogo

```powershell
python herramientas\comprobar.py         # verifica que todo compile
python herramientas\validar_catalogo.py  # IDs únicos, caracteres, argumentos
python herramientas\ver_catalogo.py      # lista los controles en consola
python herramientas\ver_catalogo.py SP-13-04   # muestra uno en detalle
```

---

## Herramientas de código abierto que encajan con esto

La auditoría señala controles que ninguna herramienta por sí sola va a resolver.
Estas son las piezas open source que cubren cada hallazgo, en orden de prioridad:

| Hallazgo | Herramienta |
|---|---|
| Sin MFA | **Authentik** o **Keycloak** para MFA/SSO; en M365, MFA nativo |
| Contraseñas en documento | **Vaultwarden** o **KeePassXC** como gestor de claves |
| Sin gestión de parches | **Wazuh** (CIS + parches + FIM) o Windows Update con políticas |
| Backups sin 3-2-1 | **Restic** o **Borg** con copia inmutable y **Ceph**/**TrueNAS** |
| Sin EDR | **Microsoft Defender for Endpoint** (ya incluido en Windows) |
| Auditoría y detección | **Wazuh** con el benchmark CIS de Windows Server |
| Sin hardening del DC | **CIS-CAT** / benchmarks CIS de Microsoft |

Ninguna de estas herramientas reemplaza el manual: lo que hacen es darle los
controles técnicos que hoy el manual sólo enuncia.

---

## Nota sobre la responsabilidad

Este informe es una herramienta de apoyo técnico. Las conclusiones legales
—especialmente el alcance de la Ley 19.886 y de la Ley 21.719 para esta
organización— deben confirmarse con la asesoría jurídica del colegio antes de
tomar decisiones en base a ellas.