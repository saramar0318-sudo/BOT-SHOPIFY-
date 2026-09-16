import os
import anthropic

api_key = os.getenv("ANTHROPIC_API_KEY")
print(f"Llave detectada en el sistema: {'SÍ' if api_key else 'NO'}")

if api_key:
    try:
        cliente = anthropic.Anthropic(api_key=api_key)
        respuesta = cliente.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=50,
            messages=[{"role": "user", "content": "Responde solo con la frase: 'Conexión exitosa a Claude'."}]
        )
        print("Respuesta de la IA:", respuesta.content[0].text)
    except Exception as e:
        print("Error al conectar con la API:", e)