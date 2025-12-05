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

## 🕒 2025-12-02 22:30:29
The code has been refactored to remove all comments and docstrings, making it more compact. No functional changes were made, ensuring the application's logic remains intact.

## 🕒 2025-12-02 22:41:40
The code has been stripped of comments and docstrings to reduce its size. No functional changes were made.

## 🕒 2025-12-02 22:52:14
Las optimizaciones incluyen:

1.  Eliminación de todos los comentarios y docstrings.
2.  Abreviación de nombres de variables locales cuando es seguro (por ejemplo, `packet_data` -> `p`).
3.  Simplificación de la función `resource_path` para mayor concisión.
4.  Inline de funciones pequeñas y llamadas directas cuando apropiado.
5.  Reestructuración de `show_tray` para usar directamente `self.tray_icon.run` en un hilo.
6.  Cambio de un bucle `run_tray` a una llamada directa.
7.  Reestructuración de `safe_stop` para mayor concisión.
8.  Eliminación de `daemon=True` redundante en el hilo `tray_icon`.
9.  Eliminación de variables temporales innecesarias para ahorrar espacio.
10. Otras optimizaciones menores para eliminar redundancia y acortar líneas.

## 🕒 2025-12-02 23:10:08
Removed comments and docstrings. Compacted some lines for brevity. Maintained all core logic and functionality.

## 🕒 2025-12-02 23:28:51
Eliminé todos los comentarios y docstrings para reducir el tamaño del código. No se realizaron cambios lógicos en el código. El código conserva su funcionalidad original.

## 🕒 2025-12-02 23:38:37
El código se ha optimizado eliminando todos los comentarios y docstrings para reducir su tamaño. No se han realizado cambios en la lógica funcional. El código resultante es más compacto, pero conserva toda la funcionalidad del original.

## 🕒 2025-12-02 23:45:45
The code has been stripped of comments and docstrings to reduce its size while maintaining functionality. Minor formatting adjustments have been made to improve readability. The core logic and structure of the application remain unchanged.

## 🕒 2025-12-02 23:52:10
The code has been stripped of comments and docstrings to reduce its size. Functionality remains identical.

## 🕒 2025-12-03 02:30:17
The code was refactored to remove all comments and docstrings, as requested. Code functionality was preserved while maximizing code density. No logic was removed.

## 🕒 2025-12-03 03:45:16
El código fue revisado y optimizado eliminando todos los comentarios y docstrings para reducir su tamaño. Se mantuvo la funcionalidad del código original, asegurando que la lógica permanezca intacta. También se preservó el bloque `if __name__ == "__main__":` al final del script.

## 🕒 2025-12-03 04:19:50
He removido todos los comentarios y docstrings. No he modificado la lógica del código. He intentado mantener el código lo más compacto posible sin sacrificar la legibilidad en la medida de lo posible.

## 🕒 2025-12-03 05:11:45
El código se ha revisado y se han eliminado todos los comentarios y docstrings para reducir el tamaño. Se ha mantenido la funcionalidad principal y la estructura del código.

## 🕒 2025-12-03 06:17:24
The code has been stripped of comments and docstrings to minimize its size. Functionality remains the same.

## 🕒 2025-12-03 07:14:14
El código se ha limpiado eliminando comentarios y docstrings para reducir el tamaño. No se han realizado cambios funcionales ni de lógica.

## 🕒 2025-12-03 08:16:11
El código se ha optimizado eliminando todos los comentarios y docstrings para reducir el tamaño del archivo. No se ha modificado la funcionalidad del código.

## 🕒 2025-12-03 09:15:51
The code has been stripped of comments and docstrings to reduce its size. No functional changes were made. The code is still long but within the character limit.

## 🕒 2025-12-03 10:13:09
El código se ha optimizado eliminando comentarios y docstrings, y se ha mantenido la estructura general para asegurar su funcionalidad. No se han realizado cambios lógicos.

## 🕒 2025-12-03 11:11:10
The code was stripped of comments and docstrings to minimize size. No functional changes were made.

## 🕒 2025-12-03 12:21:07
The code has been refactored to remove all comments and docstrings, reducing its size significantly. No functional changes were made. The structure and logic remain identical to the original code.

## 🕒 2025-12-03 13:29:40
The code was optimized by removing all comments and docstrings to reduce its size. Functionality was preserved while adhering to the specified format.

## 🕒 2025-12-03 14:12:01
The code has been stripped of comments and docstrings to save space. The core logic remains intact and functional.

## 🕒 2025-12-03 15:12:56
El código ha sido revisado y optimizado eliminando todos los comentarios y docstrings para reducir su tamaño. La funcionalidad principal se ha mantenido intacta, asegurando que las funciones sigan operando según lo previsto. Se han conservado las estructuras de control de flujo y la lógica esencial del programa.

## 🕒 2025-12-03 16:15:35
El código ha sido revisado y optimizado eliminando comentarios y docstrings para reducir el tamaño del archivo. La lógica principal se ha mantenido intacta, asegurando que la funcionalidad del programa permanezca sin cambios.

## 🕒 2025-12-03 17:15:12
El código ha sido revisado y optimizado eliminando comentarios y docstrings para reducir el tamaño. Se ha mantenido la funcionalidad principal y la estructura del código. No se realizaron cambios lógicos.

## 🕒 2025-12-03 18:16:53
The code has been stripped of comments and docstrings to minimize its length. No logic was altered.

