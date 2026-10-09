"""
Contador de huevos en banda - Etapa 1
-------------------------------------
Cuenta cada huevo que cruza una línea virtual y mide su largo y ancho (mm).
Funciona con OpenCV puro (sin IA ni entrenamiento), así que corre en
Raspberry Pi o en un computador modesto.

Requisitos del montaje:
  - Cámara fija arriba de la banda, a altura constante.
  - Fondo de la banda oscuro y mate (negro o gris oscuro).
  - Luz LED uniforme, sin sombras fuertes.
  - Huevos separados (que no se toquen entre sí).

Uso:
  python contador_huevos.py --fuente 0                  # cámara web
  python contador_huevos.py --fuente video.mp4          # probar con un video
  python contador_huevos.py --fuente 0 --calibrar 24.4  # calibrar con un objeto de 24.4 mm
  python contador_huevos.py --fuente 0 --mm-por-pixel 0.21 --sin-ventana
"""

import argparse
import csv
import math
import os
import time
from datetime import datetime

import cv2
import numpy as np


# ----------------------------------------------------------------------
# Rastreador simple por centroides: asigna un ID a cada huevo
# ----------------------------------------------------------------------
class Rastreador:
    def __init__(self, dist_max=80, frames_max_perdido=10):
        self.siguiente_id = 1
        self.objetos = {}  # id -> dict(centro, perdido, medidas, contado)
        self.dist_max = dist_max
        self.frames_max_perdido = frames_max_perdido

    def actualizar(self, detecciones):
        """detecciones: lista de dict(centro=(x,y), largo_px, ancho_px, area_px)"""
        ids = list(self.objetos.keys())
        usados_det = set()
        usados_obj = set()

        # Emparejar por distancia mínima (greedy)
        pares = []
        for oid in ids:
            cx, cy = self.objetos[oid]["centro"]
            for j, d in enumerate(detecciones):
                dx, dy = d["centro"]
                dist = math.hypot(cx - dx, cy - dy)
                if dist <= self.dist_max:
                    pares.append((dist, oid, j))
        pares.sort()

        for _, oid, j in pares:
            if oid in usados_obj or j in usados_det:
                continue
            obj = self.objetos[oid]
            obj["centro_anterior"] = obj["centro"]
            obj["centro"] = detecciones[j]["centro"]
            obj["perdido"] = 0
            obj["medidas"].append(detecciones[j])
            usados_obj.add(oid)
            usados_det.add(j)

        # Objetos no vistos en este frame
        for oid in ids:
            if oid not in usados_obj:
                self.objetos[oid]["perdido"] += 1
                self.objetos[oid]["centro_anterior"] = self.objetos[oid]["centro"]
                if self.objetos[oid]["perdido"] > self.frames_max_perdido:
                    del self.objetos[oid]

        # Detecciones nuevas
        for j, d in enumerate(detecciones):
            if j not in usados_det:
                self.objetos[self.siguiente_id] = {
                    "centro": d["centro"],
                    "centro_anterior": d["centro"],
                    "perdido": 0,
                    "medidas": [d],
                    "contado": False,
                }
                self.siguiente_id += 1

        return self.objetos


