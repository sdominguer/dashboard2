import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
from groq import Groq
import io
from office365.sharepoint.client_context import ClientContext
from office365.runtime.auth.user_credential import UserCredential

# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Auditoría Pro: Operaciones & IA", layout="wide", page_icon="🌙")

# --- 2. CSS (Mantenido según tu diseño) ---
st.markdown("""
    <style>
    .stApp { background-color: #0E1117; color: #FFFFFF; }
    h1, h2, h3, h4, p, span, label { color: #FFFFFF !important; }
    .ai-container { background-color: #161B22; border-radius: 12px; padding: 25px; border-left: 5px solid #1E88E5; margin-top: 15px; }
    </style>
""", unsafe_allow_html=True)

# --- 3. LÓGICA DE CONEXIÓN Y PROCESAMIENTO ---

@st.cache_data
def get_sp_dataframe(server_relative_url):
    """Lee un archivo de SharePoint y devuelve un DataFrame independiente."""
    try:
        ctx = ClientContext(st.secrets["https://eafit.sharepoint.com/sites/Section_1709_2661"]).with_credentials(
            UserCredential(st.secrets["dagomezm3"], st.secrets["Keops71*"])
        )
        response = ctx.web.get_file_by_server_relative_url(server_relative_url).execute_query()
        df = pd.read_csv(io.BytesIO(response.content))
        
        # Limpieza básica de tu lógica original
        cols_num = ['Precio_Venta_Final', 'Costo_Unitario_USD', 'Cantidad_Vendida', 'Costo_Envio', 'Satisfaccion_NPS', 'Stock_Actual']
        for col in cols_num:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        
        # Crear copia editable
        return df.copy()
    except Exception as e:
        st.error(f"Error en archivo {server_relative_url}: {e}")
        return pd.DataFrame()

# --- 4. CARGA INTERNA DE LOS 3 DATAFRAMES ---

# Define aquí tus 3 rutas de SharePoint
URL_FILE_1 = "https://eafit.sharepoint.com/sites/Section_1709_2661/Documentos%20compartidos/General/feedback_clientes_v2.csv?web=1"
URL_FILE_2 = "https://eafit.sharepoint.com/sites/Section_1709_2661/Documentos%20compartidos/General/transacciones_logistica_v2.csv?web=1"
URL_FILE_3 = "https://eafit.sharepoint.com/sites/Section_1709_2661/Documentos%20compartidos/General/inventario_central_v2.csv?web=1"

# Creación de los 3 DataFrames independientes
df_sp_1 = get_sp_dataframe(URL_FILE_1)
df_sp_2 = get_sp_dataframe(URL_FILE_2)
df_sp_3 = get_sp_dataframe(URL_FILE_3)

# --- 5. SIDEBAR (PARA CARGA EXTERNA) ---
with st.sidebar:
    st.title("🚜 Operaciones Pro")
    groq_key = st.text_input("Groq API Key", type="password")
    
    st.divider()
    uploaded_file = st.file_uploader("📂 Cargar Archivo Externo (Adicional)", type=["csv"])
    
    df_externo = pd.DataFrame()
    if uploaded_file:
        df_externo = pd.read_csv(uploaded_file)
        st.success("Archivo externo cargado")

# --- 6. DASHBOARD Y VISUALIZACIÓN ---
st.title("📊 Auditoría Multifuente")

# Selector para decidir qué DataFrame trabajar en el Dashboard
opcion = st.selectbox("Seleccione la fuente de datos a analizar:", 
                     ["SharePoint - Archivo 1", "SharePoint - Archivo 2", "SharePoint - Archivo 3", "Archivo Externo"])

# Asignar el DataFrame seleccionado a la variable 'df' que usa tu lógica original
if opcion == "SharePoint - Archivo 1":
    df_raw = df_sp_1
elif opcion == "SharePoint - Archivo 2":
    df_raw = df_sp_2
elif opcion == "SharePoint - Archivo 3":
    df_raw = df_sp_3
else:
    df_raw = df_externo

# --- LÓGICA ORIGINAL DE FILTROS Y GRÁFICOS ---
if not df_raw.empty:
    # (Aquí sigue el resto de tu código: filtros por categoría, tabs, métricas e IA)
    # Ejemplo rápido de integración con tu lógica:
    if 'Categoria' in df_raw.columns:
        all_cats = sorted(df_raw['Categoria'].unique())
        sel_cats = st.multiselect("Categorías", all_cats, default=all_cats)
        df = df_raw[df_raw['Categoria'].isin(sel_cats)]
        
        st.write(f"Analizando: {opcion}")
        st.dataframe(df.head()) # Muestra el DF editable seleccionado
        
        # ... Aquí insertas tus TABS y lógica de Groq ...
else:
    st.warning("La fuente seleccionada está vacía o no se ha cargado.")
