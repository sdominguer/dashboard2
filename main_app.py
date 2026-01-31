import streamlit as st
import pandas as pd
import plotly.express as px
import os

# Intentamos importar Groq (Manejo de errores amigable)
try:
    from groq import Groq
except ImportError:
    st.error("⚠️ Error: Falta instalar la librería 'groq'. Agrégala a tu requirements.txt")
    Groq = None

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="AgroAnalytics Pro + AI",
    layout="wide",
    page_icon="🌾",
    initial_sidebar_state="expanded"
)

# --- PALETA TIERRA (Contrastada para ambos modos) ---
EARTH_PALETTE = ["#556B2F", "#8B4513", "#CD853F", "#DAA520", "#BC8F8F", "#2E8B57"]

# --- CSS LIMPIO (ESTILO AGRO-CLEAN) ---
st.markdown("""
    <style>
    /* Ajustes generales: más espacio y limpieza */
    .block-container { padding-top: 3rem; padding-bottom: 3rem; max-width: 95%; }
    
    /* Fuentes: Gris carbón suave en lugar de negro puro */
    h1, h2, h3 { 
        font-family: 'Inter', 'Segoe UI', sans-serif; 
        color: #454B40; 
        font-weight: 500;
        letter-spacing: -0.5px;
    }
    
    /* Tarjetas de Métricas: Estilo 'Float' sin bordes agresivos */
    div[data-testid="metric-container"] {
        background-color: #FFFFFF;
        border: 1px solid #F0F2F0;
        border-bottom: 2px solid #E0E4D9;
        padding: 20px;
        border-radius: 12px;
    }
    
    /* --- TABS SUTILES Y ELEGANTES --- */
    .stTabs [data-baseweb="tab-list"] {
        gap: 30px; /* Más espacio entre palabras */
        background-color: transparent;
        border-bottom: 1px solid #E6EAE6; /* Línea divisoria muy fina */
        margin-bottom: 20px;
    }

    .stTabs [data-baseweb="tab"] {
        height: 50px;
        background-color: transparent !important;
        border: none !important;
    }

    /* Texto de los Tabs: Gris suave, tamaño equilibrado */
    .stTabs [data-baseweb="tab"] p {
        color: #9BA398 !important; /* Gris ceniza suave */
        font-size: 19px !important;
        font-weight: 400 !important;
        transition: all 0.4s ease;
    }

    /* Tab Seleccionado: Solo texto oscuro y una línea minimalista */
    .stTabs [aria-selected="true"] p {
        color: #556B2F !important; /* El verde solo aparece aquí */
        font-weight: 600 !important;
    }

    /* La barrita indicadora de Streamlit hecha más fina */
    .stTabs [data-baseweb="tab-highlight"] {
        background-color: #556B2F !important;
        height: 2px !important;
    }
    
    /* Botones: Estilo minimalista */
    .stButton > button {
        background-color: #F9FBF9;
        color: #556B2F;
        border: 1px solid #E0E4D9;
        border-radius: 8px;
        padding: 0.5rem 2rem;
        transition: 0.3s;
    }
    .stButton > button:hover {
        background-color: #556B2F;
        color: white;
        border-color: #556B2F;
    }
    </style>
""", unsafe_allow_html=True)

# --- FUNCIÓN DE CARGA ---
@st.cache_data
def load_data(file):
    df = pd.read_csv(file)
    if 'Fecha_Ultima_Auditoria' in df.columns:
        df['Fecha_Ultima_Auditoria'] = pd.to_datetime(df['Fecha_Ultima_Auditoria'])
    return df

