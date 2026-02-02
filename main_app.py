import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
from groq import Groq

# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Auditoría Pro: Operaciones & IA", layout="wide", page_icon="🌙")

# --- 2. ESTILOS CSS PERSONALIZADOS ---
COLOR_AZUL = "#1E88E5"
COLOR_GRIS = "#475569"
COLOR_ROJO = "#EF4444"
COLOR_VERDE = "#10B981"
COLOR_FONDO = "#0E1117"

st.markdown(f"""
    <style>
    .stApp {{ background-color: {COLOR_FONDO}; color: #FFFFFF; }}
    h1, h2, h3, h4, p, span, label {{ color: #FFFFFF !important; }}
    .ai-container {{ background-color: #161B22; border-radius: 12px; padding: 25px; border-left: 5px solid {COLOR_AZUL}; margin-top: 15px; }}
    .question-box {{ background-color: #161B22; padding: 20px; border-radius: 10px; border: 1px solid {COLOR_GRIS}; margin-bottom: 20px; }}
    div[data-testid="stMetricValue"] {{ font-size: 28px !important; }}
    </style>
""", unsafe_allow_html=True)

# --- 3. FUNCIONES DE PROCESAMIENTO ---
@st.cache_data
def load_and_process(file_source):
    """Carga archivos y asegura que las columnas financieras sean numéricas."""
    df = pd.read_csv(file_source)
    # Limpieza básica de nombres de columnas
    df.columns = [c.strip() for c in df.columns]
    
    cols_num = ['Precio_Venta_Final', 'Costo_Unitario_USD', 'Cantidad_Vendida', 'Costo_Envio', 'Satisfaccion_NPS', 'Stock_Actual']
    for col in cols_num:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    
    # Cálculo de utilidad si las columnas existen
    if all(c in df.columns for c in ['Precio_Venta_Final', 'Cantidad_Vendida', 'Costo_Unitario_USD', 'Costo_Envio']):
        df['Utilidad_Total'] = (df['Precio_Venta_Final'] * df['Cantidad_Vendida']) - \
                               (df['Costo_Unitario_USD'] * df['Cantidad_Vendida']) - \
                               df['Costo_Envio']
    return df

# --- 4. SIDEBAR ---
with st.sidebar:
    st.title("🚜 Operaciones Pro")
    with st.expander("🔑 Configuración IA", expanded=False):
        default_key = st.secrets.get("GROQ_API_KEY", "")
        groq_key = st.text_input("Groq API Key", type="password", value=default_key)
    
    uploaded_file = st.file_uploader("📂 Cargar Datos Maestro (Local)", type=["csv"])

