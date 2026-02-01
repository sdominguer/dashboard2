import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
from groq import Groq

# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Auditoría Pro: Operaciones & IA", layout="wide", page_icon="🌙")

# --- 2. PALETA DE COLORES Y CSS ---
COLOR_AZUL = "#1E88E5"
COLOR_GRIS = "#475569"
COLOR_ROJO = "#EF4444"
COLOR_VERDE = "#10B981"
COLOR_FONDO = "#0E1117"

st.markdown(f"""
    <style>
    .stApp {{ background-color: {COLOR_FONDO}; color: #FFFFFF; }}
    h1, h2, h3, h4, p, span, label {{ color: #FFFFFF !important; }}
    
    /* Métricas Transparentes */
    div[data-testid="metric-container"] {{
        background-color: transparent !important;
        border: none !important;
        box-shadow: none !important;
    }}
    [data-testid="stMetricValue"] {{ font-size: 32px !important; font-weight: 700 !important; }}

    /* Contenedores Especiales */
    .ai-container {{
        background-color: #161B22;
        border-radius: 12px;
        padding: 25px;
        border-left: 5px solid {COLOR_AZUL};
        margin-top: 15px;
        line-height: 1.6;
    }}
    .question-box {{
        background-color: #161B22;
        padding: 20px;
        border-radius: 10px;
        border: 1px solid {COLOR_GRIS};
        margin-bottom: 20px;
    }}
    /* Estilo de Tabs */
    .stTabs [data-baseweb="tab-list"] {{ gap: 24px; border-bottom: 1px solid #30363D; }}
    .stTabs [aria-selected="true"] p {{ color: {COLOR_AZUL} !important; font-weight: bold; }}
    </style>
""", unsafe_allow_html=True)

# --- 3. LÓGICA DE DATOS ---
@st.cache_data
def load_and_process(file):
    df = pd.read_csv(file)
    # Limpieza de columnas críticas
    cols_num = ['Precio_Venta_Final', 'Costo_Unitario_USD', 'Cantidad_Vendida', 'Costo_Envio', 'Satisfaccion_NPS', 'Stock_Actual']
    for col in cols_num:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    
    # Cálculo de Utilidad
    df['Utilidad_Total'] = (df['Precio_Venta_Final'] * df['Cantidad_Vendida']) - \
                           (df['Costo_Unitario_USD'] * df['Cantidad_Vendida']) - \
                           df['Costo_Envio']
    return df

# --- 4. SIDEBAR ---
with st.sidebar:
    st.title("🚜 Operaciones Pro")
    with st.expander("🔑 Configuración IA", expanded=True):
        groq_key = st.text_input("Groq API Key", type="password")
    
    uploaded_file = st.file_uploader("📂 Cargar Datos CSV", type=["csv"])
    if uploaded_file:
        df_raw = load_and_process(uploaded_file)
        st.divider()
        all_cats = sorted(df_raw['Categoria'].unique())
        sel_cats = st.multiselect("Categorías", all_cats, default=all_cats)
        limit = st.slider("Muestra de datos", 50, len(df_raw), 500)

