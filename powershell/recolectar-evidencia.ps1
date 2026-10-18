<#
.SYNOPSIS
    Recolecta evidencia técnica de un equipo Windows para la auditoría spaudit.

.DESCRIPTION
    Genera, en la carpeta 'evidencia\red', los archivos que spaudit sabe leer:
      net_accounts.txt          política de contraseñas del dominio (net accounts)
      auditpol.txt              directiva de auditoría avanzada
      usuarios_ad.csv           cuentas del directorio activo
      grupos_ad.csv             miembros de los grupos privilegiados
      comparticiones.csv        recursos compartidos y sus permisos
      defender_estado.csv       estado de Microsoft Defender por equipo
      defender_preferencias.txt preferencias de Defender
      sistema.csv               versión del sistema operativo y último parche
      hotfix.csv                parches instalados
      registry_seguridad.txt    firma SMB, NTLM, LAPS y valores de endurecimiento
      bitlocker.csv             estado de cifrado de disco
      smb_compartimientos.txt   listados SMB adicionales

    Todo es de sólo lectura: el script no modifica la configuración del equipo.

.PARAMETER Salida
    Carpeta de destino. Por defecto, 'evidencia\red' junto a este script.

.PARAMETER Dominio
    Dominio de Active Directory. Si se omite, se detecta automáticamente.

.NOTES
    LA POLÍTICA DE EJECUCIÓN PUEDE IMPEDIR QUE ESTE SCRIPT CORRA. En Windows
   RestrictedLanguage, RemoteSigned o AllSigned —lo habitual en equipos
    institucionales— el doble clic o el `& .\recolectar-evidencia.ps1` falla con
    "la ejecución de scripts está deshabilitada en este sistema".

    La forma de correrlo sin cambiar la política de la máquina es el bypass de
    proceso, que dura lo que dura la sesión y no toca nada del equipo:

        powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\recolectar-evidencia.ps1

    Bypass de PROCESO, no de máquina. No se pide `Set-ExecutionPolicy Unrestricted`.

.EXAMPLE
    .\recolectar-evidencia.ps1
    Ejecuta en el CONTROLADOR DE DOMINIO y exporta todo.

.EXAMPLE
    powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\recolectar-evidencia.ps1 -Salida "C:\evidencia\red"
    Lo mismo, en un equipo donde la política de ejecución no permite el script.
#>
[CmdletBinding()]
param(
    [string]$Salida = (Join-Path $PSScriptRoot "evidencia\red"),
    [string]$Dominio
)

$ErrorActionPreference = "Continue"
$Progreso = $true

# ---------------------------------------------------------------- utilidades
function Escribir {
    # Se escribe línea por línea con WriteAllLines: evita depender de los
    # escapes de PowerShell para los saltos de línea, que son frágiles al
    # copiar y pegar entre editores y sistemas.
    param([string]$Ruta, [string[]]$Contenido)
    $lineas = @($Contenido) -split "`r?`n"
    $lineas = @($lineas | Where-Object { $_ -ne $null })
    if ($lineas.Count -eq 0) {
        # A diferencia de `Exportar-CsvSeguro`, acá NO se escribe el archivo: un
        # archivo de texto sin una sola línea no tiene cabecera que lo delate, y
        # el verificador no tiene forma de distinguir "se miró y no había nada"
        # de "nadie miró". Decir que falta es más honesto que escribir un vacío.
        Write-Host ("  [vacio] " + (Split-Path $Ruta -Leaf) + "  (0 lineas: no se escribe)") -ForegroundColor DarkGray
        return
    }
    $utf8 = New-Object System.Text.UTF8Encoding($false)
    [IO.File]::WriteAllLines($Ruta, [string[]]$lineas, $utf8)
    $tam = (Get-Item $Ruta).Length
    Write-Host ("  [ok]    " + (Split-Path $Ruta -Leaf) + "  (" + $tam + " bytes, " + $lineas.Count + " lineas)") -ForegroundColor Green
}

