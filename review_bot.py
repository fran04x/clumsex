import os
from google import genai

# --- CONFIGURACIÓN ---
# El nombre exacto tal cual está en tu repositorio
NOMBRE_ARCHIVO_CODIGO = "clumsex v12.2 stable.py"
# ---------------------

def run_review():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("Falta la API Key en los secretos del repositorio.")

    # 1. VERIFICAR Y LEER EL ARCHIVO
    if not os.path.exists(NOMBRE_ARCHIVO_CODIGO):
        # Listar archivos para depuración en los logs si falla
        print(f"ERROR CRÍTICO: No encuentro '{NOMBRE_ARCHIVO_CODIGO}'.")
        print("Archivos encontrados en el directorio actual:", os.listdir())
        return

    with open(NOMBRE_ARCHIVO_CODIGO, "r", encoding="utf-8") as f:
        contenido_codigo = f.read()

    # 2. PREPARAR EL PROMPT
    prompt = f"""
    Actúa como un experto en Python y optimización de redes (WinDivert/Raw Sockets).
    Tu tarea es actualizar y optimizar el siguiente script.
    
    INSTRUCCIONES:
    1. Analiza el código buscando cuellos de botella, fugas de memoria o lógica ineficiente.
    2. Aplica correcciones y mejoras de rendimiento.
    3. Entrega EL CÓDIGO COMPLETO y LISTO PARA USAR. 
    4. NO expliques los cambios, solo entrega el bloque de código Python.
    
    --- ARCHIVO: {NOMBRE_ARCHIVO_CODIGO} ---
    {contenido_codigo}
    """

    # 3. ENVIAR A GEMINI
    # Usamos gemini-2.0-flash por ser el modelo más rápido y eficiente para iteraciones frecuentes
    client = genai.Client(api_key=api_key)
    
    try:
        print(f"Enviando '{NOMBRE_ARCHIVO_CODIGO}' a Gemini para actualización...")
        response = client.models.generate_content(
            model='gemini-2.0-flash', 
            contents=prompt
        )
        
        print("\n" + "▼"*30)
        print(">>> INICIO DEL CÓDIGO ACTUALIZADO <<<")
        print("▼"*30 + "\n")
        
        # Imprime el código limpio para que lo copies desde el log
        print(response.text) 
        
        print("\n" + "▲"*30)
        print(">>> FIN DEL CÓDIGO ACTUALIZADO <<<")
        print("▲"*30 + "\n")
        
    except Exception as e:
        print(f"Error en la llamada a la API: {e}")
        # Forzar error para que GitHub notifique el fallo (X roja)
        raise e

if __name__ == "__main__":
    run_review()
