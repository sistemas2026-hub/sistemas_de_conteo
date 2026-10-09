# Sistema de conteo y calidad de huevos

Sistema de visión por computadora para una granja de gallinas ponedoras: cuenta los huevos que pasan por una banda transportadora y controla su calidad.

Está pensado para ser **liviano**: corre en un computador modesto y, más adelante, en una Raspberry Pi 5, sin tarjeta gráfica.

## Etapas

1. **Conteo y medición en banda** *(hecha)*. OpenCV sin IA: detecta los huevos por contraste sobre fondo oscuro, los rastrea, los cuenta al cruzar una línea virtual, mide largo y ancho en mm y guarda cada huevo en un CSV.
2. **Detección de defectos** (roto, sucio, deforme) con YOLO nano de Ultralytics, entrenado en Google Colab con fotos reales de los huevos de la granja.
3. **Clasificación por peso** con báscula / celda de carga, porque la norma colombiana NTC 1240 clasifica por peso y no por medida visual.
4. **Separación automática** con ESP32 o Arduino y servos, usando la velocidad de la banda.

## Estructura

```
src/       código (contador_huevos.py)
docs/      guías (GUIA_ETAPA1.md: materiales, calibración y limitaciones)
datos/     registros CSV (no se suben a Git)
fotos/     imágenes para entrenar la etapa 2 (no se suben a Git)
```

## Instalación

Requiere Python 3. Desde la carpeta del proyecto:

**Windows (PowerShell)**
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

**Linux / Raspberry Pi**
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

En Raspberry Pi sin pantalla se puede usar `opencv-python-headless` en lugar de `opencv-python`.

## Ejecución

### Con doble clic (Windows)

| Archivo | Qué hace |
|---|---|
| `contar.bat` | Abre el contador con la cámara y la calibración configuradas. Guarda en `datos\registro_mm.csv` |
| `calibrar.bat` | Pide la medida real del objeto (ej. una moneda) y abre el modo calibración |
| `config.bat` | Configuración: dirección de la cámara (`FUENTE`), calibración (`MM_POR_PIXEL`) y archivo CSV |

Si cambia la IP del celular o se recalibra, solo se edita `config.bat` (clic derecho → Editar).
Para salir del video: clic en la ventana y tecla **Q**.

**Celular como cámara:** con la app IP Webcam (Play Store), el celular y el computador en la misma red Wi-Fi, se usa la dirección que muestra la app con `/video` al final, por ejemplo `http://192.168.1.XX:8080/video`.

### Desde la terminal

Ver todas las opciones:
```bash
python src/contador_huevos.py --help
```

Calibrar con un objeto de largo conocido (cambia 24.4 por la medida real en mm):
```bash
python src/contador_huevos.py --fuente 0 --calibrar 24.4
```

Contar usando el valor mm/px obtenido y guardando el registro en `datos/`:
```bash
python src/contador_huevos.py --fuente 0 --mm-por-pixel 0.21 --csv datos/registro_huevos.csv
```

En Raspberry sin pantalla, agrega `--sin-ventana`. Para probar con un video en lugar de la cámara: `--fuente video.mp4`.

> Si no se indica `--csv`, el registro se guarda como `registro_huevos.csv` en la carpeta desde donde se ejecuta el programa.

Los detalles de montaje, calibración y ajustes están en [docs/GUIA_ETAPA1.md](docs/GUIA_ETAPA1.md).
