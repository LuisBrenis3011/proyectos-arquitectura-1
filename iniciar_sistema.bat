@echo off
echo Iniciando Sistema Biometrico Moderno...

start "Orquestador Flask" cmd /k "cd /d %~dp0 && .venv\Scripts\activate && py servidor_api.py"

timeout /t 4 /nobreak >nul

start "Kiosco Biometrico" cmd /k "cd /d %~dp0 && .venv\Scripts\activate && py app_biometria.py"

echo Listo. El orquestador y el kiosco estan corriendo.