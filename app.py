import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from io import BytesIO
import tempfile
import os
import json
import zipfile
from project_mapper_core import (
    analyze_project, format_size, download_from_url,
    compare_projects, generate_pdf_report
)

st.set_page_config(page_title="Project Mapper", page_icon="📂", layout="wide")

st.title("Project Mapper")
st.markdown("**Analiza la estructura, peso y distribucion de cualquier proyecto en segundos.**")

with st.sidebar:
    st.header("Configuracion")
    max_depth = st.slider("Profundidad del arbol", 1, 5, 3)
    st.markdown("---")
    st.markdown("### Como funciona")
    st.markdown("""
    1. Sube un ZIP.
    2. O usa una URL de Google Drive/Dropbox.
    3. O prueba con el ejemplo.
    4. Obtén informe y descarga PDF.
    """)
    st.markdown("---")
    st.markdown("### Comparativa")
    st.markdown("Sube dos proyectos y compara.")

tab1, tab2, tab3 = st.tabs(["Analisis", "Comparativa", "Remoto"])

with tab1:
    col1, col2 = st.columns(2)
    with col1:
        uploaded_file = st.file_uploader("Sube tu proyecto (ZIP)", type=['zip'], key="upload_analysis")
        if uploaded_file is not None:
            with st.spinner("Analizando..."):
                zip_bytes = uploaded_file.getvalue()
                with tempfile.TemporaryDirectory() as tmpdir:
                    with zipfile.ZipFile(BytesIO(zip_bytes), 'r') as zip_ref:
                        zip_ref.extractall(tmpdir)
                    items = os.listdir(tmpdir)
                    if len(items) == 1 and os.path.isdir(os.path.join(tmpdir, items[0])):
                        project_path = os.path.join(tmpdir, items[0])
                    else:
                        project_path = tmpdir
                    data = analyze_project(project_path, max_depth=max_depth)
                    st.session_state['data'] = data
                    st.success("Proyecto analizado")
    with col2:
        if st.button("Usar proyecto de ejemplo"):
            with st.spinner("Generando ejemplo..."):
                with tempfile.TemporaryDirectory() as tmpdir:
                    os.makedirs(os.path.join(tmpdir, 'src'), exist_ok=True)
                    os.makedirs(os.path.join(tmpdir, 'docs'), exist_ok=True)
                    with open(os.path.join(tmpdir, 'README.md'), 'w') as f:
                        f.write('# Ejemplo')
                    with open(os.path.join(tmpdir, 'src', 'main.py'), 'w') as f:
                        f.write('print("Hola")')
                    with open(os.path.join(tmpdir, 'docs', 'manual.pdf'), 'wb') as f:
                        f.write(b'%PDF-1.4%' + b'\x00' * 1024 * 100)
                    data = analyze_project(tmpdir, max_depth=max_depth)
                    st.session_state['data'] = data
                    st.success("Ejemplo cargado")

    if 'data' in st.session_state and 'error' not in st.session_state['data']:
        data = st.session_state['data']
        st.header("Informe")
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Carpetas", data['total_dirs'])
        col2.metric("Archivos", data['total_files'])
        col3.metric("Peso total", data['size_human'])
        col4.metric("Recomendacion", data['recommendation'])

        st.subheader("Distribucion por extension")
        ext_data = data['ext_distribution']
        if ext_data:
            df_ext = pd.DataFrame([
                {'Extension': ext, 'Archivos': info['count'], 'Tamano (KB)': info['size'] / 1024}
                for ext, info in ext_data.items()
            ]).sort_values('Tamano (KB)', ascending=False)
            fig = px.pie(df_ext, values='Tamano (KB)', names='Extension', title='Peso por extension')
            st.plotly_chart(fig, use_container_width=True)
            st.dataframe(df_ext, use_container_width=True)
        else:
            st.info("No se encontraron archivos con extensiones conocidas.")

        st.subheader("Estructura de carpetas")
        for path, content in data['structure'].items():
            display_path = path if path else '(raiz)'
            st.markdown(f"**{display_path}**")
            if content['dirs']:
                st.write(f"  Subcarpetas: {', '.join(content['dirs'])}")
            if content['files']:
                st.write(f"  Archivos: {', '.join(content['files'][:10])}{'...' if len(content['files']) > 10 else ''}")
            st.write("---")

        st.subheader("Descargar informe")
        col1, col2, col3 = st.columns(3)
        with col1:
            json_str = json.dumps(data, indent=2, default=str)
            st.download_button("JSON", json_str, "informe.json", "application/json")
        with col2:
            if st.button("Generar PDF"):
                with st.spinner("Generando PDF..."):
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_pdf:
                        generate_pdf_report(data, tmp_pdf.name)
                        with open(tmp_pdf.name, 'rb') as f:
                            pdf_bytes = f.read()
                        st.download_button("Descargar PDF", pdf_bytes, "informe.pdf", "application/pdf")
        with col3:
            lines = [
                f"Informe del proyecto",
                f"==================",
                f"",
                f"Total carpetas: {data['total_dirs']}",
                f"Total archivos: {data['total_files']}",
                f"Peso total: {data['size_human']}",
                f"Recomendacion: {data['recommendation']}",
                f"",
                f"Estructura:"
            ]
            for path, content in data['structure'].items():
                display_path = path if path else '(raiz)'
                lines.append(f"  {display_path}")
                if content['dirs']:
                    lines.append(f"    Subcarpetas: {', '.join(content['dirs'])}")
                if content['files']:
                    lines.append(f"    Archivos: {', '.join(content['files'][:10])}{'...' if len(content['files']) > 10 else ''}")
            txt_report = "\n".join(lines)
            st.download_button("TXT resumen", txt_report, "resumen.txt", "text/plain")

