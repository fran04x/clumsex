import os
import datetime
from google import genai

# --- CONFIGURACIÓN ---
FILE_CODE = "clumsex.py"
FILE_LOG = "CHANGELOG.md"
SEPARATOR = "___LOG_SECTION___" # La marca mágica para separar código de texto
# ---------------------

def clean_code_part(code_text):
    """Limpia fences de markdown del bloque de código."""
    lines = code_text.strip().split('\n')
    # Eliminar ```python o ``` del inicio
    if lines and lines[0].strip().startswith('```'):
        lines = lines[1:]
    # Eliminar ``` del final
    if lines and lines[-1].strip() == '```':
        lines = lines[:-1]
    return '\n'.join(lines).strip()

def run_review():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("Falta la clave API.")
        return

    if not os.path.exists(FILE_CODE):
        print(f"Error: No encuentro {FILE_CODE}")
        return

    with open(FILE_CODE, "r", encoding="utf-8") as f:
        old_code = f.read()

    # --- PROMPT ACTUALIZADO ---
    # Le pedimos explícitamente el formato dividido
    prompt = f"""
    Actúa como experto en Python Senior. Tu tarea es mantener y optimizar este script.
    
    1. Analiza el código buscando mejoras de CPU, memoria, limpieza o corrección de bugs.
    2. Genera el código completo optimizado.
    3. Redacta un breve log explicando QUÉ cambiaste y POR QUÉ (ej: "Optimicé el loop X para reducir CPU").
    
    IMPORTANTE: Debes devolver la respuesta en este formato EXACTO:
    
    [CÓDIGO PYTHON COMPLETO AQUÍ]
    {SEPARATOR}
    [TU LOG AQUÍ]
    
    --- CÓDIGO ACTUAL ---
    {old_code}
    """
    
    client = genai.Client(api_key=api_key)
    
    try:
        print(f"Consultando a Gemini...")
        response = client.models.generate_content(model='gemini-2.0-flash', contents=prompt)
        full_text = response.text
        
        # --- LÓGICA DE SEPARACIÓN ---
        if SEPARATOR in full_text:
            parts = full_text.split(SEPARATOR)
            raw_code = parts[0]
            log_text = parts[1].strip()
        else:
            # Fallback por si Gemini olvida el separador (raro, pero posible)
            print("⚠️ Gemini no usó el separador. Guardando solo código.")
            raw_code = full_text
            log_text = "Actualización automática (Sin detalles generados)."

        # 1. Guardar Código
        clean_code = clean_code_part(raw_code)
        
        # Timestamp para forzar commit del código
        ahora = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        watermark = f"# --- AUTO-UPDATED: {ahora} UTC ---"
        
        lines = clean_code.split('\n')
        if lines and lines[0].startswith("# --- AUTO-UPDATED:"):
            lines[0] = watermark
            final_code = '\n'.join(lines)
        else:
            final_code = f"{watermark}\n{clean_code}"

        with open(FILE_CODE, "w", encoding="utf-8") as f:
            f.write(final_code)

        # 2. Guardar Log (Append mode 'a')
        # Formato Markdown bonito para que se lea bien en GitHub
        log_entry = f"\n\n## 🕒 Versión {ahora}\n{log_text}"
        
        with open(FILE_LOG, "a", encoding="utf-8") as f:
            f.write(log_entry)
            
        print(f"ÉXITO: Código actualizado y Log añadido a {FILE_LOG}")

    except Exception as e:
        print(f"Error crítico: {e}")
        raise e

if __name__ == "__main__":
    run_review()
