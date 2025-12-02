import os
import datetime
from google import genai

# --- CONFIGURACIÓN ---
NOMBRE_ARCHIVO_CODIGO = "clumsex v12.2 stable.py"
# ---------------------

def clean_gemini_response(response_text):
    """Limpia las fences de Markdown y espacios."""
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

    # 1. LEER EL ARCHIVO
    if not os.path.exists(NOMBRE_ARCHIVO_CODIGO):
        print(f"ERROR: No encuentro el archivo '{NOMBRE_ARCHIVO_CODIGO}'.")
        return

    with open(NOMBRE_ARCHIVO_CODIGO, "r", encoding="utf-8") as f:
        contenido_codigo = f.read()

    # 2. PREPARAR EL PROMPT
    prompt = f"""
    Actúa como experto en Python. Entrega ÚNICAMENTE el código Python completo y corregido.
    Si no hay nada que corregir, devuelve el mismo código pero asegúrate de que esté completo.
    --- CÓDIGO A REVISAR ---
    {contenido_codigo}
    """
    
    client = genai.Client(api_key=api_key)
    
    try:
        print(f"Enviando a Gemini...")
        response = client.models.generate_content(model='gemini-2.0-flash', contents=prompt)
        
        # 3. LIMPIAR Y AGREGAR TIMESTAMP (ESTO FUERZA EL COMMIT)
        code_limpio = clean_gemini_response(response.text)
        
        # Generar marca de tiempo
        ahora = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        watermark = f"# --- AUTO-UPDATED: {ahora} UTC ---"
        
        # Si el código ya tiene una marca de tiempo en la primera línea, la reemplazamos
        lines = code_limpio.split('\n')
        if lines and lines[0].startswith("# --- AUTO-UPDATED:"):
            lines[0] = watermark
            new_content = '\n'.join(lines)
        else:
            new_content = f"{watermark}\n{code_limpio}"

        # 4. GUARDAR
        with open(NOMBRE_ARCHIVO_CODIGO, "w", encoding="utf-8") as f:
            f.write(new_content)
            
        print(f"ÉXITO: Código guardado con marca de tiempo: {ahora}")
        
    except Exception as e:
        print(f"Error: {e}")
        raise e

if __name__ == "__main__":
    run_review()
