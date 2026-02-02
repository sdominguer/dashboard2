import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
from groq import Groq
import re

# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Auditoría Pro: Operaciones & IA", layout="wide", page_icon="🌙")

# --- 2. ESTILOS CSS (Mantenidos) ---
COLOR_AZUL = "#1E88E5"
COLOR_GRIS = "#475569"
COLOR_ROJO = "#EF4444"
COLOR_VERDE = "#10B981"
COLOR_FONDO = "#0E1117"

st.markdown(f"""
    <style>
    .stApp {{ background-color: {COLOR_FONDO}; color: #FFFFFF; }}
    h1, h2, h3, h4, p, span, label {{ color: #FFFFFF !important; }}
    div[data-testid="metric-container"] {{ background-color: transparent !important; border: none !important; }}
    [data-testid="stMetricValue"] {{ font-size: 32px !important; font-weight: 700 !important; }}
    .ai-container {{ background-color: #161B22; border-radius: 12px; padding: 25px; border-left: 5px solid {COLOR_AZUL}; margin-top: 15px; }}
    .question-box {{ background-color: #161B22; padding: 20px; border-radius: 10px; border: 1px solid {COLOR_GRIS}; margin-bottom: 20px; }}
    </style>
""", unsafe_allow_html=True)

# --- 3. LÓGICA DE DATOS MEJORADA ---
@st.cache_data
def load_and_process(file_source):
    """Carga y procesa archivos ya sea desde upload local o URL de Teams"""
    df = pd.read_csv(file_source)
    cols_num = ['Precio_Venta_Final', 'Costo_Unitario_USD', 'Cantidad_Vendida', 'Costo_Envio', 'Satisfaccion_NPS', 'Stock_Actual']
    for col in cols_num:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    
    if all(c in df.columns for c in ['Precio_Venta_Final', 'Cantidad_Vendida', 'Costo_Unitario_USD', 'Costo_Envio']):
        df['Utilidad_Total'] = (df['Precio_Venta_Final'] * df['Cantidad_Vendida']) - \
                               (df['Costo_Unitario_USD'] * df['Cantidad_Vendida']) - \
                               df['Costo_Envio']
    return df

# --- 4. SIDEBAR ---
with st.sidebar:
    st.title("🚜 Operaciones Pro")
    with st.expander("🔑 Configuración IA", expanded=False):
        # Intentamos obtener la key de secrets, si no, pedimos input
        default_key = st.secrets.get("GROQ_API_KEY", "")
        groq_key = st.text_input("Groq API Key", type="password", value=default_key)
    
    # El disparador principal sigue siendo el archivo manual
    uploaded_file = st.file_uploader("📂 Cargar Datos Maestro (Local)", type=["csv"])