function Exportar-CsvSeguro {
    # `$Columnas` es la lista de encabezados que el archivo tiene que tener
    # aunque no haya ni una fila.
    #
    # POR QUÉ EXISTE. Un conjunto vacío es un RESULTADO, no una ausencia: en un
    # equipo sin recursos compartidos, "no hay ninguno" es lo que hay que
    # reportar. Sin escribir el archivo, el verificador dice "Falta el archivo
    # `comparticiones.csv`", que suena a que nadie miró. Con la cabecera
    # escrita, el archivo existe, se lee, y el control dice la verdad.
    #
    # Antes se cambiaron los colores de este mensaje y el fondo quedó igual. El
    # texto que recibe el auditor es el que decide si alguien entiende el
    # informe.
    param([object[]]$Datos, [string]$Ruta, [string[]]$Columnas)

    $nombre = Split-Path $Ruta -Leaf

    if (-not $Datos -or $Datos.Count -eq 0) {
        if (-not $Columnas -or $Columnas.Count -eq 0) {
            Write-Host ("  [vacio] " + $nombre + "  (0 registros; sin columnas declaradas: no se escribe)") -ForegroundColor DarkGray
            return
        }
        $cabecera = ($Columnas | ForEach-Object { '"' + ($_ -replace '"', '""') + '"' }) -join ","
        $utf8 = New-Object System.Text.UTF8Encoding($false)
        [IO.File]::WriteAllLines($Ruta, [string[]]@($cabecera), $utf8)
        Write-Host ("  [vacio] " + $nombre + "  (0 registros; cabecera escrita: se miró y no había)") -ForegroundColor DarkGray
        return
    }

    $Datos | Export-Csv -Path $Ruta -NoTypeInformation -Encoding UTF8
    Write-Host ("  [ok]    " + $nombre + "  (" + $Datos.Count + " registros)") -ForegroundColor Green
}

function Titulo {
    param([string]$Texto)
    Write-Host ""
    Write-Host ("== " + $Texto) -ForegroundColor Cyan
}

function Informar-Fallo {
    # Un fallo por permisos y un fallo por otra cosa son dos hechos distintos,
    # y el remedy también. Decir "Acceso denegado" sin más deja al auditor
    # pensando que algo está roto en el equipo, cuando lo único que falta es
    # abrir la consola como administrador.
    param([string]$Que, $Error_)

    $mensaje = ""
    if ($Error_.Exception) { $mensaje = $Error_.Exception.Message } else { $mensaje = [string]$Error_ }

    if ($mensaje -match "denegado|Access is denied|UnauthorizedAccess|Permission") {
        Write-Host ("  [permiso] " + $Que + ": " + $mensaje) -ForegroundColor Yellow
        if (-not $script:esAdmin) {
            Write-Host ("             No se escribió el archivo. El informe va a decir que falta la evidencia,") -ForegroundColor Yellow
            Write-Host ("             que es verdad pero no es lo que pasó: pasó que no se pudo mirar.") -ForegroundColor Yellow
            Write-Host ("             Vuelva a correr este script en una consola de ADMINISTRADOR.") -ForegroundColor Yellow
        }
        return
    }
    Write-Host ("  [error] " + $Que + ": " + $mensaje) -ForegroundColor Red
}

# Marcadores. Son deliberadamente DISTINTOS y no se deben unificar nunca.
#
# La diferencia entre los dos primeros no es de estilo, es de auditoría:
#   <no definido>             -> se consultó y NO existe. Es evidencia.
#   <sin permiso de lectura>  -> se intentó y no se pudo. NO es evidencia de nada.
#   <no informado>            -> el valor existe pero la API no lo devolvió.
#
# Antes los tres casos escribian "<no definido o sin permiso>" y el verificador
# lo leia como "la clave no existe". Ejecutado como usuario normal, eso
# convertia ignorancia en incumplimiento, en controles marcados como criticos.
# Ver la seccion "Correr el recolector como administrador" del README.
$MarcaAusente    = "<no definido>"
$MarcaSinLectura = "<sin permiso de lectura>"
$MarcaSinDato    = "<no informado>"

function Valor-O-Cargador {
    # Normaliza una preferencia de Defender. Get-MpPreference devuelve el
    # texto "N/A: Must be an administrator to view ..." cuando el proceso no es
    # administrador, y $null para varios campos. Ninguno de los dos significa
    # "esta opcion esta desactivada": significan "no lo supe".
    param($Valor)
    if ($null -eq $Valor) { return $MarcaSinDato }
    $texto = [string]$Valor
    if ($texto -match "^N/A" -or $texto -match "Must be an administrator") {
        return $MarcaSinLectura
    }
    if ($texto.Trim().Length -eq 0) { return $MarcaSinDato }
    return $texto
}

