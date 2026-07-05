# 📂 Project Mapper

[![Streamlit App](https://img.shields.io/badge/Deployed%20on-Streamlit%20Cloud-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)](https://project-mapper.streamlit.app)
[![License](https://img.shields.io/github/license/joseasenjo/project-mapper)](https://github.com/joseasenjo/project-mapper/blob/main/LICENSE)
[![Python Version](https://img.shields.io/badge/Python-3.9%2B-blue)](https://www.python.org/downloads/)
[![GitHub stars](https://img.shields.io/github/stars/joseasenjo/project-mapper)](https://github.com/joseasenjo/project-mapper/stargazers)
[![GitHub forks](https://img.shields.io/github/forks/joseasenjo/project-mapper)](https://github.com/joseasenjo/project-mapper/network)

**Project Mapper** es una herramienta de análisis de proyectos que te permite escanear cualquier carpeta y obtener un informe detallado de su estructura, peso y distribución de archivos. Ideal para desarrolladores, gestores de proyectos y equipos de infraestructura.

---

## 🚀 Características

- **Análisis local**: Sube un archivo ZIP de tu proyecto o usa el proyecto de ejemplo integrado.
- **Análisis remoto**: Proporciona un enlace de Google Drive o Dropbox para analizar proyectos alojados en la nube.
- **Informes detallados**: Obtén métricas como:
  - Número de carpetas y archivos.
  - Peso total del proyecto.
  - Distribución de tamaño por extensión de archivo.
  - Estructura de carpetas (árbol de directorios).
  - Recomendación de infraestructura (VPS) basada en el tamaño total.
- **Comparativa de proyectos**: Sube dos proyectos y compara sus métricas lado a lado.
- **Exportación de informes**:
  - **JSON**: Para integración con otras herramientas.
  - **PDF**: Informe profesional generado con ReportLab.
  - **TXT**: Resumen en texto plano.
- **Tema oscuro personalizado** con acentos dorados, coherente con la identidad visual del autor.

---

## 🛠️ Stack Tecnológico

| Tecnología | Propósito |
|------------|-----------|
| [Streamlit](https://streamlit.io/) | Framework para la interfaz de usuario. |
| [Pandas](https://pandas.pydata.org/) | Manipulación de datos para las tablas. |
| [Plotly](https://plotly.com/) | Gráficos interactivos para visualizar distribuciones. |
| [ReportLab](https://www.reportlab.com/) | Generación de informes en PDF. |
| [gdown](https://github.com/wkentaro/gdown) | Descarga de archivos desde Google Drive. |
| [requests](https://docs.python-requests.org/) | Descarga de archivos desde Dropbox y URLs genéricas. |

---

## 📦 Instalación

Para ejecutar Project Mapper localmente:

```bash
# Clona el repositorio
git clone https://github.com/joseasenjo/project-mapper.git
cd project-mapper

# Instala las dependencias
pip install -r requirements.txt

# Ejecuta la aplicación
streamlit run app.py
