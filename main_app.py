import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
from groq import Groq

# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="Auditoría Pro: Operaciones & IA",
    layout="wide",
    page_icon="🌙"
)

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

div[data-testid="metric-container"] {{
    background-color: transparent !important;
    border: none !important;
    box-shadow: none !important;
}}
[data-testid="stMetricValue"] {{
    font-size: 32px !important;
    font-weight: 700 !important;
}}

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

.stTabs [data-baseweb="tab-list"] {{
    gap: 24px;
    border-bottom: 1px solid #30363D;
}}
.stTabs [aria-selected="true"] p {{
    color: {COLOR_AZUL} !important;
    font-weight: bold;
}}
</style>
""", unsafe_allow_html=True)

# --- 3. LÓGICA DE DATOS ---
@st.cache_data
def load_and_process(source):
    df = pd.read_csv(source)

    cols_num = [
        'Precio_Venta_Final', 'Costo_Unitario_USD', 'Cantidad_Vendida',
        'Costo_Envio', 'Satisfaccion_NPS', 'Stock_Actual'
    ]

    for col in cols_num:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

    df['Utilidad_Total'] = (
        (df['Precio_Venta_Final'] * df['Cantidad_Vendida']) -
        (df['Costo_Unitario_USD'] * df['Cantidad_Vendida']) -
        df['Costo_Envio']
    )

    return df

# --- 4. SIDEBAR ---
with st.sidebar:
    st.title("🚜 Operaciones Pro")

    with st.expander("🔑 Configuración IA", expanded=True):
        groq_key = st.text_input("Groq API Key", type="password")

    st.divider()

    origen_datos = st.radio(
        "📌 Origen de los datos",
        ["SharePoint (Teams)", "Cargar CSV desde mi PC"]
    )

    # -------- SHAREPOINT --------
    if origen_datos == "SharePoint (Teams)":
        try:
            sp_files = st.secrets["sharepoint"]
        except KeyError:
            st.error("❌ No existe [sharepoint] en secrets.toml")
            st.stop()

        dataset_sel = st.selectbox(
            "Selecciona el dataset",
            options=list(sp_files.keys())
        )

        if st.button("📥 Cargar dataset"):
            df_raw = load_and_process(sp_files[dataset_sel])

    # -------- CARGA LOCAL --------
    else:
        uploaded_file = st.file_uploader(
            "📂 Cargar Datos CSV",
            type=["csv"]
        )

        if uploaded_file:
            df_raw = load_and_process(uploaded_file)

    # -------- FILTROS --------
    if "df_raw" in locals():
        st.divider()
        all_cats = sorted(df_raw['Categoria'].dropna().unique())
        sel_cats = st.multiselect("Categorías", all_cats, default=all_cats)
        limit = st.slider("Muestra de datos", 50, len(df_raw), min(500, len(df_raw)))

# --- 5. DASHBOARD PRINCIPAL ---
if "df_raw" in locals():

    df = df_raw[df_raw['Categoria'].isin(sel_cats)].head(limit)

    rev_total = df['Precio_Venta_Final'].sum()
    profit_total = df['Utilidad_Total'].sum()

    st.title("📊 Intelligence Business Dashboard")

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Ingresos Totales", f"${rev_total:,.0f}")
    m2.metric(
        "Utilidad Neta",
        f"${profit_total:,.0f}",
        delta=f"{(profit_total / rev_total * 100):.1f}%" if rev_total > 0 else "0%",
        delta_color="normal" if profit_total >= 0 else "inverse"
    )
    m3.metric(
        "NPS (Mediana)",
        f"{df[df['Satisfaccion_NPS'] > 0]['Satisfaccion_NPS'].median():.1f}"
    )
    m4.metric("Unidades", f"{df['Cantidad_Vendida'].sum():,.0f}")

    tab1, tab2, tab3, tab4 = st.tabs(
        ["📊 Cuantitativo", "👤 Cualitativo", "🕵️ Auditoría IA", "📋 Disclaimers"]
    )

    # --- TAB 1 ---
    with tab1:
        c1, c2 = st.columns(2)

        with c1:
            fig_bar = px.bar(
                df.groupby('Categoria')['Utilidad_Total'].sum().reset_index(),
                x='Categoria',
                y='Utilidad_Total',
                color='Utilidad_Total',
                color_continuous_scale=[COLOR_ROJO, "#FFD700", COLOR_VERDE],
                template="plotly_dark",
                title="Rentabilidad por Segmento"
            )
            st.plotly_chart(fig_bar, use_container_width=True)

        with c2:
            fig_stock = px.scatter(
                df,
                x='Stock_Actual',
                y='Utilidad_Total',
                color='Categoria',
                template="plotly_dark",
                title="Relación Stock vs Ganancia"
            )
            st.plotly_chart(fig_stock, use_container_width=True)

    # --- TAB 2 ---
    with tab2:
        c3, c4 = st.columns(2)

        with c3:
            fig_pie = px.pie(
                df,
                names='Estado_Envio',
                hole=0.4,
                template="plotly_dark",
                title="Estado de Envíos"
            )
            st.plotly_chart(fig_pie, use_container_width=True)

        with c4:
            fig_nps = px.box(
                df,
                x='Ciudad_Destino',
                y='Satisfaccion_NPS',
                template="plotly_dark",
                title="Distribución NPS por Ciudad"
            )
            st.plotly_chart(fig_nps, use_container_width=True)

    # --- TAB 3 (IA) ---
    with tab3:
        st.subheader("Respuestas de Consultoría Estratégica")

        if st.button("🧠 Ejecutar Diagnóstico Maestro") and groq_key:
            client = Groq(api_key=groq_key)
            st.success("Diagnóstico ejecutado correctamente (placeholder)")

    # --- TAB 4 ---
    with tab4:
        st.subheader("Limpieza del dataset")
        st.write("Registros totales:", df.shape[0])
        st.write("Registros sin nulos:", df.dropna().shape[0])
