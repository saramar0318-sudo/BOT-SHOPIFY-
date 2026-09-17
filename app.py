import os
import re
import io
import requests
import streamlit as st
import importlib

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# --- FORZAR RECARGA DEL MÓDULO IA PARA EVITAR MEMORIA EN CACHÉ DE PYTHON ---
import claude_ia
importlib.reload(claude_ia)
from claude_ia import generar_contenido_producto

from shopify_api import crear_producto_shopify
from marca_agua import procesar_imagen_streamlit

st.set_page_config(page_title="OPENBOX SV - Automatización", page_icon="📦", layout="wide")

# --- 1. SISTEMA DE SEGURIDAD BÁSICO ---
PASSWORD_CORRECTA = os.getenv("APP_PASSWORD", "Grupomfenix26")

def verificar_password():
    if "autenticado" not in st.session_state:
        st.session_state.autenticado = False

    if not st.session_state.autenticado:
        st.title("🔒 Acceso Restringido - OPENBOX SV")
        pwd = st.text_input("Ingresa la contraseña de acceso:", type="password")
        if st.button("Entrar"):
            if pwd == PASSWORD_CORRECTA:
                st.session_state.autenticado = True
                st.rerun()
            else:
                st.error("Contraseña incorrecta")
        return False
    return True

if not verificar_password():
    st.stop()

# --- CONTROL INFALIBLE DE REINICIO DE FORMULARIO ---
if "form_version" not in st.session_state:
    st.session_state.form_version = 0

def reiniciar_proceso():
    """Esta función cambia la versión del formulario, destruyendo los campos anteriores y creando unos nuevos en blanco."""
    st.session_state.form_version += 1

# --- INTERFAZ PRINCIPAL ---
col_titulo, col_btn = st.columns([4, 1])

with col_titulo:
    st.title("📦 OPENBOX SV - Publicador Automatico")

with col_btn:
    st.write("") 
    st.button("🔄 Reiniciar / Limpiar", use_container_width=True, on_click=reiniciar_proceso)

# --- FUNCIÓN CON CACHÉ PARA LA IA ---
@st.cache_data(show_spinner=False)
def obtener_datos_inteligentes_con_cache(link, notas, imagen_bytes=None, mime_type="image/jpeg"):
    return generar_contenido_producto(link, notas, imagen_bytes, mime_type)
    
# --- FUNCIÓN INTELIGENTE DE SKU ---
def extraer_sku_inteligente(link, titulo_producto):
    if link:
        match_asin = re.search(r"/(?:dp|gp/product|exec/obidos/asin)/([A-Z0-9]{10})", link, re.IGNORECASE)
        if match_asin:
            return match_asin.group(1).upper()
        
        match_asin_alt = re.search(r"/([A-Z0-9]{10})(?:[/?]|$)", link)
        if match_asin_alt:
            return match_asin_alt.group(1).upper()
        
        partes_url = [p for p in link.split("/") if len(p) > 3 and not p.startswith("http")]
        if partes_url:
            sucia = partes_url[-1].split("?")[0].split("-")
            palabras_clave = [p.upper() for p in sucia if p.isalnum() and not p.isdigit() or len(p) >= 3]
            if palabras_clave:
                sku_url = "-".join(palabras_clave[:3])
                if len(sku_url) > 3:
                    return sku_url[:20]

    if titulo_producto:
        palabras = re.findall(r'\b\w+\b', titulo_producto.upper())
        if palabras:
            base = "-".join(palabras[:3])
            return base[:20]

    return "OPENBOX-REF-01"

# --- SECCIÓN 1: DATOS Y ENLACES ---
link_producto = st.text_input("Enlace del producto (Amazon, etc.)", key=f"link_{st.session_state.form_version}")
notas_manuales = st.text_area("Notas / Especificaciones (opcional)", key=f"notas_{st.session_state.form_version}")
titulo_manual = st.text_input("Título del producto (Déjalo vacío para generarlo automáticamente con IA)", key=f"titulo_{st.session_state.form_version}")

# --- SECCIÓN 2: CONFIGURACIÓN COMERCIAL Y ESTADO ---
st.markdown("---")
st.subheader("💵 Detalles de Venta, Inventario y Publicación")

estado_publicacion_shopify = st.selectbox(
    "Estado del producto en Shopify", 
    ["Borrador (Draft) - Recomendado para revisar", "Activo (Visible al público de inmediato)"],
    key=f"estado_shop_{st.session_state.form_version}"
)

col1, col2, col3 = st.columns(3)
with col1:
    precio_venta = st.number_input("Precio de Venta ($)", min_value=0.0, value=10.0, format="%.2f", key=f"pv_{st.session_state.form_version}")
    precio_comparacion = st.number_input("Precio Regular / Tachado ($)", min_value=0.0, value=20.0, format="%.2f", key=f"pc_{st.session_state.form_version}")

with col2:
    estado_del_producto = st.selectbox(
        "Estado Estético", 
        [
            "Nuevo", 
            "Openbox (Producto nuevo con pequeños detalles estéticos)", 
            "Segunda Mano( Exelente estado)",
            "Segunda Mano(Detalles estéticos)",
            "Reacondicionado"
        ],
        key=f"estado_del_producto_{st.session_state.form_version}"
    )
    garantia = st.selectbox("Garantía", ["30 Días", "45 Días", "Sin Garantía"], key=f"garantia_del_producto_{st.session_state.form_version}")

