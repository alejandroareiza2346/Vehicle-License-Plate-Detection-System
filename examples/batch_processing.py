"""
Procesamiento en lote de múltiples imágenes.

Este script procesa todas las imágenes en un directorio y genera
un reporte con los resultados de detección de placas.
"""

import os
import sys
import argparse
import glob
import json
from datetime import datetime
import cv2

# Agregar el directorio src al path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from src.detector import AdvancedPlateDetector
from src.extractor import AdvancedPlateExtractor
from src.ocr_reader import OCRReader
from src.utils import load_image, resize_image, save_image


from typing import Optional

def process_single_image(image_path: str, detector, extractor, ocr_reader, output_dir: Optional[str] = None):
    """
    Procesa una sola imagen.
    
    Args:
        image_path (str): Ruta a la imagen
        detector: Detector de placas
        extractor: Extractor de regiones
        ocr_reader: Lector OCR
        output_dir (str): Directorio de salida
        
    Returns:
        dict: Resultados del procesamiento
    """
    result = {
        'image_path': image_path,
        'image_name': os.path.basename(image_path),
        'timestamp': datetime.now().isoformat(),
        'success': False,
        'plates_detected': 0,
        'plates_recognized': 0,
        'plates_data': []
    }
    
    try:
        # Cargar imagen
        image = load_image(image_path)
        if image is None:
            result['error'] = "No se pudo cargar la imagen"
            return result
        
        # Redimensionar
        image = resize_image(image, max_width=800)
        
        # Detectar placas
        plates = detector.detect_plates(image)
        result['plates_detected'] = len(plates)
        
        if plates:
            # Extraer regiones
            all_enhanced = extractor.extract_and_enhance_all(image, plates)
            
            # Procesar cada placa
            for i, (coords, enhanced_versions) in enumerate(zip(plates, all_enhanced)):
                plate_data = {
                    'plate_id': i + 1,
                    'coordinates': coords,
                    'text': '',
                    'confidence': 0.0
                }
                
                # OCR
                text = ocr_reader.read_text_multiple_versions(enhanced_versions)
                
                if text and ocr_reader.validate_plate_text(text):
                    plate_data['text'] = text
                    plate_data['confidence'] = 1.0  # Simplificado
                    result['plates_recognized'] += 1
                
                result['plates_data'].append(plate_data)
            
            # Guardar imagen con resultados si se especifica directorio
            if output_dir:
                output_image = image.copy()
                for plate_data in result['plates_data']:
                    x, y, w, h = plate_data['coordinates']
                    
                    # Color según si se reconoció texto
                    color = (0, 255, 0) if plate_data['text'] else (0, 0, 255)
                    cv2.rectangle(output_image, (x, y), (x + w, y + h), color, 2)
                    
                    # Agregar texto si se reconoció
                    if plate_data['text']:
                        cv2.putText(
                            output_image,
                            plate_data['text'],
                            (x, y - 10),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.7,
                            color,
                            2
                        )
                
                # Guardar imagen
                output_path = os.path.join(
                    output_dir,
                    f"result_{os.path.splitext(os.path.basename(image_path))[0]}.jpg"
                )
                save_image(output_image, output_path)
                result['output_image'] = output_path
        
        result['success'] = True
        
    except Exception as e:
        result['error'] = str(e)
    
    return result


from typing import Optional

