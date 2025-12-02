# 📜 Historial de Cambios - Clumsex

Este documento registra la evolución del proyecto. Las entradas inferiores son generadas automáticamente por el sistema de Integración Continua (CI/CD) impulsado por Google Gemini.

---

## 📦 [v12.2] - Versión Base Stable
**Fecha:** 02 de Diciembre, 2025
**Tipo:** Manual
* **Core:** Carga inicial del código fuente `clumsex.py`.
* **Red:** Implementación de intercepción de paquetes mediante `pydivert` (WinDivert).
* **GUI:** Interfaz gráfica con Tkinter y Overlay con soporte "click-through".
* **Auto-Update:** Configuración inicial del workflow de GitHub Actions.

---
*(A partir de este punto, los registros son generados automáticamente por el Bot)*


## 🕒 Versión 2025-12-02 18:32:57
Actualización automática (Sin detalles generados).

## 🕒 Versión 2025-12-02 18:48:20
- **Reemplacé `sys._MEIPASS` con `sys._MEIPASS` y `AttributeError`** para la detección del path en ejecutable compilado.
- **Simplifiqué el condicional de la imagen del ícono del tray** en `create_tray_image` para hacerlo más conciso.
- **Unifiqué el manejo de excepciones** para hacer el código más legible y evitar repeticiones. Donde antes había `except:` ahora hay `except Exception:`.
- **Eliminé `finally: state.

## 🕒 Versión 2025-12-02 19:10:20
- **Capture Worker: Reducción de Serialización (CPU/Memoria):** En el `capture_worker`, se modificó la forma en que los paquetes se

## 🕒 Versión 2025-12-02 19:17:15
Actualización automática (Sin detalles generados).

## 🕒 Versión 2025-12-02 19:17:58
Actualización automática (Sin detalles generados).

## 🕒 Versión 2025-12-02 19:18:43
Actualización automática (Sin detalles generados).

## 🕒 Versión 2025-12-02 19:40:25
Actualización automática.

## 🕒 Versión 2025-12-02 19:49:35
Actualización automática.

## 🕒 Versión 2025-12-02 20:11:58
Actualización automática.

## 🕒 2025-12-02 20:28:17
✅ **Tarea:** Añadir un background muy minimalista y transparente al timer, el background debe ser de color negro y ocupar muy pocos recursos, solo debe verse cuando el lag switch este activo.
Update: Añadir un background muy minimalista y transparente al timer, el background debe ser de color negro y ocupar muy pocos recursos, solo debe verse cuando el lag switch este activo.

## 🕒 2025-12-02 20:39:22
✅ **Tarea:** Optimizar la funcion flush_worker para usar menos memoria.
Update: Optimizar la funcion flush_worker para usar menos memoria.

## 🕒 2025-12-02 20:53:25
Optimización general

## 🕒 2025-12-02 21:37:48
✅ **Tarea:** Corrige un error de sintaxis en el codigo donde se busca el ejecutable "RotMG Exalt" pero en realidad se llama "RotMGExalt".
Se corrigió un error de sintaxis en la clase `GlobalState`. La variable `self.game_window_title` se cambió de `"RotMG Exalt"` a `"RotMGExalt"` para que coincida con el nombre real del ejecutable. Adicionalmente, se eliminaron todos los comentarios y docstrings según las instrucciones, y se ajustó el formato para mantener la legibilidad y la compacidad.

## 🕒 2025-12-02 21:39:30
✅ **Tarea:** Corrige un error que causa que el timer se pueda arrastrar aun teniendo la opcion bloqueada desde la ventana principal de clumsex. (Creo que solo aparece cuando la ventana RotMGExalt no está presente) tambien elimina la posibilidad de que aparezca el timer cuando la ventana RotMGExalt.exe no está presente.
Se implementaron dos cambios principales en la clase `OverlayTimer`:
1.  **Prevención de arrastre al estar bloqueado:** Se añadió un chequeo `if state.lock_timer: return` al inicio de los métodos `click_win`, `drag_win` y `release_win`. Esto asegura que el timer solo pueda ser arrastrado si la opción "Lock Timer Position" está desactivada en la GUI principal.
2.  **Visibilidad condicionada a la ventana del juego:** Se modificó la lógica de la variable `is_visible` en el método `update_view`. Ahora, la visibilidad del timer no solo depende de `state.lock_timer` o `state.lag_event.is_set()`, sino que también requiere que la ventana `RotMGExalt` esté presente. Se usa `ctypes.windll.user32.FindWindowW` para verificar su existencia, y el timer se oculta (`withdraw()`) si la ventana del juego no se encuentra, incluso si la opción de bloqueo está desactivada o el lag está activo.

## 🕒 2025-12-02 21:46:06
El código ha sido optimizado eliminando comentarios y docstrings, reduciendo el espacio utilizado. No se ha modificado la lógica funcional.

## 🕒 2025-12-02 21:52:16
The code was stripped of all comments and docstrings to reduce its size, as requested. No logic was changed.

## 🕒 2025-12-02 22:10:02
The code has been stripped of all comments and docstrings to minimize its length. Functionality remains intact, though readability is reduced. The core logic and program structure are preserved.