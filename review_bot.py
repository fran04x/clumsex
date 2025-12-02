import os
import datetime
from google import genai

# --- CONFIGURACIÓN ---
NOMBRE_ARCHIVO_CODIGO = "clumsex.py" 
# ---------------------

def clean_gemini_response(response_text):
    lines = response_text.strip().split('\n')
    if lines and lines[0].strip().startswith('```'):
        lines = lines[1:]
    if lines and lines[-1].strip() == '```':
        lines = lines[:-1]
    return '\n'.join(lines).strip()

def run_review():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("Falta la clave API.")
        return

    if not os.path.exists(NOMBRE_ARCHIVO_CODIGO):
        print(f"ERROR: No encuentro '{NOMBRE_ARCHIVO_CODIGO}' en el directorio actual.")
        print("Archivos disponibles:", os.listdir())
        return

    with open(NOMBRE_ARCHIVO_CODIGO, "r", encoding="utf-8") as f:
        contenido_codigo = f.read()

    # Prompt
    prompt = f"""
    Actúa como experto en Python. Optimiza y mejora el siguiente código.
    IMPORTANTE: Devuelve el código completo listo para usar.
    --- CÓDIGO ---
    {contenido_codigo}
    """
    
    client = genai.Client(api_key=api_key)
    
    try:
        print(f"Enviando '{NOMBRE_ARCHIVO_CODIGO}' a Gemini...")
        response = client.models.generate_content(model='gemini-2.0-flash', contents=prompt)
        
        code_limpio = clean_gemini_response(response.text)
        
        # Timestamp
        ahora = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        watermark = f"# --- AUTO-UPDATED: {ahora} UTC ---"
        
        lines = code_limpio.split('\n')
        if lines and lines[0].startswith("# --- AUTO-UPDATED:"):
            lines[0] = watermark
            new_content = '\n'.join(lines)
        else:
            new_content = f"{watermark}\n{code_limpio}"

        with open(NOMBRE_ARCHIVO_CODIGO, "w", encoding="utf-8") as f:
            f.write(new_content)
            
        print(f"ÉXITO: '{NOMBRE_ARCHIVO_CODIGO}' actualizado localmente.")
        
    except Exception as e:
        print(f"Error: {e}")
        raise e

if __name__ == "__main__":
    run_review()
