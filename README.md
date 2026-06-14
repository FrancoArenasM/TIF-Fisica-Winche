# Simulador de Dinámica de Winche Pesquero - TIF Física (Fase 2)

Este proyecto contiene una simulación interactiva para el modelado y análisis dinámico de un winche pesquero durante el izaje de una red de pesca (captura de Bonito). Incluye tanto un simulador interactivo en **Python** (usando `matplotlib` para la visualización del Diagrama de Cuerpo Libre y telemetría) como un simulador **Web** interactivo.

Este trabajo forma parte del **Trabajo de Investigación Formativa (TIF)** de la materia de Física.

---

## Estructura del Proyecto

El repositorio está organizado de la siguiente manera:

*   `simulacion_winche.py`: El script principal de la simulación interactiva en Python. Muestra un Diagrama de Cuerpo Libre (DCL) dinámico con vectores de fuerza en tiempo real (Tensión, Peso, Arrastre Hidrodinámico, Fuerza de Propulsión, Reacción) y gráficos de telemetría de potencia y tensión.
*   `capturar_pruebas.py`: Script auxiliar para la captura de pruebas y validaciones de datos del simulador.
*   `test_telemetria.py`: Script de prueba de la telemetría del sistema.
*   `requirements.txt`: Archivo de dependencias del proyecto.
*   `simulacion/`: Carpeta que contiene la versión Web del simulador (`index.html`, `style.css`, `app.js`) y capturas de prueba.
*   `TIF_Fisica_Winche.tex`: Documento fuente en LaTeX del informe científico.
*   Documentos adjuntos de pautas e informes en formatos `.docx` y `.md`.

---

## 1. Simulación en Python (Escritorio)

La simulación en Python utiliza **Matplotlib** y **NumPy** para simular la física (método numérico de Euler-Cromer) e interactuar mediante controles (sliders y botones de opción) en tiempo real.

### Requisitos

Asegúrate de tener Python instalado (versión 3.8 o superior recomendada).

### Instalación de Dependencias

Para instalar las dependencias necesarias, abre una terminal en la carpeta del proyecto y ejecuta:

```bash
pip install -r requirements.txt
```

### Ejecutar el Simulador

Para iniciar el simulador dinámico, ejecuta el siguiente comando:

```bash
python simulacion_winche.py
```

#### Controles del Simulador:
*   **Masa (kg):** Controla el peso de la red con la captura de Bonito.
*   **V. Izaje (m/s):** Velocidad a la que el winche enrolla el cable.
*   **Corriente (m/s):** Velocidad de la corriente marina transversal (afecta al arrastre hidrodinámico).
*   **Rigidez Cable (N/m):** Constante elástica del cable.
*   **Motor (Yanmar / Cat C1.5 / Chongqing):** Selecciona el modelo de motor para validar si la potencia requerida excede su límite de operación.
*   **Estado (Sumergida / En Aire):** Cambia si la red se encuentra bajo el agua (con efecto de arrastre hidrodinámico) o en el aire.

---

## 2. Simulación Web

Si deseas abrir el simulador web interactivo en tu navegador:

1.  Navega a la carpeta `simulacion/`.
2.  Abre el archivo `index.html` en cualquier navegador web moderno (Chrome, Firefox, Edge, Safari, etc.).

No requiere instalar ningún servidor ni dependencias adicionales; corre directamente en el lado del cliente (HTML5, CSS3, Vanilla JS).

---

## ¿Cómo subirlo a tu propio GitHub?

Si quieres subir este proyecto a tu perfil de GitHub, sigue estos pasos desde una terminal (por ejemplo, Git Bash o CMD/PowerShell en Windows):

1.  **Inicializa el repositorio local:**
    ```bash
    git init
    ```

2.  **Agrega todos los archivos al repositorio (el archivo `.gitignore` evitará subir archivos innecesarios):**
    ```bash
    git add .
    ```

3.  **Realiza el primer commit:**
    ```bash
    git commit -m "Primer commit: Simulador de Winche Pesquero y documentos del TIF"
    ```

4.  **Crea un repositorio vacío en tu cuenta de GitHub** (sin README, gitignore ni licencia para evitar conflictos).

5.  **Vincula tu repositorio local con el de GitHub** (reemplaza con tu enlace):
    ```bash
    git remote add origin https://github.com/TU_USUARIO/TU_REPOSITORIO.git
    ```

6.  **Renombra la rama a `main`:**
    ```bash
    git branch -M main
    ```

7.  **Sube los archivos a GitHub:**
    ```bash
    git push -u origin main
    ```
