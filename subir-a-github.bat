@echo off
chcp 65001 >nul
cd /d "%~dp0"
title Subir Panel Financiero a GitHub

echo ============================================================
echo   Subiendo el proyecto a GitHub
echo   Repositorio: gonzalolima-crypto/PanelFinanciero
echo ============================================================
echo.
echo   La PRIMERA vez se va a abrir una ventana para iniciar
echo   sesion en GitHub (con el navegador). Aprobala y listo:
echo   queda recordado para siempre.
echo.
pause

git push -u origin main

echo.
if %errorlevel%==0 (
  echo   LISTO. Codigo subido a:
  echo   https://github.com/gonzalolima-crypto/PanelFinanciero
) else (
  echo   Algo fallo. Sacale una foto a esta ventana y pasamela.
)
echo.
pause
