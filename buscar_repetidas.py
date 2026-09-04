# -*- coding: utf-8 -*-
"""
Busca fotos y videos REPETIDOS (archivos idénticos, aunque tengan
distinto nombre, tipo "foto - Copia.jpg").

Uso:
  1) python buscar_repetidas.py           -> solo muestra el informe, no borra nada
  2) python buscar_repetidas.py --mover   -> mueve las repetidas a la carpeta "_repetidas"

Nunca borra archivos: las mueve, para que puedas revisarlas antes.
"""
import os
import sys
import hashlib
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CUARENTENA = ROOT / "_repetidas"

EXT = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp', '.heic',
       '.mp4', '.mov', '.avi', '.mkv', '.webm', '.m4v'}

SKIP_DIRS = {'System Volume Information', '$RECYCLE.BIN', 'miniaturas',
             'portada', '_repetidas', '.git'}


def firma(path, bloque=1024 * 1024):
    """Huella del contenido del archivo."""
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        while True:
            datos = f.read(bloque)
            if not datos:
                break
            h.update(datos)
    return h.hexdigest()


def main():
    mover = '--mover' in sys.argv
    vistos = {}
    repetidas = []

    def prioridad(nombre):
        """Los nombres 'limpios' se revisan primero, para conservarlos a ellos
        y marcar como repetidas las versiones '- Copia', '(1)', etc."""
        bajo = nombre.lower()
        sucio = ('copia' in bajo or 'copy' in bajo or '(1)' in bajo
                 or '(2)' in bajo or '(3)' in bajo)
        return (1 if sucio else 0, len(nombre), nombre)

    for carpeta, subdirs, archivos in os.walk(ROOT):
        subdirs[:] = [d for d in subdirs if d not in SKIP_DIRS and not d.startswith('.')]
        for nombre in sorted(archivos, key=prioridad):
            ruta = Path(carpeta) / nombre
            if ruta.suffix.lower() not in EXT:
                continue
            try:
                clave = (ruta.stat().st_size, firma(ruta))
            except OSError:
                continue
            if clave in vistos:
                repetidas.append((ruta, vistos[clave]))
            else:
                vistos[clave] = ruta

    if not repetidas:
        print("No se encontraron archivos repetidos.")
        input("Presiona ENTER para salir...")
        return

    total_mb = sum(r.stat().st_size for r, _ in repetidas) / (1024 * 1024)
    print(f"Se encontraron {len(repetidas)} archivos repetidos ({total_mb:.1f} MB).\n")
    for repetida, original in repetidas:
        print(f"  REPETIDA: {repetida.relative_to(ROOT)}")
        print(f"  copia de: {original.relative_to(ROOT)}\n")

    if not mover:
        print("Esto fue solo un informe, no se movio nada.")
        print('Para moverlas a la carpeta "_repetidas", ejecuta:')
        print("   python buscar_repetidas.py --mover")
    else:
        CUARENTENA.mkdir(exist_ok=True)
        movidos = 0
        for repetida, _ in repetidas:
            destino = CUARENTENA / repetida.relative_to(ROOT)
            destino.parent.mkdir(parents=True, exist_ok=True)
            try:
                shutil.move(str(repetida), str(destino))
                movidos += 1
            except OSError as e:
                print(f"No se pudo mover {repetida.name}: {e}")
        print(f"\nListo. Se movieron {movidos} archivos a la carpeta '_repetidas'.")
        print("Revisalos y, si estas de acuerdo, borra esa carpeta.")
        print("Despues vuelve a ejecutar 'Actualizar Galeria'.")

    input("\nPresiona ENTER para salir...")


if __name__ == '__main__':
    main()
