@echo off
chcp 65001 >nul
cd /d "%~dp0"
call config.bat

echo Contando huevos desde %FUENTE%
echo Calibración: %MM_POR_PIXEL% mm/px   Registro: %CSV%
echo Para salir: haz clic en la ventana del video y presiona Q
echo.
.venv\Scripts\python.exe src\contador_huevos.py --fuente %FUENTE% --mm-por-pixel %MM_POR_PIXEL% --csv %CSV%

echo.
pause