with tab2:
    st.header("Comparativa de proyectos")
    col1, col2 = st.columns(2)
    data1 = None; data2 = None
    with col1:
        uploaded1 = st.file_uploader("Proyecto 1", type=['zip'], key="comp1")
        if uploaded1 is not None:
            with st.spinner("Analizando..."):
                zip_bytes = uploaded1.getvalue()
                with tempfile.TemporaryDirectory() as tmpdir:
                    with zipfile.ZipFile(BytesIO(zip_bytes), 'r') as zip_ref:
                        zip_ref.extractall(tmpdir)
                    items = os.listdir(tmpdir)
                    if len(items) == 1 and os.path.isdir(os.path.join(tmpdir, items[0])):
                        project_path = os.path.join(tmpdir, items[0])
                    else:
                        project_path = tmpdir
                    data1 = analyze_project(project_path, max_depth=max_depth)
                    st.success("Proyecto 1 analizado")
    with col2:
        uploaded2 = st.file_uploader("Proyecto 2", type=['zip'], key="comp2")
        if uploaded2 is not None:
            with st.spinner("Analizando..."):
                zip_bytes = uploaded2.getvalue()
                with tempfile.TemporaryDirectory() as tmpdir:
                    with zipfile.ZipFile(BytesIO(zip_bytes), 'r') as zip_ref:
                        zip_ref.extractall(tmpdir)
                    items = os.listdir(tmpdir)
                    if len(items) == 1 and os.path.isdir(os.path.join(tmpdir, items[0])):
                        project_path = os.path.join(tmpdir, items[0])
                    else:
                        project_path = tmpdir
                    data2 = analyze_project(project_path, max_depth=max_depth)
                    st.success("Proyecto 2 analizado")

    if data1 and data2:
        diff = compare_projects(data1, data2)
        col1, col2, col3 = st.columns(3)
        col1.metric("Tamano Proyecto 1", data1['size_human'])
        col2.metric("Tamano Proyecto 2", data2['size_human'])
        diff_bytes = diff['size_diff']['diff_bytes']
        diff_text = f"{abs(diff_bytes) / (1024*1024):.2f} MB"
        if diff_bytes > 0:
            col3.metric("Diferencia", diff_text, "Proyecto 1 es mayor")
        elif diff_bytes < 0:
            col3.metric("Diferencia", diff_text, "Proyecto 2 es mayor")
        else:
            col3.metric("Diferencia", "0 MB", "Iguales")

        st.write("**Archivos:**")
        st.write(f"Proyecto 1: {data1['total_files']} archivos, Proyecto 2: {data2['total_files']} archivos")
        
        st.write("**Distribucion de extensiones (comparativa):**")
        ext1 = data1['ext_distribution']; ext2 = data2['ext_distribution']
        all_exts = set(ext1.keys()) | set(ext2.keys())
        comp_data = []
        for ext in all_exts:
            size1 = ext1.get(ext, {}).get('size', 0)
            size2 = ext2.get(ext, {}).get('size', 0)
            comp_data.append({'Extension': ext, 'Proyecto1 (KB)': size1/1024, 'Proyecto2 (KB)': size2/1024})
        df_comp = pd.DataFrame(comp_data)
        st.dataframe(df_comp, use_container_width=True)

        fig = go.Figure()
        fig.add_trace(go.Bar(x=df_comp['Extension'], y=df_comp['Proyecto1 (KB)'], name='Proyecto 1'))
        fig.add_trace(go.Bar(x=df_comp['Extension'], y=df_comp['Proyecto2 (KB)'], name='Proyecto 2'))
        fig.update_layout(barmode='group', title='Comparativa de tamano por extension (KB)')
        st.plotly_chart(fig, use_container_width=True)

with tab3:
    st.header("Analizar desde URL remota")
    remote_url = st.text_input("URL del ZIP (Google Drive / Dropbox)")
    if st.button("Descargar y analizar"):
        if remote_url:
            with st.spinner("Descargando..."):
                try:
                    content = download_from_url(remote_url)
                    with tempfile.TemporaryDirectory() as tmpdir:
                        zip_path = os.path.join(tmpdir, 'project.zip')
                        with open(zip_path, 'wb') as f:
                            f.write(content)
                        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                            zip_ref.extractall(tmpdir)
                        items = os.listdir(tmpdir)
                        if len(items) == 1 and os.path.isdir(os.path.join(tmpdir, items[0])):
                            project_path = os.path.join(tmpdir, items[0])
                        else:
                            project_path = tmpdir
                        data = analyze_project(project_path, max_depth=max_depth)
                        st.session_state['data'] = data
                        st.success("Proyecto analizado")
                except Exception as e:
                    st.error(f"Error: {e}")
        else:
            st.warning("Introduce una URL.")

    if 'data' in st.session_state and 'error' not in st.session_state['data']:
        st.info("Los resultados se muestran en la pestaña 'Analisis'.")

st.markdown("---")
st.caption("Desarrollado por Jose Luis Asenjo")
