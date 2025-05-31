@echo off
echo ========================================
echo    INSTALADOR DE PLACAS VEHICULARES
echo ========================================
echo.

echo 1. Verificando Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python no está instalado o no está en el PATH
    echo Por favor instale Python desde: https://python.org
    pause
    exit /b 1
)
echo    ✅ Python está instalado

echo.
echo 2. Creando entorno virtual...
if exist venv (
    echo    ⚠️  El entorno virtual ya existe, omitiendo...
) else (
    python -m venv venv
    echo    ✅ Entorno virtual creado
)

echo.
echo 3. Activando entorno virtual...
call venv\Scripts\activate.bat

echo.
echo 4. Actualizando pip...
python -m pip install --upgrade pip

echo.
echo 5. Instalando dependencias...
pip install -r requirements.txt

echo.
echo 6. Verificando instalación de Tesseract...
tesseract --version >nul 2>&1
if errorlevel 1 (
    echo    ⚠️  ADVERTENCIA: Tesseract no está instalado
    echo    Para usar OCR, instale Tesseract desde:
    echo    https://github.com/UB-Mannheim/tesseract/wiki
    echo.
) else (
    echo    ✅ Tesseract está instalado
)

echo.
echo 7. Creando directorios necesarios...
if not exist "results" mkdir results
if not exist "images\samples" mkdir images\samples
echo    ✅ Directorios creados

echo.
echo ========================================
echo         INSTALACIÓN COMPLETADA
echo ========================================
echo.
echo Para usar el proyecto:
echo.
echo 1. Activar entorno virtual:
echo    venv\Scripts\activate
echo.
echo 2. Ejecutar detección básica:
echo    python examples\basic_detection.py --image images\samples\tu_imagen.jpg
echo.
echo 3. Ver todas las opciones:
echo    python examples\basic_detection.py --help
echo.
echo NOTA: Coloque sus imágenes de prueba en images\samples\
echo.
pause