# --- 5. LÓGICA DE CARGA Y PROCESAMIENTO ---
if uploaded_file:
    # 5.1 Carga del archivo local
    df_raw = load_and_process(uploaded_file)
    
    # 5.2 Carga de archivos de Teams
    try:
        if 'teams_data' not in st.session_state:
            with st.status("Conectando con servidores de Teams...", expanded=False) as status:
                df_t1 = load_and_process(st.secrets["URL_TEAMS_1"]) # Ventas/Feedback
                df_t2 = load_and_process(st.secrets["URL_TEAMS_2"]) # Inventario
                df_t3 = load_and_process(st.secrets["URL_TEAMS_3"]) # Logística
                st.session_state.teams_data = {"ventas": df_t1, "inventario": df_t2, "logistica": df_t3}
                status.update(label="✅ Datos de Teams sincronizados", state="complete")
        
        df_feed = st.session_state.teams_data["ventas"]
        df_invO = st.session_state.teams_data["inventario"]
        df_trans = st.session_state.teams_data["logistica"]
        
    except Exception as e:
        st.error(f"Error al leer de Teams. Verifica los Secrets. Error: {e}")
        st.stop()

    # --- 6. DASHBOARD PRINCIPAL ---
    st.title("📊 Intelligence Business Dashboard")
    
    # Filtros rápidos
    all_cats = sorted(df_raw['Categoria'].unique()) if 'Categoria' in df_raw.columns else []
    sel_cats = st.sidebar.multiselect("Filtrar por Categoría", all_cats, default=all_cats)
    df_filtered = df_raw[df_raw['Categoria'].isin(sel_cats)] if all_cats else df_raw

    # Métricas superiores
    m1, m2, m3, m4 = st.columns(4)
    rev = df_filtered['Precio_Venta_Final'].sum() if 'Precio_Venta_Final' in df_filtered.columns else 0
    util = df_filtered['Utilidad_Total'].sum() if 'Utilidad_Total' in df_filtered.columns else 0
    
    m1.metric("Ingresos Totales", f"${rev:,.0f}")
    m2.metric("Utilidad Neta", f"${util:,.0f}", delta=f"{(util/rev*100):.1f}%" if rev > 0 else "0%")
    m3.metric("Unidades Vendidas", f"{df_filtered['Cantidad_Vendida'].sum():,.0f}")
    m4.metric("NPS Promedio", f"{df_filtered[df_filtered['Satisfaccion_NPS']>0]['Satisfaccion_NPS'].mean():.1f}")

    tab1, tab2, tab3, tab4 = st.tabs(["📊 Cuantitativo", "👤 Cualitativo", "🕵️ Auditoría IA", "🧹 Saneamiento de Datos"])

    # --- TAB 1: CUANTITATIVO ---
    with tab1:
        c1, c2 = st.columns(2)
        with c1:
            fig_bar = px.bar(df_filtered.groupby('Categoria')['Utilidad_Total'].sum().reset_index(), 
                             x='Categoria', y='Utilidad_Total', template="plotly_dark", title="Rentabilidad por Segmento")
            st.plotly_chart(fig_bar, use_container_width=True)
        with c2:
            fig_stock = px.scatter(df_filtered, x='Stock_Actual', y='Utilidad_Total', color='Categoria',
                                   template="plotly_dark", title="Relación Stock vs Ganancia")
            st.plotly_chart(fig_stock, use_container_width=True)

    # --- TAB 3: IA ---
    with tab3:
        st.subheader("Consultoría Estratégica con IA")
        if st.button("🧠 Ejecutar Diagnóstico Maestro"):
            if groq_key:
                with st.spinner("Analizando micro-datos..."):
                    client = Groq(api_key=groq_key)
                    prompt = f"Analiza estos datos financieros: Ingresos ${rev}, Utilidad ${util}. Proporciona 3 puntos críticos de mejora."
                    chat = client.chat.completions.create(
                        model="llama-3.3-70b-versatile",
                        messages=[{"role": "user", "content": prompt}]
                    )
                    st.markdown(f'<div class="ai-container">{chat.choices[0].message.content}</div>', unsafe_allow_html=True)
            else:
                st.warning("Configura tu API Key en el lateral.")

    # --- TAB 4: SANEAMIENTO (TU LÓGICA DE LIMPIEZA) ---
    with tab4:
        st.subheader("🧹 Limpieza y Consolidación")
        
        # 1. Limpieza en Cascada de Inventario
        df_inv = df_invO.copy()
        cond_cat = (df_inv['Categoria'] == '???')
        cond_stk = (pd.to_numeric(df_inv['Stock_Actual'], errors='coerce') <= 0)
        cond_lead = (df_inv['Lead_Time_Dias'].isna())

        df_inv1 = df_inv[~(cond_cat & cond_stk & cond_lead)].copy()
        df_inv2 = df_inv1[~(cond_cat & cond_lead)].copy()
        df_inv3 = df_inv2[~(cond_cat & cond_stk)].copy()

        # 2. Imputación
        mediana_lead = pd.to_numeric(df_inv3['Lead_Time_Dias'], errors='coerce').median()
        df_inv3['Lead_Time_Dias'] = df_inv3['Lead_Time_Dias'].fillna(mediana_lead)
        
        # 3. Cruce Final
        df_rich = pd.merge(df_trans, df_inv3, on='SKU_ID', how='left')
        df_full = pd.merge(df_rich, df_feed, on='Transaccion_ID', how='left')

        # Visualización de Resultados
        p_final = (df_inv3.shape[0]/df_invO.shape[0])*100
        st.info(f"Integridad de Inventarios: {p_final:.2f}%")
        st.progress(p_final/100)
        
        st.write("### Vista Previa del Cruce Maestro")
        st.dataframe(df_full.head(10), use_container_width=True)
        
        st.download_button("📥 Descargar Data Maestra Limpia", df_full.to_csv(index=False), "data_auditoria_final.csv")

else:
    st.info("🌙 Sistema en espera. Cargue el archivo CSV local para comenzar.")