# ----------------------------------------------------------------------
# Detección de huevos con umbral + contornos
# ----------------------------------------------------------------------
def detectar_huevos(frame, area_min, area_max, fondo_claro=False, umbral_min=60):
    gris = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    gris = cv2.GaussianBlur(gris, (7, 7), 0)
    if fondo_claro:
        gris = 255 - gris  # así el huevo siempre queda "más claro" que el fondo

    # Umbral automático (Otsu), pero nunca por debajo de umbral_min:
    # con la banda vacía, Otsu solo vería ruido y crearía huevos falsos.
    otsu, _ = cv2.threshold(gris, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    umbral = max(otsu, umbral_min)
    _, mascara = cv2.threshold(gris, umbral, 255, cv2.THRESH_BINARY)

    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    mascara = cv2.morphologyEx(mascara, cv2.MORPH_OPEN, kernel, iterations=2)
    mascara = cv2.morphologyEx(mascara, cv2.MORPH_CLOSE, kernel, iterations=2)

    contornos, _ = cv2.findContours(mascara, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    detecciones = []
    for c in contornos:
        area = cv2.contourArea(c)
        if area < area_min or area > area_max or len(c) < 5:
            continue
        # Filtro de forma: un huevo es sólido (sin huecos ni entrantes) y ovalado
        casco = cv2.convexHull(c)
        solidez = area / max(cv2.contourArea(casco), 1)
        if solidez < 0.9:
            continue
        (cx, cy), (eje1, eje2), angulo = cv2.fitEllipse(c)
        proporcion = max(eje1, eje2) / max(min(eje1, eje2), 1)
        if proporcion > 1.8:
            continue
        detecciones.append({
            "centro": (int(cx), int(cy)),
            "largo_px": max(eje1, eje2),
            "ancho_px": min(eje1, eje2),
            "area_px": area,
            "elipse": ((cx, cy), (eje1, eje2), angulo),
        })
    return detecciones, mascara


# ----------------------------------------------------------------------
# Programa principal
# ----------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser(description="Contador de huevos en banda")
    ap.add_argument("--fuente", default="0", help="Índice de cámara (0, 1...) o ruta de video")
    ap.add_argument("--mm-por-pixel", type=float, default=None,
                    help="Factor de calibración. Si no se da, las medidas quedan en píxeles")
    ap.add_argument("--calibrar", type=float, default=None, metavar="MM_REALES",
                    help="Modo calibración: pon un objeto de tamaño conocido y da su largo real en mm")
    ap.add_argument("--linea", type=float, default=0.5,
                    help="Posición de la línea de conteo (0 a 1 del ancho de imagen)")
    ap.add_argument("--direccion", choices=["derecha", "izquierda"], default="derecha",
                    help="Hacia dónde se mueve la banda en la imagen")
    ap.add_argument("--area-min", type=int, default=1500, help="Área mínima en px para ser huevo")
    ap.add_argument("--area-max", type=int, default=60000, help="Área máxima en px para ser huevo")
    ap.add_argument("--umbral-min", type=int, default=60,
                    help="Brillo mínimo (0-255) para considerar algo huevo. Súbelo si cuenta sombras o manchas")
    ap.add_argument("--fondo-claro", action="store_true", help="Usar si el fondo es más claro que los huevos")
    ap.add_argument("--ancho", type=int, default=640, help="Ancho de procesamiento (más pequeño = más rápido)")
    ap.add_argument("--csv", default="registro_huevos.csv", help="Archivo donde se guarda cada huevo")
    ap.add_argument("--sin-ventana", action="store_true", help="No mostrar video (para Raspberry sin pantalla)")
    args = ap.parse_args()

    fuente = int(args.fuente) if args.fuente.isdigit() else args.fuente
    cap = cv2.VideoCapture(fuente)
    if not cap.isOpened():
        raise SystemExit(f"No se pudo abrir la fuente: {args.fuente}")

    # ---------------- Modo calibración ----------------
    if args.calibrar:
        print("Modo calibración: pon UN objeto de tamaño conocido bajo la cámara. Presiona Q para salir.")
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            frame = redimensionar(frame, args.ancho)
            dets, _ = detectar_huevos(frame, args.area_min, args.area_max, args.fondo_claro, args.umbral_min)
            if dets:
                d = max(dets, key=lambda x: x["area_px"])
                factor = args.calibrar / d["largo_px"]
                texto = f"largo={d['largo_px']:.1f}px -> mm/px={factor:.4f}"
                cv2.ellipse(frame, d["elipse"], (0, 255, 0), 2)
                cv2.putText(frame, texto, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                print(texto, end="\r")
            if args.sin_ventana:
                continue
            cv2.imshow("Calibracion", frame)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
        print("\nUsa el valor mm/px con --mm-por-pixel")
        cap.release()
        cv2.destroyAllWindows()
        return

    # ---------------- Modo conteo ----------------
    nuevo = not os.path.exists(args.csv)
    archivo = open(args.csv, "a", newline="", encoding="utf-8")
    escritor = csv.writer(archivo)
    unidad = "mm" if args.mm_por_pixel else "px"
    if nuevo:
        escritor.writerow(["fecha_hora", "numero", f"largo_{unidad}", f"ancho_{unidad}", f"area_{unidad}2"])

    rastreador = Rastreador()
    total = 0
    t_prev = time.time()
    fps = 0.0

    print("Contando... Presiona Q para salir." if not args.sin_ventana else "Contando... Ctrl+C para salir.")
    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            frame = redimensionar(frame, args.ancho)
            alto, ancho = frame.shape[:2]
            x_linea = int(ancho * args.linea)

            dets, _ = detectar_huevos(frame, args.area_min, args.area_max, args.fondo_claro, args.umbral_min)
            objetos = rastreador.actualizar(dets)

            for oid, obj in objetos.items():
                if obj["contado"] or obj["perdido"] > 0:
                    continue
                x_ant = obj["centro_anterior"][0]
                x_act = obj["centro"][0]
                cruzo = (x_ant < x_linea <= x_act) if args.direccion == "derecha" else (x_ant > x_linea >= x_act)
                if cruzo:
                    obj["contado"] = True
                    total += 1
                    # Promedio de medidas a lo largo del recorrido (más estable)
                    largo = np.median([m["largo_px"] for m in obj["medidas"]])
                    anch = np.median([m["ancho_px"] for m in obj["medidas"]])
                    area = np.median([m["area_px"] for m in obj["medidas"]])
                    f = args.mm_por_pixel or 1.0
                    escritor.writerow([
                        datetime.now().isoformat(timespec="seconds"), total,
                        round(largo * f, 1), round(anch * f, 1), round(area * f * f, 1),
                    ])
                    archivo.flush()
                    if args.sin_ventana:
                        print(f"Huevo #{total}: largo={largo*f:.1f}{unidad} ancho={anch*f:.1f}{unidad}")

            # FPS
            ahora = time.time()
            fps = 0.9 * fps + 0.1 * (1.0 / max(ahora - t_prev, 1e-6))
            t_prev = ahora

            if not args.sin_ventana:
                cv2.line(frame, (x_linea, 0), (x_linea, alto), (0, 0, 255), 2)
                for d in dets:
                    cv2.ellipse(frame, d["elipse"], (0, 255, 0), 2)
                for oid, obj in objetos.items():
                    if obj["perdido"] == 0:
                        color = (255, 200, 0) if obj["contado"] else (0, 255, 255)
                        cv2.putText(frame, str(oid), obj["centro"], cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
                cv2.putText(frame, f"Total: {total}", (10, 35), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 2)
                cv2.putText(frame, f"FPS: {fps:.0f}", (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 1)
                cv2.imshow("Contador de huevos", frame)
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break
    except KeyboardInterrupt:
        pass
    finally:
        cap.release()
        archivo.close()
        cv2.destroyAllWindows()
        print(f"\nTotal contado: {total}. Registro guardado en {args.csv}")


def redimensionar(frame, ancho_objetivo):
    h, w = frame.shape[:2]
    if w <= ancho_objetivo:
        return frame
    escala = ancho_objetivo / w
    return cv2.resize(frame, (ancho_objetivo, int(h * escala)))


if __name__ == "__main__":
    main()
