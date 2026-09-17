import base64
import os
import requests
import anthropic

def generar_contenido_producto(link_producto, notas_manuales, imagen_bytes=None, mime_type="image/jpeg"):
    api_key = os.getenv("ANTHROPIC_API_KEY")
    client = anthropic.Anthropic(api_key=api_key)
    
    # 1. Intento de Scraping silencioso (si falla, no interrumpe el flujo)
    texto_web = ""
    if link_producto:
        try:
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
            res = requests.get(link_producto, headers=headers, timeout=5)
            if res.status_code == 200:
                texto_web = res.text[:2000]  # Primeros caracteres limpios
        except Exception:
            pass

    # 2. Construcción del Prompt Híbrido
    prompt = f"""
    Analiza la imagen adjunta y la información disponible para redactar la ficha de producto de e-commerce:
    - Información extraída del enlace: {texto_web if texto_web else 'No disponible'}
    - Notas del usuario: {notas_manuales if notas_manuales else 'Sin notas'}

    Instrucciones:
    1. Identifica en la imagen marca, color, compartimentos, tipo de producto y detalles clave.
    2. Genera un título atractivo y comercial.
    3. Escribe una descripción persuasiva en viñetas resaltando beneficios principales.
    4. NUNCA respondas con plantillas genéricas de disculpa; usa la inspección visual si no hay texto web.
    5. Si ves medidas o especificaciones técnicas, inclúyelas en la descripción, si no estan en cm, conviértelas a cm y agrega la unidad. Si hay medidas en pulgadas, conviértelas a cm y agrega la unidad.

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

    # 4. Llamada limpia a Claude 3.5 Sonnet
    response = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=2000,
        messages=[{"role": "user", "content": content_payload}]
    )

    return response.content[0].text