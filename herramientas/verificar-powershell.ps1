$ErrorActionPreference = "Stop"
$ruta = Join-Path $PSScriptRoot "..\powershell\recolectar-evidencia.ps1"
$ruta = (Resolve-Path $ruta).Path

$errores = $null
$tokens = $null
$ast = [System.Management.Automation.Language.Parser]::ParseFile($ruta, [ref]$tokens, [ref]$errores)

Write-Host ("Archivo: " + $ruta)
Write-Host ("Lineas:  " + (Get-Content $ruta).Count)
Write-Host ("Tokens:  " + $tokens.Count)
if ($errores -and $errores.Count -gt 0) {
    Write-Host ""
    Write-Host ("ERRORES DE ANALISIS: " + $errores.Count) -ForegroundColor Red
    foreach ($e in $errores) {
        Write-Host ("  linea " + $e.Extent.StartLineNumber + ": " + $e.Message) -ForegroundColor Red
    }
    exit 1
} else {
    Write-Host "Analisis sintactico: OK" -ForegroundColor Green
}

# Comprobaciones adicionales sobre el contenido esperado
$contenido = Get-Content $ruta -Raw
$esperados = @(
    "net_accounts.txt", "auditpol.txt", "usuarios_ad.csv", "grupos_ad.csv",
    "defender_estado.csv", "defender_preferencias.txt", "sistema.csv",
    "registry_seguridad.txt", "bitlocker.csv", "comparticiones.csv"
)
$falta = @()
foreach ($e in $esperados) {
    if ($contenido -notmatch [regex]::Escape($e)) { $falta += $e }
}
if ($falta.Count -gt 0) {
    Write-Host ("FALTA generar: " + ($falta -join ", ")) -ForegroundColor Red
    exit 1
}
Write-Host "Cobertura de archivos esperados: OK" -ForegroundColor Green
exit 0