with col3:
    inventario_stock = st.number_input("Cantidad en Stock", min_value=1, value=1, key=f"stock_{st.session_state.form_version}")
    empaque_opcion = st.selectbox(
        "Tipo de Empaque / Caja", 
        ["Caja Original", "Caja Genérica", "Sin Caja / En Bolsa"], 
        key=f"empaque_{st.session_state.form_version}"
    )

# --- SECCIÓN 3: GESTIÓN MANUAL DE IMÁGENES ---
st.markdown("---")
st.subheader("🖼️ Gestión de Imágenes y Marcas de Agua")

aplicar_marca_agua_check = st.checkbox("Aplicar marcas de agua gráficas automáticas", value=True, key=f"agua_{st.session_state.form_version}")

archivos_referencia_manuales = st.file_uploader(
    "1️⃣ Fotos de Referencia (Catálogo / Web) - Solo 'logo.png' | Irán PRIMERO (Miniatura)", 
    accept_multiple_files=True, 
    type=["jpg", "png", "jpeg", "heic"],
    key=f"ref_{st.session_state.form_version}"
)

archivos_reales = st.file_uploader(
    "2️⃣ Fotos Reales del Producto - 'logo.png' + 'foto_real.png' | Irán DESPUÉS", 
    accept_multiple_files=True, 
    type=["jpg", "png", "jpeg", "heic"],
    key=f"reales_{st.session_state.form_version}"
)

# --- BOTONES Y EJECUCIÓN AL FINAL ---
st.markdown("---")

col_accion, col_cache = st.columns([3, 1])

with col_cache:
    if st.button("🧹 Limpiar Caché", key="btn_clear_cache_bottom"):
        st.cache_data.clear()
        st.success("¡Caché borrado con éxito!")

with col_accion:
    btn_publicar = st.button("🚀 Procesar y Publicar en Shopify", key=f"btn_publish_{st.session_state.form_version}")

if btn_publicar:
    with st.spinner("Conectando con IA, generando SKU inteligente, procesando imágenes y publicando..."):
        
        try:
            # --- Capturar la primera foto disponible para la IA (Visión Multimodal) ---
            primera_imagen_bytes = None
            mime_type = "image/jpeg"

            todas_las_fotos = (archivos_referencia_manuales or []) + (archivos_reales or [])
            if todas_las_fotos:
                primera_foto = todas_las_fotos[0]
                primera_imagen_bytes = primera_foto.getvalue()
                if primera_foto.type:
                    mime_type = primera_foto.type

            # 1. Obtención de datos de IA (Pasando la imagen como respaldo visual)
            contenido_ia = obtener_datos_inteligentes_con_cache(
                link_producto, 
                notas_manuales, 
                primera_imagen_bytes, 
                mime_type
            )
            
            if not contenido_ia or not isinstance(contenido_ia, dict):
                st.error("⚠️ La IA no devolvió un formato válido.")
                st.stop()

            # Asignación de Título y Descripción
            if titulo_manual.strip():
                titulo_final = titulo_manual.strip().upper()
            else:
                titulo_final = contenido_ia.get("titulo", "PRODUCTO OPENBOX EN LIQUIDACIÓN").strip().upper()
                
            descripcion_final = contenido_ia.get("descripcion", "").strip()
            sku_detectado = extraer_sku_inteligente(link_producto, titulo_final)

            # 2. Procesamiento de Imágenes
            imagenes_referencia = []
            imagenes_reales_lista = []

            if archivos_referencia_manuales:
                for archivo in archivos_referencia_manuales:
                    if aplicar_marca_agua_check:
                        img_buf = procesar_imagen_streamlit(archivo, es_foto_real=False)
                    else:
                        img_buf = io.BytesIO(archivo.getvalue())
                    imagenes_referencia.append((f"01_ref_{archivo.name}", img_buf))

            if archivos_reales:
                for archivo in archivos_reales:
                    if aplicar_marca_agua_check:
                        img_buf = procesar_imagen_streamlit(archivo, es_foto_real=True)
                    else:
                        img_buf = io.BytesIO(archivo.getvalue())
                    imagenes_reales_lista.append((f"02_real_{archivo.name}", img_buf))

            imagenes_procesadas = imagenes_referencia + imagenes_reales_lista

            if not imagenes_procesadas:
                st.warning("⚠️ Debes subir al menos una imagen para publicar.")
            else:
                status_shopify = "draft" if "Borrador" in estado_publicacion_shopify else "active"

                # 3. Envío a Shopify API
                exito, resultado = crear_producto_shopify(
                    titulo=titulo_final,
                    descripcion_html=descripcion_final,
                    precio=precio_venta,
                    precio_comparacion=precio_comparacion,
                    cantidad=int(inventario_stock),
                    imagenes_procesadas=imagenes_procesadas,
                    empaque=empaque_opcion,
                    estado_estetico=estado_del_producto,
                    garantia=garantia,
                    sku=sku_detectado,
                    status=status_shopify
                )

                if exito:
                    st.cache_data.clear()
                    st.balloons()
                    st.success(f"🎉 ¡Producto procesado con éxito! (SKU generado: `{sku_detectado}`)")
                    st.markdown(f"**Enlace al producto:** [Ver en Shopify]({resultado})")
                    st.info("💡 Haz clic en '🔄 Reiniciar / Limpiar' arriba a la derecha para preparar el siguiente producto.")
                else:
                    st.error(f"❌ Error al publicar en Shopify: {resultado}")

        except Exception as e:
            st.error(f"Ocurrió un error inesperado: {e}")