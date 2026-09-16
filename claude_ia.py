import os
import re
import requests
import anthropic

def generar_contenido_producto(link_producto, notas_manuales):
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("Falta la credencial ANTHROPIC_API_KEY en las variables de entorno.")

    cliente = anthropic.Anthropic(api_key=api_key)
    texto_base = ""
    asin_detectado = ""

    if link_producto:
        # Extraer ASIN de Amazon si está presente
        match_asin = re.search(r"/(?:dp|gp/product)/([A-Z0-9]{10})", link_producto, re.IGNORECASE)
        if match_asin:
            asin_detectado = match_asin.group(1).upper()

        if "/dp/" in link_producto:
            base_link = link_producto.split("/ref=")[0].split("?")[0]
        else:
            base_link = link_producto.split("?")[0]

        try:
            jina_url = f"https://r.jina.ai/{base_link}"
            headers = {
                "Accept": "text/plain",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
            }
            response = requests.get(jina_url, headers=headers, timeout=10)
            
            # Verificar si Amazon devolvió bloqueo o CAPTCHA
            contenido = response.text.lower()
            if "robot check" in contenido or "captcha" in contenido or "api-services-support" in contenido:
                print("[AVISO] Amazon bloqueó el raspado directo.")
                if asin_detectado:
                    texto_base += f"\n\nCódigo de producto Amazon ASIN: {asin_detectado}"
            elif response.status_code == 200 and len(response.text) > 200:
                texto_base += f"\n\nInformación extraída de la web:\n{response.text[:10000]}"
        except Exception as e:
            if asin_detectado:
                texto_base += f"\n\nCódigo de producto Amazon ASIN: {asin_detectado}"

    if notas_manuales:
        texto_base += f"\n\nNotas / Descripción del usuario:\n{notas_manuales}"

    # Si Amazon bloqueó y no hay notas, creamos una pista con el ASIN
    if not texto_base.strip():
        texto_base = f"Producto Amazon con ASIN {asin_detectado if asin_detectado else 'desconocido'}"

    prompt = f"""
    Eres un experto en e-commerce y copywriter senior para el mercado Salvadoreño. 
    Basándote en la siguiente información sobre el producto:
    1. Genera un TÍTULO comercial, limpio, atractivo y optimizado para ventas en El Salvador y en Shopify. **Debe estar 100% en español**, adaptado comercialmente y tener máximo 70 caracteres.
    2. Genera una DESCRIPCIÓN en formato HTML puro (usando solo <p>, <ul>, <li>, <strong>) con un párrafo introductorio persuasivo y viñetas técnicas en español.
    3. Si ves medidas o especificaciones técnicas, inclúyelas en la descripción, si no estan en cm, conviértelas a cm y agrega la unidad. Si hay medidas en pulgadas, conviértelas a cm y agrega la unidad.

    Devuelve la respuesta estrictamente en este formato exacto separado por etiquetas clave:
    ---TITULO---
    [Aquí el título comercial en español]
    ---DESCRIPCION---
    [Aquí el código HTML de la descripción en español]

    Información del producto:
    {texto_base}
    """

    try:
        mensaje = cliente.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1200,
            messages=[{"role": "user", "content": prompt}]
        )
        
        texto_respuesta = mensaje.content[0].text.strip()
        titulo_generado = "MOPA Y CEPILLO DE LIMPIEZA EXTENSIBLE"
        descripcion_generada = "<p>Herramienta de limpieza ajustable de alta eficiencia para hogar y autos.</p>"
        
        if "---TITULO---" in texto_respuesta and "---DESCRIPCION---" in texto_respuesta:
            partes = texto_respuesta.split("---DESCRIPCION---")
            titulo_generado = partes[0].replace("---TITULO---", "").strip()
            descripcion_generada = partes[1].strip()
            
        return {
            "titulo": titulo_generado,
            "descripcion": descripcion_generada
        }
    except Exception as e:
        raise ValueError(f"Error en la API de Claude: {e}")