def process_batch(input_dir: str, output_dir: Optional[str] = None, report_path: Optional[str] = None):
    """
    Procesa todas las imágenes en un directorio.
    
    Args:
        input_dir (str): Directorio con imágenes de entrada
        output_dir (str): Directorio para guardar resultados
        report_path (str): Ruta para guardar el reporte JSON
    """
    print(f"🔄 Iniciando procesamiento en lote...")
    print(f"📁 Directorio de entrada: {input_dir}")
    
    # Crear directorio de salida si es necesario
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        print(f"📁 Directorio de salida: {output_dir}")
    
    # Encontrar todas las imágenes
    image_extensions = ['*.jpg', '*.jpeg', '*.png', '*.bmp', '*.tiff', '*.tif']
    image_files = []
    
    for ext in image_extensions:
        pattern = os.path.join(input_dir, ext)
        image_files.extend(glob.glob(pattern))
        # También buscar en mayúsculas
        pattern = os.path.join(input_dir, ext.upper())
        image_files.extend(glob.glob(pattern))
    
    # Remover duplicados
    image_files = list(set(image_files))
    
    print(f"🖼️  Imágenes encontradas: {len(image_files)}")
    
    if not image_files:
        print("❌ No se encontraron imágenes en el directorio")
        return
    
    # Inicializar componentes
    print("🛠️  Inicializando componentes...")
    detector = AdvancedPlateDetector()
    extractor = AdvancedPlateExtractor()
    ocr_reader = OCRReader()
    
    # Procesar cada imagen
    results = []
    total_plates_detected = 0
    total_plates_recognized = 0
    
    print("🚀 Iniciando procesamiento...\n")
    
    for i, image_path in enumerate(image_files, 1):
        print(f"[{i}/{len(image_files)}] Procesando: {os.path.basename(image_path)}")
        
        result = process_single_image(
            image_path, detector, extractor, ocr_reader, output_dir
        )
        
        results.append(result)
        
        if result['success']:
            total_plates_detected += result['plates_detected']
            total_plates_recognized += result['plates_recognized']
            
            print(f"   ✅ Placas detectadas: {result['plates_detected']}")
            print(f"   ✅ Placas reconocidas: {result['plates_recognized']}")
            
            # Mostrar textos reconocidos
            for plate_data in result['plates_data']:
                if plate_data['text']:
                    print(f"      📋 {plate_data['text']}")
        else:
            print(f"   ❌ Error: {result.get('error', 'Desconocido')}")
        
        print()
    
    # Generar reporte
    report = {
        'summary': {
            'total_images': len(image_files),
            'successful_images': sum(1 for r in results if r['success']),
            'failed_images': sum(1 for r in results if not r['success']),
            'total_plates_detected': total_plates_detected,
            'total_plates_recognized': total_plates_recognized,
            'recognition_rate': total_plates_recognized / max(total_plates_detected, 1),
            'processing_date': datetime.now().isoformat()
        },
        'results': results
    }
    
    # Guardar reporte
    if report_path:
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        print(f"📊 Reporte guardado en: {report_path}")
    
    # Mostrar resumen
    print("=" * 50)
    print("📊 RESUMEN DEL PROCESAMIENTO EN LOTE")
    print("=" * 50)
    print(f"Imágenes procesadas: {report['summary']['total_images']}")
    print(f"Procesamiento exitoso: {report['summary']['successful_images']}")
    print(f"Procesamiento fallido: {report['summary']['failed_images']}")
    print(f"Placas detectadas: {report['summary']['total_plates_detected']}")
    print(f"Placas reconocidas: {report['summary']['total_plates_recognized']}")
    print(f"Tasa de reconocimiento: {report['summary']['recognition_rate']:.2%}")
    
    # Mostrar todas las placas reconocidas
    all_recognized_plates = []
    for result in results:
        for plate_data in result['plates_data']:
            if plate_data['text']:
                all_recognized_plates.append({
                    'image': result['image_name'],
                    'text': plate_data['text']
                })
    
    if all_recognized_plates:
        print(f"\n📋 PLACAS RECONOCIDAS ({len(all_recognized_plates)}):")
        for plate in all_recognized_plates:
            print(f"   • {plate['image']}: {plate['text']}")


def main():
    """Función principal del script."""
    parser = argparse.ArgumentParser(
        description="Procesamiento en lote de detección de placas vehiculares",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos de uso:
  python batch_processing.py --input ../images/samples/
  python batch_processing.py --input ../images/samples/ --output ../results/
  python batch_processing.py --input ../images/samples/ --output ../results/ --report reporte.json
        """
    )
    
    parser.add_argument(
        '--input', '-i',
        required=True,
        help='Directorio con imágenes de entrada'
    )
    
    parser.add_argument(
        '--output', '-o',
        help='Directorio para guardar imágenes con resultados'
    )
    
    parser.add_argument(
        '--report', '-r',
        help='Archivo para guardar reporte JSON'
    )
    
    args = parser.parse_args()
    
    # Verificar que el directorio de entrada existe
    if not os.path.isdir(args.input):
        print(f"❌ Error: El directorio {args.input} no existe")
        return
    
    # Ejecutar procesamiento en lote
    process_batch(
        input_dir=args.input,
        output_dir=args.output,
        report_path=args.report
    )


if __name__ == "__main__":
    main()
