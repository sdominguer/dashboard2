import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
from groq import Groq

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Auditoría de Operaciones Pro", layout="wide", page_icon="🌙")

# --- CSS: DARK MODE & MÉTRICAS FLOTANTES ---
st.markdown("""
    <style>
    .stApp { background-color: #0E1117; color: #FFFFFF; }
    h1, h2, h3, p, span, label { color: #FFFFFF !important; }
    div[data-testid="metric-container"] { background-color: transparent !important; border: none !important; }
    [data-testid="stMetricValue"] { color: #FFFFFF !important; font-size: 32px !important; font-weight: 700 !important; }
    
    .ai-container {
        background-color: #161B22;
        border-radius: 12px;
        padding: 25px;
        border-left: 5px solid #58A6FF;
        margin-top: 15px;
    }
    .question-box {
        background-color: #0d1117;
        padding: 15px;
        border-radius: 8px;
        border: 1px dashed #30363d;
        margin-bottom: 10px;
    }
    </style>
""", unsafe_allow_html=True)

# --- PROCESAMIENTO ---
@st.cache_data
def process_data(file):
    df = pd.read_csv(file)
    cols = ['Precio_Venta_Final', 'Costo_Unitario_USD', 'Cantidad_Vendida', 'Costo_Envio', 'Satisfaccion_NPS', 'Stock_Actual']
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
        groq_api_key = st.text_input("Groq API Key", type="password")
    
    uploaded_file = st.file_uploader("📂 Cargar Datos CSV", type=["csv"])
    if uploaded_file:
        df_raw = process_data(uploaded_file)
        sel_cats = st.multiselect("Categorías", sorted(df_raw['Categoria'].unique()), default=df_raw['Categoria'].unique())
        n_registros = st.slider("Registros", 50, len(df_raw), 500)

# --- DASHBOARD ---
if uploaded_file:
    df = df_raw[df_raw['Categoria'].isin(sel_cats)].head(n_registros)
    revenue = df['Precio_Venta_Final'].sum()
    profit = df['Utilidad_Total'].sum()

    st.title("📈 Strategic Business Intelligence")

    # MÉTRICAS TOP
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Ingresos", f"${revenue:,.0f}")
    m2.metric("Utilidad", f"${profit:,.0f}", delta=f"{(profit/revenue*100):.1f}%" if revenue != 0 else "0%")
    m3.metric("NPS Mediano", f"{df[df['Satisfaccion_NPS']>0]['Satisfaccion_NPS'].median():.1f}")
    m4.metric("SKUs Críticos", len(df[df['Utilidad_Total'] < 0]))

    tab_cuant, tab_cual, tab_ia = st.tabs(["📊 Análisis Cuantitativo", "👤 Análisis Cualitativo", "🤖 Auditoría con IA"])

    # --- TAB 1: CUANTITATIVO ---
    with tab_cuant:
        st.subheader("Rendimiento Financiero y de Inventario")
        c1, c2 = st.columns(2)
        with c1:
            fig_bar = px.bar(df.groupby('Categoria')['Utilidad_Total'].sum().reset_index(), 
                             x='Categoria', y='Utilidad_Total', color='Utilidad_Total',
                             color_continuous_scale='RdYlGn', template="plotly_dark", title="Rentabilidad por Categoría")
            st.plotly_chart(fig_bar, use_container_width=True)
        with c2:
            fig_scat = px.scatter(df, x='Stock_Actual', y='Utilidad_Total', color='Categoria',
                                  size='Cantidad_Vendida', template="plotly_dark", title="Stock vs Utilidad")
            st.plotly_chart(fig_scat, use_container_width=True)

    # --- TAB 2: CUALITATIVO ---
    with tab_cual:
        st.subheader("Sentimiento del Cliente y Logística")
        c3, c4 = st.columns(2)
        with c3:
            fig_pie = px.pie(df, names='Estado_Envio', hole=0.4, template="plotly_dark", title="Estado de Entregas")
            st.plotly_chart(fig_pie, use_container_width=True)
        with c4:
            # Heatmap simple de satisfacción
            fig_heat = px.density_heatmap(df, x='Ciudad_Destino', y='Rating_Producto', 
                                          z='Satisfaccion_NPS', template="plotly_dark", title="Satisfacción por Ciudad")
            st.plotly_chart(fig_heat, use_container_width=True)
        
        st.markdown("**Comentarios Críticos Detectados:**")
        st.dataframe(df[df['Rating_Producto'] <= 2][['SKU_ID', 'Comentario_Texto', 'Ciudad_Destino']].head(10))

    # --- TAB 3: IA ---
    with tab_ia:
        st.subheader("🕵️ Auditoría Estratégica Automática")
        
        # Desplegar las preguntas antes
        with st.container():
            st.markdown('<div class="question-box">', unsafe_allow_html=True)
            st.markdown("""
            **Preguntas a Resolver:**
            1. **Fuga de Capital:** ¿Los SKUs con margen negativo son una falla de precios Online?
            2. **Crisis Logística:** ¿Qué zona requiere cambio inmediato de operador por bajo NPS?
            3. **Venta Invisible:** ¿Qué impacto financiero tienen los SKUs fuera de inventario?
            4. **Diagnóstico de Fidelidad:** ¿Por qué hay stock alto con sentimiento negativo?
            5. **Riesgo Operativo:** ¿Qué bodegas operan a ciegas por falta de revisión?
            """)
            st.markdown('</div>', unsafe_allow_html=True)

        if st.button("🧠 Ejecutar Consultoría IA"):
            if groq_api_key:
                with st.spinner("IA analizando patrones de riesgo..."):
                    try:
                        client = Groq(api_key=groq_api_key)
                        # Resumen concentrado para la IA
                        resumen = {
                            "negativos": df[df['Utilidad_Total'] < 0][['Categoria', 'Canal_Venta', 'Utilidad_Total']].to_string(),
                            "logistica": df.groupby('Ciudad_Destino')[['Tiempo_Entrega_Real', 'Satisfaccion_NPS']].mean().to_string(),
                            "fantasmas_usd": df[df['Categoria'] == 'SKU_FANTASMA']['Precio_Venta_Final'].sum(),
                            "stock_sentimiento": df.groupby('Categoria')[['Stock_Actual', 'Satisfaccion_NPS']].mean().to_string()
                        }
                        
                        prompt = f"Analiza estos datos y responde las 5 preguntas de auditoría mencionadas arriba: {resumen}. Sé directo y profesional."
                        
                        chat = client.chat.completions.create(
                            model="llama-3.3-70b-versatile",
                            messages=[{"role": "user", "content": prompt}]
                        )
                        st.markdown(f'<div class="ai-container">{chat.choices[0].message.content}</div>', unsafe_allow_html=True)
                    except Exception as e:
                        st.error(f"Error: {e}")
            else:
                st.warning("⚠️ Ingresa la API Key en el sidebar.")

else:
    st.info("🌙 Cargue el archivo CSV para iniciar la auditoría.")