if (-not (Test-Path $Salida)) {
    New-Item -ItemType Directory -Path $Salida -Force | Out-Null
}
Write-Host "spaudit :: recolección de evidencia" -ForegroundColor White
Write-Host ("Destino: " + (Resolve-Path $Salida).Path)
Write-Host ("Equipo:  " + $env:COMPUTERNAME + "   Fecha: " + (Get-Date -Format "yyyy-MM-dd HH:mm"))

# Algunos apartados (BitLocker, auditpol,certainas claves del registro y la consulta
# del directorio activo) necesitan privilegios de administrador.
$identidad = [Security.Principal.WindowsIdentity]::GetCurrent()
$principal = New-Object Security.Principal.WindowsPrincipal($identidad)
$esAdmin = $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if ($esAdmin) {
    Write-Host "Permisos: administrador (recolección completa)" -ForegroundColor Green
} else {
    Write-Host "Permisos: usuario normal. BitLocker, auditoría y Active Directory pueden quedar vacíos." -ForegroundColor Yellow
    Write-Host "          Para una recolección completa, ejecute PowerShell como administrador." -ForegroundColor Yellow
}

# ------------------------------------------------------------ 1. Sistema
Titulo "Sistema operativo y parches"

$so = Get-CimInstance Win32_OperatingSystem -ErrorAction SilentlyContinue
$ultimoHotfix = (Get-HotFix -ErrorAction SilentlyContinue |
                 Sort-Object InstalledOn -Descending |
                 Select-Object -First 1)

$filaSistema = [pscustomobject]@{
    Equipo               = $env:COMPUTERNAME
    SO                   = if ($so) { $so.Caption } else { "" }
    Version              = if ($so) { $so.Version } else { "" }
    Build                = if ($so) { $so.BuildNumber } else { "" }
    UltimaInstalacion    = if ($so) { $so.InstallDate.ToString("yyyy-MM-dd") } else { "" }
    UltimoParche         = if ($ultimoHotfix) { $ultimoHotfix.HotFixID } else { "" }
    UltimaActualizacion  = if ($ultimoHotfix) { $ultimoHotfix.InstalledOn.ToString("yyyy-MM-dd") } else { "" }
}
Exportar-CsvSeguro -Datos @($filaSistema) -Ruta (Join-Path $Salida "sistema.csv") -Columnas @(
    "Equipo", "SO", "Version", "Build", "UltimaInstalacion", "UltimoParche", "UltimaActualizacion")

$parches = Get-HotFix -ErrorAction SilentlyContinue | Select-Object HotFixID, InstalledOn, Description
Exportar-CsvSeguro -Datos $parches -Ruta (Join-Path $Salida "hotfix.csv") -Columnas @(
    "HotFixID", "InstalledOn", "Description")

# ----------------------------------------------- 2. Política de contraseñas
Titulo "Política de contraseñas y bloqueo de cuentas"

$netAccounts = & net accounts 2>&1 | Out-String
Escribir -Ruta (Join-Path $Salida "net_accounts.txt") -Contenido $netAccounts

# ------------------------------------------------------- 3. Auditoría
Titulo "Directiva de auditoría"
$rutaAudit = Join-Path $Salida "auditpol.txt"
try {
    auditpol /get /subcategory:* /r > $rutaAudit 2>&1
    Escribir -Ruta $rutaAudit -Contenido (Get-Content $rutaAudit -Raw)
} catch {
    Informar-Fallo -Que "auditpol" -Error_ $_
}
$logon = & auditpol /get /subcategory:"Logon" 2>&1 | Out-String
if ($logon) {
    Escribir -Ruta (Join-Path $Salida "auditpol_logon.txt") -Contenido $logon
}

