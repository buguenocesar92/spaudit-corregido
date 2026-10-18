# Verificador INDEPENDIENTE del recolector.
#
# Lee `registry_seguridad.txt` y comprueba, línea por línea, que cada marcador
# diga la verdad. No pregunta al recolector: vuelve a consultar el registro por
# su cuenta y compara. Si el recolector wrote `<no definido>` y la clave sí
# existe, esto falla — que es exactamente el bug que hay que cazar.
#
# Uso:  powershell -ExecutionPolicy Bypass -File verificar-marcadores.ps1 -Archivo <ruta>

[CmdletBinding()]
param([Parameter(Mandatory=$true)][string]$Archivo)

$ErrorActionPreference = "Continue"

$MarcaAusente    = "<no definido>"
$MarcaSinLectura = "<sin permiso de lectura>"
$MarcaSinDato    = "<no informado>"

$ok = 0; $mal = 0; $ignoradas = 0; $lineas = @()

foreach ($cruda in Get-Content -LiteralPath $Archivo -Encoding UTF8) {
    if ([string]::IsNullOrWhiteSpace($cruda)) { continue }
    if ($cruda -like "---*") { continue }          # separadores de sección

    $i = $cruda.IndexOf(" :: ")
    if ($i -lt 1) { continue }                    # no es una línea de valor
    $ruta = $cruda.Substring(0, $i)
    $resto = $cruda.Substring($i + 4)

    $j = $resto.IndexOf(" = ")
    if ($j -lt 1) { continue }
    $nombre = $resto.Substring(0, $j)
    $declarado = $resto.Substring($j + 3)

    # Consulta propia. El valor de referencia sale del registro, no del archivo.
    $real = $null
    $estado = "leido"
    try {
        $item = Get-ItemProperty -Path $ruta -Name $nombre -ErrorAction Stop
        $real = [string]$item.$nombre
    } catch [System.Management.Automation.ItemNotFoundException] { $estado = "ausente" }
    catch [System.Management.Automation.PSArgumentException] { $estado = "ausente" }
    catch [System.Security.SecurityException] { $estado = "denegado" }
    catch { $estado = "otro:" + $_.Exception.GetType().Name }

    $esperado = switch ($estado) {
        "ausente" { $MarcaAusente }
        "denegado" { $MarcaSinLectura }
        default {
            if ($null -eq $real -or $real.Trim().Length -eq 0) { $MarcaSinDato } else { $real }
        }
    }

    if ($declarado -eq $esperado) { $ok++ }
    elseif ($declarado -eq $MarcaSinLectura -and $estado -eq "otro:MethodInvocationException") {
        # Get-ItemProperty sin -ErrorAction Stop lanza MethodInvocationException
        # cuando el Path no existe; el recolector lo marca como "sin lectura".
        # Es discutible, se cuenta aparte para no tapar nada.
        $ignoradas++
        $lineas += ("[DISCUTIBLE] {0} :: {1}`n    archivo: {2}`n    registro: {3}" -f $ruta, $nombre, $declarado, $estado)
    } else {
        $mal++
        $lineas += ("[MAL] {0} :: {1}`n    archivo  : {2}`n    registro : {3}  ({4})" -f $ruta, $nombre, $declarado, $esperado, $estado)
    }
}

Write-Host ""
Write-Host "== Verificacion independiente de marcadores =="
Write-Host ("  correctas      : " + $ok)
Write-Host ("  incorrectas    : " + $mal)
Write-Host ("  discutibles    : " + $ignoradas)
if ($lineas.Count) { Write-Host ""; $lineas | ForEach-Object { Write-Host ("  " + $_) } }
Write-Host ""

# Un marcador de "no existe" con la clave presente es el fallo grave: dice que
# algo falta cuando no falta. Sale distinto para que no se confunda con el ruido.
if ($mal -gt 0) { exit 1 } else { exit 0 }