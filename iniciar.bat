@echo off
chcp 65001 >nul
cd /d "%~dp0"
title Panel Financiero

echo ============================================================
echo   PANEL FINANCIERO
echo ============================================================
echo.

where py >nul 2>nul
if errorlevel 1 (
  echo  [ERROR] No se encontro Python.
  echo  Instalalo desde https://www.python.org/downloads/
  echo  y en el instalador tilda "Add Python to PATH".
  echo.
  pause
  exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
  echo  Primera vez: instalando lo necesario.
  echo  Esto puede tardar entre 3 y 5 minutos. NO cierres esta ventana.
  echo  Espera hasta que diga "LISTO".
  echo.
  py -m venv .venv
  ".venv\Scripts\python.exe" -m pip install --upgrade pip
  ".venv\Scripts\python.exe" -m pip install -r requirements.txt
  if errorlevel 1 (
    echo.
    echo  [ERROR] Fallo la instalacion. Sacale una foto a esta ventana.
    echo.
    pause
    exit /b 1
  )
  echo.
  echo  LISTO. Instalacion terminada.
  echo.
)

if not exist ".env" (
  copy ".env.example" ".env" >nul
  echo  Se creo el archivo .env . Si queres proteger el panel con
  echo  contrasena, abrilo con el Bloc de notas y completa APP_PASSWORD.
  echo.
)

echo  Iniciando la aplicacion...
echo  En unos segundos se va a abrir SOLO el navegador.
echo  Si no se abre, entra vos a:  http://localhost:8000
echo.
echo  ------------------------------------------------------------
echo   PARA APAGAR LA APP: cerra esta ventana.
echo   NO la cierres mientras uses el panel.
echo  ------------------------------------------------------------
echo.

start "" powershell -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -Command "$ok=$false; for($i=0;$i -lt 120 -and -not $ok;$i++){try{Invoke-WebRequest -UseBasicParsing 'http://localhost:8000/health' -TimeoutSec 2 | Out-Null; $ok=$true}catch{Start-Sleep -Milliseconds 700}}; if($ok){Start-Process 'http://localhost:8000'}"

".venv\Scripts\python.exe" run.py

echo.
echo  La aplicacion se detuvo.
pause
