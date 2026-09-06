<#
.SINOPSIS
    Atajos del proyecto para Windows, equivalentes al Makefile.

.DESCRIPCION
    En Windows no viene `make` instalado. Este script acepta exactamente los
    mismos nombres de objetivo que el Makefile y hace lo mismo, sin instalar
    nada.

.EJEMPLO
    .\make.ps1                 muestra la ayuda
    .\make.ps1 instalar        crea el entorno virtual e instala dependencias
    .\make.ps1 correr          inicia la aplicacion
    .\make.ps1 probar          ejecuta la suite de pruebas
#>

[CmdletBinding()]
param(
    [Parameter(Position = 0)]
    [string]$Objetivo = "ayuda"
)

Set-Location -Path $PSScriptRoot

# ---------------------------------------------------------------------------
# Estado del script
# ---------------------------------------------------------------------------

# Codigo de salida. Las funciones lo fijan aqui en vez de devolverlo con
# `return`, porque un valor devuelto se mezclaria en el pipeline con la salida
# de pytest y el codigo dejaria de ser fiable cuando una prueba falla.
$script:CodigoSalida = 0

$VenvPython = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"

function Get-Python {
    <#
        Devuelve el interprete a usar: el del entorno virtual si existe, y si
        no el del sistema. Se prefiere el lanzador `py` porque en varias
        maquinas el `python` del PATH apunta a otra instalacion.
    #>
    if (Test-Path $VenvPython) {
        return @{ Exe = $VenvPython; Args = @() }
    }
    if (Get-Command py -ErrorAction SilentlyContinue) {
        return @{ Exe = "py"; Args = @("-3") }
    }
    return @{ Exe = "python"; Args = @() }
}

function Invoke-Python {
    <# Ejecuta el interprete elegido y guarda su codigo de salida. #>
    param([string[]]$Argumentos)

    $py = Get-Python
    & $py.Exe @($py.Args + $Argumentos)
    $script:CodigoSalida = $LASTEXITCODE
}

function Invoke-Pytest {
    param([string[]]$Argumentos = @())
    Invoke-Python (@("-m", "pytest") + $Argumentos)
}

function Get-SalidaPytest {
    <# Ejecuta pytest capturando su salida, para poder filtrarla. #>
    param([string[]]$Argumentos)

    $py = Get-Python
    return (& $py.Exe @($py.Args + @("-m", "pytest") + $Argumentos) 2>&1)
}

function Escribir-Titulo([string]$Texto) {
    Write-Host ""
    Write-Host $Texto -ForegroundColor Cyan
}

# ---------------------------------------------------------------------------
# Objetivos
# ---------------------------------------------------------------------------

function Objetivo-Ayuda {
    $py = Get-Python
    Write-Host ""
    Write-Host "Sistema de prestamo de equipos - objetivos disponibles" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "  .\make.ps1 instalar            crea el entorno virtual e instala las dependencias"
    Write-Host "  .\make.ps1 correr              inicia la aplicacion de linea de comando"
    Write-Host "  .\make.ps1 probar              ejecuta toda la suite de pruebas"
    Write-Host "  .\make.ps1 verificar           ejecuta la suite y muestra el resumen por categoria"
    Write-Host ""
    Write-Host "  .\make.ps1 probar-funcional    solo los casos funcionales"
    Write-Host "  .\make.ps1 probar-borde        solo los casos de borde"
    Write-Host "  .\make.ps1 probar-negativo     solo los casos negativos"
    Write-Host "  .\make.ps1 probar-reglas       solo los casos que combinan reglas"
    Write-Host "  .\make.ps1 probar-escenario    solo el escenario completo"
    Write-Host "  .\make.ps1 probar-pendientes   lista los casos aun marcados xfail"
    Write-Host ""
    Write-Host "  .\make.ps1 evidencia           guarda la salida de las pruebas en evidencias\"
    Write-Host "  .\make.ps1 demo                regenera los datos de demostracion"
    Write-Host "  .\make.ps1 reiniciar           borra datos y logs, y vuelve a cargar la demo"
    Write-Host "  .\make.ps1 registro            muestra las ultimas lineas del log de eventos"
    Write-Host "  .\make.ps1 limpiar             borra caches, logs y archivos temporales"
    Write-Host ""
    if (Test-Path $VenvPython) {
        Write-Host "Interprete en uso: .venv\Scripts\python.exe" -ForegroundColor Green
    }
    else {
        Write-Host "Todavia no existe el entorno virtual. Ejecuta:  .\make.ps1 instalar" -ForegroundColor Yellow
        Write-Host "Interprete que se usaria: $($py.Exe) $($py.Args -join ' ')"
    }
    Write-Host ""
}

function Objetivo-Instalar {
    Escribir-Titulo "Creando el entorno virtual en .venv"
    Invoke-Python @("-m", "venv", ".venv")
    if ($script:CodigoSalida -ne 0) { return }

    Escribir-Titulo "Instalando dependencias"
    & $VenvPython -m pip install --upgrade pip --quiet
    & $VenvPython -m pip install -r requirements.txt
    $script:CodigoSalida = $LASTEXITCODE
    if ($script:CodigoSalida -ne 0) { return }

    Write-Host ""
    Write-Host "Listo. Los objetivos correr y probar ya usan el entorno virtual." -ForegroundColor Green
}