# --- 5. DASHBOARD PRINCIPAL ---
if uploaded_file:
    # Aplicar filtros
    df = df_raw[df_raw['Categoria'].isin(sel_cats)].head(limit)
    rev_total = df['Precio_Venta_Final'].sum()
    profit_total = df['Utilidad_Total'].sum()

    st.title("📊 Intelligence Business Dashboard")
    
    # Métricas Superiores
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Ingresos Totales", f"${rev_total:,.0f}")
    m2.metric("Utilidad Neta", f"${profit_total:,.0f}", 
              delta=f"{(profit_total/rev_total*100):.1f}%" if rev_total > 0 else "0%",
              delta_color="normal" if profit_total >= 0 else "inverse")
    m3.metric("NPS (Mediana)", f"{df[df['Satisfaccion_NPS']>0]['Satisfaccion_NPS'].median():.1f}")
    m4.metric("Unidades", f"{df['Cantidad_Vendida'].sum():,.0f}")

    # Tabs de navegación
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Cuantitativo", "👤 Cualitativo", "🕵️ Auditoría IA"," 📋 Disclaimers"])

    # --- TAB 1: CUANTITATIVO ---
    with tab1:
        st.subheader("Rendimiento Financiero")
        c1, c2 = st.columns(2)
        with c1:
            fig_bar = px.bar(df.groupby('Categoria')['Utilidad_Total'].sum().reset_index(), 
                             x='Categoria', y='Utilidad_Total', color='Utilidad_Total',
                             color_continuous_scale=[COLOR_ROJO, "#FFD700", COLOR_VERDE],
                             template="plotly_dark", title="Rentabilidad por Segmento")
            st.plotly_chart(fig_bar, use_container_width=True)
        with c2:
            fig_stock = px.scatter(df, x='Stock_Actual', y='Utilidad_Total', color='Categoria',
                                   color_discrete_sequence=px.colors.sequential.Blues_r,
                                   template="plotly_dark", title="Relación Stock vs Ganancia")
            st.plotly_chart(fig_stock, use_container_width=True)

    # --- TAB 2: CUALITATIVO ---
    with tab2:
        st.subheader("Análisis de Servicio")
        c3, c4 = st.columns(2)
        with c3:
            fig_pie = px.pie(df, names='Estado_Envio', hole=0.4, 
                             color_discrete_sequence=[COLOR_AZUL, COLOR_GRIS, "#1e293b"],
                             template="plotly_dark", title="Estado de Envíos")
            st.plotly_chart(fig_pie, use_container_width=True)
        with c4:
            fig_nps = px.box(df, x='Ciudad_Destino', y='Satisfaccion_NPS', 
                             color_discrete_sequence=[COLOR_AZUL],
                             template="plotly_dark", title="Distribución NPS por Ciudad")
            st.plotly_chart(fig_nps, use_container_width=True)

    # --- TAB 3: AUDITORÍA CON IA ---
    with tab3:
        st.subheader("Respuestas de Consultoría Estratégica")
        
        st.markdown(f"""
        <div class="question-box">
        <h4 style='color:{COLOR_AZUL}'>Preguntas que la IA resolverá:</h4>
        1. <b>Fuga de Capital:</b> ¿Margen negativo es falla de precios Online?<br>
        2. <b>Crisis Logística:</b> ¿Qué zona requiere cambio de operador?<br>
        3. <b>Venta Invisible:</b> ¿Impacto de SKUs fuera de maestro?<br>
        4. <b>Diagnóstico Fidelidad:</b> ¿Por qué stock alto con sentimiento negativo?<br>
        5. <b>Riesgo Operativo:</b> ¿Qué bodegas operan a ciegas?
        </div>
        """, unsafe_allow_html=True)

        if st.button("🧠 Ejecutar Diagnóstico Maestro"):
            if groq_key:
                with st.spinner("Analizando micro-datos y tendencias..."):
                    try:
                        client = Groq(api_key=groq_key)
                        
                        # Datos consolidados para que la IA no alucine
                        fuga = df[df['Utilidad_Total'] < 0].groupby('Canal_Venta')['Utilidad_Total'].sum().to_dict()
                        logistica = df.groupby('Ciudad_Destino')[['Tiempo_Entrega_Real', 'Satisfaccion_NPS']].mean().to_dict()
                        fantasmas = df[df['Categoria'].str.contains('Fantasma|No Catalogado', na=False)]['Precio_Venta_Final'].sum()
                        paradoja = df.groupby('Categoria')[['Stock_Actual', 'Satisfaccion_NPS']].mean().to_dict()

                        prompt = f"""
                        Eres un Auditor Senior. Basado en estos datos REALES, responde las 5 preguntas de la caja anterior:
                        - Pérdidas por Canal: {fuga}
                        - Logística por Ciudad: {logistica}
                        - Venta SKUs Fantasma: ${fantasmas}
                        - Stock vs NPS: {paradoja}
                        - Ingreso Total: ${rev_total}

                        Instrucciones:
                        - Sé directo, crítico y profesional.
                        - Usa Markdown con negritas.
                        - Si el impacto de SKUs fantasma es > 0, calcula su % frente al ingreso total.
                        """
                        
                        chat = client.chat.completions.create(
                            model="llama-3.3-70b-versatile",
                            messages=[{"role": "user", "content": prompt}],
                            temperature=0.2
                        )
                        st.markdown(f'<div class="ai-container">{chat.choices[0].message.content}</div>', unsafe_allow_html=True)
                    except Exception as e:
                        st.error(f"Error de conexión: {e}")
            else:
                st.warning("⚠️ Ingresa la API Key en el menú lateral.")
    # --- TAB 3: ELIMINACION DE LOS DATOS ---
    with tab4:
        st.subheader("Limpieza del dataset")
    
        st.write("en el primer join obtengo"," ",df.shape[0]," ","de registros pero descartando los SKU_ID fantasma que no estan en la tabla de productos obtengo",df.dropna().shape[0]," ","registros")
        st.write("en el segundo join tomando elementos nulos del primero obtengo"," ",df.shape[0]," ","registros pero descartando las Transaccion_ID fantasma (que no estan en la tabla de Feedbacks) y \n los SKU_ID Fantasma  obtengo",df.dropna().shape[0]," ","registros", "si eliminamos datos fantasma mantendriamos"," ",(df.dropna().shape[0]/df.shape[0])*100,"\n % de los datos")
        df_sku=(pd.DataFrame(df.groupby('SKU_ID')['Ultima_Revision'].count().reset_index()))
        st.write"tenemos"," ",df_sku[df_sku['Ultima_Revision']==0].reset_index().shape[0]," ","SKU Fantasmas")
        df_tra=(pd.DataFrame(df.groupby('Transaccion_ID')['Ultima_Revision'].count().reset_index()))
        st.write("tenemos"," ",df_tra[df_tra['Ultima_Revision']==0].reset_index().shape[0]," ","transacciones Fantasmas")

else:
    st.info("🌙 Sistema en espera. Por favor cargue el archivo CSV en el panel lateral.")
