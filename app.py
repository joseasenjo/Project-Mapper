import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from io import BytesIO
import zipfile
import tempfile
import os
import json
from project_mapper_core import analyze_project, format_size

st.set_page_config(page_title="Project Mapper", page_icon="📂", layout="wide")

st.title("📂 Project Mapper")
st.markdown("**Analiza la estructura, peso y distribución de cualquier proyecto en segundos.**")

# Sidebar
with st.sidebar:
    st.header("⚙️ Configuración")
    max_depth = st.slider("Profundidad del árbol", 1, 5, 3, help="Niveles de carpetas a mostrar")
    st.markdown("---")
    st.markdown("### ¿Cómo funciona?")
    st.markdown("""
    1. Sube un archivo ZIP de tu proyecto.
    2. O usa el proyecto de ejemplo para probar.
    3. Obtén un informe completo con gráficos.
    """)

# Opciones de entrada
col1, col2 = st.columns(2)

with col1:
    uploaded_file = st.file_uploader("📤 Sube tu proyecto (ZIP)", type=['zip'])
    if uploaded_file is not None:
        with tempfile.TemporaryDirectory() as tmpdir:
            with zipfile.ZipFile(uploaded_file, 'r') as zip_ref:
                zip_ref.extractall(tmpdir)
            # El proyecto se ha extraído en tmpdir, pero puede tener una carpeta raíz adicional
            # Buscamos la primera carpeta que contenga archivos
            items = os.listdir(tmpdir)
            if len(items) == 1 and os.path.isdir(os.path.join(tmpdir, items[0])):
                project_path = os.path.join(tmpdir, items[0])
            else:
                project_path = tmpdir
            data = analyze_project(project_path, max_depth=max_depth)
            st.session_state['data'] = data
            st.success("✅ Proyecto analizado correctamente")

with col2:
    if st.button("📁 Usar proyecto de ejemplo"):
        # Creamos una estructura de ejemplo en memoria
        with tempfile.TemporaryDirectory() as tmpdir:
            # Crear algunos archivos y carpetas de ejemplo
            os.makedirs(os.path.join(tmpdir, 'src'), exist_ok=True)
            os.makedirs(os.path.join(tmpdir, 'docs'), exist_ok=True)
            with open(os.path.join(tmpdir, 'README.md'), 'w') as f:
                f.write('# Proyecto de ejemplo')
            with open(os.path.join(tmpdir, 'src', 'main.py'), 'w') as f:
                f.write('print("Hola mundo")')
            with open(os.path.join(tmpdir, 'src', 'utils.py'), 'w') as f:
                f.write('# utilidades')
            with open(os.path.join(tmpdir, 'docs', 'manual.pdf'), 'wb') as f:
                f.write(b'%PDF-1.4%' + b'\x00' * 1024 * 100)  # 100 KB de PDF falso
            data = analyze_project(tmpdir, max_depth=max_depth)
            st.session_state['data'] = data
            st.success("✅ Proyecto de ejemplo cargado")

# Mostrar resultados si existen
if 'data' in st.session_state and 'error' not in st.session_state['data']:
    data = st.session_state['data']
    st.header("📊 Informe del Proyecto")
    
    # Métricas generales
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("📁 Carpetas", data['total_dirs'])
    col2.metric("📄 Archivos", data['total_files'])
    col3.metric("💾 Peso total", data['size_human'])
    col4.metric("📊 Recomendación", data['recommendation'])

    # Distribución por extensión (gráfico)
    st.subheader("📂 Distribución por extensión")
    ext_data = data['ext_distribution']
    if ext_data:
        df_ext = pd.DataFrame([
            {'Extensión': ext, 'Archivos': info['count'], 'Tamaño (KB)': info['size'] / 1024}
            for ext, info in ext_data.items()
        ]).sort_values('Tamaño (KB)', ascending=False)
        fig = px.pie(df_ext, values='Tamaño (KB)', names='Extensión', title='Peso por extensión')
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(df_ext, use_container_width=True)
    else:
        st.info("No se encontraron archivos con extensiones conocidas.")

    # Estructura de carpetas
    st.subheader("📁 Estructura de carpetas")
    structure = data['structure']
    for path, content in structure.items():
        display_path = path if path else '📂 (raíz)'
        st.markdown(f"**{display_path}**")
        if content['dirs']:
            st.write(f"  📁 Subcarpetas: {', '.join(content['dirs'])}")
        if content['files']:
            st.write(f"  📄 Archivos: {', '.join(content['files'][:10])}{'...' if len(content['files']) > 10 else ''}")
        st.write("---")

    # Exportar informe
    st.subheader("📥 Descargar informe")
    col1, col2 = st.columns(2)
    with col1:
        # Descargar JSON
        json_str = json.dumps(data, indent=2, default=str)
        st.download_button(
            label="📄 Descargar JSON",
            data=json_str,
            file_name="informe_proyecto.json",
            mime="application/json"
        )
    with col2:
        # Generar informe en PDF (usando reportlab o fpdf sería más complejo, lo dejamos como descarga de texto)
        # Por simplicidad, generamos un archivo de texto con el resumen
        lines = [
            f"Informe del proyecto",
            f"==================",
            f"",
            f"Total carpetas: {data['total_dirs']}",
            f"Total archivos: {data['total_files']}",
            f"Peso total: {data['size_human']}",
            f"Recomendación: {data['recommendation']}",
            f"",
            f"Estructura:"
        ]
        for path, content in data['structure'].items():
            display_path = path if path else '(raíz)'
            lines.append(f"  {display_path}")
            if content['dirs']:
                lines.append(f"    Subcarpetas: {', '.join(content['dirs'])}")
            if content['files']:
                lines.append(f"    Archivos: {', '.join(content['files'][:10])}{'...' if len(content['files']) > 10 else ''}")
        text_report = "\n".join(lines)
        st.download_button(
            label="📝 Descargar TXT resumen",
            data=text_report,
            file_name="resumen_proyecto.txt",
            mime="text/plain"
        )

elif 'data' in st.session_state and 'error' in st.session_state['data']:
    st.error(f"❌ Error: {st.session_state['data']['error']}")

st.markdown("---")
st.caption("Desarrollado por [Jose Luis Asenjo](https://joseasenjo.github.io/portfolio/)")
