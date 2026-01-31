import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from groq import Groq

# Configuración de la página
st.set_page_config(page_title="Data Intelligence Dashboard", layout="wide")

# --- TÍTULO Y CARGA DE ARCHIVO ---
st.title("🚀 Dashboard de Operaciones Críticas")
st.markdown("Sube tu archivo `df_consolidado.csv` para comenzar el análisis.")

# Widget para subir el archivo
uploaded_file = st.file_uploader("Elige tu archivo CSV", type="csv")

# Función de limpieza y procesamiento (Se ejecuta solo al subir el archivo)
def process_data(file):
    try:
        df = pd.read_csv(file)
        
        # 1. Asegurar tipos de datos numéricos (Evita errores de cálculo)
        cols_num = ['Precio_Venta_Final', 'Costo_Unitario_USD', 'Cantidad_Vendida', 'Costo_Envio', 'Satisfaccion_NPS']
        for col in cols_num:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        
        # 2. Lógica de Utilidad
        if all(c in df.columns for c in ['Precio_Venta_Final', 'Cantidad_Vendida', 'Costo_Unitario_USD', 'Costo_Envio']):
            df['Utilidad_Total'] = (df['Precio_Venta_Final'] * df['Cantidad_Vendida']) - \
                                   (df['Costo_Unitario_USD'] * df['Cantidad_Vendida']) - \
                                   df['Costo_Envio']
        
        # 3. Limpieza de etiquetas para visualización
        if 'Categoria' in df.columns:
            df['Categoria'] = df['Categoria'].fillna('No Catalogado (Fantasma)')
            
        return df
    except Exception as e:
        st.error(f"Error procesando el archivo: {e}")
        return None

# --- LÓGICA PRINCIPAL ---
if uploaded_file is not None:
    df = process_data(uploaded_file)
    
    if df is not None:
        # --- FILTROS EN BARRA LATERAL ---
        st.sidebar.header("🕹️ Filtros de Datos")
        
        # Filtro de Ciudad
        ciudades = st.sidebar.multiselect(
            "Selecciona Ciudades:", 
            options=df['Ciudad_Destino'].unique(), 
            default=df['Ciudad_Destino'].unique()
        )
        
        # Filtro de Categoría
        categorias = st.sidebar.multiselect(
            "Selecciona Categorías:", 
            options=df['Categoria'].unique(), 
            default=df['Categoria'].unique()
        )
        
        df_filt = df[(df['Ciudad_Destino'].isin(ciudades)) & (df['Categoria'].isin(categorias))]

        # --- MÉTRICAS ---
        m1, m2, m3, m4 = st.columns(4)
        with m1:
            st.metric("Ventas Totales", f"${df_filt['Precio_Venta_Final'].sum():,.2f}")
        with m2:
            utilidad = df_filt['Utilidad_Total'].sum()
            st.metric("Utilidad Neta", f"${utilidad:,.2f}", delta_color="normal")
        with m3:
            nps = df_filt[df_filt['Satisfaccion_NPS'] != 0]['Satisfaccion_NPS'].mean()
            st.metric("NPS Promedio", f"{nps:.1f}" if not np.isnan(nps) else "N/A")
        with m4:
            fantasmas = len(df_filt[df_filt['Categoria'].str.contains('Fantasma', na=False)])
            st.metric("Registros Críticos", fantasmas)

        st.divider()

        # --- GRÁFICAS ---
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("💰 Rentabilidad por Categoría")
            fig_rent = px.bar(
                df_filt.groupby('Categoria')['Utilidad_Total'].sum().reset_index(),
                x='Categoria', y='Utilidad_Total', 
                color='Utilidad_Total', color_continuous_scale='RdYlGn'
            )
            st.plotly_chart(fig_rent, use_container_width=True)

        with col2:
            st.subheader("📍 Desempeño por Ciudad")
            fig_city = px.box(df_filt, x='Ciudad_Destino', y='Utilidad_Total', color='Ciudad_Destino')
            st.plotly_chart(fig_city, use_container_width=True)

        # --- SECCIÓN DE IA ---
        st.divider()
        st.subheader("🤖 Análisis Inteligente con Groq")
        api_key = st.text_input("Ingresa tu Groq API Key:", type="password")
        pregunta = st.text_input("Haz una pregunta sobre los datos subidos:")

        if api_key and pregunta:
            try:
                client = Groq(api_key=api_key)
                # Resumen compacto para la IA
                resumen = df_filt.describe().to_string()
                
                response = client.chat.completions.create(
                    messages=[
                        {"role": "system", "content": "Analiza estos datos contables y logísticos. Sé breve y directo."},
                        {"role": "user", "content": f"Datos: {resumen[:1000]}... Pregunta: {pregunta}"}
                    ],
                    model="llama3-8b-8192",
                )
                st.info(response.choices[0].message.content)
            except Exception as e:
                st.error(f"Error con la IA: {e}")

else:
    st.info("👆 Por favor, sube un archivo CSV para generar el reporte.")
    st.image("https://streamlit.io/images/brand/streamlit-mark-color.png", width=100)
