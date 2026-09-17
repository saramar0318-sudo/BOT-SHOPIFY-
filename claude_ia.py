import base64
import os
import json
import re
import requests
import anthropic

def generar_contenido_producto(link_producto, notas_manuales, imagen_bytes=None, mime_type="image/jpeg"):
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        return {"titulo": "PRODUCTO OPENBOX", "descripcion": "Error: No se encontró la API Key de Anthropic."}
        
    client = anthropic.Anthropic(api_key=api_key)
    
    # 1. Intento de Scraping silencioso
    texto_web = ""
    if link_producto:
        try:
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
            res = requests.get(link_producto, headers=headers, timeout=5)
            if res.status_code == 200:
                texto_web = res.text[:2000]  # Primeros caracteres limpios
        except Exception:
            pass

    # 2. Construcción del Prompt Híbrido (Pidiendo respuesta en JSON)
    prompt = f"""
    Analiza la imagen adjunta y la información disponible para redactar la ficha de producto de e-commerce:
    - Información extraída del enlace: {texto_web if texto_web else 'No disponible'}
    - Notas del usuario: {notas_manuales if notas_manuales else 'Sin notas'}

    Instrucciones:
    1. Identifica en la imagen marca, color, compartimentos, tipo de producto y detalles clave.
    2. Genera un título atractivo y comercial en MAYÚSCULAS.
    3. Escribe una descripción persuasiva en viñetas HTML (usa etiquetas <ul> y <li>) resaltando beneficios principales.
    4. NUNCA respondas con plantillas genéricas de disculpa; usa la inspección visual si no hay texto web.
    5. Si ves medidas o especificaciones técnicas, inclúyelas en la descripción. Convertir pulgadas a cm si es necesario.

    Responde ÚNICAMENTE en formato JSON estricto con la siguiente estructura:
    {{
        "titulo": "TITULO DEL PRODUCTO AQUI",
        "descripcion": "<ul><li>Detalle 1</li><li>Detalle 2</li></ul>"
    }}
    """

    content_payload = []

    # 3. Adjuntar Imagen (Visión activa)
    if imagen_bytes:
        b64_img = base64.b64encode(imagen_bytes).decode("utf-8")
        content_payload.append({
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": mime_type,
                "data": b64_img
            }
        })

    content_payload.append({"type": "text", "text": prompt})

    # 4. Llamada a Claude
    try:
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=2000,
            messages=[{"role": "user", "content": content_payload}]
        )

        raw_text = response.content[0].text
        
        # Extraer JSON de la respuesta
        match = re.search(r'\{.*\}', raw_text, re.DOTALL)
        if match:
            return json.loads(match.group(0))
        else:
            return {
                "titulo": "PRODUCTO EN LIQUIDACIÓN",
                "descripcion": f"<ul><li>{raw_text}</li></ul>"
            }
    except Exception as e:
        return {
            "titulo": "PRODUCTO EN LIQUIDACIÓN",
            "descripcion": f"Error al generar contenido: {e}"
        }