# --------------------------------------------- 4. Active Directory (opcional)
Titulo "Active Directory"
$modulosAD = Get-Module -ListAvailable ActiveDirectory
if ($modulosAD) {
    if (-not $Dominio) {
        $Dominio = $env:USERDNSDOMAIN
        Write-Host ("  dominio detectado: " + $Dominio)
    }
    Import-Module ActiveDirectory -ErrorAction SilentlyContinue

    $usuarios = Get-ADUser -Filter * -Properties DisplayName, Department, Enabled,
        PasswordLastSet, PasswordExpired, PasswordNeverExpires, LastLogonDate,
        MemberOf -ErrorAction SilentlyContinue | ForEach-Object {
            [pscustomobject]@{
                SamAccountName    = $_.SamAccountName
                Nombre            = $_.DisplayName
                Department        = $_.Department
                Enabled           = [bool]$_.Enabled
                PasswordLastSet   = if ($_.PasswordLastSet -and $_.PasswordLastSet.Year -gt 1600) {
                                        $_.PasswordLastSet.ToString("yyyy-MM-dd") } else { "nunca" }
                PasswordExpired   = [bool]$_.PasswordExpired
                NeverExpires      = [bool]$_.PasswordNeverExpires
                UltimoAcceso      = if ($_.LastLogonDate) { $_.LastLogonDate.ToString("yyyy-MM-dd") } else { "nunca" }
                MemberOf          = ($_.MemberOf -join " | ")
            }
        }
    Exportar-CsvSeguro -Datos $usuarios -Ruta (Join-Path $Salida "usuarios_ad.csv") -Columnas @(
        "SamAccountName", "Nombre", "Department", "Enabled", "PasswordLastSet",
        "PasswordExpired", "NeverExpires", "UltimoAcceso", "MemberOf")

    $gruposPrivilegio = @("Domain Admins", "Enterprise Admins", "Schema Admins", "Administrators")
    $miembros = @()
    foreach ($grupo in $gruposPrivilegio) {
        $g = Get-ADGroup -Filter ("Name -eq '" + $grupo + "'") -ErrorAction SilentlyContinue
        if ($g) {
            Get-ADGroupMember -Identity $g -ErrorAction SilentlyContinue | ForEach-Object {
                $miembros += [pscustomobject]@{
                    Grupo    = $grupo
                    Miembro  = $_.SamAccountName
                    Tipo     = $_.objectClass
                }
            }
        }
    }
    Exportar-CsvSeguro -Datos $miembros -Ruta (Join-Path $Salida "grupos_ad.csv") -Columnas @(
        "Grupo", "Miembro", "Tipo")

    $organizativas = Get-ADOrganizationalUnit -Filter * -ErrorAction SilentlyContinue |
                     Select-Object Name, DistinguishedName
    Exportar-CsvSeguro -Datos $organizativas -Ruta (Join-Path $Salida "ous_ad.csv") -Columnas @(
        "Name", "DistinguishedName")
} else {
    Write-Host ("  [omitido] El modulo ActiveDirectory no esta instalado en este equipo.") -ForegroundColor Yellow
    Write-Host ("             Ejecute este script en el CONTROLADOR DE DOMINIO.") -ForegroundColor Yellow
}

# --------------------------------------------------- 5. Recursos compartidos
Titulo "Recursos compartidos"
try {
    $compartidos = Get-SmbShare | Where-Object { -not $_.Special } | Select-Object Name, Path, Description
    Exportar-CsvSeguro -Datos $compartidos -Ruta (Join-Path $Salida "comparticiones.csv") -Columnas @(
        "Name", "Path", "Description")

    $permisos = @()
    foreach ($c in $compartidos) {
        try {
            Get-SmbShareAccess -Name $c.Name -ErrorAction SilentlyContinue | ForEach-Object {
                $permisos += [pscustomobject]@{
                    Nombre  = $c.Name
                    Ruta    = $c.Path
                    Acceso  = $_.AccountName + " / " + $_.AccessRight
                    Tipo    = $_.AccessControlType
                }
            }
        } catch { }
    }
    Exportar-CsvSeguro -Datos $permisos -Ruta (Join-Path $Salida "permisos_comparticiones.csv") -Columnas @(
            "Nombre", "Ruta", "Acceso", "Tipo")
} catch {
    Informar-Fallo -Que "recursos compartidos" -Error_ $_
}

