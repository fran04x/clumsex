import os
import datetime
import sys
from google import genai

# --- CONFIGURACIÓN ---
FILE_CODE = "clumsex.py"
FILE_LOG = "CHANGELOG.md"
FILE_TODO = "TODO.md"
SEPARATOR = "___LOG_SECTION___"
MAX_RETRIES = 3
# ---------------------

def clean_code_part(code_text):
    lines = code_text.strip().split('\n')
    if lines and lines[0].strip().startswith('```'):
        lines = lines[1:]
    if lines and lines[-1].strip() == '```':
        lines = lines[:-1]
    return '\n'.join(lines).strip()

def ensure_execution_block(code_content):
    if 'if __name__ == "__main__":' not in code_content and "if __name__ == '__main__':" not in code_content:
        code_content += '\n\nif __name__ == "__main__":\n    app = ClumsexGUI()\n    app.mainloop()'
    return code_content

def check_syntax(code_string):
    try:
        compile(code_string, '<string>', 'exec')
        return True, ""
    except Exception as e:
        return False, str(e)

def get_next_task():
    """Lee el TODO.md y extrae la primera tarea pendiente."""
    if not os.path.exists(FILE_TODO):
        return None, []
    
    with open(FILE_TODO, "r", encoding="utf-8") as f:
        lines = f.readlines()
    
    task = None
    remaining_lines = []
    
    # Busca la primera línea que empiece con guión o checkbox vacío
    for i, line in enumerate(lines):
        clean_line = line.strip()
        # Detecta formatos: "- Tarea", "- [ ] Tarea", "* Tarea"
        if not task and (clean_line.startswith("- [ ]") or (clean_line.startswith("- ") and "[x]" not in clean_line)):
            task = clean_line.replace("- [ ]", "").replace("- ", "").strip()
        else:
            remaining_lines.append(line)
            
    return task, remaining_lines

def run_review():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("Falta la clave API.")
        sys.exit(1)

    if not os.path.exists(FILE_CODE):
        print(f"Error: No encuentro {FILE_CODE}")
        return

    # 1. Obtener la misión del TODO.md
    current_task, remaining_todo_lines = get_next_task()
    
    if current_task:
        print(f"📋 Misión detectada: {current_task}")
        mission_prompt = f"TU MISIÓN PRIORITARIA: Implementar esta tarea: '{current_task}'."
    else:
        print("💤 No hay tareas en TODO.md. Modo Mantenimiento (Optimización).")
        mission_prompt = "TU MISIÓN: Analizar el código, buscar bugs o mejoras de rendimiento y aplicarlas."

    # Leer código actual
    with open(FILE_CODE, "r", encoding="utf-8") as f:
        current_code = f.read()

    client = genai.Client(api_key=api_key)
    attempt = 0
    
    # Prompt Base
    current_prompt_text = f"""
    Actúa como experto en Python. {mission_prompt}
    
    REGLAS:
    1. NO ELIMINES FUNCIONES EXISTENTES a menos que la tarea lo pida.
    2. Asegura el bloque `if __name__ == "__main__":` al final.
    3. Devuelve el código completo.
    
    Formato:
    [CÓDIGO]
    {SEPARATOR}
    [LOG EXPLICATIVO]
    
    --- CÓDIGO ACTUAL ---
    {current_code}
    """

    while attempt < MAX_RETRIES:
        attempt += 1
        print(f"🔄 Intento {attempt}/{MAX_RETRIES}...")

        try:
            response = client.models.generate_content(model='gemini-2.0-flash', contents=current_prompt_text)
            full_text = response.text
            
            if SEPARATOR in full_text:
                parts = full_text.split(SEPARATOR)
                raw_code = parts[0]
                log_text = parts[1].strip()
            else:
                raw_code = full_text
                log_text = f"Tarea completada: {current_task}" if current_task else "Optimización general."

            candidate_code = clean_code_part(raw_code)
            candidate_code = ensure_execution_block(candidate_code)

            # Auto-curación de sintaxis
            is_valid, error_msg = check_syntax(candidate_code)
            
            if is_valid:
                # --- GUARDADO ---
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

                # Log
                log_prefix = f"✅ **TAREA COMPLETADA:** {current_task}\n" if current_task else ""
                with open(FILE_LOG, "a", encoding="utf-8") as f:
                    f.write(f"\n\n## 🕒 Versión {ahora}\n{log_prefix}{log_text}")
                
                # Actualizar TODO.md (Borrar la tarea hecha)
                if current_task:
                    with open(FILE_TODO, "w", encoding="utf-8") as f:
                        f.writelines(remaining_todo_lines)
                    print("🗑️ Tarea eliminada del archivo TODO.")

                return

            else:
                print(f"❌ Error sintaxis: {error_msg}")
                current_prompt_text = f"El código tiene error: {error_msg}. Corrígelo y devuélvelo completo."

        except Exception as e:
            print(f"Error API: {e}")
    
    sys.exit(1)

if __name__ == "__main__":
    run_review()
