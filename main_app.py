import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
from groq import Groq

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Auditoría Pro: Operaciones & IA", layout="wide", page_icon="🌙")

# --- PALETA DE COLORES PERSONALIZADA ---
COLOR_AZUL = "#1E88E5"
COLOR_GRIS = "#475569"
COLOR_ROJO = "#EF4444"
COLOR_VERDE = "#10B981"
COLOR_FONDO = "#0E1117"

# --- CSS: MODO OSCURO & ESTILO MINIMALISTA ---
st.markdown(f"""
    <style>
    .stApp {{ background-color: {COLOR_FONDO}; color: #FFFFFF; }}
    h1, h2, h3, p, span, label {{ color: #FFFFFF !important; }}
    
    /* Métricas Transparentes (Sin fondo blanco) */
    div[data-testid="metric-container"] {{
        background-color: transparent !important;
        border: none !important;
        box-shadow: none !important;
    }}
    
    /* Contenedor de IA con borde azul sutil */
    .ai-container {{
        background-color: #161B22;
        border-radius: 12px;
        padding: 25px;
        border-left: 5px solid {COLOR_AZUL};
        margin-top: 15px;
    }}
    
    .question-box {{
        background-color: #161B22;
        padding: 20px;
        border-radius: 10px;
        border: 1px solid {COLOR_GRIS};
        margin-bottom: 20px;
    }}
    </style>
""", unsafe_allow_html=True)

# --- PROCESAMIENTO DE DATOS ---
@st.cache_data
def process_data(file):
    df = pd.read_csv(file)
    cols = ['Precio_Venta_Final', 'Costo_Unitario_USD', 'Cantidad_Vendida', 'Costo_Envio', 'Satisfaccion_NPS', 'Stock_Actual']
    for col in cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    
    # Utilidad = Ingreso - Costo - Envío
    df['Utilidad_Total'] = (df['Precio_Venta_Final'] * df['Cantidad_Vendida']) - \
                           (df['Costo_Unitario_USD'] * df['Cantidad_Vendida']) - \
                           df['Costo_Envio']
    return df

# --- SIDEBAR ---
with st.sidebar:
    st.title("🚜 Control Center")
    with st.expander("🔑 Configuración IA", expanded=True):
        groq_api_key = st.text_input("Groq API Key", type="password")
    
    uploaded_file = st.file_uploader("📂 Cargar Datos CSV", type=["csv"])
    if uploaded_file:
        df_raw = process_data(uploaded_file)
        st.divider()
        sel_cats = st.multiselect("Filtrar Categorías", sorted(df_raw['Categoria'].unique()), default=df_raw['Categoria'].unique())
        n_registros = st.slider("Volumen de datos", 50, len(df_raw), 500)