# ------------------------------------------------------------ 6. Defender
Titulo "Microsoft Defender"
try {
    $estado = Get-MpComputerStatus -ErrorAction Stop
    $fila = [pscustomobject]@{
        Equipo                     = $env:COMPUTERNAME
        AntivirusEnabled           = [bool]$estado.AntivirusEnabled
        RealTimeProtectionEnabled  = [bool]$estado.RealTimeProtectionEnabled
        AntispywareEnabled         = [bool]$estado.AntispywareEnabled
        TamperProtection           = [bool]$estado.TamperProtection
        AntivirusSignatureAge      = $estado.AntivirusSignatureAge
        UltimaActualizacionFirmas  = if ($estado.AntivirusSignatureLastUpdated) {
                                        $estado.AntivirusSignatureLastUpdated.ToString("yyyy-MM-dd") } else { "" }
        QuickScanAge               = $estado.QuickScanAge
        FullScanAge                = $estado.FullScanAge
        BehaviorMonitorEnabled     = [bool]$estado.BehaviorMonitorEnabled
        IoavProtectionEnabled      = [bool]$estado.IoavProtectionEnabled
        NISEnabled                 = [bool]$estado.NISEnabled
    }
    Exportar-CsvSeguro -Datos @($fila) -Ruta (Join-Path $Salida "defender_estado.csv") -Columnas @(
        "Equipo", "AntivirusEnabled", "RealTimeProtectionEnabled", "AntispywareEnabled",
        "TamperProtection", "AntivirusSignatureAge", "UltimaActualizacionFirmas",
        "QuickScanAge", "FullScanAge", "BehaviorMonitorEnabled", "IoavProtectionEnabled",
        "NISEnabled")

    $pref = Get-MpPreference -ErrorAction SilentlyContinue
    # OJO: en PowerShell, mezclar "+" y "," dentro de @( ) NO crea un elemento
    # por línea (la coma tiene mayor precedencia que +). Por eso cada entrada va
    # entre paréntesis: así el archivo sale con una línea por parámetro.
    $lineas = @(
        ("DisableRealtimeMonitoring = " + (Valor-O-Cargador $pref.DisableRealtimeMonitoring)),
        ("DisableBehaviorMonitoring = " + (Valor-O-Cargador $pref.DisableBehaviorMonitoring)),
        ("DisableScriptScanning = " + (Valor-O-Cargador $pref.DisableScriptScanning)),
        ("EnableControlledFolderAccess = " + (Valor-O-Cargador $pref.EnableControlledFolderAccess)),
        ("ControlledFolderAccessProtectedFolders = " + (Valor-O-Cargador ($pref.ControlledFolderAccessProtectedFolders -join " | "))),
        ("PUAProtection = " + (Valor-O-Cargador $pref.PUAProtection)),
        ("DisableRemovableMediaExecution = " + (Valor-O-Cargador $pref.DisableRemovableMediaExecution)),
        ("RemovableMediaScan = " + (Valor-O-Cargador $pref.RemovableMediaScan)),
        ("ExclusionPath = " + (Valor-O-Cargador ($pref.ExclusionPath -join " | "))),
        ("ExclusionProcess = " + (Valor-O-Cargador ($pref.ExclusionProcess -join " | "))),
        ("ExclusionExtension = " + (Valor-O-Cargador ($pref.ExclusionExtension -join " | "))),
        ("MAPSReporting = " + (Valor-O-Cargador $pref.MAPSReporting)),
        ("SubmitSamplesConsent = " + (Valor-O-Cargador $pref.SubmitSamplesConsent))
    )
    Escribir -Ruta (Join-Path $Salida "defender_preferencias.txt") -Contenido $lineas
} catch {
    Informar-Fallo -Que "Defender" -Error_ $_
}

# ---------------------------------------------- 7. Endurecimiento del registro
Titulo "Endurecimiento (SMB, NTLM, LAPS, RestrictAnonymous)"
$rutaReg = Join-Path $Salida "registry_seguridad.txt"
# ArrayList (no arreglo): permite .Add() desde dentro de la función auxiliar.
$lineasReg = New-Object System.Collections.ArrayList

