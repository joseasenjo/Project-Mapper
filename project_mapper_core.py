import os
import json
from collections import defaultdict
from pathlib import Path

def analyze_project(root_path, max_depth=3):
    """
    Analiza un proyecto y devuelve un diccionario con:
    - total_size (bytes)
    - total_files, total_dirs
    - ext_distribution: {ext: {'count': n, 'size': bytes}}
    - structure: {path: {'dirs': [...], 'files': [...]}}
    - recommendation: str
    """
    if not os.path.isdir(root_path):
        return {'error': f'La ruta {root_path} no es válida'}

    total_size = 0
    total_files = 0
    total_dirs = 0
    ext_count = defaultdict(int)
    ext_size = defaultdict(int)
    structure = {}

    for dirpath, dirnames, filenames in os.walk(root_path):
        # Excluir carpetas ocultas (opcional)
        # dirnames[:] = [d for d in dirnames if not d.startswith('.')]
        rel_path = os.path.relpath(dirpath, root_path)
        if rel_path == '.':
            rel_path = ''
        depth = rel_path.count(os.sep) if rel_path else 0
        if depth > max_depth:
            continue
        total_dirs += 1
        structure[rel_path] = {'dirs': dirnames, 'files': filenames}
        for f in filenames:
            fp = os.path.join(dirpath, f)
            if os.path.exists(fp):
                size = os.path.getsize(fp)
                total_size += size
                total_files += 1
                ext = os.path.splitext(f)[1].lower() or 'sin_ext'
                ext_count[ext] += 1
                ext_size[ext] += size

    # Recomendación
    size_mb = total_size / (1024 * 1024)
    if size_mb < 10:
        rec = 'Muy ligero (<10 MB)'
    elif size_mb < 100:
        rec = 'Ligero (10-100 MB)'
    elif size_mb < 1024:
        rec = 'Moderado (100 MB - 1 GB)'
    else:
        rec = 'Pesado (>1 GB). Considera optimizar.'

    return {
        'total_size': total_size,
        'total_files': total_files,
        'total_dirs': total_dirs,
        'ext_distribution': {ext: {'count': ext_count[ext], 'size': ext_size[ext]} for ext in ext_count},
        'structure': structure,
        'recommendation': rec,
        'size_human': format_size(total_size),
        'max_depth': max_depth
    }

def format_size(size_bytes):
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} TB"
