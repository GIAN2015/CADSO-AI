import streamlit as st
import requests
from requests_oauthlib import OAuth1
import pandas as pd
from groq import Groq
import io
import re

# ==========================================
# 1. CONFIGURACIÓN DE LA PÁGINA Y CSS (¡LA MAGIA VISUAL!)
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
    col1, col2, col3 = st.columns([1, 1.5, 1]) # Centramos el cuadro de login
    
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
    st.stop() # Detiene la ejecución para proteger los datos de abajo

# ==========================================
# 3. CREDENCIALES (SOLO SE LEEN SI HAY LOGIN EXITOSO)
# ==========================================
ACCOUNT_ID = st.secrets["ACCOUNT_ID"]
CONSUMER_KEY = st.secrets["CONSUMER_KEY"]
CONSUMER_SECRET = st.secrets["CONSUMER_SECRET"]
TOKEN_ID = st.secrets["TOKEN_ID"]
TOKEN_SECRET = st.secrets["TOKEN_SECRET"]
GROQ_API_KEY = st.secrets["GROQ_API_KEY"]

client_groq = Groq(api_key=GROQ_API_KEY)

# Inicializar variables de estado para el DataFrame
if 'df' not in st.session_state:
    st.session_state.df = None

# ==========================================
# 4. CONEXIÓN Y LIMPIEZA
# ==========================================
def consultar_datos_netsuite():
    base_url = f"https://{ACCOUNT_ID}.restlets.api.netsuite.com/app/site/hosting/restlet.nl?script=128&deploy=1"
    auth = OAuth1(CONSUMER_KEY, CONSUMER_SECRET, TOKEN_ID, TOKEN_SECRET, 
                  realm=ACCOUNT_ID, signature_method='HMAC-SHA256')
    return requests.get(base_url, auth=auth)

# ==========================================
# 5. INTERFAZ VISUAL (DISEÑO V5.0)
# ==========================================

# Banner Superior
registros_txt = f"{len(st.session_state.df)} REGISTROS" if st.session_state.df is not None else "ESPERANDO DATA"
st.markdown(f"""
    <div class="top-banner">
        <div><h3>🟠 CAD SOLUTIONS - AI <span style="background-color: #f26522; font-size: 0.8rem; padding: 2px 8px; border-radius: 12px; vertical-align: middle;">ENGINE V5.0</span></h3></div>
        <div style="font-size: 0.8rem;"><span class="status-dot">●</span> MOTOR LISTO - {registros_txt}</div>
    </div>
""", unsafe_allow_html=True)

# Sincronización (Solo se muestra si no hay datos)
if st.session_state.df is None:
    if st.button("📥 Sincronizar Datos desde NetSuite (Inicialización)"):
        with st.spinner("Descargando y preparando base de datos..."):
            res = consultar_datos_netsuite()
            if res.status_code == 200:
                data = res.json()
                items = list(data.values()) if isinstance(data, dict) else data
                df = pd.DataFrame(items)
                
                # --- TU LIMPIEZA DE DATOS INTACTA ---
                for col in df.columns:
                    if any(keyword in col.lower() for keyword in ['total', 'monto', 'previsto']):
                        df[col] = pd.to_numeric(df[col].astype(str).replace(r'[\$,]', '', regex=True), errors='coerce').fillna(0)
                    if 'fecha' in col.lower():
                        df[col] = pd.to_datetime(df[col], dayfirst=True, errors='coerce')
                
                st.session_state.df = df
                st.rerun() # Recarga la página para mostrar el dashboard
            else:
                st.error(f"Error al conectar con NetSuite: Código {res.status_code}")