function Agregar-Valor {
    param([string]$Ruta, [string]$Nombre)
    try {
        $item = Get-ItemProperty -Path $Ruta -Name $Nombre -ErrorAction Stop
        [void]$lineasReg.Add($Ruta + " :: " + $Nombre + " = " + $item.$Nombre)
    } catch [System.Management.Automation.ItemNotFoundException] {
        # La ruta o la clave del registro no existe.
        [void]$lineasReg.Add($Ruta + " :: " + $Nombre + " = " + $MarcaAusente)
    } catch [System.Management.Automation.PSArgumentException] {
        # La clave existe pero la propiedad no esta dentro de ella.
        [void]$lineasReg.Add($Ruta + " :: " + $Nombre + " = " + $MarcaAusente)
    } catch [System.Security.SecurityException] {
        # Acceso denegado: no hay manera de saber si la clave existe.
        [void]$lineasReg.Add($Ruta + " :: " + $Nombre + " = " + $MarcaSinLectura)
    } catch {
        # Cualquier otro fallo tambien es "no supe", nunca "no existe".
        [void]$lineasReg.Add($Ruta + " :: " + $Nombre + " = " + $MarcaSinLectura +
                             " [" + $_.Exception.GetType().Name + "]")
    }
}

$rutaLsa = "HKLM:\SYSTEM\CurrentControlSet\Control\Lsa"
$rutaSmb = "HKLM:\SYSTEM\CurrentControlSet\Services\LanmanServer\Parameters"
$rutaCliente = "HKLM:\SYSTEM\CurrentControlSet\Services\LanmanWorkstation\Parameters"
$rutaLaps = "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\LAPS"
$rutaPol = "HKLM:\SOFTWARE\Policies\Microsoft\Windows Defender"
$rutaFuego = "HKLM:\SOFTWARE\Policies\Microsoft\WindowsFirewall"

foreach ($n in @("LmCompatibilityLevel", "NoLmHash", "RestrictAnonymous", "RestrictAnonymousSAM",
                 "EveryoneIncludesAnonymous", "LimitBlankPasswordUse")) {
    Agregar-Valor -Ruta $rutaLsa -Nombre $n
}
foreach ($n in @("RequireSecurityMode", "EnableSecuritySignature", "EnableSecurityMssigner",
                 "EnableSMBQUIC", "RestrictNullSessAccess")) {
    Agregar-Valor -Ruta $rutaSmb -Nombre $n
}
foreach ($n in @("LmCompatibilityLevel", "EnableInsecureGuestLogons",
                 "EnableSecuritySignature", "ValidateLMChallenge")) {
    Agregar-Valor -Ruta $rutaCliente -Nombre $n
}
foreach ($n in @("ConfigureLAPSRootKey", "Backoff") ) {
    Agregar-Valor -Ruta $rutaLaps -Nombre $n
}
[void]$lineasReg.Add("")
[void]$lineasReg.Add("--- Windows Defender (politicas) ---")
foreach ($n in @("DisableRealtimeMonitoring", "PUAProtection",
                 "EnableControlledFolderAccess", "DisableOnAUWithoutWss")) {
    Agregar-Valor -Ruta $rutaPol -Nombre $n
}
[void]$lineasReg.Add("")
[void]$lineasReg.Add("--- Cortafuegos (politicas) ---")
foreach ($prof in @(1, 2, 3)) {
    $p = $rutaFuego + "\" + $prof.ToString("0000")
    foreach ($n in @("EnableFirewall", "DefaultOutboundAction", "DefaultInboundAction")) {
        Agregar-Valor -Ruta $p -Nombre $n
    }
}
[void]$lineasReg.Add("")
[void]$lineasReg.Add("--- Actualizaciones automaticas ---")
foreach ($n in @("NoAutoUpdate", "AUOptions", "AutomaticMaintenanceEnabled")) {
    Agregar-Valor -Ruta "HKLM:\SOFTWARE\Policies\Microsoft\Windows\WindowsUpdate\AU" -Nombre $n
}

Escribir -Ruta $rutaReg -Contenido $lineasReg

