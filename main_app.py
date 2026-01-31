import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
from groq import Groq

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Executive Logistics Dash", layout="wide", page_icon="📈")

# --- CSS PERSONALIZADO (BUSINESS CLEAN) ---
st.markdown("""
    <style>
    .stMetric { background-color: #ffffff; border-radius: 10px; padding: 15px; border: 1px solid #f0f2f6; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    .stTabs [data-baseweb="tab-list"] { gap: 24px; }
    .stTabs [data-baseweb="tab"] p { font-size: 18px; color: #4b5563; }
    .stTabs [aria-selected="true"] p { color: #1e40af !important; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

# --- CARGA Y PROCESAMIENTO ---
def process_data(file):
    df = pd.read_csv(file)
    # Asegurar que las columnas clave sean numéricas
    cols = ['Precio_Venta_Final', 'Costo_Unitario_USD', 'Cantidad_Vendida', 'Costo_Envio', 'Satisfaccion_NPS']
    for col in cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    
    # Cálculo de Utilidad (Margen Neto por transacción)
    df['Utilidad_Total'] = (df['Precio_Venta_Final'] * df['Cantidad_Vendida']) - \
                           (df['Costo_Unitario_USD'] * df['Cantidad_Vendida']) - \
                           df['Costo_Envio']
    return df

# --- SIDEBAR (CONTROLES) ---
with st.sidebar:
    st.title("⚙️ Configuración")
    uploaded_file = st.file_uploader("Subir CSV Consolidado", type=["csv"])
    
    if uploaded_file:
        df_raw = process_data(uploaded_file)
        
        st.divider()
        st.subheader("Filtros de Análisis")
        
        # 1. Filtro de Ciudad
        ciudades = st.multiselect("Ciudades", sorted(df_raw['Ciudad_Destino'].unique()), default=df_raw['Ciudad_Destino'].unique()[:3])
        
        # 2. Filtro de Categoría (NUEVO)
        cats_disponibles = sorted(df_raw['Categoria'].unique())
        categorias = st.multiselect("Categorías", cats_disponibles, default=cats_disponibles)
        
        # 3. Slider de Cantidad de Datos (NUEVO)
        n_registros = st.slider("Cantidad de registros a analizar", 10, len(df_raw), min(500, len(df_raw)))
        
        st.divider()
        groq_api_key = st.text_input("Groq API Key", type="password")

# --- DASHBOARD ---
if uploaded_file:
    # Aplicar filtros
    df = df_raw[
        (df_raw['Ciudad_Destino'].isin(ciudades)) & 
        (df_raw['Categoria'].isin(categorias))
    ].head(n_registros)

    st.title("📊 Intelligence Business Dashboard")
    st.markdown(f"Mostrando los primeros **{n_registros}** registros filtrados.")

    # KPIs Cuantitativos
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Ingresos", f"${df['Precio_Venta_Final'].sum():,.0f}")
    k2.metric("Utilidad", f"${df['Utilidad_Total'].sum():,.0f}", 
              delta=f"{(df['Utilidad_Total'].sum()/df['Precio_Venta_Final'].sum()*100):.1f}%" if df['Precio_Venta_Final'].sum() != 0 else "0%")
    k3.metric("NPS Mediano", f"{df[df['Satisfaccion_NPS']>0]['Satisfaccion_NPS'].median():.1f}")
    k4.metric("Unidades", f"{df['Cantidad_Vendida'].sum():,.0f}")

    # IA Section
    with st.expander("🤖 Análisis Estratégico IA", expanded=False):
        if st.button("Generar Reporte con Groq"):
            if groq_api_key:
                client = Groq(api_key=groq_api_key)
                contexto = df.groupby('Categoria')['Utilidad_Total'].sum().to_string()
                chat = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[{"role": "user", "content": f"Analiza esta utilidad por categoría y dame 2 consejos: {contexto}"}]
                )
                st.write(chat.choices[0].message.content)
            else: st.warning("Ingresa la API Key en el menú lateral.")

    # Tabs para organización
    tab_grafico, tab_datos = st.tabs(["📈 Gráficos", "📋 Datos Críticos"])

    with tab_grafico:
        col_a, col_b = st.columns(2)
        with col_a:
            fig_cat = px.bar(df.groupby('Categoria')['Utilidad_Total'].sum().reset_index(), 
                             x='Categoria', y='Utilidad_Total', color='Utilidad_Total',
                             color_continuous_scale='RdYlGn', title="Utilidad por Categoría")
            st.plotly_chart(fig_cat, use_container_width=True)
        with col_b:
            fig_ship = px.scatter(df, x='Tiempo_Entrega_Real', y='Satisfaccion_NPS', 
                                  color='Categoria', size='Cantidad_Vendida',
                                  title="Entrega vs Satisfacción")
            st.plotly_chart(fig_ship, use_container_width=True)

    with tab_datos:
        st.subheader("Alertas de Margen Negativo")
        # Mostramos los que están perdiendo dinero (Cualitativo/Cuantitativo mixto)
        st.dataframe(df[df['Utilidad_Total'] < 0][['Transaccion_ID', 'SKU_ID', 'Utilidad_Total', 'Ciudad_Destino']].sort_values('Utilidad_Total'))

else:
    st.info("👋 Sube un archivo CSV en el menú lateral para activar el Dashboard.")
