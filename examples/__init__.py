"""
Archivo de inicialización del paquete examples.

Proporciona acceso fácil a los scripts de ejemplo.
"""

__version__ = "1.0.0"
__description__ = "Ejemplos de uso para el sistema de detección de placas vehiculares"

# Scripts disponibles
AVAILABLE_EXAMPLES = {
    'basic_detection': 'Detección básica en una imagen',
    'batch_processing': 'Procesamiento en lote de múltiples imágenes', 
    'video_detection': 'Detección en video y tiempo real'
}

def list_examples():
    """Lista todos los ejemplos disponibles."""
    print("📚 EJEMPLOS DISPONIBLES:")
    print("=" * 40)
    for script, description in AVAILABLE_EXAMPLES.items():
        print(f"• {script}.py: {description}")

if __name__ == "__main__":
    list_examples()
