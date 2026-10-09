@echo off
chcp 65001 >nul
cd /d "%~dp0"
call config.bat

echo Pon UN objeto de medida conocida (por ejemplo una moneda) en el centro del fondo negro.
echo Sin huevos ni manos en la imagen.
echo.
set /p MEDIDA=Medida real del objeto en mm (usa punto, ej. 23.70):
echo.
echo El valor mm/px aparece en verde arriba a la izquierda del video.
echo Anótalo y cópialo en config.bat (línea MM_POR_PIXEL).
echo Para salir: haz clic en la ventana del video y presiona Q
echo.
rem --area-min 300 para que acepte objetos pequeños como una moneda
.venv\Scripts\python.exe src\contador_huevos.py --fuente %FUENTE% --calibrar %MEDIDA% --area-min 300

echo.
pause
