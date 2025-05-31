"""
Ejemplo básico de detección de placas vehiculares.

Este script demuestra el uso básico del sistema de detección de placas,
desde la carga de la imagen hasta la visualización de resultados.
"""

import os
import sys
import argparse
import cv2
import numpy as np

# Agregar el directorio src al path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from src.detector import PlateDetector
from src.extractor import PlateExtractor
from src.ocr_reader import OCRReader
from src.utils import load_image, resize_image, draw_rectangle, display_images, save_image


from typing import Optional

def detect_and_recognize_plates(image_path: str, output_path: Optional[str] = None, show_steps: bool = False):
    """
    Función principal para detectar y reconocer placas vehiculares.
    
    Args:
        image_path (str): Ruta a la imagen de entrada
        output_path (str): Ruta para guardar la imagen con resultados
        show_steps (bool): Mostrar pasos del procesamiento
    """
    print(f"🚗 Iniciando detección de placas en: {image_path}")
    
    # 1. Cargar imagen
    print("📁 Cargando imagen...")
    image = load_image(image_path)
    if image is None:
        print("❌ Error: No se pudo cargar la imagen")
        return
    
    # Redimensionar si es muy grande
    image = resize_image(image, max_width=800)
    print(f"✅ Imagen cargada - Dimensiones: {image.shape[:2]}")
    
    # 2. Detectar placas
    print("🔍 Detectando placas...")
    detector = PlateDetector()
    plates = detector.detect_plates(image)
    print(f"✅ Placas detectadas: {len(plates)}")
    
    if not plates:
        print("⚠️  No se detectaron placas en la imagen")
        return
    
    # 3. Extraer regiones de placas
    print("✂️  Extrayendo regiones de placas...")
    extractor = PlateExtractor()
    plate_regions = extractor.extract_all_plates(image, plates)
    print(f"✅ Regiones extraídas: {len(plate_regions)}")
    
    # 4. Procesar con OCR
    print("🔤 Reconociendo texto con OCR...")
    ocr_reader = OCRReader()
    
    results = []
    for i, region in enumerate(plate_regions):
        # Mejorar región para OCR
        enhanced_versions = extractor.preprocess_for_ocr(region)
        
        # Reconocer texto
        text = ocr_reader.read_text_multiple_versions(enhanced_versions)
        
        if text:
            results.append((plates[i], text))
            print(f"📋 Placa {i+1}: {text}")
        else:
            print(f"❌ No se pudo reconocer texto en placa {i+1}")
    
    # 5. Visualizar resultados
    print("🎨 Creando visualización...")
    result_image = image.copy()
    
    for (x, y, w, h), text in results:
        # Dibujar rectángulo
        result_image = draw_rectangle(result_image, x, y, w, h)
        
        # Agregar texto
        cv2.putText(
            result_image, 
            text, 
            (x, y - 10), 
            cv2.FONT_HERSHEY_SIMPLEX, 
            0.8, 
            (0, 255, 0), 
            2
        )
    
    # 6. Mostrar y/o guardar resultados
    if show_steps:
        # Mostrar proceso paso a paso
        steps = detector.visualize_detection_process(image)
        step_titles = [
            "Original",
            "Preprocesado", 
            "Bordes",
            "Contornos",
            "Placas Detectadas"
        ]
        display_images(steps, step_titles)
    
    # Mostrar resultado final
    display_images([image, result_image], ["Original", "Resultado"])
    
    # Guardar si se especifica
    if output_path:
        if save_image(result_image, output_path):
            print(f"💾 Resultado guardado en: {output_path}")
    
    # Resumen final
    print(f"\n📊 RESUMEN:")
    print(f"   • Placas detectadas: {len(plates)}")
    print(f"   • Texto reconocido: {len(results)} placas")
    for i, (_, text) in enumerate(results):
        print(f"   • Placa {i+1}: {text}")


def main():
    """Función principal del script."""
    parser = argparse.ArgumentParser(
        description="Detección e identificación de placas vehiculares",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos de uso:
  python basic_detection.py --image ../images/samples/carro.jpg
  python basic_detection.py --image ../images/samples/carro.jpg --output resultado.jpg --steps
        """
    )
    
    parser.add_argument(
        '--image', '-i',
        required=True,
        help='Ruta a la imagen de entrada'
    )
    
    parser.add_argument(
        '--output', '-o',
        help='Ruta para guardar la imagen con resultados'
    )
    
    parser.add_argument(
        '--steps', '-s',
        action='store_true',
        help='Mostrar pasos del procesamiento'
    )
    
    args = parser.parse_args()
    
    # Verificar que el archivo existe
    if not os.path.exists(args.image):
        print(f"❌ Error: El archivo {args.image} no existe")
        return
    
    # Ejecutar detección
    detect_and_recognize_plates(
        image_path=args.image,
        output_path=args.output,
        show_steps=args.steps
    )


if __name__ == "__main__":
    main()
