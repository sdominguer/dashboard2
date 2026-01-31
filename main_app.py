import streamlit as st
import pandas as pd
import plotly.express as px

# Configuración de la página
st.set_page_config(page_title="Dashboard Logística & Ventas", layout="wide")

# Cargar datos
@st.cache_data
def load_data():
    df = pd.read_csv('df_consolidado.csv')
    # Recalculamos utilidad por seguridad
    df['Utilidad_Total'] = (df['Precio_Venta_Final'] * df['Cantidad_Vendida']) - \
                           (df['Costo_Unitario_USD'] * df['Cantidad_Vendida']) - \
                           df['Costo_Envio']
    return df

df = load_data()

# --- TÍTULO Y MÉTRICAS CLAVE ---
st.title("📊 Análisis de Operaciones y Rentabilidad")
st.markdown("### KPIs Principales")

m1, m2, m3, m4 = st.columns(4)
m1.metric("Ventas Totales", f"${df['Precio_Venta_Final'].sum():,.0f}")
m2.metric("Utilidad Total", f"${df['Utilidad_Total'].sum():,.0f}", delta_color="inverse")
m3.metric("NPS Promedio", round(df[df['Satisfaccion_NPS'] != 0]['Satisfaccion_NPS'].mean(), 2))
m4.metric("SKUs Fantasmas", len(df[df['Categoria'] == 'No Catalogado (Fantasma)']))

st.divider()

# --- FILTROS ---
st.sidebar.header("Filtros de Análisis")
ciudad = st.sidebar.multiselect("Selecciona Ciudad:", options=df['Ciudad_Destino'].unique(), default=df['Ciudad_Destino'].unique())
df_filt = df[df['Ciudad_Destino'].isin(ciudad)]

# --- VISUALIZACIONES ---
col1, col2 = st.columns(2)

with col1:
    st.subheader("Rentabilidad por Categoría")
    # Agrupamos para ver quién pierde dinero
    fig_cat = px.bar(df_filt.groupby('Categoria')['Utilidad_Total'].sum().reset_index(), 
                     x='Categoria', y='Utilidad_Total', 
                     color='Utilidad_Total', color_continuous_scale='RdYlGn',
                     title="Utilidad Neta por Segmento")
    st.plotly_chart(fig_cat, use_container_width=True)

with col2:
    st.subheader("Relación: Tiempo Entrega vs Satisfacción")
    # Solo tomamos donde hay feedback real
    df_feed = df_filt[df_filt['Rating_Logistica'] > 0]
    fig_scat = px.scatter(df_feed, x='Tiempo_Entrega_Real', y='Rating_Logistica', 
                          color='Estado_Envio', size='Cantidad_Vendida',
                          title="¿A más demora, peor calificación?")
    st.plotly_chart(fig_scat, use_container_width=True)

# --- ANÁLISIS DE ERRORES ---
st.divider()
st.subheader("🔍 Auditoría de Integridad de Datos")
col3, col4 = st.columns(2)

with col3:
    st.write("Top 5 Ciudades con más 'SKUs Fantasmas'")
    fantasmas = df[df['Categoria'] == 'No Catalogado (Fantasma)']
    st.table(fantasmas['Ciudad_Destino'].value_counts().head(5))

with col4:
    st.write("Alertas de Margen Negativo (Pérdidas Críticas)")
    perdidas = df_filt[df_filt['Utilidad_Total'] < 0].sort_values('Utilidad_Total').head(10)
    st.dataframe(perdidas[['Transaccion_ID', 'SKU_ID', 'Utilidad_Total', 'Ciudad_Destino']])

st.success("Dashboard actualizado correctamente.")
