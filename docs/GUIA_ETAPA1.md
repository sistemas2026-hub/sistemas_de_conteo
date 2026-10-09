# Contador de huevos en banda — Etapa 1

Objetivo: contar cada huevo que pasa por la banda y medir su largo y ancho en mm.
Cada huevo queda registrado en `registro_huevos.csv` (se abre en Excel o Google Sheets).

Esta etapa **no usa IA**: detecta los huevos por contraste contra el fondo.
Por eso no hay que entrenar nada y corre en equipos modestos.
La detección de defectos (roto, sucio) es la etapa 2 y ahí sí se entrena un modelo.

---

## Materiales

**Mínimo para probar (puedes empezar sin banda):**
- Computador con Windows, Linux o Mac (sirve uno viejo), o Raspberry Pi 4/5.
- Cámara web USB. Mejor si permite **enfoque y exposición manuales**: las que ajustan solas cambian el brillo y afectan las medidas.
- Fondo **negro mate** (cartulina, tela o pintura sin brillo).
- Luz LED blanca uniforme: tira LED o panel, a ambos lados, para evitar sombras.
- Soporte fijo para la cámara (no debe moverse nunca después de calibrar).
- Una moneda u objeto de tamaño conocido para calibrar.

**Para la banda:**
- Banda transportadora pequeña con superficie oscura. Ideal con **cunas o separadores** para que cada huevo vaya en su puesto y no se toquen.
- Motor con control de velocidad (paso a paso o DC con controlador).
- Encoder en el motor: no es necesario para contar, pero sí para la etapa 4 (separación automática).
- Una caja o túnel sobre la zona de la cámara para bloquear la luz exterior.

> No pongo precios ni modelos exactos porque dependen de lo que consigas en tu zona.

---

## Instalación

```bash
pip install opencv-python numpy
```

En Raspberry Pi sin pantalla usa `opencv-python-headless`.

---

## Uso paso a paso

**1. Prueba que la cámara se vea bien**
```bash
python src/contador_huevos.py --fuente 0
```
Pon un huevo bajo la cámara: debe aparecer un óvalo verde alrededor.
Si no aparece o aparecen manchas, revisa la luz y el fondo antes de seguir.

**2. Calibra (convierte píxeles a milímetros)**
Pon UN objeto de largo conocido, por ejemplo una moneda. Mide su diámetro real con regla o calibrador.
```bash
python src/contador_huevos.py --fuente 0 --calibrar 24.4
```
(cambia 24.4 por la medida real en mm). Anota el valor `mm/px` que muestra.
Debes repetir esto si mueves la cámara o cambias la altura.

**3. Cuenta**
```bash
python src/contador_huevos.py --fuente 0 --mm-por-pixel 0.21
```
(usa tu valor de calibración). Presiona **Q** para salir.

En Raspberry sin pantalla:
```bash
python src/contador_huevos.py --fuente 0 --mm-por-pixel 0.21 --sin-ventana
```

---

## Ajustes útiles

| Opción | Para qué |
|---|---|
| `--direccion izquierda` | Si la banda se mueve hacia la izquierda en la imagen |
| `--linea 0.5` | Dónde está la línea de conteo (0 = borde izquierdo, 1 = borde derecho) |
| `--umbral-min 60` | Súbelo si cuenta sombras o reflejos; bájalo si no ve huevos muy oscuros |
| `--area-min` / `--area-max` | Tamaño en píxeles para aceptar algo como huevo (dependen de la altura de la cámara) |
| `--fondo-claro` | Si tu fondo es más claro que los huevos |
| `--ancho 640` | Resolución de trabajo. Bájala (ej. 480) si va lento |

---

## Limitaciones de esta etapa (para no llevarte sorpresas)

- **Huevos pegados** se cuentan como uno solo. Las cunas o separadores en la banda lo resuelven.
- **Huevos marrones sobre fondo oscuro** necesitan buena luz. Prueba con tus huevos reales.
- **Largo y ancho no son peso.** Para clasificar por categoría (AAA, AA, A…) según la norma colombiana, que es por peso, usa una báscula, o pesa unos cientos de huevos y compara con lo que mide la cámara para saber si la estimación te sirve.
- El código se probó con un **video simulado** (10 huevos de 3 tamaños: los contó y midió correctamente). Con tu montaje real seguramente habrá que ajustar `--umbral-min` y las áreas.

---

## Siguiente etapa

Etapa 2: detectar huevos rotos y sucios. Para eso necesitarás fotos reales de tus huevos (buenos y defectuosos), así que desde ya puedes ir guardando ejemplos con el montaje de esta etapa.
