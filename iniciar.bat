@echo off
chcp 65001 >nul
cd /d "%~dp0"
title Panel Financiero

if not exist ".venv\Scripts\python.exe" (
  echo ============================================================
  echo   Primera vez: instalando lo necesario. Puede tardar unos
  echo   minutos. No cierres esta ventana.
  echo ============================================================
  py -m venv .venv
  ".venv\Scripts\python.exe" -m pip install --upgrade pip
  ".venv\Scripts\python.exe" -m pip install -r requirements.txt
  echo.
)

if not exist ".env" (
  copy ".env.example" ".env" >nul
  echo Se creo el archivo .env . Abrilo con el Bloc de notas y pega tu
  echo clave de Gemini en la linea GEMINI_API_KEY=  (ver GUIA.md).
  echo.
)

echo Abriendo el Panel Financiero en el navegador...
start "" http://localhost:8000
echo.
echo Para APAGAR la aplicacion, cerra esta ventana o presiona Ctrl+C.
echo.
".venv\Scripts\python.exe" run.py
pause
