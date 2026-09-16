import os
import requests
import base64

def obtener_access_token(shop_name, client_id, client_secret):
    shop_clean = shop_name.replace(".myshopify.com", "").strip()
    url = f"https://{shop_clean}.myshopify.com/admin/oauth/access_token"
    payload = {
        "client_id": client_id,
        "client_secret": client_secret,
        "grant_type": "client_credentials"
    }
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    response = requests.post(url, json=payload, headers=headers)
    if response.status_code == 200:
        return response.json().get("access_token")
    else:
        raise ValueError(f"Fallo OAuth Shopify ({response.status_code}): {response.text}")

def crear_producto_shopify(titulo, descripcion_html, precio, precio_comparacion, cantidad, imagenes_procesadas, empaque, estado_estetico, garantia, sku, status):
    shop_name = os.getenv("SHOPIFY_SHOP_NAME", "1dsitk-6f")
    client_id = os.getenv("SHOPIFY_CLIENT_ID")
    client_secret = os.getenv("SHOPIFY_CLIENT_SECRET")

    if not client_id or not client_secret:
        raise ValueError("Faltan las credenciales SHOPIFY_CLIENT_ID o SHOPIFY_CLIENT_SECRET.")

    shop_clean = shop_name.replace(".myshopify.com", "").strip()
    access_token = obtener_access_token(shop_clean, client_id, client_secret)

    graphql_url_env = os.getenv("SHOPIFY_GRAPHQL_URL", "")
    api_version = "2026-07"
    if "/api/" in graphql_url_env:
        try:
            api_version = graphql_url_env.split("/api/")[1].split("/")[0]
        except Exception:
            pass

    url = f"https://{shop_clean}.myshopify.com/admin/api/{api_version}/products.json"
    
    headers = {
        "Content-Type": "application/json",
        "X-Shopify-Access-Token": access_token
    }

    lista_imagenes = []
    for nombre_archivo, buffer in imagenes_procesadas:
        buffer.seek(0)
        encoded_string = base64.b64encode(buffer.read()).decode("utf-8")
        lista_imagenes.append({
            "attachment": encoded_string,
            "filename": nombre_archivo
        })

    # Opcional: Bloque visual de detalles en la descripción si deseas mantenerlo
    detalles_extra = f"""
    <p><strong>Detalles del producto:</strong></p>
    <ul>
        <li><strong>Estado Estético:</strong> {estado_estetico}</li>
        <li><strong>Empaque:</strong> {empaque}</li>
        <li><strong>Garantía:</strong> {garantia}</li>
    </ul>
    """
    descripcion_completa = descripcion_html + detalles_extra

   # Sanitizamos los valores asegurando que no envíen espacios extra ni valores nulos
    val_empaque = str(empaque).strip() if empaque else "Caja Original"
    val_garantia = str(garantia).strip() if garantia else "30 Días"
    val_estado = str(estado_estetico).strip() if estado_estetico else "Nuevo"

    metacampos = [
        {
            "namespace": "custom",
            "key": "empaque",
            "value": val_empaque,
            "type": "single_line_text_field"
        },
        {
            "namespace": "custom",
            "key": "garantia_del_producto",
            "value": val_garantia,
            "type": "single_line_text_field"
        },
        {
            "namespace": "custom",
            "key": "estado_del_producto",
            "value": val_estado,
            "type": "single_line_text_field"
        }
    ]

    # Preparamos la variante cuidando el valor de compare_at_price
    variante_data = {
        "price": str(precio),
        "inventory_quantity": cantidad,
        "inventory_management": "shopify",
        "sku": sku
    }
    
    if precio_comparacion and float(precio_comparacion) > 0:
        variante_data["compare_at_price"] = str(precio_comparacion)

    payload = {
        "product": {
            "title": titulo,
            "body_html": descripcion_completa,
            "status": status,
            "tags": f"Openbox, {val_estado}, {val_empaque}",
            "variants": [variante_data],
            "images": lista_imagenes,
            "metafields": metacampos
        }
    }

    response = requests.post(url, json=payload, headers=headers)

    print(f"CÓDIGO DE RESPUESTA: {response.status_code}")
    print(f"RESPUESTA COMPLETA: {response.text}")
    
    if response.status_code == 201:
        data = response.json()
        product_handle = data["product"]["handle"]
        product_url = f"https://{shop_clean}.myshopify.com/products/{product_handle}"
        return True, product_url
    else:
        return False, f"Error {response.status_code}: {response.text}"