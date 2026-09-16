import os
import requests
from dotenv import load_dotenv

# Carga las variables del archivo .env
load_dotenv()

url = os.getenv("SHOPIFY_GRAPHQL_URL")
token = os.getenv("SHOPIFY_ACCESS_TOKEN")

print("--- VERIFICANDO CONFIGURACIÓN ---")
print(f"URL configurada: {url}")
print(f"Token configurado: {token[:10]}... (oculto por seguridad)" if token else "¡TOKEN VACÍO O NO ENCONTRADO!")

headers = {
    "X-Shopify-Access-Token": token,
    "Content-Type": "application/json",
}

# 1. Prueba básica de lectura de la tienda
query_shop = """
{
  shop {
    name
    email
    currencyCode
  }
}
"""

response = requests.post(url, json={"query": query_shop}, headers=headers)
print("\n--- PRUEBA 1: Lectura de la tienda ---")
print("Estado HTTP:", response.status_code)
print("Respuesta:", response.json())

# 2. Prueba de permisos de escritura (intentar consultar metadatos de creación de productos)
query_permisos = """
{
  __type(name: "ProductCreatePayload") {
    name
  }
}
"""
response_permisos = requests.post(url, json={"query": query_permisos}, headers=headers)
print("\n--- PRUEBA 2: Verificación del esquema de GraphQL ---")
print("Estado HTTP:", response_permisos.status_code)
print("Respuesta:", response_permisos.json())