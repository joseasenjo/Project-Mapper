import os
import json
import tempfile
import zipfile
from collections import defaultdict
from pathlib import Path
import requests
import gdown
import io
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT
import time

def analyze_project(root_path, max_depth=3):
    """
    Analiza un proyecto y devuelve un diccionario con:
    - total_size (bytes), total_files, total_dirs
    - ext_distribution: {ext: {'count': n, 'size': bytes}}
    - structure: {path: {'dirs': [...], 'files': [...]}}
    - recommendation: str
    - size_human: str
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

def extract_zip_from_bytes(zip_bytes):
    """Extrae un archivo ZIP desde bytes y devuelve la ruta temporal."""
    with tempfile.TemporaryDirectory() as tmpdir:
        with zipfile.ZipFile(io.BytesIO(zip_bytes), 'r') as zip_ref:
            zip_ref.extractall(tmpdir)
        # Buscar la carpeta raíz si hay una sola
        items = os.listdir(tmpdir)
        if len(items) == 1 and os.path.isdir(os.path.join(tmpdir, items[0])):
            return os.path.join(tmpdir, items[0])
        else:
            return tmpdir

def download_from_google_drive(url):
    """Descarga un archivo desde Google Drive usando gdown y devuelve el contenido en bytes."""
    try:
        # Extraer el ID del archivo de la URL
        if 'drive.google.com' in url:
            import re
            match = re.search(r'/d/([a-zA-Z0-9_-]+)', url)
            if match:
                file_id = match.group(1)
                output = tempfile.NamedTemporaryFile(delete=False, suffix='.zip')
                gdown.download(id=file_id, output=output.name, quiet=True)
                with open(output.name, 'rb') as f:
                    content = f.read()
                os.unlink(output.name)
                return content
            else:
                raise ValueError("No se pudo extraer el ID del archivo de Google Drive")
        else:
            # Si es un enlace directo (posible)
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            return response.content
    except Exception as e:
        raise Exception(f"Error al descargar de Google Drive: {e}")

def download_from_dropbox(url):
    """Descarga un archivo desde Dropbox (enlace compartido) y devuelve el contenido en bytes."""
    try:
        # Convertir enlace compartido a descarga directa
        if 'dropbox.com' in url:
            if '?dl=0' in url:
                url = url.replace('?dl=0', '?dl=1')
            elif '?dl=' not in url:
                url += '?dl=1'
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        return response.content
    except Exception as e:
        raise Exception(f"Error al descargar de Dropbox: {e}")

def download_from_url(url):
    """Detecta el tipo de URL y descarga el contenido."""
    if 'drive.google.com' in url:
        return download_from_google_drive(url)
    elif 'dropbox.com' in url:
        return download_from_dropbox(url)
    else:
        # Intenta descargar directamente
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        return response.content

def compare_projects(data1, data2):
    """Compara dos proyectos y devuelve un diccionario con diferencias."""
    diff = {}
    # Comparar tamaño
    diff['size_diff'] = {
        'project1': data1['size_human'],
        'project2': data2['size_human'],
        'diff_bytes': data1['total_size'] - data2['total_size']
    }
    # Comparar número de archivos
    diff['files_diff'] = {
        'project1': data1['total_files'],
        'project2': data2['total_files'],
        'diff': data1['total_files'] - data2['total_files']
    }
    # Comparar distribución de extensiones (top 5)
    ext1 = data1['ext_distribution']
    ext2 = data2['ext_distribution']
    all_exts = set(ext1.keys()) | set(ext2.keys())
    ext_diff = {}
    for ext in all_exts:
        size1 = ext1.get(ext, {}).get('size', 0)
        size2 = ext2.get(ext, {}).get('size', 0)
        if size1 != size2:
            ext_diff[ext] = {'size1': size1, 'size2': size2}
    diff['ext_diff'] = ext_diff
    return diff

def generate_pdf_report(data, filename="informe.pdf"):
    """Genera un informe en PDF a partir de los datos del proyecto."""
    doc = SimpleDocTemplate(filename, pagesize=letter,
                            rightMargin=72, leftMargin=72,
                            topMargin=72, bottomMargin=72)
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('Title', parent=styles['Heading1'], alignment=TA_CENTER, fontSize=24)
    heading_style = ParagraphStyle('Heading', parent=styles['Heading2'], fontSize=16, textColor=colors.darkblue)
    normal_style = styles['Normal']
    
    story = []

    # Título
    story.append(Paragraph("Informe de Análisis de Proyecto", title_style))
    story.append(Spacer(1, 0.25*inch))

    # Metadatos
    story.append(Paragraph("Resumen", heading_style))
    story.append(Paragraph(f"Total carpetas: {data['total_dirs']}", normal_style))
    story.append(Paragraph(f"Total archivos: {data['total_files']}", normal_style))
    story.append(Paragraph(f"Peso total: {data['size_human']}", normal_style))
    story.append(Paragraph(f"Recomendación: {data['recommendation']}", normal_style))
    story.append(Spacer(1, 0.2*inch))

    # Distribución por extensión (tabla)
    story.append(Paragraph("Distribución por extensión", heading_style))
    table_data = [['Extensión', 'Cantidad', 'Tamaño']]
    for ext, info in sorted(data['ext_distribution'].items(), key=lambda x: x[1]['size'], reverse=True)[:10]:
        table_data.append([ext, str(info['count']), format_size(info['size'])])
    table = Table(table_data, colWidths=[2*inch, 1*inch, 2*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.grey),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0,0), (-1,0), 12),
        ('BACKGROUND', (0,1), (-1,-1), colors.beige),
        ('GRID', (0,0), (-1,-1), 1, colors.black),
    ]))
    story.append(table)
    story.append(Spacer(1, 0.2*inch))

    # Estructura de carpetas (texto simple)
    story.append(Paragraph("Estructura de carpetas", heading_style))
    for path, content in data['structure'].items():
        display_path = path if path else '(raíz)'
        story.append(Paragraph(f"<b>{display_path}</b>", normal_style))
        if content['dirs']:
            story.append(Paragraph(f"Subcarpetas: {', '.join(content['dirs'])}", normal_style))
        if content['files']:
            story.append(Paragraph(f"Archivos: {', '.join(content['files'][:10])}{'...' if len(content['files']) > 10 else ''}", normal_style))
        story.append(Spacer(1, 0.1*inch))

    doc.build(story)
