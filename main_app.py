import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

st.set_page_config(page_title="Executive Sales Analytics", layout="wide")

# Estilos de color personalizados (Ventas y Negocios)
COLOR_SUCCESS = "#28a745" # Verde Ventas
COLOR_DANGER = "#dc3545"  # Rojo Pérdidas
COLOR_NEUTRAL = "#007bff" # Azul Logística

uploaded_file = st.file_uploader("📂 Cargar Reporte Consolidado (CSV)", type="csv")

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    
    # Procesamiento rápido de métricas
    df['Utilidad_Total'] = (df['Precio_Venta_Final'] * df['Cantidad_Vendida']) - (df['Costo_Unitario_USD'] * df['Cantidad_Vendida']) - df['Costo_Envio']
    
    st.title("📊 Financial & Operational Dashboard")
    st.divider()

    # --- 1. SECCIÓN CUANTITATIVA (Métricas de Dinero) ---
    st.subheader("🔢 Indicadores Cuantitativos (Performance)")
    c1, c2, c3, c4 = st.columns(4)
    
    total_revenue = df['Precio_Venta_Final'].sum()
    total_profit = df['Utilidad_Total'].sum()
    profit_margin = (total_profit / total_revenue) * 100 if total_revenue != 0 else 0
    
    c1.metric("Ingresos Brutos", f"${total_revenue:,.2f}")
    c2.metric("Utilidad Neta", f"${total_profit:,.2f}", delta=f"{profit_margin:.1f}% Margen")
    c3.metric("Ticket Promedio", f"${df['Precio_Venta_Final'].mean():,.2f}")
    c4.metric("Volumen de Unidades", f"{df['Cantidad_Vendida'].sum():,.0f}")

    # --- 2. SECCIÓN GRÁFICA (Tendencias y Distribución) ---
    st.divider()
    st.subheader("📈 Análisis Gráfico Visual")
    g1, g2 = st.columns(2)

    with g1:
        # Gráfico de barras con escala de colores de ventas (Rojo a Verde)
        fig_rent = px.bar(
            df.groupby('Categoria')['Utilidad_Total'].sum().reset_index(),
            x='Categoria', y='Utilidad_Total',
            title="Rentabilidad por Categoría",
            color='Utilidad_Total',
            color_continuous_scale=[COLOR_DANGER, "#ffc107", COLOR_SUCCESS]
        )
        st.plotly_chart(fig_rent, use_container_width=True)

    with g2:
        # Gráfico de dispersión para eficiencia logística
        fig_disp = px.scatter(
            df, x='Precio_Venta_Final', y='Costo_Envio',
            color='Estado_Envio', size='Cantidad_Vendida',
            title="Relación Precio vs. Costo de Envío",
            color_discrete_sequence=px.colors.qualitative.Safe
        )
        st.plotly_chart(fig_disp, use_container_width=True)

    # --- 3. SECCIÓN CUALITATIVA (Feedback y Soporte) ---
    st.divider()
    st.subheader("🗣️ Análisis Cualitativo (Voz del Cliente)")
    f1, f2 = st.columns([1, 2])

    with f1:
        # Resumen de satisfacción
        avg_nps = df[df['Satisfaccion_NPS'] > 0]['Satisfaccion_NPS'].mean()
        st.info(f"**NPS General:** {avg_nps:.1f} / 100")
        
        # Conteo de tickets
        tickets = df['Ticket_Soporte_Abierto'].value_counts()
        fig_tick = px.pie(values=tickets.values, names=tickets.index, 
                          title="Estado de Tickets",
                          color_discrete_map={'Sí': COLOR_DANGER, 'No': COLOR_SUCCESS, 'Sin Registro': '#6c757d'})
        st.plotly_chart(fig_tick, use_container_width=True)

    with f2:
        # Tabla de comentarios críticos (Cualitativo puro)
        st.write("**Últimos Comentarios de Clientes (Rating Bajo):**")
        criticos = df[df['Rating_Producto'] <= 2][['SKU_ID', 'Comentario_Texto', 'Rating_Producto']].head(10)
        st.dataframe(criticos, use_container_width=True)

else:
    st.warning("Esperando archivo CSV para segmentar datos...")
