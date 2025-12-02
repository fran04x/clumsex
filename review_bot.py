import os
from google import genai

# --- CONFIGURACIÓN ---
NOMBRE_ARCHIVO_CODIGO = "clumsex v12.2 stable.py"
# ---------------------

def run_review():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("Falta la clave API.")
        return

    # 1. VERIFICAR Y LEER EL ARCHIVO
    if not os.path.exists(NOMBRE_ARCHIVO_CODIGO):
        print(f"ERROR: No encuentro el archivo '{NOMBRE_ARCHIVO_CODIGO}'.")
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
    client = genai.Client(api_key=api_key)
    
    try:
        print(f"Enviando '{NOMBRE_ARCHIVO_CODIGO}' a Gemini para actualización...")
        response = client.models.generate_content(
            model='gemini-2.0-flash', 
            contents=prompt
        )
        
        # 4. GUARDAR EL CÓDIGO NUEVO EN EL MISMO ARCHIVO
        new_content = response.text
        with open(NOMBRE_ARCHIVO_CODIGO, "w", encoding="utf-8") as f:
            f.write(new_content)
            
        print(f"ÉXITO: Código optimizado guardado localmente en '{NOMBRE_ARCHIVO_CODIGO}'.")
        
    except Exception as e:
        print(f"Error en la llamada a la API: {e}")
        raise e

if __name__ == "__main__":
    run_review()