# --- FUNCIÓN GENERADORA DE CONTEXTO PARA LA IA ---
def generate_analysis(df, api_key):
    """Envía los datos resumidos a Groq para obtener un análisis"""
    client = Groq(api_key=api_key)
    
    # Preparamos los datos resumidos para que la IA entienda las gráficas sin verlas
    stats_dept = df.groupby("Departamento")["Produccion_Anual_Ton"].sum().to_string()
    stats_cultivo = df.groupby("Tipo_Cultivo")[["Area_Hectareas", "Produccion_Anual_Ton"]].sum().to_string()
    corr = df[["Area_Hectareas", "Produccion_Anual_Ton", "Precio_Venta_Por_Ton_COP"]].corr().to_string()
    
    prompt = f"""
    Actúa como un Agrónomo Senior experto en Ciencia de Datos.
    Analiza los siguientes datos resumidos de una cosecha en Colombia y genera un reporte ejecutivo de 3 párrafos breves.
    
    Datos de Producción por Departamento:
    {stats_dept}
    
    Datos de Cultivos (Área y Producción):
    {stats_cultivo}
    
    Correlaciones clave:
    {corr}
    
    Tu tarea:
    1. Identifica qué departamento lidera la producción.
    2. Analiza qué cultivo es el más eficiente (relación área/producción).
    3. Menciona si existe una correlación interesante entre tamaño de finca y productividad.
    4. Da una recomendación estratégica corta.
    
    Usa formato Markdown con negritas para los hallazgos clave. Responde en Español.
    """
    
    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=600
        )
        return completion.choices[0].message.content
    except Exception as e:
        return f"Error al conectar con la IA: {e}"

# --- SIDEBAR ---
with st.sidebar:
    st.title("🚜 Panel de Control")
    
    # SECCIÓN DE API KEY
    with st.expander("🔑 Configuración IA", expanded=True):
        st.markdown("Para activar el análisis inteligente, ingresa tu API Key de Groq.")
        groq_api_key = st.text_input("Groq API Key", type="password")
        st.caption("[Consigue tu Key gratis aquí](https://console.groq.com)")

    st.divider()
    
    uploaded_file = st.file_uploader("📂 Cargar Datos (CSV)", type=["csv"])
    
    if uploaded_file:
        df_raw = load_data(uploaded_file)
        
        st.subheader("Filtros")
        all_depts = sorted(df_raw["Departamento"].unique())
        sel_depts = st.multiselect("Departamentos", all_depts, default=all_depts[:2])
            
        all_crops = sorted(df_raw["Tipo_Cultivo"].unique())
        sel_crops = st.multiselect("Cultivos", all_crops, default=all_crops)
        
        st.divider()
        st.info("💡 Consejo: Filtra los datos para que la IA analice segmentos específicos.")

