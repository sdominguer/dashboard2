import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
import os

# Manejo de errores para Groq
try:
    from groq import Groq
except ImportError:
    st.error("⚠️ Error: Falta 'groq' en requirements.txt")
    Groq = None

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="Global Logistics AI Dash",
    layout="wide",
    page_icon="🛳️",
    initial_sidebar_state="expanded"
)

# --- PALETA CORPORATIVA (Steel & Gold) ---
BI_PALETTE = ["#1A3A5F", "#D4AF37", "#4A6274", "#C0C0C0", "#2E8B57", "#CD5C5C"]

# --- CSS PERSONALIZADO (ESTILO BUSINESS-CLEAN) ---
st.markdown("""
    <style>
    .block-container { padding-top: 2rem; max-width: 95%; }
    h1, h2, h3 { font-family: 'Segoe UI', sans-serif; color: #1A3A5F; font-weight: 600; }
    
    /* Tarjetas de Métricas */
    div[data-testid="metric-container"] {
        background-color: #FFFFFF;
        border: 1px solid #E8EBE8;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }

    /* Estilo de los TABS */
    .stTabs [data-baseweb="tab-list"] { gap: 24px; border-bottom: 1px solid #E0E0E0; }
    .stTabs [data-baseweb="tab"] p { font-size: 18px; color: #7F8C8D; }
    .stTabs [aria-selected="true"] p { color: #1A3A5F !important; font-weight: 700; }
    .stTabs [data-baseweb="tab-highlight"] { background-color: #1A3A5F !important; }

    /* Botón Analizar con IA */
    .stButton > button {
        background-color: #1A3A5F;
        color: white;
        border-radius: 20px;
        padding: 0.5rem 2.5rem;
        border: none;
    }
    </style>
""", unsafe_allow_html=True)

# --- CARGA DE DATOS ---
def process_data(file):
    df = pd.read_csv(file)
    # Convertir a numérico lo crítico
    for col in ['Precio_Venta_Final', 'Costo_Unitario_USD', 'Cantidad_Vendida', 'Costo_Envio', 'Satisfaccion_NPS']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    
    # Cálculo de Utilidad
    df['Utilidad_Total'] = (df['Precio_Venta_Final'] * df['Cantidad_Vendida']) - \
                           (df['Costo_Unitario_USD'] * df['Cantidad_Vendida']) - \
                           df['Costo_Envio']
    return df

# --- FUNCIÓN IA ---
def get_ai_insight(df, api_key):
    client = Groq(api_key=api_key)
    stats = df.groupby('Categoria')['Utilidad_Total'].sum().to_string()
    
    prompt = f"""
    Eres un CFO experto. Analiza estos datos de rentabilidad por categoría:
    {stats}
    1. Identifica la categoría más rentable y la que genera más pérdidas.
    2. Da una recomendación de reducción de costos o ajuste de precios.
    Responde en 3 puntos breves usando Markdown.
    """
    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}]
        )
        return completion.choices[0].message.content
    except Exception as e:
        return f"Error en IA: {e}"

# --- SIDEBAR ---
with st.sidebar:
    st.title("⚙️ Operaciones")
    groq_api_key = st.text_input("Groq API Key", type="password")
    uploaded_file = st.file_uploader("Cargar CSV Consolidado", type=["csv"])
    
    if uploaded_file:
        df_raw = process_data(uploaded_file)
        sel_ciudades = st.multiselect("Ciudades", sorted(df_raw['Ciudad_Destino'].unique()), default=df_raw['Ciudad_Destino'].unique()[:3])

# --- DASHBOARD PRINCIPAL ---
if uploaded_file and sel_ciudades:
    df = df_raw[df_raw['Ciudad_Destino'].isin(sel_ciudades)].copy()

    st.title("🛳️ Global Sales & Logistics Intelligence")
    
    # KPIs
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Ventas Totales", f"${df['Precio_Venta_Final'].sum():,.0f}")
    k2.metric("Utilidad Neta", f"${df['Utilidad_Total'].sum():,.0f}")
    k3.metric("NPS", f"{df[df['Satisfaccion_NPS']>0]['Satisfaccion_NPS'].mean():.1f}")
    k4.metric("Volumen", f"{df['Cantidad_Vendida'].sum():,.0f}")

    # IA INSIGHTS
    with st.container(border=True):
        c_ia1, c_ia2 = st.columns([1, 5])
        c_ia1.image("https://cdn-icons-png.flaticon.com/512/4712/4712139.png", width=70)
        with c_ia2:
            st.subheader("🤖 Consultor Financiero AI")
            if st.button("Generar Diagnóstico Estratégico"):
                if groq_api_key:
                    with st.spinner("Analizando balances..."):
                        st.markdown(get_ai_insight(df, groq_api_key))
                else: st.warning("Ingresa la API Key")

    # TABS
    tab1, tab2, tab3 = st.tabs(["📊 Rentabilidad", "🚚 Logística", "👤 Clientes"])

    with tab1:
        fig_bar = px.bar(df.groupby('Categoria')['Utilidad_Total'].sum().reset_index(), 
                         x='Utilidad_Total', y='Categoria', orientation='h',
                         color='Utilidad_Total', color_continuous_scale='RdYlGn',
                         title="<b>Utilidad Neta por Categoría</b>")
        st.plotly_chart(fig_bar, use_container_width=True)

    with tab2:
        fig_ship = px.scatter(df, x='Tiempo_Entrega_Real', y='Costo_Envio', 
                              color='Estado_Envio', size='Precio_Venta_Final',
                              color_discrete_sequence=BI_PALETTE)
        st.plotly_chart(fig_ship, use_container_width=True)

    with tab3:
        st.subheader("Comentarios de Calidad Crítica")
        st.dataframe(df[df['Rating_Producto'] <= 2][['SKU_ID', 'Comentario_Texto', 'Ciudad_Destino']].head(10), use_container_width=True)

elif not uploaded_file:
    st.info("👋 Sube el archivo para iniciar el análisis corporativo.")