# --- 5. LÓGICA DE CARGA HÍBRIDA (EL CORAZÓN DEL CAMBIO) ---
if uploaded_file:
    # 5.1 Carga del archivo local
    df_raw = load_and_process(uploaded_file)
    
    # 5.2 Carga AUTOMÁTICA de los 3 archivos de Teams (Solo si se cargó el local)
    # Se guardan en st.session_state para que estén disponibles globalmente
    try:
        if 'teams_data' not in st.session_state:
            with st.status("Conectando con servidores de Teams...", expanded=False) as status:
                st.write("Descargando archivo de Ventas...")
                df_t1 = load_and_process(st.secrets["URL_TEAMS_1"])
                st.write("Descargando archivo de Inventarios...")
                df_t2 = load_and_process(st.secrets["URL_TEAMS_2"])
                st.write("Descargando archivo de Logística...")
                df_t3 = load_and_process(st.secrets["URL_TEAMS_3"])
                st.session_state.teams_data = {"ventas": df_t1, "inventario": df_t2, "logistica": df_t3}
                status.update(label="✅ Datos de Teams sincronizados", state="complete")
        
        # Atajos para usar los dataframes de Teams
        df_teams_1 = st.session_state.teams_data["ventas"]
        df_teams_2 = st.session_state.teams_data["inventario"]
        df_teams_3 = st.session_state.teams_data["logistica"]
        df_inv = st.session_state.teams_data["inventario"]
        df_invO = st.session_state.teams_data["inventario"]
        df_trans_raw=st.session_state.teams_data["logistica"]
        df_feed=st.session_state.teams_data["ventas"]
     

    except Exception as e:
        st.error(f"Error al leer de Teams. Verifica los enlaces en Secrets. Error: {e}")

    # --- 6. DASHBOARD PRINCIPAL ---
    # Filtros sobre df_raw (archivo local)
    all_cats = sorted(df_raw['Categoria'].unique())
    sel_cats = st.sidebar.multiselect("Categorías", all_cats, default=all_cats)
    limit = st.sidebar.slider("Muestra de datos", 50, len(df_raw), 500)
    
    df = df_raw[df_raw['Categoria'].isin(sel_cats)].head(limit)
    
    # Métricas y Tabs (Se mantiene tu lógica original)
    rev_total = df['Precio_Venta_Final'].sum()
    profit_total = df['Utilidad_Total'].sum()

    st.title("📊 Intelligence Business Dashboard")
    
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Ingresos Totales", f"${rev_total:,.0f}")
    m2.metric("Utilidad Neta", f"${profit_total:,.0f}", 
              delta=f"{(profit_total/rev_total*100):.1f}%" if rev_total > 0 else "0%")
    m3.metric("NPS (Mediana)", f"{df[df['Satisfaccion_NPS']>0]['Satisfaccion_NPS'].median():.1f}")
    m4.metric("Unidades", f"{df['Cantidad_Vendida'].sum():,.0f}")

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




        # 1. Definimos las máscaras (condiciones)
        cond_categoria = (df_inv['Categoria'] == '???')
        cond_stock = (df_inv['Stock_Actual'].isna()) | (pd.to_numeric(df_inv['Stock_Actual'], errors='coerce') <= 0)
        cond_lead_time = (df_inv['Lead_Time_Dias'].isna())
        
        # 2. Combinamos las 3 condiciones con el operador & (AND)
        # Esto identifica las filas que cumplen TODO al tiempo
        filas_a_eliminar = cond_categoria & cond_stock & cond_lead_time
        

        st.caption("Proceso automático de filtrado y depuración de datos provenientes de Teams")

        # Usamos un contenedor con borde para agrupar la limpieza
        with st.container():
            st.info("📊 **Fase 1: Eliminación de Registros Inconsistentes: Tabla de Inventarios**")
            
            # Creamos columnas para mostrar el progreso de forma visual
            col_a, col_b, col_c = st.columns(3)
            df_inv1=df_inv[~filas_a_eliminar].copy()
            filas_a_eliminar2 = cond_categoria & cond_lead_time
            # 3. Mantenemos solo lo que NO cumple la combinación (usando el signo ~)
            df_inv2=df_inv1[~filas_a_eliminar2].copy()
            filas_a_eliminar3 = cond_categoria & cond_stock
            # 3. Mantenemos solo lo que NO cumple la combinación (usando el signo ~)
            df_inv3=df_inv2[~filas_a_eliminar3].copy()
            
            # Cálculo de porcentajes para reusar
            p1 = (df_inv1.shape[0]/df_invO.shape[0])*100
            p2 = (df_inv2.shape[0]/df_invO.shape[0])*100
            p3 = (df_inv3.shape[0]/df_invO.shape[0])*100
            p_final = (df_inv3.shape[0]/df_invO.shape[0])*100
            df_inv=df_inv3
        
            with col_a:
                st.metric("Filtro Multicondición", f"{p1:.1f}%", help="Categoría=??? + Stock Negativo/NaN + Sin Lead Time")
            with col_b:
                st.metric("Filtro Lead Time", f"{p2:.1f}%", help="Categoría=??? + Sin Lead Time")
            with col_c:
                st.metric("Filtro Stock Crítico", f"{p3:.1f}%", help="Categoría=??? + Stock Negativo/NaN")
        
            # Barra de estado final
            st.write("**Integridad Final de la tabla:**")
            st.progress(p_final / 100)
            st.markdown(f"> **Conclusión:** Se ha preservado el **{p_final:.2f}%** de la data original de inventarios tras aplicar las reglas de negocio.")
        
        st.divider()
        
        # Sección de Imputación con diseño de "Pasos"
        st.markdown(f"### 🛠️ Protocolo de Imputación de Datos")
           
        with st.expander("Ver detalles del proceso técnico", expanded=True):
            
            c1, c2, c3 = st.columns([1, 1, 1])
            
            with c1:
                st.markdown(f"""
                <div style="background-color:#161B22; padding:15px; border-radius:10px; border-top: 3px solid {COLOR_AZUL}">
                <h5 style="margin:0">1. Estandarización</h5>
                <p style="font-size:0.85rem; color:#8b949e">Conversión a numérica forzando NaN en valores tipo texto(Tablas:Inventario,Ventas,Feedback).</p>
                </div>
                """, unsafe_allow_html=True)
        
            with c2:
                st.markdown(f"""
                <div style="background-color:#161B22; padding:15px; border-radius:10px; border-top: 3px solid {COLOR_VERDE}">
                <h5 style="margin:0">2. Análisis Estadístico</h5>
                <p style="font-size:0.85rem; color:#8b949e">Cálculo de mediana robusta sobre valores numéricos existentes para evitar sesgos(Tablas:Inventario,Ventas,Feedback).</p>
                </div>
                """, unsafe_allow_html=True)
        
            with c3:
                st.markdown(f"""
                <div style="background-color:#161B22; padding:15px; border-radius:10px; border-top: 3px solid #FFD700">
                <h5 style="margin:0">3. Regex Parsing</h5>
                <p style="font-size:0.85rem; color:#8b949e">Aplicación de expresiones regulares para identificar categorías mediante patrones(Tablas:Inventario).</p>
                </div>
                """, unsafe_allow_html=True)

    
    def audit_report(df, name):
        print(f"--- Reporte: {name} ---")
        print(f"Nulos por columna:\n{df.isnull().sum() / len(df) * 100}%")
        print(f"Duplicados: {df.duplicated().sum()}")
        print("-" * 30)

    audit_report(df_inv, "Inventario")
    audit_report(df_trans_raw, "Transacciones")
    audit_report(df_feed, "Feedback")
    
    import re

    def simplificar_lead_time(valor):
        val_str = str(valor).lower().strip()
        if val_str == 'inmediato': return 0.0
        numeros = re.findall(r'\d+', val_str)
        return float(max(numeros, key=int)) if numeros else np.nan

        # 1. Limpiamos los textos a números (dejando los NaN como tales)
    df_inv['Lead_Time_Dias'] = df_inv['Lead_Time_Dias'].apply(simplificar_lead_time)
    
    # 2. Llenamos los NaN resultantes con la mediana de la columna
    mediana_lead = df_inv['Lead_Time_Dias'].median()
    df_inv['Lead_Time_Dias'] = df_inv['Lead_Time_Dias'].fillna(mediana_lead)

    # Llenar vacíos con una etiqueta de control
    df_trans=pd.DataFrame(df_trans_raw.copy())
    #df_trans['Estado_Envio'] = df_trans_raw['Estado_Envio'].fillna('No especificado')

        # 1. Diccionario de mapeo para estandarizar
    mapeo_ciudades = {
        'MED': 'Medellín',
        'BOG': 'Bogotá',
    }
    
    # 3. Aplicamos el reemplazo (solo para las que coinciden con el diccionario)
    df_trans['Ciudad_Destino'] = df_trans['Ciudad_Destino'].replace(mapeo_ciudades)


    # 1. Definimos los valores que consideramos "ruido"
    ruido = ['---', 'N/A',"nan"]
    
    # 2. Limpiamos: pasamos a minúsculas, quitamos espacios y reemplazamos
    df_feed['Comentario_Texto'] = df_feed['Comentario_Texto'].astype(str).str.lower().str.strip()
    
    # 3. Reemplazamos el ruido y los nulos por "Sin comentario"
    df_feed['Comentario_Texto'] = df_feed['Comentario_Texto'].replace(ruido, 'sin comentario')
    df_feed['Comentario_Texto'] = df_feed['Comentario_Texto'].fillna('sin comentario')
    
    # 4. Verificamos los primeros resultados
    print("Muestra de comentarios limpios:")
    print(df_feed['Comentario_Texto'].unique()[:10])

    # 2. Reemplazamos tanto los nulos reales como las variantes de texto
    # Usamos fillna para los vacíos y replace para los que sí tienen texto "nan" o "N/A"
    df_feed['Recomienda_Marca'] = df_feed['Recomienda_Marca'].replace(['nan', 'n/a', 'None', 'N/A'], np.nan)
    df_feed['Recomienda_Marca'] = df_feed['Recomienda_Marca'].fillna('SIN RESPUESTA')
    
    # 3. Por si acaso quedaron como string 'nan' después del astype(str)
    df_feed.loc[df_feed['Recomienda_Marca'] == 'nan', 'Recomienda_Marca'] = 'SIN RESPUESTA'
    
    print(df_feed['Recomienda_Marca'].value_counts())

    # 1. Calculamos la mediana (ignorando los nulos automáticamente)
    mediana_envio = df_trans['Costo_Envio'].median()
    
    # 2. Rellenamos los vacíos con ese valor
    df_trans['Costo_Envio'] = df_trans['Costo_Envio'].fillna(mediana_envio)
    
    # 3. Verificamos que ya no queden nulos
    print(f"La mediana aplicada fue: {mediana_envio}")
    print(f"Nulos restantes en Costo_Envio: {df_trans['Costo_Envio'].isnull().sum()}")
    print(df_trans['Costo_Envio'])

    # Esto convierte 'norte', 'NORTE' y 'norte ' en 'Norte'
    df_inv['Bodega_Origen'] = df_inv['Bodega_Origen'].astype(str).str.strip().str.capitalize()
    
    # 2. Verificamos el conteo corregido
    print("Conteo de registros por Bodega (Corregido):")
    df_inv["Bodega_Origen"].value_counts()

        # 1. Convertimos la columna a numérica (forzando errores a NaN)
    # Esto convierte "25-30 días" o "Inmediato" en NaN temporalmente para calcular la mediana
    lead_time_numerico = pd.to_numeric(df_inv['Lead_Time_Dias'], errors='coerce')
    
    # 2. Calculamos la mediana de los valores que SÍ son números
    mediana_lead = lead_time_numerico.median()
    
    # 3. Llenamos los nulos originales en df_inv con esa mediana
    # Nota: Esto solo afectará a los que quedaron después de tu limpieza anterior
    df_inv['Lead_Time_Dias'] = df_inv['Lead_Time_Dias'].fillna(mediana_lead)
    
    # 4. (Opcional) Si también quieres reemplazar la palabra texto "nan" que mencionamos antes:
    df_inv['Lead_Time_Dias'] = df_inv['Lead_Time_Dias'].replace('nan', mediana_lead)
    
    print(f"La mediana calculada fue: {mediana_lead}")
    print(f"Valores nulos restantes: {df_inv['Lead_Time_Dias'].isna().sum()}")

        # Diccionario de normalización usando Regex
    mapa_categorias = {
        r'(?i)smart-?phones?': 'Smartphone',
        r'(?i)laptops?': 'Laptop',
        r'(?i)monitores?': 'Monitor',
        r'(?i)accesorios?': 'Accesorio',
        r'\?{3}': 'No Definido'
    }
    
    # Aplicar la limpieza
    for patron, reemplazo in mapa_categorias.items():
        df_inv['Categoria'] = df_inv['Categoria'].str.replace(patron, reemplazo, regex=True)
    
    print(df_inv['Categoria'].unique())

        # 1. Corregir Cantidad_Vendida: Valores negativos se convierten en 0
    # (También podrías usar .abs() si asumes que el número es correcto pero el signo no)
    df_trans['Cantidad_Vendida'] = df_trans['Cantidad_Vendida'].clip(lower=0)
    
    # 2. Guardar archivos actualizados en el entorno
    df_inv.to_csv('inventario_central_limpio.csv', index=False)
    df_trans.to_csv('transacciones_logistica_limpias.csv', index=False)
    df_feed.to_csv('feedback_clientes_limpio.csv', index=False)

        # 1. Reemplazamos los 999 por NaN para que no afecten el cálculo
    df_trans['Tiempo_Entrega_Real'] = df_trans['Tiempo_Entrega_Real'].replace(999, np.nan)
    
    # 2. Calculamos la mediana de los tiempos reales (ej. 3 o 5 días)
    mediana_entrega = df_trans['Tiempo_Entrega_Real'].median()
    
    # 3. Imputamos la mediana en esos huecos
    df_trans['Tiempo_Entrega_Real'] = df_trans['Tiempo_Entrega_Real'].fillna(mediana_entrega)

        # 1. Definimos el rango válido (1 a 5)
    # Usamos el método .between() que es muy eficiente en Pandas
    rango_valido = df_feed['Rating_Producto'].between(1, 5)
    
    # 2. Mantenemos solo las filas que cumplen la condición
    df_feed = df_feed[rango_valido].copy()
    
    # 3. Verificación de seguridad
    print(f"Rating mínimo: {df_feed['Rating_Producto'].min()}")
    print(f"Rating máximo: {df_feed['Rating_Producto'].max()}")
    print(f"Ahora tienes {len(df_feed)} filas con ratings reales.")

        # 1. Convertimos la columna a numérica (forzando errores a NaN)
    # Esto convierte "25-30 días" o "Inmediato" en NaN temporalmente para calcular la mediana
    lead_time_numerico = pd.to_numeric(df_inv['Lead_Time_Dias'], errors='coerce')
    
    # 2. Calculamos la mediana de los valores que SÍ son números
    mediana_lead = lead_time_numerico.median()
    
    # 3. Llenamos los nulos originales en df_inv con esa mediana
    # Nota: Esto solo afectará a los que quedaron después de tu limpieza anterior
    df_inv['Lead_Time_Dias'] = df_inv['Lead_Time_Dias'].fillna(mediana_lead)
    
    # 4. (Opcional) Si también quieres reemplazar la palabra texto "nan" que mencionamos antes:
    df_inv['Lead_Time_Dias'] = df_inv['Lead_Time_Dias'].replace('nan', mediana_lead)

        # 1. Calculamos la mediana de los ratings válidos (1 a 5)
    mediana_rating = df_feed.loc[df_feed['Rating_Producto'].between(1, 5), 'Rating_Producto'].median()
    
    # 2. Definimos las condiciones de error
    # El signo ~ significa "NO", es decir, que NO esté en el rango
    rating_fuera = ~df_feed['Rating_Producto'].between(1, 5)
    edad_fuera = ~df_feed['Edad_Cliente'].between(0, 100)
    
    # --- REGLA 1: ELIMINAR FILA ---
    # Si Rating está mal Y la Edad está mal (ej. Rating 99 y Edad 195)
    filas_para_eliminar = rating_fuera & edad_fuera
    df_feed = df_feed[~filas_para_eliminar].copy()
    
    # --- REGLA 2: CAMBIAR POR MEDIANA ---
    # Si el rating está mal pero la edad está BIEN (ej. Rating 99 y Edad 25)
    cond_imputar = (~df_feed['Rating_Producto'].between(1, 5)) & (df_feed['Edad_Cliente'].between(0, 100))
    df_feed.loc[cond_imputar, 'Rating_Producto'] = mediana_rating


    
    df_rich=pd.merge(df_trans,df_inv3,on='SKU_ID',how='left')
    print("en el primer join obtengo"," ",df_rich.shape[0]," ","de registros pero descartando los SKU_ID fantasma que no estan en la tabla de productos obtengo",df_rich.dropna().shape[0]," ","registros")
    df_full=pd.merge(df_rich,df_feed,on='Transaccion_ID',how='left')
    print("en el segundo join tomando elementos nulos del primero obtengo"," ",df_full.shape[0]," ","registros pero descartando las Transaccion_ID fantasma (que no estan en la tabla de Feedbacks) y \n los SKU_ID Fantasma  obtengo",df_full.dropna().shape[0]," ","registros", "si eliminamos datos fantasma mantendriamos"," ",(df_full.dropna().shape[0]/df_full.shape[0])*100,"\n % de los datos")
    #print(df_full)
    
    df_sku=(pd.DataFrame(df_full.groupby('SKU_ID')['Ultima_Revision'].count().reset_index()))
    
    print("tenemos"," ",df_sku[df_sku['Ultima_Revision']==0].reset_index().shape[0]," ","SKU Fantasmas")
    
    df_tra=(pd.DataFrame(df_full.groupby('Transaccion_ID')['Ultima_Revision'].count().reset_index()))
    
    print("tenemos"," ",df_tra[df_tra['Ultima_Revision']==0].reset_index().shape[0]," ","transacciones Fantasmas")



else:
    st.info("🌙 Sistema en espera. Por favor cargue el archivo CSV en el panel lateral.")
