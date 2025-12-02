# ⚡ Clumsex - Advanced Network Interceptor

![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)
![Platform](https://img.shields.io/badge/Platform-Windows-win.svg)
![Status](https://img.shields.io/badge/Status-Active-green.svg)
![AI Powered](https://img.shields.io/badge/AI-Gemini%20Auto--Updates-purple)

**Clumsex** es una herramienta avanzada de manipulación de tráfico de red (Network Lag Switch) escrita en Python. A diferencia de los limitadores tradicionales que simplemente bloquean el tráfico, Clumsex utiliza un sistema de **Buffering & Flush** basado en el algoritmo *Token Bucket*. Esto permite acumular paquetes y liberarlos controladamente, manteniendo la conexión activa sin desconexiones del servidor.

> ⚠️ **Disclaimer:** Esta herramienta es para fines educativos y de pruebas de red. El uso de este software en juegos en línea puede violar los Términos de Servicio (ToS) y resultar en baneos. Úsalo bajo tu propia responsabilidad.

## 🚀 Características Principales

* **Manipulación de Paquetes TCP:** Intercepta, retiene y reenvía paquetes salientes en puertos específicos.
* **Algoritmo Token Bucket:** Sistema de *Flush* inteligente que evita picos de CPU y desconexiones abruptas al liberar el tráfico acumulado.
* **Overlay Visual:** Temporizador "Siempre visible" (Always-on-top) con soporte *Click-through* que se integra sobre la ventana del juego.
* **Trigger Personalizable:** Soporte completo para remapear la activación a cualquier tecla del teclado o botón del mouse.
* **Optimización de Sistema:** Ajustes automáticos de prioridad de proceso y temporizadores multimedia de Windows para mínima latencia.
* **Auto-Actualización por IA:** Integración con GitHub Actions y Google Gemini para optimización continua y automática del código cada 10 minutos.

## 🛠️ Instalación

### Requisitos Previos
* Windows 10/11 (64-bit).
* Python 3.11 o superior.
* Permisos de Administrador (Necesario para interactuar con el driver WinDivert).

### Pasos
1.  Clona el repositorio:
    ```bash
    git clone [https://github.com/fran04x/clumsex.git](https://github.com/fran04x/clumsex.git)
    cd clumsex
    ```

2.  Instala las dependencias:
    ```bash
    pip install -r requirements.txt
    ```
    *(Nota: Asegúrate de tener las librerías `pydivert`, `pynput`, `pystray`, `Pillow`, `google-genai`)*.

## 🎮 Uso

1.  Ejecuta el script principal con permisos de administrador:
    ```bash
    python clumsex.py
    ```
2.  **Configuración:**
    * **Target Port:** El puerto del juego/aplicación que deseas controlar (Ej. `2050`).
    * **Duration:** Tiempo máximo que el lag se mantendrá activo antes de apagarse automáticamente (seguridad).
    * **Trigger:** Haz clic en "Remap" para asignar tu tecla preferida.

3.  **Activación:**
    * Presiona tu tecla asignada. El indicador cambiará a **VERDE** y el overlay mostrará el tiempo restante.
    * El tráfico se acumulará en memoria.
    * Presiona nuevamente (o espera el tiempo límite) para liberar (Flush) todo el tráfico de golpe.

## 🤖 Sistema de Auto-Actualización (CI/CD con Gemini)

Este proyecto cuenta con un pipeline único de desarrollo continuo impulsado por IA:

1.  **Trigger:** GitHub Actions se ejecuta cada 10 minutos.
2.  **Análisis:** El bot lee el código fuente actual (`clumsex.py`).
3.  **Optimización:** Envía el código a la API de **Google Gemini 2.0 Flash** buscando bugs, optimizaciones de CPU o mejoras de sintaxis.
4.  **Despliegue:** Si Gemini genera una versión mejorada, el bot realiza un commit automático al repositorio con la etiqueta `[AUTO-UPDATE]`.

## ⚙️ Estructura del Proyecto

* `clumsex.py`: Código fuente principal (GUI, Lógica de Red, Overlay).
* `review_bot.py`: Bot encargado de la comunicación con la API de Gemini para las actualizaciones.
* `.github/workflows/auto_review.yml`: Configuración del cronograma de GitHub Actions.

## 📄 Créditos y Librerías

* **WinDivert:** Librería núcleo para la interceptación de paquetes en Windows.
* **PyDivert:** Binding de Python para WinDivert.
* **Tkinter:** Interfaz gráfica.

---
*Desarrollado con ❤️ y mucha cafeína.*
