import os
import datetime
from google import genai

# --- CONFIGURACIÓN ---
FILE_CODE = "clumsex.py"
FILE_LOG = "CHANGELOG.md"
SEPARATOR = "___LOG_SECTION___"
# ---------------------

def clean_code_part(code_text):
    """Limpia fences de markdown del bloque de código."""
    lines = code_text.strip().split('\n')
    if lines and lines[0].strip().startswith('```'):
        lines = lines[1:]
    if lines and lines[-1].strip() == '```':
        lines = lines[:-1]
    return '\n'.join(lines).strip()

def ensure_execution_block(code_content):
    """
    Sistema de Seguridad:
    Si Gemini se olvida (o se corta) el bloque de arranque, 
    esta función lo inyecta a la fuerza.
    """
    check_str = 'if __name__ == "__main__":'
    check_str_alt = "if __name__ == '__main__':"
    
    if check_str not in code_content and check_str_alt not in code_content:
        print("⚠️ ALERTA: Gemini olvidó el bloque de arranque. Inyectándolo automáticamente.")
        code_content += '\n\nif __name__ == "__main__":\n    app = ClumsexGUI()\n    app.mainloop()'
    
    return code_content

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

    # Prompt optimizado para evitar cortes por longitud
    prompt = f"""
    Actúa como experto en Python. Optimiza este script manteniendo TODA su funcionalidad.
    
    INSTRUCCIONES CRÍTICAS:
    1. NO ELIMINES FUNCIONES.
    2. Asegúrate de que el código termine con el bloque `if __name__ == "__main__":`.
    3. Si el código es muy largo, prioriza la estabilidad sobre la reescritura total.
    4. Usa el formato de respuesta exacto abajo.

    [CÓDIGO PYTHON COMPLETO]
    {SEPARATOR}
    [BREVE LOG DE CAMBIOS]
    
    --- CÓDIGO ACTUAL ---
    {old_code}
    """
    
    client = genai.Client(api_key=api_key)
    
    try:
        print(f"Consultando a Gemini...")
        response = client.models.generate_content(model='gemini-2.0-flash', contents=prompt)
        full_text = response.text
        
        if SEPARATOR in full_text:
            parts = full_text.split(SEPARATOR)
            raw_code = parts[0]
            log_text = parts[1].strip()
        else:
            print("⚠️ Gemini no usó el separador. Intentando recuperar código.")
            raw_code = full_text
            log_text = "Actualización automática (Sin detalles)."

        # 1. Limpieza y Curación del Código
        clean_code = clean_code_part(raw_code)
        
        # === AQUÍ ESTÁ EL ARREGLO ===
        # Si Gemini cortó el final, esto lo repara:
        final_code_logic = ensure_execution_block(clean_code)
        
        # Timestamp
        ahora = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        watermark = f"# --- AUTO-UPDATED: {ahora} UTC ---"
        
        lines = final_code_logic.split('\n')
        if lines and lines[0].startswith("# --- AUTO-UPDATED:"):
            lines[0] = watermark
            final_content = '\n'.join(lines)
        else:
            final_content = f"{watermark}\n{final_code_logic}"

        with open(FILE_CODE, "w", encoding="utf-8") as f:
            f.write(final_content)

        # 2. Guardar Log
        log_entry = f"\n\n## 🕒 Versión {ahora}\n{log_text}"
        with open(FILE_LOG, "a", encoding="utf-8") as f:
            f.write(log_entry)
            
        print(f"ÉXITO: Código reparado y guardado.")

    except Exception as e:
        print(f"Error crítico: {e}")
        raise e

if __name__ == "__main__":
    run_review()