## 🕒 2025-12-03 19:10:40
He eliminado todos los comentarios y docstrings, compactado el código manteniendo la funcionalidad.

## 🕒 2025-12-03 20:12:45
El código se ha optimizado eliminando comentarios y docstrings para reducir el tamaño del archivo. Se ha mantenido la lógica original y la estructura del código para asegurar su funcionalidad. No se han realizado cambios en el comportamiento del programa.

## 🕒 2025-12-03 21:10:27
The code has been stripped of all comments and docstrings as requested. The core logic and functionality remain intact. No significant optimizations were performed, focusing on adhering to the prompt's strict output requirements.

## 🕒 2025-12-03 22:11:51
The code has been stripped of comments and docstrings to reduce its size. Functionality remains the same.

## 🕒 2025-12-03 23:09:07
He eliminado todos los comentarios y docstrings. Además, se han mantenido los nombres de las variables y la estructura del código original para garantizar la funcionalidad. El código se ha compactado, pero sin sacrificar la legibilidad.

## 🕒 2025-12-04 00:48:44
He eliminado todos los comentarios y docstrings para ahorrar caracteres y cumplido con las instrucciones de salida. No se ha cortado ninguna lógica.

## 🕒 2025-12-04 02:30:54
The code has been stripped of all comments and docstrings to reduce its size.  No functional changes were made; the logic remains identical to the original. The code is now more compact.

## 🕒 2025-12-04 03:46:40
The code has been stripped of all comments and docstrings to reduce its size. No functional changes were made.

## 🕒 2025-12-04 04:21:20
El código se ha compactado eliminando comentarios y docstrings. No se ha modificado la lógica.

## 🕒 2025-12-04 05:11:32
Eliminé comentarios y docstrings para reducir el tamaño del código. El código permanece funcional.

## 🕒 2025-12-04 06:17:07
El código se ha optimizado eliminando todos los comentarios y docstrings, y reduciendo los espacios en blanco innecesarios para compactarlo. La funcionalidad principal se ha mantenido intacta.

## 🕒 2025-12-04 07:13:34
El código se ha revisado y se han eliminado todos los comentarios y docstrings para reducir el tamaño del código. Se ha mantenido la funcionalidad intacta, aunque se ha priorizado la eliminación de comentarios y la compresión general del código.

## 🕒 2025-12-04 08:16:30
The code has been stripped of all comments and docstrings to minimize its length while maintaining functionality. No logic has been altered.

## 🕒 2025-12-04 09:15:00
Removed all comments and docstrings to reduce size. The code's core logic remains intact. Minor formatting adjustments were made for readability.

## 🕒 2025-12-04 10:13:01
El código ha sido limpiado de comentarios y docstrings. Se ha mantenido la estructura y funcionalidad original, optimizando el espacio.

## 🕒 2025-12-04 11:11:22
The code was stripped of all comments and docstrings to minimize its size. Functionality was preserved.

## 🕒 2025-12-04 12:21:40
El código se ha compactado eliminando todos los comentarios y docstrings. Se ha mantenido la funcionalidad intacta, aunque la legibilidad se ha reducido en favor de la brevedad. No se han realizado cambios lógicos ni optimizaciones algorítmicas.

## 🕒 2025-12-04 13:30:20
El código fue revisado y optimizado eliminando comentarios y docstrings. La funcionalidad principal se mantiene intacta, y el código se ha mantenido compacto.

## 🕒 2025-12-04 14:12:43
The code was stripped of all comments and docstrings as requested to reduce the size. No functional changes were made. The code is now more compact while preserving all the original logic.

## 🕒 2025-12-04 15:13:35
The code has been stripped of all comments and docstrings to reduce its size, while maintaining its overall structure and functionality. This includes removing comments from all functions, class definitions, and the main execution block.

## 🕒 2025-12-04 16:14:49
El código se ha optimizado eliminando todos los comentarios y docstrings, y reduciendo el espaciado en blanco siempre que no afecte la legibilidad. No se han realizado cambios en la lógica funcional.

## 🕒 2025-12-04 17:15:09
El código se ha compactado eliminando comentarios y docstrings. No se ha modificado la lógica del programa.

## 🕒 2025-12-04 18:17:07
The code was stripped of comments and docstrings to reduce its size. Functionality was preserved.

## 🕒 2025-12-04 19:11:47
El código se ha optimizado eliminando todos los comentarios y docstrings, reduciendo el tamaño del archivo. La lógica del programa se ha mantenido intacta, asegurando que todas las funciones sigan operando como se esperaba. El bloque `if __name__ == "__main__":` se conserva al final.

## 🕒 2025-12-04 20:12:23
The code was stripped of comments and docstrings. No functional changes were made.

## 🕒 2025-12-04 21:10:38
El código se ha optimizado eliminando todos los comentarios y docstrings. Se ha mantenido la estructura y funcionalidad del código original.

## 🕒 2025-12-04 22:09:04
He eliminado todos los comentarios y docstrings, compactado el código lo máximo posible sin alterar su funcionalidad, y he mantenido la estructura general del programa. El bloque `if __name__ == "__main__":` permanece al final del script.

## 🕒 2025-12-04 23:10:31
El código se ha optimizado eliminando todos los comentarios y docstrings. Se ha mantenido la funcionalidad del programa.

## 🕒 2025-12-05 00:49:12
The code has been compressed by removing all comments and docstrings. No logic was changed.