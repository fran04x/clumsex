import os
import datetime
import subprocess
import sys
from google import genai

# --- CONFIGURACIÓN ---
FILE_CODE = "clumsex.py"
FILE_LOG = "CHANGELOG.md"
SEPARATOR = "___LOG_SECTION___"
MAX_RETRIES = 3  # Vidas del bot
# ---------------------

def clean_code_part(code_text):
    """Limpia fences de markdown."""
    lines = code_text.strip().split('\n')
    if lines and lines[0].strip().startswith('```'):
        lines = lines[1:]
    if lines and lines[-1].strip() == '```':
        lines = lines[:-1]
    return '\n'.join(lines).strip()

def ensure_execution_block(code_content):
    """Garantiza que el script tenga arranque."""
    if 'if __name__ == "__main__":' not in code_content and "if __name__ == '__main__':" not in code_content:
        code_content += '\n\nif __name__ == "__main__":\n    app = ClumsexGUI()\n    app.mainloop()'
    return code_content

def check_syntax(code_string):
    """
    Intenta compilar el código en memoria para ver si tiene errores.
    Retorna: (True, "") si está bien.
    Retorna: (False, "Error msg") si falla.
    """
    try:
        compile(code_string, '<string>', 'exec')
        return True, ""
    except Exception as e:
        return False, str(e)

def run_review():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("Falta la clave API.")
        sys.exit(1)

    if not os.path.exists(FILE_CODE):
        print(f"Error: No encuentro {FILE_CODE}")
        return

    # Leemos el código ORIGINAL (la base estable)
    with open(FILE_CODE, "r", encoding="utf-8") as f:
        current_code = f.read()

    client = genai.Client(api_key=api_key)
    
    # Historial de intentos para este ciclo
    attempt = 0
    # El prompt inicial es optimizar
    current_prompt = f"""
    Actúa como experto en Python. Optimiza este script manteniendo funcionalidad.
    NO ELIMINES FUNCIONES. Asegura el bloque `if __name__ == "__main__":` al final.
    
    Formato de respuesta:
    [CÓDIGO]
    {SEPARATOR}
    [LOG]
    
    --- CÓDIGO ---
    {current_code}
    """

    while attempt < MAX_RETRIES:
        attempt += 1
        print(f"🔄 Intento de generación {attempt}/{MAX_RETRIES}...")

        try:
            response = client.models.generate_content(model='gemini-2.0-flash', contents=current_prompt)
            full_text = response.text
            
            # Separar código y log
            if SEPARATOR in full_text:
                parts = full_text.split(SEPARATOR)
                raw_code = parts[0]
                log_text = parts[1].strip()
            else:
                raw_code = full_text
                log_text = "Actualización automática."

            # Limpiar y asegurar arranque
            candidate_code = clean_code_part(raw_code)
            candidate_code = ensure_execution_block(candidate_code)

            # === LA MAGIA: AUTO-CURACIÓN ===
            is_valid, error_msg = check_syntax(candidate_code)
            
            if is_valid:
                print("✅ Código válido generado. Guardando...")
                
                # Timestamp y Guardado
                ahora = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                watermark = f"# --- AUTO-UPDATED: {ahora} UTC ---"
                
                lines = candidate_code.split('\n')
                if lines and lines[0].startswith("# --- AUTO-UPDATED:"):
                    lines[0] = watermark
                    final_content = '\n'.join(lines)
                else:
                    final_content = f"{watermark}\n{candidate_code}"

                with open(FILE_CODE, "w", encoding="utf-8") as f:
                    f.write(final_content)

                with open(FILE_LOG, "a", encoding="utf-8") as f:
                    f.write(f"\n\n## 🕒 Versión {ahora}\n{log_text}")
                
                return # ¡ÉXITO! Salimos del loop

            else:
                print(f"❌ Gemini falló. Error detectado: {error_msg}")
                # === AQUÍ ESTÁ TU IDEA ===
                # En lugar de empezar de cero, le damos el error para que se corrija a sí mismo
                current_prompt = f"""
                El código que generaste tiene un error de sintaxis y NO se puede ejecutar.
                
                ERROR DETECTADO:
                {error_msg}
                
                Por favor, corrige el código anterior basándote en este error.
                Devuelve el código COMPLETO corregido nuevamente con el mismo formato.
                """
                # El loop continúa... Gemini recibirá este nuevo prompt en el siguiente giro

        except Exception as e:
            print(f"Error de API: {e}")
    
    print("⛔ Se agotaron los intentos. No se aplicaron cambios.")
    sys.exit(1) # Fallar el workflow si no se logró nada

if __name__ == "__main__":
    run_review()
