import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
from groq import Groq

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Executive Dark Analytics", layout="wide", page_icon="🌙")

# --- CSS: MODO OSCURO TOTAL Y MÉTRICAS FLOTANTES ---
st.markdown("""
    <style>
    /* Fondo oscuro para toda la aplicación */
    .stApp {
        background-color: #0E1117;
        color: #FFFFFF;
    }

    /* Forzar color blanco en títulos y textos */
    h1, h2, h3, p, span, label {
        color: #FFFFFF !important;
    }

    /* Quitar fondo a las métricas (Transparencia Total) */
    div[data-testid="metric-container"] {
        background-color: transparent !important;
        border: none !important;
        box-shadow: none !important;
    }

    /* Estilo específico para los valores de las métricas */
    [data-testid="stMetricValue"] {
        color: #FFFFFF !important;
        font-size: 32px !important;
        font-weight: 700 !important;
    }
    
    [data-testid="stMetricLabel"] {
        color: #A0AEC0 !important; /* Gris claro para las etiquetas */
    }

    /* Tabs en Modo Oscuro */
    .stTabs [data-baseweb="tab-list"] {
        background-color: transparent;
        border-bottom: 1px solid #30363D;
    }
    .stTabs [data-baseweb="tab"] p {
        color: #8B949E !important;
    }
    .stTabs [aria-selected="true"] p {
        color: #58A6FF !important;
    }
    .stTabs [data-baseweb="tab-highlight"] {
        background-color: #58A6FF !important;
    }

    /* Input de API y Sidebar */
    .stTextInput>div>div>input {
        background-color: #161B22;
        color: white;
        border: 1px solid #30363D;
    }
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
    st.title("🌙 Control Center")
    
    # SECCIÓN API KEY
    with st.expander("🔑 Configuración IA", expanded=True):
        groq_api_key = st.text_input("Groq API Key", type="password", placeholder="gsk_...")
        st.caption("Usa tu clave de Groq para análisis predictivo.")

    st.divider()
    uploaded_file = st.file_uploader("📂 Subir archivo CSV", type=["csv"])
    
    if uploaded_file:
        df_raw = process_data(uploaded_file)
        st.subheader("Filtros Globales")
        
        # Filtro de Categoría
        cats = sorted(df_raw['Categoria'].unique())
        sel_cats = st.multiselect("Categorías", cats, default=cats)
        
        # Slider de cantidad
        n_registros = st.slider("Volumen de datos", 50, len(df_raw), 500)

# --- CUERPO PRINCIPAL ---
if uploaded_file:
    df = df_raw[df_raw['Categoria'].isin(sel_cats)].head(n_registros)

    st.title("📈 Strategic Business Intelligence")
    st.markdown("Dashboard ejecutivo con interfaz de alto contraste.")

    # --- MÉTRICAS (FONDO TRANSPARENTE, LETRAS BLANCAS) ---
    st.markdown("###")
    m1, m2, m3, m4 = st.columns(4)
    
    revenue = df['Precio_Venta_Final'].sum()
    profit = df['Utilidad_Total'].sum()
    
    m1.metric("Ingresos Totales", f"${revenue:,.0f}")
    m2.metric("Utilidad Neta", f"${profit:,.0f}", delta=f"{(profit/revenue*100):.1f}%" if revenue != 0 else "0%")
    m3.metric("NPS (Mediana)", f"{df[df['Satisfaccion_NPS']>0]['Satisfaccion_NPS'].median():.1f}")
    m4.metric("Unidades Vendidas", f"{df['Cantidad_Vendida'].sum():,.0f}")

    # --- SECCIÓN IA ---
    if groq_api_key:
        st.markdown("###")
        with st.container():
            st.subheader("✨ Insights con Inteligencia Artificial")
            if st.button("🧠 Generar Diagnóstico de Rentabilidad"):
                try:
                    client = Groq(api_key=groq_api_key)
                    resumen_ia = df.groupby('Categoria')['Utilidad_Total'].sum().to_string()
                    
                    chat = client.chat.completions.create(
                        model="llama-3.3-70b-versatile",
                        messages=[{"role": "system", "content": "Eres un analista financiero. Sé conciso."},
                                  {"role": "user", "content": f"Basado en estos datos de utilidad: {resumen_ia}, ¿cuál es el riesgo principal?"}]
                    )
                    st.info(chat.choices[0].message.content)
                except Exception as e:
                    st.error(f"Error de API: {e}")

    # --- TABS GRÁFICOS ---
    st.markdown("###")
    t1, t2 = st.tabs(["📊 Visualización de Datos", "📋 Registro de Auditoría"])

    with t1:
        c1, c2 = st.columns(2)
        
        with c1:
            # Gráfico de barras ajustado a fondo oscuro
            fig_bar = px.bar(df.groupby('Categoria')['Utilidad_Total'].sum().reset_index(), 
                             x='Categoria', y='Utilidad_Total',
                             color='Utilidad_Total', 
                             color_continuous_scale='RdYlGn',
                             template="plotly_dark") # PLANTILLA OSCURA
            st.plotly_chart(fig_bar, use_container_width=True)
            
        with c2:
            fig_scatter = px.scatter(df, x='Tiempo_Entrega_Real', y='Satisfaccion_NPS', 
                                     color='Categoria', size='Cantidad_Vendida',
                                     template="plotly_dark")
            st.plotly_chart(fig_scatter, use_container_width=True)

    with t2:
        st.markdown("**Transacciones Críticas (Utilidad < 0)**")
        # Estilizar el dataframe para que combine con el fondo oscuro
        st.dataframe(df[df['Utilidad_Total'] < 0][['Transaccion_ID', 'SKU_ID', 'Utilidad_Total', 'Ciudad_Destino']].style.background_gradient(cmap='Reds'))

else:
    st.info("🌙 Bienvenido. Por favor, carga un archivo CSV en el panel lateral para iluminar el dashboard.")