# --- DASHBOARD PRINCIPAL ---
if uploaded_file:
    df = df_raw[df_raw['Categoria'].isin(sel_cats)].head(n_registros)
    revenue = df['Precio_Venta_Final'].sum()
    profit = df['Utilidad_Total'].sum()

    st.title("📈 Intelligence Business Dashboard")

    # --- MÉTRICAS TOP (AZULES Y GRISES CON ALERTAS) ---
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Ingresos Totales", f"${revenue:,.0f}")
    
    # Delta en rojo si hay pérdida, verde si hay ganancia
    m2.metric("Utilidad Neta", f"${profit:,.0f}", 
              delta=f"{(profit/revenue*100):.1f}% Margen" if revenue != 0 else "0%",
              delta_color="normal" if profit >= 0 else "inverse")
    
    m3.metric("NPS (Mediana)", f"{df[df['Satisfaccion_NPS']>0]['Satisfaccion_NPS'].median():.1f}")
    m4.metric("Unidades Movilizadas", f"{df['Cantidad_Vendida'].sum():,.0f}")

    # --- TABS ---
    tab_cuant, tab_cual, tab_ia = st.tabs(["📊 Cuantitativo", "👤 Cualitativo", "🕵️ Auditoría IA"])

    # 1. TAB CUANTITATIVO (AZULES Y SEMÁFORO)
    with tab_cuant:
        st.subheader("Análisis Financiero y Stock")
        c1, c2 = st.columns(2)
        with c1:
            # Gráfico de barras con escala de color semáforo (Rojo a Verde)
            fig_bar = px.bar(df.groupby('Categoria')['Utilidad_Total'].sum().reset_index(), 
                             x='Categoria', y='Utilidad_Total', 
                             color='Utilidad_Total',
                             color_continuous_scale=[COLOR_ROJO, "#FFD700", COLOR_VERDE],
                             template="plotly_dark", title="Utilidad por Categoría")
            st.plotly_chart(fig_bar, use_container_width=True)
        with c2:
            # Dispersión en azules y grises
            fig_scat = px.scatter(df, x='Stock_Actual', y='Utilidad_Total', 
                                  color='Categoria', size='Cantidad_Vendida',
                                  color_discrete_sequence=px.colors.sequential.Blues_r,
                                  template="plotly_dark", title="Eficiencia de Inventario")
            st.plotly_chart(fig_scat, use_container_width=True)

    # 2. TAB CUALITATIVO (AZULES Y GRISES)
    with tab_cual:
        st.subheader("Experiencia del Cliente")
        c3, c4 = st.columns(2)
        with c3:
            fig_pie = px.pie(df, names='Estado_Envio', hole=0.4, 
                             color_discrete_sequence=[COLOR_AZUL, COLOR_GRIS, "#1e293b", "#334155"],
                             template="plotly_dark", title="Distribución Logística")
            st.plotly_chart(fig_pie, use_container_width=True)
        with c4:
            fig_nps = px.box(df, x='Ciudad_Destino', y='Satisfaccion_NPS',
                             color_discrete_sequence=[COLOR_AZUL],
                             template="plotly_dark", title="Variación NPS por Ciudad")
            st.plotly_chart(fig_nps, use_container_width=True)

    # 3. TAB IA (AUDITORÍA ESTRATÉGICA)
    with tab_ia:
        st.subheader("Respuestas de Consultoría Estratégica")
        
        with st.container():
            st.markdown(f"""
            <div class="question-box">
            <h4 style='color:{COLOR_AZUL}'>Preguntas de Auditoría:</h4>
            1. <b>Fuga de Capital:</b> ¿Margen negativo es falla de precios Online?<br>
            2. <b>Crisis Logística:</b> ¿Qué zona requiere cambio de operador?<br>
            3. <b>Venta Invisible:</b> ¿Impacto de SKUs fuera de maestro?<br>
            4. <b>Diagnóstico Fidelidad:</b> ¿Por qué stock alto con sentimiento negativo?<br>
            5. <b>Riesgo Operativo:</b> ¿Qué bodegas operan a ciegas?<br>
            </div>
            """, unsafe_allow_html=True)

        if st.button("🧠 Ejecutar Auditoría con IA"):
            if groq_api_key:
                with st.spinner("IA procesando diagnósticos..."):
                    try:
                        client = Groq(api_key=groq_api_key)
                        resumen = {
                            "perdid": df[df['Utilidad_Total'] < 0][['Categoria', 'Utilidad_Total']].to_string(),
                            "logist": df.groupby('Ciudad_Destino')[['Tiempo_Entrega_Real', 'Satisfaccion_NPS']].mean().to_string(),
                            "fantas": df[df['Categoria'] == 'SKU_FANTASMA']['Precio_Venta_Final'].sum()
                        }
                        
                        prompt = f"Responde las 5 preguntas basándote en: {resumen}. Sé breve, usa puntos y lenguaje ejecutivo."
                        
                        chat = client.chat.completions.create(
                            model="llama-3.3-70b-versatile",
                            messages=[{"role": "user", "content": prompt}]
                        )
                        st.markdown(f'<div class="ai-container">{chat.choices[0].message.content}</div>', unsafe_allow_html=True)
                    except Exception as e:
                        st.error(f"Error: {e}")
            else:
                st.warning("⚠️ Ingresa la API Key en el menú lateral.")

else:
    st.info("🌙 Cargue el archivo CSV para iluminar el dashboard.")