function Objetivo-Correr {
    Invoke-Python @("main.py")
}

function Objetivo-Probar {
    Invoke-Pytest
}

function Objetivo-ProbarMarca([string]$Marca) {
    Invoke-Pytest @("-m", $Marca)
}

function Objetivo-ProbarPendientes {
    Escribir-Titulo "Casos a la espera de que se implemente su requerimiento"
    $pendientes = Get-SalidaPytest @("-q", "-rx") | Select-String -Pattern "^XFAIL"
    if ($pendientes) {
        $pendientes | ForEach-Object { Write-Host "  $_" }
    }
    else {
        Write-Host "  Ninguno. Todos los requerimientos estan implementados." -ForegroundColor Green
    }
}

function Objetivo-Evidencia {
    New-Item -ItemType Directory -Path "evidencias" -Force | Out-Null
    $archivo = "evidencias\pytest-$(Get-Date -Format 'yyyy-MM-dd').txt"

    Get-SalidaPytest @("-v") | Out-File -FilePath $archivo -Encoding utf8

    Write-Host "Evidencia guardada en $archivo" -ForegroundColor Green
    Get-Content $archivo -Tail 3
}

function Objetivo-Demo {
    Invoke-Python @("scripts\cargar_demo.py", "--forzar")
}

function Objetivo-Reiniciar {
    foreach ($carpeta in @("data", "logs")) {
        if (Test-Path $carpeta) {
            Remove-Item -Recurse -Force $carpeta
        }
    }
    Write-Host "Datos y logs eliminados." -ForegroundColor Yellow
    Invoke-Python @("scripts\cargar_demo.py", "--forzar")
}

function Objetivo-Registro {
    $log = "logs\eventos.log"
    if (Test-Path $log) {
        Get-Content $log -Tail 30
    }
    else {
        Write-Host "Todavia no hay eventos registrados."
    }
}

function Objetivo-Limpiar {
    foreach ($carpeta in @(".pytest_cache", "logs")) {
        if (Test-Path $carpeta) {
            Remove-Item -Recurse -Force $carpeta
        }
    }
    Get-ChildItem -Path . -Directory -Recurse -Filter "__pycache__" -ErrorAction SilentlyContinue |
        Remove-Item -Recurse -Force -ErrorAction SilentlyContinue

    Write-Host "Caches, logs y archivos temporales eliminados." -ForegroundColor Green
    Write-Host "Los datos de data\ se conservan. Usa reiniciar si quieres borrarlos tambien."
}

function Contar-Casos([string]$Marca) {
    <# Extrae el primer numero de la linea "N/M tests collected" de pytest. #>
    $linea = Get-SalidaPytest @("-m", $Marca, "--collect-only", "-q") |
        Select-String -Pattern "(\d+)/\d+ tests collected" |
        Select-Object -First 1
    if ($linea) {
        return $linea.Matches[0].Groups[1].Value
    }
    return "0"
}

function Objetivo-Verificar {
    Invoke-Pytest
    $codigoPruebas = $script:CodigoSalida

    Escribir-Titulo "Casos por categoria (minimo exigido por la tarea entre parentesis)"
    Write-Host "  funcionales (5) : $(Contar-Casos 'funcional')"
    Write-Host "  borde       (4) : $(Contar-Casos 'borde')"
    Write-Host "  negativos   (3) : $(Contar-Casos 'negativo')"
    Write-Host "  reglas      (2) : $(Contar-Casos 'reglas')"
    Write-Host "  escenario   (1) : $(Contar-Casos 'escenario')"
    Write-Host ""

    # El codigo de salida es el de la suite, no el del recuento.
    $script:CodigoSalida = $codigoPruebas
}

# ---------------------------------------------------------------------------
# Despacho
# ---------------------------------------------------------------------------

switch ($Objetivo.ToLower()) {
    "ayuda"             { Objetivo-Ayuda }
    "help"              { Objetivo-Ayuda }
    "instalar"          { Objetivo-Instalar }
    "correr"            { Objetivo-Correr }
    "probar"            { Objetivo-Probar }
    "probar-funcional"  { Objetivo-ProbarMarca "funcional" }
    "probar-borde"      { Objetivo-ProbarMarca "borde" }
    "probar-negativo"   { Objetivo-ProbarMarca "negativo" }
    "probar-reglas"     { Objetivo-ProbarMarca "reglas" }
    "probar-escenario"  { Objetivo-ProbarMarca "escenario" }
    "probar-pendientes" { Objetivo-ProbarPendientes }
    "evidencia"         { Objetivo-Evidencia }
    "demo"              { Objetivo-Demo }
    "reiniciar"         { Objetivo-Reiniciar }
    "registro"          { Objetivo-Registro }
    "limpiar"           { Objetivo-Limpiar }
    "verificar"         { Objetivo-Verificar }
    default {
        Write-Host ""
        Write-Host "Objetivo desconocido: $Objetivo" -ForegroundColor Red
        Objetivo-Ayuda
        $script:CodigoSalida = 1
    }
}

exit $script:CodigoSalida
