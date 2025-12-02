import os
import datetime
import sys
import re
from google import genai

# --- CONFIGURACIÓN ---
FILE_CODE = "clumsex.py"
FILE_LOG = "CHANGELOG.md"
FILE_TODO = "TODO.md"
SEPARATOR = "___LOG_SECTION___"
MAX_RETRIES = 3
# ---------------------

def extract_python_code(text):
    """
    Busca quirúrgicamente el bloque de código entre fences de markdown.
    Si no encuentra fences, asume que todo el texto es código.
    """
    # Patrón: Busca ```python (contenido) ``` o ``` (contenido) ```
    pattern = r"```(?:python)?\s*(.*?)```"
    match = re.search(pattern, text, re.DOTALL)
    
    if match:
        # Devuelve solo lo que está ADENTRO de las comillas
        return match.group(1).strip()
    else:
        # Si no hay fences, intentamos limpiar líneas sueltas de chat
        lines = text.split('\n')
        # Si la primera línea no parece código (no import, no def, no class, no #), la borramos
        if lines and not (lines[0].startswith('import') or lines[0].startswith('from') or lines[0].startswith('#')):
             # Un intento básico de limpieza si falla el regex
             return text.replace("```python", "").replace("```", "").strip()
        return text.strip()

def ensure_execution_block(code_content):
    # Solo agrega el bloque si realmente falta y el archivo parece completo
    if 'if __name__ == "__main__":' not in code_content and "if __name__ == '__main__':" not in code_content:
        # Solo inyectar si parece que el código termina abruptamente o es una clase GUI
        code_content += '\n\nif __name__ == "__main__":\n    app = ClumsexGUI()\n    app.mainloop()'
    return code_content

def check_syntax(code_string):
    try:
        compile(code_string, '<string>', 'exec')
        return True, ""
    except Exception as e:
        return False, str(e)

def get_next_task():
    if not os.path.exists(FILE_TODO):
        return None, []
    
    with open(FILE_TODO, "r", encoding="utf-8") as f:
        lines = f.readlines()
    
    task = None
    remaining_lines = []
    
    for line in lines:
        clean_line = line.strip()
        # Detecta la primera tarea pendiente
        if not task and (clean_line.startswith("- [ ]") or (clean_line.startswith("- ") and "[x]" not in clean_line)):
            task = clean_line.replace("- [ ]", "").replace("- ", "").strip()
        else:
            remaining_lines.append(line)
            
    return task, remaining_lines

def run_review():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("Falta clave API")
        sys.exit(1)

    if not os.path.exists(FILE_CODE):
        print(f"Error: No existe {FILE_CODE}")
        return

    # 1. Obtener Misión
    current_task, remaining_todo = get_next_task()
    
    if current_task:
        print(f"📋 Misión: {current_task}")
        mission_prompt = f"TU ÚNICA PRIORIDAD es implementar esta tarea del TODO: '{current_task}'."
    else:
        print("💤 Modo Mantenimiento")
        mission_prompt = "Tu tarea es revisar el código, optimizar funciones lentas y limpiar sintaxis."

    with open(FILE_CODE, "r", encoding="utf-8") as f:
        current_code = f.read()

    client = genai.Client(api_key=api_key)
    attempt = 0

    # Prompt Refinado para evitar charla
    prompt_template = """
    Actúa como experto en Python Senior. {mission}
    
    IMPORTANTE:
    1. El código es muy largo. PARA AHORRAR ESPACIO: ELIMINA TODOS LOS COMENTARIOS Y DOCSTRINGS.
    2. Mantén el código compacto pero legible.
    3. NO ELIMINES NINGUNA FUNCIÓN LÓGICA.
    4. Asegura el bloque `if __name__ == "__main__":` al final.
    
    Formato OBLIGATORIO de respuesta:
    ```python
    ... código completo aquí ...
    ```
    {separator}
    ... explicación breve del cambio ...

    --- CÓDIGO ACTUAL ---
    {code}
    """

    while attempt < MAX_RETRIES:
        attempt += 1
        print(f"🔄 Intento {attempt}/{MAX_RETRIES}...")

        try:
            full_prompt = prompt_template.format(
                mission=mission_prompt,
                separator=SEPARATOR,
                code=current_code
            )
            
            # Usamos 2.0 Flash porque maneja contextos largos mejor
            response = client.models.generate_content(model='gemini-2.0-pro', contents=full_prompt)
            full_text = response.text
            
            # 1. Separar Log
            if SEPARATOR in full_text:
                parts = full_text.split(SEPARATOR)
                code_part = parts[0]
                log_part = parts[1].strip()
            else:
                code_part = full_text
                log_part = f"Update: {current_task}" if current_task else "Optimización general"

            # 2. Extracción Quirúrgica (Regex)
            clean_code = extract_python_code(code_part)
            clean_code = ensure_execution_block(clean_code)

            # 3. Validación
            is_valid, error_msg = check_syntax(clean_code)
            
            if is_valid:
                # Guardar
                ahora = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                header = f"# --- AUTO-UPDATED: {ahora} UTC ---"
                
                lines = clean_code.split('\n')
                if lines and lines[0].startswith("# --- AUTO-UPDATED:"):
                    lines[0] = header
                    final_content = '\n'.join(lines)
                else:
                    final_content = f"{header}\n{clean_code}"

                with open(FILE_CODE, "w", encoding="utf-8") as f:
                    f.write(final_content)
                
                # Log
                log_msg = f"\n\n## 🕒 {ahora}\n"
                if current_task: log_msg += f"✅ **Tarea:** {current_task}\n"
                log_msg += log_part
                
                with open(FILE_LOG, "a", encoding="utf-8") as f:
                    f.write(log_msg)

                # Borrar tarea del TODO
                if current_task:
                    with open(FILE_TODO, "w", encoding="utf-8") as f:
                        f.writelines(remaining_todo)

                print("✅ Éxito total.")
                return

            else:
                print(f"❌ Error Sintaxis: {error_msg}")
                # Reintentar dándole el error a la IA
                # Actualizamos el código "current" para el prompt de error, 
                # pero mantenemos la misión original en contexto
                mission_prompt = f"El código anterior falló con: {error_msg}. CORRIGE EL ERROR DE SINTAXIS y devuelve todo completo."

        except Exception as e:
            print(f"🔥 Error API/Script: {e}")
    
    sys.exit(1)

if __name__ == "__main__":
    run_review()
