import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
from groq import Groq

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Executive Logistics Dash", layout="wide", page_icon="📈")

# --- CSS PERSONALIZADO (MÉTRICAS SIN FONDO Y ESTILO LIMPIO) ---
st.markdown("""
    <style>
    /* Fondo general de la app */
    .stApp { background-color: #F8F9FA; }

    /* Quitar fondo blanco y bordes a las métricas para que sean transparentes */
    div[data-testid="metric-container"] {
        background-color: rgba(0,0,0,0) !important;
        border: none !important;
        box-shadow: none !important;
        padding: 0px !important;
    }
    
    /* Ajuste de fuentes para métricas */
    [data-testid="stMetricValue"] { font-size: 28px !important; color: #1e40af !important; }
    [data-testid="stMetricLabel"] { font-size: 16px !important; color: #4b5563 !important; }

    /* Tabs minimalistas */
    .stTabs [data-baseweb="tab-list"] { gap: 24px; border-bottom: 1px solid #E0E0E0; }
    .stTabs [aria-selected="true"] p { color: #1e40af !important; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

# --- CARGA Y PROCESAMIENTO ---
@st.cache_data
def process_data(file):
    df = pd.read_csv(file)
    cols = ['Precio_Venta_Final', 'Costo_Unitario_USD', 'Cantidad_Vendida', 'Costo_Envio', 'Satisfaccion_NPS']
    for col in cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    
    df['Utilidad_Total'] = (df['Precio_Venta_Final'] * df['Cantidad_Vendida']) - \
                           (df['Costo_Unitario_USD'] * df['Cantidad_Vendida']) - \
                           df['Costo_Envio']
    return df

# --- SIDEBAR ---
with st.sidebar:
    st.title("🚜 Panel de Control")
    
    # SECCIÓN API KEY (Reintegrada)
    with st.expander("🔑 Configuración IA", expanded=True):
        st.markdown("Ingresa tu clave para activar el análisis inteligente.")
        groq_api_key = st.text_input("Groq API Key", type="password")
        st.caption("[Consigue tu Key aquí](https://console.groq.com)")

    st.divider()
    uploaded_file = st.file_uploader("📂 Subir CSV Consolidado", type=["csv"])
    
    if uploaded_file:
        df_raw = process_data(uploaded_file)
        st.subheader("Filtros")
        
        # Filtro de Categoría
        cats = sorted(df_raw['Categoria'].unique())
        sel_cats = st.multiselect("Categorías", cats, default=cats)
        
        # Slider de cantidad de datos
        n_registros = st.slider("Registros a analizar", 10, len(df_raw), 500)

# --- CUERPO PRINCIPAL ---
if uploaded_file:
    # Aplicar filtros y límite del slider
    df = df_raw[df_raw['Categoria'].isin(sel_cats)].head(n_registros)

    st.title("📊 Intelligence Business Dashboard")
    st.markdown(f"**Análisis actual:** {n_registros} registros filtrados por categoría.")

    # --- SECCIÓN CUANTITATIVA (Métricas Transparentes) ---
    st.markdown("###")
    m1, m2, m3, m4 = st.columns(4)
    
    revenue = df['Precio_Venta_Final'].sum()
    profit = df['Utilidad_Total'].sum()
    margin = (profit / revenue * 100) if revenue != 0 else 0
    
    m1.metric("Ingresos", f"${revenue:,.0f}")
    m2.metric("Utilidad", f"${profit:,.0f}", delta=f"{margin:.1f}%")
    m3.metric("NPS Mediano", f"{df[df['Satisfaccion_NPS']>0]['Satisfaccion_NPS'].median():.1f}")
    m4.metric("Unidades", f"{df['Cantidad_Vendida'].sum():,.0f}")

    st.markdown("###")

    # --- SECCIÓN IA ---
    if groq_api_key:
        with st.container(border=True):
            col_ia_icon, col_ia_text = st.columns([1, 6])
            col_ia_icon.image("https://cdn-icons-png.flaticon.com/512/2040/2040946.png", width=60)
            with col_ia_text:
                st.subheader("✨ Análisis Estratégico AI")
                if st.button("🧠 Generar Hallazgos con IA"):
                    client = Groq(api_key=groq_api_key)
                    # Resumen simplificado para la IA
                    resumen = df.groupby('Categoria')['Utilidad_Total'].sum().sort_values().to_string()
                    
                    try:
                        chat = client.chat.completions.create(
                            model="llama-3.3-70b-versatile",
                            messages=[{"role": "user", "content": f"Analiza esta utilidad por categoría y detecta riesgos: {resumen}"}]
                        )
                        st.markdown(chat.choices[0].message.content)
                    except Exception as e:
                        st.error(f"Error de conexión: {e}")

    # --- SECCIÓN GRÁFICA Y TABS ---
    st.markdown("###")
    t1, t2 = st.tabs(["📈 Visualización", "📋 Auditoría"])

    with t1:
        c_a, c_b = st.columns(2)
        with c_a:
            fig_bar = px.bar(df.groupby('Categoria')['Utilidad_Total'].sum().reset_index(), 
                             x='Categoria', y='Utilidad_Total', color='Utilidad_Total',
                             color_continuous_scale='RdYlGn', template="plotly_white")
            st.plotly_chart(fig_bar, use_container_width=True)
        with c_b:
            fig_pie = px.pie(df, names='Estado_Envio', title="Estado de Logística", hole=0.4)
            st.plotly_chart(fig_pie, use_container_width=True)

    with t2:
        st.write("**Alertas: Transacciones con Utilidad Negativa**")
        st.dataframe(df[df['Utilidad_Total'] < 0][['Transaccion_ID', 'SKU_ID', 'Utilidad_Total', 'Ciudad_Destino']].sort_values('Utilidad_Total'))

else:
    st.info("👋 Por favor, carga el archivo CSV en el panel lateral para visualizar los datos.")
