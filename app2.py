import streamlit as st
import requests
from requests_oauthlib import OAuth1
import pandas as pd
from groq import Groq
import io
import re

# ==========================================
# 1. CONFIGURACIÓN DE LA PÁGINA Y CSS 
# ==========================================
st.set_page_config(page_title="CAD SOLUTIONS AI - V5.0", layout="wide", initial_sidebar_state="collapsed")

# Inyectamos CSS personalizado para imitar tu diseño exacto
st.markdown("""
    <style>
    :root {
        --blue: #0c243c;
        --orange: #f26522;
        --bg-color: #f4f7f9;
    }
    
    /* Fondo de la aplicación */
    .stApp { background-color: var(--bg-color); }
    
    /* Barra Superior Tipo Dashboard */
    .top-banner {
        background-color: var(--blue);
        color: white;
        padding: 15px 20px;
        border-radius: 8px;
        border-bottom: 5px solid var(--orange);
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 25px;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    .top-banner h3 { margin: 0; font-size: 1.5rem; font-weight: bold; color: white; }
    .status-dot { color: #00ff00; font-size: 0.8rem; }
    
    /* Títulos de las tarjetas */
    .card-title {
        background-color: #e2e8f0;
        color: var(--blue);
        padding: 10px 15px;
        border-radius: 5px;
        font-weight: bold;
        margin-bottom: 15px;
        display: flex;
        align-items: center;
        gap: 10px;
    }
    
    /* Caja de Resultado Principal */
    .result-box {
        background-color: var(--blue);
        color: var(--orange);
        padding: 20px;
        border-radius: 10px;
        text-align: right;
        margin-top: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .result-label { color: white; font-size: 0.9rem; margin-bottom: 5px; text-transform: uppercase; text-align: left;}
    .result-value { font-size: 2.8rem; font-weight: bold; line-height: 1; }
    
    /* Personalización de Botones Streamlit */
    .stButton>button {
        background-color: var(--blue);
        color: white;
        width: 100%;
        border-radius: 5px;
        border: 1px solid var(--blue);
        font-weight: bold;
        padding: 10px 0;
        transition: all 0.3s ease;
    }
    .stButton>button:hover { background-color: var(--orange); color: white; border-color: var(--orange); }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 2. SISTEMA DE LOGIN (CANDADO DE SEGURIDAD)
# ==========================================
if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False

def mostrar_login():
    st.markdown("<br><br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1.5, 1])
    
    with col2:
        st.markdown("""
            <div style="background-color: var(--blue); padding: 15px; border-radius: 8px 8px 0 0; text-align: center;">
                <h3 style="color: white; margin: 0;">🔒 ACCESO SEGURO - AI V5.0</h3>
            </div>
        """, unsafe_allow_html=True)
        
        with st.form("login_form"):
            usuario = st.text_input("Usuario")
            contrasena = st.text_input("Contraseña", type="password")
            submit_button = st.form_submit_button("INGRESAR AL SISTEMA")
            
            if submit_button:
                if usuario == "CADSO2026" and contrasena == "X9#mK!p2$vLq8@zW":
                    st.session_state["autenticado"] = True
                    st.rerun()
                else:
                    st.error("❌ Credenciales incorrectas. Acceso denegado.")

if not st.session_state["autenticado"]:
    mostrar_login()
    st.stop()

# ==========================================
# 3. CREDENCIALES (PROTEGIDAS)
# ==========================================

ACCOUNT_ID = st.secrets["ACCOUNT_ID"]
CONSUMER_KEY = st.secrets["CONSUMER_KEY"]
CONSUMER_SECRET = st.secrets["CONSUMER_SECRET"]
TOKEN_ID = st.secrets["TOKEN_ID"]
TOKEN_SECRET = st.secrets["TOKEN_SECRET"]
GROQ_API_KEY = st.secrets["GROQ_API_KEY"]


# Iniciamos el cliente de Groq con la API Key seguramente almacenada en Streamlit Secrets

client_groq = Groq(api_key=GROQ_API_KEY)

if 'df' not in st.session_state:
    st.session_state.df = None

# ==========================================
# 4. CONEXIÓN Y LIMPIEZA DE NETSUITE
# ==========================================
def consultar_datos_netsuite():
    base_url = f"https://{ACCOUNT_ID}.restlets.api.netsuite.com/app/site/hosting/restlet.nl?script=128&deploy=1"
    auth = OAuth1(CONSUMER_KEY, CONSUMER_SECRET, TOKEN_ID, TOKEN_SECRET, 
                  realm=ACCOUNT_ID, signature_method='HMAC-SHA256')
    return requests.get(base_url, auth=auth)

# ==========================================
# 5. INTERFAZ VISUAL (DISEÑO V5.0)
# ==========================================
registros_txt = f"{len(st.session_state.df)} REGISTROS" if st.session_state.df is not None else "ESPERANDO DATA"
st.markdown(f"""
    <div class="top-banner">
        <div><h3>🟠 CAD SOLUTIONS - AI <span style="background-color: #f26522; font-size: 0.8rem; padding: 2px 8px; border-radius: 12px; vertical-align: middle;">ENGINE V5.0</span></h3></div>
        <div style="font-size: 0.8rem;"><span class="status-dot">●</span> MOTOR LISTO - {registros_txt}</div>
    </div>
""", unsafe_allow_html=True)

if st.session_state.df is None:
    if st.button("📥 Sincronizar Datos desde NetSuite (Inicialización)"):
        with st.spinner("Descargando y preparando base de datos..."):
            res = consultar_datos_netsuite()
            if res.status_code == 200:
                data = res.json()
                items = list(data.values()) if isinstance(data, dict) else data
                df = pd.DataFrame(items)
                
                for col in df.columns:
                    if any(keyword in col.lower() for keyword in ['total', 'monto', 'previsto']):
                        df[col] = pd.to_numeric(df[col].astype(str).replace(r'[\$,]', '', regex=True), errors='coerce').fillna(0)
                    if 'fecha' in col.lower():
                        df[col] = pd.to_datetime(df[col], dayfirst=True, errors='coerce')
                
                st.session_state.df = df
                st.rerun()
            else:
                st.error(f"Error al conectar con NetSuite: Código {res.status_code}")

if st.session_state.df is not None:
    df = st.session_state.df
    
    col1, espaciador, col2 = st.columns([3.5, 0.2, 6.3])
    
    # -------- COLUMNA IZQUIERDA (CHAT) --------
    with col1:
        st.markdown('<div class="card-title">🧠 CONSULTOR DE NEGOCIOS IA</div>', unsafe_allow_html=True)
        st.caption("HAZ TU CONSULTA EN LENGUAJE NATURAL")
        pregunta = st.text_area(" ", placeholder="Ej: Información de la oportunidad 656", height=120, label_visibility="collapsed")
        
        btn_analizar = st.button("ANALIZAR DATOS")
        
        res_placeholder = st.empty()        # 1. Caja de resultado (Azul)
        detalles_placeholder = st.empty()   # 2. Detalles (Celeste)
        veredicto_placeholder = st.empty()  # 3. El veredicto de la IA (Verde)
        
        if not pregunta or not btn_analizar:
             res_placeholder.markdown("""
                <div class="result-box">
                    <div class="result-label">RESULTADO PRINCIPAL</div>
                    <div class="result-value">0.00</div>
                </div>
            """, unsafe_allow_html=True)

    # -------- COLUMNA DERECHA (TABLAS) --------
    with col2:
        # ¡AQUÍ ESTÁ EL SECRETO! Creamos un espacio vacío a la derecha, justo ARRIBA del título de la base de datos
        tabla_derecha_placeholder = st.empty() 
        
        st.markdown('<div class="card-title">📋 BASE DE DATOS SINCRONIZADA</div>', unsafe_allow_html=True)
        st.dataframe(df, use_container_width=True, height=500)

    # ==========================================
    # 6. LÓGICA DE AGENTE DE 2 PASOS + TABLAS
    # ==========================================
    if btn_analizar and pregunta:
        columnas_lista = ", ".join(df.columns.tolist())
        buffer = io.StringIO()
        df.info(buf=buffer)
        info_tabla = buffer.getvalue()

        prompt_extraccion = f"""
        Eres un Analista de Datos Senior de Inteligencia Artificial de CAD SOLUTIONS.
        Genera ÚNICAMENTE código Python con pandas para responder la pregunta. El dataframe `df` ya existe en memoria, NO uses read_csv.

        ESTRUCTURA DE TU BASE DE DATOS (Columnas disponibles):
        {columnas_lista}
        
        Información técnica de tipos:
        {info_tabla}
f
        🚨 REGLAS ESTRICTAS DE NEGOCIO:
        1. DUPLICADOS (VITAL): ANTES de hacer cualquier cálculo, elimina filas repetidas por oportunidad: 
           `df = df.drop_duplicates(subset=['idOportunidad'])`.
        2. DINERO: Para sumar ganancias o montos previstos, usa la columna `MontootalPrevisto`.
        3. FECHAS: Convierte fechas así: `df['fechaCierre'] = pd.to_datetime(df['fechaCierre'], errors='coerce')`. Usa `fechaCierre` para ventas ganadas y `fechaCreacion` para nuevas oportunidades.
        4. ESTADOS: Usa `estadoOportunidad` (CERRADA, OPORTUNIDAD PERDIDA, OPORTUNIDAD PROCESO, EN NEGOCIACIÓN).
        5. TEXTOS Y NOMBRES: Usa `.str.contains('texto', case=False, na=False)`.
        6. FILTROS MÚLTIPLES: Encadena los filtros correctamente si hay varias condiciones.
        7. TILDES: Al buscar textos (Vendedores, Empresas, Nombres), usa expresiones regulares para ignorar tildes: `str.contains('ver[oó]nika', case=False, regex=True)`.
        8. NUNCA fuerces `float()` sobre variables que sean texto puro (como rubros, estados de oportunidad o nombres de empresas). Si el usuario pide un nombre o rubro, devuelve ese String tal cual.
        
        🎯 INSTRUCCIONES DE SALIDA:
        Analiza la pregunta y genera TRES variables exactas:
        - Variable `respuesta_final` (FLOAT, INT o STRING): El monto, cantidad o texto exacto. (Ojo: NO uses float() si es un String).
        - Variable `detalles` (STRING): Texto con el desglose. Si es dinero, formatea f"${{monto:,.2f}}". Usa '\\n'.
        - Variable `tabla_resultado` (DATAFRAME o None): Si el usuario pide información, listas o detalles de registros específicos, guarda aquí el DataFrame filtrado con esas filas. Si solo pide un cálculo global, pon `tabla_resultado = None`.

        Devuelve SOLO código Python limpio. NO agregues ```python al inicio ni ``` al final. Nada de texto extra.

        PREGUNTA DEL USUARIO: {pregunta}
        """
        
        with col1:
            with st.spinner("Procesando datos..."):
                try:
                    # PASO 1: Generar código Pandas
                    completion = client_groq.chat.completions.create(
                        model="llama-3.3-70b-versatile", 
                        messages=[{"role": "user", "content": prompt_extraccion}],
                        temperature=0
                    )
                    
                    raw_content = completion.choices[0].message.content
                    code_match = re.search(r'```(?:python)?\n?(.*?)```', raw_content, re.DOTALL)
                    codigo_limpio = code_match.group(1).strip() if code_match else raw_content.strip()

                    # Ejecutar el código generado por la IA
                    vars_locales = {'df': df.copy(), 'pd': pd}
                    exec(codigo_limpio, {}, vars_locales)
                    
                    # Recuperar variables
                    res_final = vars_locales.get('respuesta_final', 0)
                    texto_detalles = vars_locales.get('detalles', 'Análisis completado sin detalles.')
                    tabla_datos = vars_locales.get('tabla_resultado', None)
                    
                    # Formatear el resultado a mostrar (Seguro contra caídas por texto)
                    try:
                        valor_formateado = f"${float(res_final):,.2f}"
                    except (ValueError, TypeError):
                        valor_formateado = str(res_final)
                    
                    # 1. MOSTRAR RESULTADO PRINCIPAL (IZQUIERDA)
                    res_placeholder.markdown(f"""
                        <div class="result-box">
                            <div class="result-label">RESULTADO PRINCIPAL</div>
                            <div class="result-value">{valor_formateado}</div>
                        </div>
                    """, unsafe_allow_html=True)
                    
                    # 2. MOSTRAR DETALLES (IZQUIERDA)
                    detalles_placeholder.info(texto_detalles)

                    # 3. MOSTRAR TABLA DE DATOS RELACIONADA ¡A LA DERECHA!
                    # Se inyecta en el placeholder que creamos arriba en la col2
                    if tabla_datos is not None and isinstance(tabla_datos, pd.DataFrame) and not tabla_datos.empty:
                        with tabla_derecha_placeholder.container():
                            # Lo pongo en expanded=True para que cuando aparezca, ya se vea la tabla sin dar clic
                            with st.expander("📊 TABLA DE RESULTADOS DE TU CONSULTA", expanded=True):
                                st.dataframe(tabla_datos, use_container_width=True)

                    # 4. GENERAR Y MOSTRAR VEREDICTO DE IA (IZQUIERDA)
                    with st.spinner("Generando veredicto consultivo..."):
                        prompt_analisis = f"""
                        Pregunta: "{pregunta}"
                        Resultado principal: {valor_formateado}
                        Detalles: {texto_detalles}

                        Eres un consultor de ventas Senior. Analiza este resultado y escribe un breve veredicto o conclusión estratégica. Sé directo y aporta valor. No expliques la matemática, máximo 3 a 4 líneas.
                        """
                        completion_analisis = client_groq.chat.completions.create(
                            model="llama-3.3-70b-versatile", 
                            messages=[{"role": "user", "content": prompt_analisis}],
                            temperature=0.5
                        )
                        veredicto_ia = completion_analisis.choices[0].message.content
                        
                        veredicto_placeholder.markdown("### 💡 Veredicto Estratégico")
                        veredicto_placeholder.success(veredicto_ia)
                    
                    # 5. MOSTRAR EL CÓDIGO (IZQUIERDA, AL FINAL)
                    with st.expander("⚙️ VER CÓDIGO GENERADO POR LA IA"):
                        st.code(codigo_limpio, language='python')
                        
                except Exception as e:
                    res_placeholder.markdown("""
                        <div class="result-box" style="border: 2px solid red;">
                            <div class="result-label" style="color:white;">ERROR DE CÁLCULO</div>
                            <div class="result-value" style="font-size: 1.5rem; color:white;">Revisa la consulta</div>
                        </div>
                    """, unsafe_allow_html=True)
                    detalles_placeholder.error(f"Error técnico: {e}")
                    with st.expander("🛠️ Ver el código que falló"):
                        st.code(vars().get('codigo_limpio', 'No se generó código'), language='python')