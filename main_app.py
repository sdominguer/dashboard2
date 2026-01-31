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
    .stApp { background-color: #0E1117; color: #FFFFFF; }
    h1, h2, h3, p, span, label { color: #FFFFFF !important; }

    /* Métricas Transparentes */
    div[data-testid="metric-container"] {
        background-color: transparent !important;
        border: none !important;
        box-shadow: none !important;
    }
    [data-testid="stMetricValue"] { color: #FFFFFF !important; font-size: 32px !important; font-weight: 700 !important; }
    [data-testid="stMetricLabel"] { color: #A0AEC0 !important; }

    /* Tabs y Sidebar */
    .stTabs [data-baseweb="tab-list"] { background-color: transparent; border-bottom: 1px solid #30363D; }
    .stTabs [aria-selected="true"] p { color: #58A6FF !important; font-weight: bold; }
    .stTabs [data-baseweb="tab-highlight"] { background-color: #58A6FF !important; }
    
    /* Contenedor de IA estilo "Glow" */
    .ai-container {
        background-color: #161B22;
        border-radius: 15px;
        padding: 25px;
        border: 1px solid #30363D;
        margin-top: 20px;
    }
    </style>
""", unsafe_allow_html=True)

# --- PROCESAMIENTO ---
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
    with st.expander("🔑 Configuración IA", expanded=True):
        groq_api_key = st.text_input("Groq API Key", type="password", placeholder="gsk_...")
    
    st.divider()
    uploaded_file = st.file_uploader("📂 Subir archivo CSV", type=["csv"])
    
    if uploaded_file:
        df_raw = process_data(uploaded_file)
        cats = sorted(df_raw['Categoria'].unique())
        sel_cats = st.multiselect("Categorías", cats, default=cats)
        n_registros = st.slider("Volumen de datos", 50, len(df_raw), 500)

# --- CUERPO PRINCIPAL ---
if uploaded_file:
    df = df_raw[df_raw['Categoria'].isin(sel_cats)].head(n_registros)

    st.title("📈 Strategic Business Intelligence")
    
    # MÉTRICAS
    m1, m2, m3, m4 = st.columns(4)
    revenue = df['Precio_Venta_Final'].sum()
    profit = df['Utilidad_Total'].sum()
    m1.metric("Ingresos Totales", f"${revenue:,.0f}")
    m2.metric("Utilidad Neta", f"${profit:,.0f}", delta=f"{(profit/revenue*100):.1f}%" if revenue != 0 else "0%")
    m3.metric("NPS (Mediana)", f"{df[df['Satisfaccion_NPS']>0]['Satisfaccion_NPS'].median():.1f}")
    m4.metric("Unidades Vendidas", f"{df['Cantidad_Vendida'].sum():,.0f}")

    # TABS
    tab_vis, tab_aud = st.tabs(["📊 Visualización de Datos", "📋 Registro de Auditoría"])

    with tab_vis:
        # Fila de Gráficas
        c1, c2 = st.columns(2)
        with c1:
            fig_bar = px.bar(df.groupby('Categoria')['Utilidad_Total'].sum().reset_index(), 
                             x='Categoria', y='Utilidad_Total', color='Utilidad_Total',
                             color_continuous_scale='RdYlGn', template="plotly_dark", title="Rentabilidad por Segmento")
            st.plotly_chart(fig_bar, use_container_width=True)
        with c2:
            fig_pie = px.pie(df, names='Estado_Envio', hole=0.4, template="plotly_dark", title="Cumplimiento Logístico")
            st.plotly_chart(fig_pie, use_container_width=True)

        # --- SECCIÓN IA: DIAGNÓSTICO ESTRATÉGICO (DEBAJO DE LAS GRÁFICAS) ---
st.divider()
st.subheader("🤖 Consultoría de Riesgo Operativo (IA)")

if groq_api_key:
    if st.button("🧠 Generar Auditoría de las 5 Preguntas Clave"):
        with st.spinner("Analizando fugas de capital y crisis logística..."):
            try:
                client = Groq(api_key=groq_api_key)
                
                # Preparamos un resumen ultra-detallado para que la IA responda con precisión
                resumen_para_ia = {
                    "fuga_capital": df[df['Utilidad_Total'] < 0][['Categoria', 'Canal_Venta', 'Utilidad_Total']].to_string(),
                    "logistica_nps": df.groupby(['Ciudad_Destino', 'Bodega_Origen'])[['Tiempo_Entrega_Real', 'Satisfaccion_NPS']].mean().to_string(),
                    "venta_invisible": df[df['Categoria'] == 'No Catalogado (Fantasma)']['Precio_Venta_Final'].sum(),
                    "paradoja_stock": df.groupby('Categoria')[['Stock_Actual', 'Satisfaccion_NPS']].mean().to_string(),
                    "tickets_revision": df.groupby('Bodega_Origen')[['Ticket_Soporte_Abierto', 'Ultima_Revision']].count().to_string()
                }
                
                prompt_maestro = f"""
                Actúa como un Auditor Senior de Operaciones. Basado en estos datos, responde de forma ejecutiva:
                
                1. RENTABILIDAD: Analiza los SKUs con margen negativo en estos datos: {resumen_para_ia['fuga_capital']}. ¿Es falla de precios en Online?
                2. LOGÍSTICA: Según esta relación Tiempo/NPS {resumen_para_ia['logistica_nps']}, ¿qué zona necesita cambio de operador?
                3. VENTA INVISIBLE: El impacto de SKUs fantasma es de ${resumen_para_ia['venta_invisible']} USD. ¿Qué porcentaje del ingreso total ({revenue}) representa este riesgo?
                4. FIDELIDAD: Analiza stock vs sentimiento: {resumen_para_ia['paradoja_stock']}. ¿Calidad o sobrecosto?
                5. RIESGO OPERATIVO: Relación Tickets/Revisión por bodega: {resumen_para_ia['tickets_revision']}. ¿Quién opera a ciegas?

                Usa un tono profesional, markdown, negritas para hallazgos y responde en Español.
                """
                
                chat = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[{"role": "system", "content": "Eres un experto en optimización de supply chain y finanzas."},
                              {"role": "user", "content": prompt_maestro}]
                )
                
                # Mostrar la respuesta en el contenedor oscuro
                st.markdown(f'<div class="ai-container">{chat.choices[0].message.content}</div>', unsafe_allow_html=True)
                
            except Exception as e:
                st.error(f"Error en el análisis: {e}")
else:
    st.warning("⚠️ Configura la API Key en el menú lateral para obtener el diagnóstico de auditoría.")

else:
    st.info("🌙 Sistema listo. Cargue el archivo CSV en el panel lateral para iniciar.")