# --- LÓGICA PRINCIPAL ---
if uploaded_file and sel_depts and sel_crops:
    # Aplicar filtros
    df = df_raw[
        (df_raw["Departamento"].isin(sel_depts)) & 
        (df_raw["Tipo_Cultivo"].isin(sel_crops))
    ].copy()

    # TÍTULO PRINCIPAL
    st.title("🌾 Inteligencia de Negocios Agrícola")
    st.markdown(f"**Panorama actual:** {len(sel_depts)} departamentos | {len(sel_crops)} cultivos analizados.")

    # --- SECCIÓN 1: KPIS (TARJETAS LIMPIAS) ---
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    
    with kpi1:
        with st.container(border=True):
            st.metric("Producción Total", f"{df['Produccion_Anual_Ton'].sum():,.0f} Ton")
    with kpi2:
        with st.container(border=True):
            st.metric("Área Cultivada", f"{df['Area_Hectareas'].sum():,.0f} Ha")
    with kpi3:
        with st.container(border=True):
            st.metric("Rendimiento Prom.", f"{(df['Produccion_Anual_Ton'].sum()/df['Area_Hectareas'].sum()):.2f} Ton/Ha")
    with kpi4:
        with st.container(border=True):
            st.metric("Fincas Activas", f"{len(df)}")

    # --- SECCIÓN NUEVA: ANÁLISIS IA ---
    st.markdown("###")
    
    # Contenedor especial para la IA
    with st.container(border=True):
        col_ia_1, col_ia_2 = st.columns([1, 4])
        
        with col_ia_1:
            st.image("https://cdn-icons-png.flaticon.com/512/2040/2040946.png", width=80)
            st.markdown("**IA Agrónoma**")
            
        with col_ia_2:
            st.subheader("✨ Análisis Inteligente de Datos")
            st.write("Genera una interpretación automática de las gráficas actuales usando Llama 3.3.")
            
            if st.button("🧠 Analizar Hallazgos con IA"):
                if not groq_api_key:
                    st.warning("⚠️ Por favor ingresa tu API Key en la barra lateral primero.")
                else:
                    with st.spinner("La IA está analizando tus datos..."):
                        analysis_result = generate_analysis(df, groq_api_key)
                        st.success("Análisis completado")
                        st.markdown(analysis_result)

    st.markdown("###") 

    # --- SECCIÓN 2: GRÁFICOS (ESTILO LIMPIO) ---
    tab_panorama, tab_detalles, tab_scatter = st.tabs(["📊 Panorama General", "🔬 Detalles Técnicos", "📍 Relación Variables"])

    # TAB 1: VISIÓN GENERAL
    with tab_panorama:
        st.subheader("Distribución de la Producción")
        
        col_graf1, col_graf2 = st.columns([2, 1], gap="large")
        
        with col_graf1:
            # Bar Chart Limpio
            fig_bar = px.bar(
                df.groupby("Departamento")["Produccion_Anual_Ton"].sum().reset_index().sort_values("Produccion_Anual_Ton", ascending=True),
                x="Produccion_Anual_Ton", y="Departamento",
                orientation='h',
                title="<b>Producción por Departamento</b>",
                color_discrete_sequence=[EARTH_PALETTE[0]],
                template="plotly_white"
            )
            fig_bar.update_layout(plot_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig_bar, use_container_width=True)

        with col_graf2:
            # Donut Chart
            fig_pie = px.pie(
                df, names="Tipo_Cultivo", values="Area_Hectareas",
                title="<b>Uso del Suelo (Ha)</b>",
                color_discrete_sequence=EARTH_PALETTE,
                hole=0.5,
                template="plotly_white"
            )
            fig_pie.update_layout(legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5))
            st.plotly_chart(fig_pie, use_container_width=True)

    # TAB 2: DETALLES TÉCNICOS
    with tab_detalles:
        st.subheader("Análisis de Calidad")
        col_d1, col_d2 = st.columns(2, gap="medium")
        
        with col_d1:
            st.markdown("**Tecnificación vs Riego**")
            fig_sun = px.sunburst(
                df, path=['Nivel_Tecnificacion', 'Sistema_Riego_Tecnificado'], 
                values='Produccion_Anual_Ton',
                color_discrete_sequence=EARTH_PALETTE,
                template="plotly_white"
            )
            st.plotly_chart(fig_sun, use_container_width=True)
                
        with col_d2:
            st.markdown("**Precios por Tipo de Suelo**")
            fig_box = px.box(
                df, x="Tipo_Suelo", y="Precio_Venta_Por_Ton_COP",
                color="Tipo_Suelo",
                color_discrete_sequence=EARTH_PALETTE,
                template="plotly_white"
            )
            fig_box.update_layout(showlegend=False)
            st.plotly_chart(fig_box, use_container_width=True)

    # TAB 3: SCATTER
    with tab_scatter:
        st.subheader("Eficiencia Productiva")
        fig_scatter = px.scatter(
            df, 
            x="Area_Hectareas", 
            y="Produccion_Anual_Ton",
            color="Departamento",
            size="Precio_Venta_Por_Ton_COP",
            hover_name="ID_Finca",
            color_discrete_sequence=EARTH_PALETTE,
            template="plotly_white",
            title="<b>Relación Área vs. Producción</b> (Burbuja = Precio)"
        )
        fig_scatter.update_layout(height=500, plot_bgcolor="rgba(0,0,0,0)")
        fig_scatter.update_xaxes(showgrid=True, gridwidth=1, gridcolor='#F0F0F0')
        fig_scatter.update_yaxes(showgrid=True, gridwidth=1, gridcolor='#F0F0F0')
        st.plotly_chart(fig_scatter, use_container_width=True)

elif not uploaded_file:
    # PANTALLA DE INICIO
    col_center, _ = st.columns([1, 0.1])
    with col_center:
        st.info("👋 **Bienvenido.** Por favor cargue su archivo `agro_colombia.csv` en el menú lateral.")
        st.image("https://images.unsplash.com/photo-1625246333195-78d9c38ad449?q=80&w=1000&auto=format&fit=crop", caption="Agro Data Analytics", use_column_width=True)
