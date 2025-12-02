import os
from google import genai

# 1. Recuperar la clave API de forma segura desde las variables de entorno de GitHub
API_KEY = os.environ.get("GEMINI_API_KEY") 
if not API_KEY:
    raise ValueError("La clave API de Gemini no está configurada.")

# 2. Inicializar el cliente
client = genai.Client(api_key=API_KEY)

# 3. Definir el prompt recurrente
prompt_code_review = "Revisa y optimiza la última versión del código 'clumsex' que te proporcioné anteriormente y entrega el código completo."

try:
    # 4. Enviar la solicitud a la API
    # Nota: Aquí se asume que esta respuesta se maneja o se envía a un canal (como un log)
    # y el resultado final (el código actualizado) es lo que yo (Gemini) te enviaré
    # en nuestra conversación al recibir este prompt.
    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=prompt_code_review
    )
    
    # Opcional: Imprimir la respuesta en el log de la Action
    print("Revisión de código solicitada con éxito.") 
    print(response.text[:200] + "...") # Muestra un fragmento de la respuesta

except Exception as e:
    print(f"Error al llamar a la API: {e}")
    raise # Falla la Action si la llamada falla