# ------------------------------------------------------------- 8. BitLocker
Titulo "Cifrado de disco (BitLocker)"
try {
    $volumenes = Get-BitLockerVolume -ErrorAction Stop | ForEach-Object {
        [pscustomobject]@{
            Equipo           = $env:COMPUTERNAME
            MountPoint       = $_.MountPoint
            VolumeType       = $_.VolumeType
            ProtectionStatus = $_.ProtectionStatus
            EncryptionMethod = $_.EncryptionMethod
        }
    }
    Exportar-CsvSeguro -Datos $volumenes -Ruta (Join-Path $Salida "bitlocker.csv") -Columnas @(
            "Equipo", "MountPoint", "VolumeType", "ProtectionStatus", "EncryptionMethod")
} catch {
    Informar-Fallo -Que "BitLocker" -Error_ $_
}

# --------------------------------------------------- 9. Servicios y tiempo
Titulo "Servicios, hora y red"
$servicios = Get-Service | Where-Object { $_.Status -eq "Running" } |
             Select-Object Name, DisplayName, StartType | Sort-Object Name
Exportar-CsvSeguro -Datos $servicios -Ruta (Join-Path $Salida "servicios.csv") -Columnas @(
             "Name", "DisplayName", "StartType")

Escribir -Ruta (Join-Path $Salida "hora.txt") -Contenido ((& w32tm /query /status 2>&1) | Out-String)

$adaptadores = Get-NetIPConfiguration -ErrorAction SilentlyContinue | ForEach-Object {
    [pscustomobject]@{
        Equipo       = $env:COMPUTERNAME
        Interfaz     = $_.InterfaceAlias
        IPv4         = ($_.IPv4Address.IPAddress -join " | ")
        Gateway      = ($_.IPv4DefaultGateway.NextHop -join " | ")
        DNS          = ($_.DNSServer.ServerAddresses -join " | ")
    }
}
Exportar-CsvSeguro -Datos $adaptadores -Ruta (Join-Path $Salida "red_local.csv") -Columnas @(
    "Equipo", "Interfaz", "IPv4", "Gateway", "DNS")

$puertos = Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue | ForEach-Object {
    [pscustomobject]@{
        Equipo = $env:COMPUTERNAME
        Puerto = $_.LocalPort
        Direccion = $_.LocalAddress
    }
}
Exportar-CsvSeguro -Datos $puertos -Ruta (Join-Path $Salida "puertos_escucha.csv") -Columnas @(
        "Equipo", "Puerto", "Direccion")

# --------------------------------------------------------------- 10. M365
Titulo "Microsoft 365 (opcional)"
$modulosGraph = Get-Module -ListAvailable -Name @( "Microsoft.Graph.Users", "MSOnline", "AzureAD" )
if ($modulosGraph) {
    try {
        Import-Module Microsoft.Graph.Users -ErrorAction Stop
        Connect-MgGraph -Scopes User.Read.All -ErrorAction Stop
        $usuariosM365 = Get-MgUser -All -Property DisplayName, Department, AccountEnabled |
            ForEach-Object {
                [pscustomobject]@{
                    User         = $_.UserPrincipalName
                    Nombre       = $_.DisplayName
                    Departamento = $_.Department
                    Habilitado   = [bool]$_.AccountEnabled
                    MFA          = "no verificado"
                }
            }
        Exportar-CsvSeguro -Datos $usuariosM365 -Ruta (Join-Path $Salida "m365_mfa.csv") -Columnas @(
                "User", "Nombre", "Departamento", "Habilitado", "MFA")
        Write-Host "  MFA real requiere el informe de MFA; ver README." -ForegroundColor Yellow
    } catch {
        Informar-Fallo -Que "Microsoft 365" -Error_ $_
    }
} else {
    Write-Host "  [omitido] Modulos de Graph no instalados." -ForegroundColor Yellow
}

# ---------------------------------------------------------------- Resumen
Titulo "Resumen"
$archivos = Get-ChildItem -Path $Salida -File
Write-Host ("  Archivos generados: " + $archivos.Count)
Write-Host ""
Write-Host "SIGUIENTE PASO" -ForegroundColor Yellow
Write-Host "  1. Copie esta carpeta completa a 'evidencia\red' del proyecto spaudit."
Write-Host "  2. Ejecute el script TAMBIEN en el controlador de dominio y en un equipo de sala."
Write-Host "  3. Para M365, exporte el informe de MFA a 'evidencia\red\m365_mfa.csv'."
Write-Host "  4. Vuelva a ejecutar:  python auditar.py"
Write-Host ""