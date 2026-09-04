# -*- coding: utf-8 -*-
"""
Escanea las carpetas de fotos, genera miniaturas livianas (para que la
galería cargue rápido) y escribe galeria-datos.js con la lista completa.

Se ejecuta con: python generar_datos.py
(o con "Actualizar Galeria.bat", que hace lo mismo con doble clic)

Requiere la librería Pillow:  pip install Pillow
"""
import os
import sys
import json
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    print("Falta la libreria Pillow. Instalala con:  pip install Pillow")
    input("Presiona ENTER para salir...")
    sys.exit(1)

ROOT = Path(__file__).resolve().parent
THUMBS_DIR = ROOT / "miniaturas"
THUMB_MAX_W = 380
THUMB_QUALITY = 72

IMG_EXT = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp', '.heic'}
VID_EXT = {'.mp4', '.mov', '.avi', '.mkv', '.webm', '.m4v'}

# Carpetas/archivos que NUNCA se deben escanear (basura del sistema operativo,
# o archivos propios de este programa). Antes esto hacia que el script se
# cayera sin avisar cuando la USB tenia "System Volume Information".
SKIP_NAMES = {
    'System Volume Information', '$RECYCLE.BIN', 'miniaturas', 'portada',
    'Thumbs.db', 'desktop.ini', 'galeria-datos.js', '.Trashes',
    '.Spotlight-V100', '.fseventsd',
}
SKIP_SUFFIXES = {'.bat', '.ps1', '.py'}


def is_skippable(name):
    if name in SKIP_NAMES:
        return True
    if name.startswith('.'):
        return True
    if Path(name).suffix.lower() in SKIP_SUFFIXES:
        return True
    if name.lower() == 'galeria jac.html':
        return True
    return False


def make_thumb(src_path, rel_path):
    """Crea (si hace falta) una miniatura liviana y devuelve su ruta relativa."""
    thumb_path = (THUMBS_DIR / rel_path).with_suffix('.jpg')
    try:
        if thumb_path.exists() and thumb_path.stat().st_mtime >= src_path.stat().st_mtime:
            return 'miniaturas/' + str(thumb_path.relative_to(THUMBS_DIR)).replace('\\', '/')
        thumb_path.parent.mkdir(parents=True, exist_ok=True)
        with Image.open(src_path) as img:
            img = img.convert('RGB')
            w, h = img.size
            if w > THUMB_MAX_W:
                new_h = max(1, int(h * (THUMB_MAX_W / w)))
                img = img.resize((THUMB_MAX_W, new_h), Image.LANCZOS)
            img.save(thumb_path, 'JPEG', quality=THUMB_QUALITY, optimize=True)
        return 'miniaturas/' + str(thumb_path.relative_to(THUMBS_DIR)).replace('\\', '/')
    except Exception:
        # Si una foto especifica no se puede abrir (formato raro, dañada, etc.)
        # simplemente se usa la original en su lugar, sin detener todo el proceso.
        return None


def build_tree(path, rel_prefix=''):
    folders = {}
    files = []
    try:
        entries = sorted(os.scandir(path), key=lambda e: e.name.lower())
    except (PermissionError, OSError):
        return {'folders': folders, 'files': files}

    for entry in entries:
        if is_skippable(entry.name):
            continue
        try:
            if entry.is_dir():
                child_rel = f"{rel_prefix}/{entry.name}" if rel_prefix else entry.name
                folders[entry.name] = build_tree(Path(entry.path), child_rel)
            else:
                ext = Path(entry.name).suffix.lower()
                rel_path = f"{rel_prefix}/{entry.name}" if rel_prefix else entry.name
                if ext in IMG_EXT:
                    thumb = make_thumb(Path(entry.path), rel_path)
                    item = {'name': entry.name, 'type': 'image', 'path': rel_path}
                    if thumb:
                        item['thumb'] = thumb
                    files.append(item)
                elif ext in VID_EXT:
                    files.append({'name': entry.name, 'type': 'video', 'path': rel_path})
        except (PermissionError, OSError):
            continue
    return {'folders': folders, 'files': files}


def make_icon_from_logo(root):
    """Busca un archivo cuyo nombre contenga 'logo' y genera Logo.ico
    para poder usarlo como icono del acceso directo del escritorio."""
    logo_path = None
    for entry in root.rglob('*'):
        if entry.is_file() and 'logo' in entry.name.lower() and entry.suffix.lower() in IMG_EXT:
            logo_path = entry
            break
    if not logo_path:
        return
    try:
        with Image.open(logo_path) as img:
            img = img.convert('RGBA')
            sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
            img.save(root / 'Logo.ico', format='ICO', sizes=sizes)
    except Exception:
        pass


def main():
    print("Escaneando carpetas y generando miniaturas, un momento...")
    tree = build_tree(ROOT)
    js = "window.GALERIA_DATA = " + json.dumps(tree, ensure_ascii=False) + ";"
    (ROOT / 'galeria-datos.js').write_text(js, encoding='utf-8')
    make_icon_from_logo(ROOT)
    print("Listo. galeria-datos.js actualizado y miniaturas en la carpeta miniaturas")


if __name__ == '__main__':
    main()
