import os
from google import genai

# --- CONFIGURACIÓN ---
NOMBRE_ARCHIVO_CODIGO = "clumsex v12.2 stable.py"
# ---------------------

def clean_gemini_response(response_text):
    """Limpia las fences de Markdown y espacios en blanco de la respuesta."""
    lines = response_text.strip().split('\n')
    if lines and lines[0].strip().startswith('```'):
        # Elimina la primera línea (e.g., ```python)
        lines = lines[1:]
    if lines and lines[-1].strip() == '```':
        # Elimina la última línea (```)
        lines = lines[:-1]
    return '\n'.join(lines).strip()

def run_review():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("Falta la clave API.")
        return

    # 1. LEER EL ARCHIVO
    if not os.path.exists(NOMBRE_ARCHIVO_CODIGO):
        print(f"ERROR: No encuentro el archivo '{NOMBRE_ARCHIVO_CODIGO}'.")
        return

    with open(NOMBRE_ARCHIVO_CODIGO, "r", encoding="utf-8") as f:
        contenido_codigo = f.read()

    # 2. PREPARAR EL PROMPT Y ENVIAR
    prompt = f"""
    Actúa como experto en Python. Entrega ÚNICAMENTE el código Python completo y corregido.
    --- CÓDIGO A REVISAR ---
    {contenido_codigo}
    """
    client = genai.Client(api_key=api_key)
    
    try:
        print(f"Enviando '{NOMBRE_ARCHIVO_CODIGO}' a Gemini...")
        response = client.models.generate_content(model='gemini-2.0-flash', contents=prompt)
        
        # 3. LIMPIAR EL CONTENIDO DE MARKDOWN
        new_content = clean_gemini_response(response.text)
        
        # 4. GUARDAR EL CÓDIGO LIMPIO EN EL MISMO ARCHIVO
        with open(NOMBRE_ARCHIVO_CODIGO, "w", encoding="utf-8") as f:
            f.write(new_content)
            
        print(f"ÉXITO: Contenido limpio guardado en '{NOMBRE_ARCHIVO_CODIGO}'.")
        
    except Exception as e:
        print(f"Error en la llamada a la API: {e}")
        raise e

if __name__ == "__main__":
    run_review()
