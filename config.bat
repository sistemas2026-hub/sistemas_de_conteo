@echo off
rem ============================================================
rem  Configuración compartida por contar.bat y calibrar.bat
rem  Edita solo estas líneas (clic derecho > Editar o Bloc de notas)
rem ============================================================

rem Dirección que muestra la app IP Webcam en el celular (agregar /video al final)
rem Para una cámara web USB usa un número: 0, 1, 2...
set FUENTE=http://192.168.101.10:8080/video

rem Valor de calibración. Repite la calibración si mueves el celular o cambias la altura.
set MM_POR_PIXEL=0.632

rem Archivo donde se guarda cada huevo contado
set CSV=datos\registro_mm.csv

rem Oculta los avisos "[mjpeg] overread" del video por Wi-Fi
set OPENCV_FFMPEG_LOGLEVEL=-8