# Mostrar Dashboard si hay datos
if st.session_state.df is not None:
    df = st.session_state.df
    
    # DIVISIÓN EN COLUMNAS DEL DISEÑO QUE PASASTE
    col1, espaciador, col2 = st.columns([3.5, 0.2, 6.3])
    
    with col1:
        st.markdown('<div class="card-title">🧠 CONSULTOR DE NEGOCIOS IA</div>', unsafe_allow_html=True)
        st.caption("HAZ TU CONSULTA EN LENGUAJE NATURAL")
        pregunta = st.text_area(" ", placeholder="Ej: ¿Cuánto es el total en Negociacion de Febrero 2026?", height=120, label_visibility="collapsed")
        
        btn_analizar = st.button("ANALIZAR DATOS")
        
        # Contenedores para el resultado dinámico
        res_placeholder = st.empty()
        detalles_placeholder = st.empty()
        
        # Estado inicial del resultado
        if not pregunta or not btn_analizar:
             res_placeholder.markdown("""
                <div class="result-box">
                    <div class="result-label">RESULTADO PRINCIPAL</div>
                    <div class="result-value">0.00</div>
                </div>
            """, unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="card-title">📋 BASE DE DATOS SINCRONIZADA</div>', unsafe_allow_html=True)
        st.dataframe(df, use_container_width=True, height=500)

    # ==========================================
    # 6. TU LÓGICA Y PROMPT INTACTOS
    # ==========================================
    if btn_analizar and pregunta:
        columnas_lista = ", ".join(df.columns.tolist())
        buffer = io.StringIO()
        df.info(buf=buffer)
        info_tabla = buffer.getvalue()

        # --- TU PROMPT ORIGINAL AL 100% ---
        prompt = f"""
        Eres un Analista de Datos Senior de Inteligencia Artificial de CAD SOLUTIONS.
        Genera ÚNICAMENTE código Python con pandas para responder la pregunta. El dataframe `df` ya existe en memoria, NO uses read_csv.

        ESTRUCTURA DE TU BASE DE DATOS (Columnas disponibles):
        {columnas_lista}
        
        Información técnica de tipos:
        {info_tabla}

        🚨 REGLAS ESTRICTAS DE NEGOCIO (¡LEE ATENTAMENTE!) 🚨:
        1. DUPLICADOS (VITAL): ANTES de hacer cualquier cálculo, elimina filas repetidas por oportunidad: 
           `df = df.drop_duplicates(subset=['idOportunidad'])`.
        2. DINERO: Para sumar ganancias o montos previstos, usa la columna `totalPrevisto`.
        3. FECHAS: Antes de filtrar fechas, asegúrate de convertirlas: `df['fechaCierre'] = pd.to_datetime(df['fechaCierre'], errors='coerce')`. Usa `fechaCierre` para ventas ganadas y `fechaCreacion` para nuevas oportunidades.
        4. ESTADOS DE OPORTUNIDAD: Usa `estadoOportunidad`. Los valores típicos son 'CERRADA' (ganada), 'OPORTUNIDAD PERDIDA', 'OPORTUNIDAD PROCESO','EN NEGOCIACIÓN'.
           - Si piden cerradas o ganadas: `df[df['estadoOportunidad'].astype(str).str.upper() == 'CERRADA']`.
        5. TEXTOS Y NOMBRES: Si te piden buscar por Vendedor, Empresa, Origen, o Tipo, usa siempre `.str.contains('texto_a_buscar', case=False, na=False)` para evitar errores de mayúsculas/minúsculas.
           - Vendedores: `representanteVentas`
           - Empresas: `nombreEmpresa`
           - Tipo (Venta/Renovación): `tipo`
           - Motivos: `motivoPerdida`
        6. FILTROS MÚLTIPLES: Si la pregunta tiene varias condiciones (Ej: "Ventas cerradas por Manuel Rivera en 2026"), encadena los filtros correctamente:
        7. SI EL TIPO DE "moneda" ES "Soles" CAMBIAR A "US Dollar" dividiendo el totalPrevisto entre 4
        🎯 INSTRUCCIONES DE SALIDA (ADÁPTATE A LA PREGUNTA):
        Analiza cuidadosamente la pregunta y genera DOS variables exactas:
        - Variable `respuesta_final` (FLOAT, INT o STRING): Si piden dinero, guarda el monto. Si piden contar, guarda la cantidad. Si piden un dato de texto (ej: nombre, rubro, estado), guarda el texto exacto.
        - Variable `detalles` (STRING): Un texto con el desglose. Si muestras dinero, formatea así: f"${{monto:,.2f}}". Usa saltos de línea ('\\n') para que sea fácil de leer.

        Devuelve SOLO código Python limpio. NO agregues ```python al inicio ni ``` al final. Nada de texto extra.

        PREGUNTA DEL USUARIO: {pregunta}
        """
        
        with col1:
            with st.spinner("Procesando..."):
                try:
                    completion = client_groq.chat.completions.create(
                        model="meta-llama/llama-4-scout-17b-16e-instruct", # Te sugerí cambiar este modelo, ajusta si es necesario
                        messages=[{"role": "user", "content": prompt}],
                        temperature=0
                    )
                    
                    raw_content = completion.choices[0].message.content
                    code_match = re.search(r'```(?:python)?\n?(.*?)```', raw_content, re.DOTALL)
                    codigo_limpio = code_match.group(1).strip() if code_match else raw_content.strip()

                    vars_locales = {'df': df.copy(), 'pd': pd}
                    exec(codigo_limpio, {}, vars_locales)
                    
                    res_final = vars_locales.get('respuesta_final', 0)
                    texto_detalles = vars_locales.get('detalles', 'Análisis completado sin detalles.')
                    
                    # Actualizar caja de resultados (¡La naranja!)
                    res_placeholder.markdown(f"""
                        <div class="result-box">
                            <div class="result-label">RESULTADO PRINCIPAL</div>
                            <div class="result-value">${float(res_final):,.2f}</div>
                        </div>
                    """, unsafe_allow_html=True)
                    
                    detalles_placeholder.info(texto_detalles)
                    
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
                        st.code(codigo_limpio, language='python')