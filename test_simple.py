#!/usr/bin/env python3
"""
Test simple para verificar que todos los módulos funcionan correctamente.
Crea una imagen de prueba y ejecuta el proceso completo de detección.
"""

import cv2
import numpy as np
import os
from src.detector import PlateDetector
from src.extractor import PlateExtractor
from src.ocr_reader import OCRReader
from src.utils import preprocess_image, draw_rectangle, display_images

def crear_imagen_prueba():
    """Crea una imagen de prueba simple con un rectángulo que simula una placa."""
    # Crear imagen base
    img = np.ones((300, 400, 3), dtype=np.uint8) * 100  # Fondo gris
    
    # Simular una placa rectangular
    cv2.rectangle(img, (150, 120), (350, 180), (255, 255, 255), -1)  # Fondo blanco
    cv2.rectangle(img, (150, 120), (350, 180), (0, 0, 0), 2)  # Borde negro
    
    # Agregar algo de "texto" simulado
    cv2.rectangle(img, (160, 135), (180, 165), (0, 0, 0), -1)  # Letra simulada
    cv2.rectangle(img, (190, 135), (210, 165), (0, 0, 0), -1)  # Letra simulada
    cv2.rectangle(img, (220, 135), (240, 165), (0, 0, 0), -1)  # Letra simulada
    cv2.rectangle(img, (260, 135), (280, 165), (0, 0, 0), -1)  # Número simulado
    cv2.rectangle(img, (290, 135), (310, 165), (0, 0, 0), -1)  # Número simulado
    cv2.rectangle(img, (320, 135), (340, 165), (0, 0, 0), -1)  # Número simulado
    
    return img

def test_completo():
    """Ejecuta una prueba completa del sistema."""
    print("🚗 Iniciando test del sistema de detección de placas...")
    
    # Crear imagen de prueba
    imagen_test = crear_imagen_prueba()
    
    # Guardar imagen de prueba
    os.makedirs("images/samples", exist_ok=True)
    cv2.imwrite("images/samples/test_image.jpg", imagen_test)
    print("✅ Imagen de prueba creada: images/samples/test_image.jpg")
    
    # Inicializar componentes
    detector = PlateDetector()
    extractor = PlateExtractor()
    ocr_reader = OCRReader()
    
    print("✅ Componentes inicializados correctamente")    # Preprocesar imagen (asegurar que esté en formato BGR)
    if len(imagen_test.shape) == 3:
        imagen_preprocesada = preprocess_image(imagen_test)
    else:
        # Convertir de escala de grises a BGR si es necesario
        imagen_bgr = cv2.cvtColor(imagen_test, cv2.COLOR_GRAY2BGR)
        imagen_preprocesada = preprocess_image(imagen_bgr)
        imagen_test = imagen_bgr  # Actualizar imagen_test para las siguientes operaciones
    print("✅ Imagen preprocesada")
      # Detectar placas (devuelve coordenadas x, y, w, h)
    coordenadas_placas = detector.detect_plates(imagen_preprocesada)
    print(f"✅ Detectados {len(coordenadas_placas)} rectángulos candidatos a placas")
    
    # Extraer regiones
    regiones_extraidas = []
    for i, (x, y, w, h) in enumerate(coordenadas_placas):
        region = extractor.extract_plate_region(imagen_test, (x, y, w, h))
        if region is not None:
            regiones_extraidas.append(region)
            cv2.imwrite(f"images/samples/region_{i}.jpg", region)
    
    print(f"✅ Extraídas {len(regiones_extraidas)} regiones válidas")
    
    # Intentar OCR en las regiones (nota: puede fallar si Tesseract no está instalado)
    textos_detectados = []
    for i, region in enumerate(regiones_extraidas):
        try:
            texto = ocr_reader.read_text(region)
            textos_detectados.append(texto)
            print(f"📝 Región {i}: '{texto}'")
        except Exception as e:
            print(f"⚠️  OCR no disponible para región {i}: {e}")
            textos_detectados.append("OCR no disponible")
      # Crear imagen de resultado con rectángulos marcados
    imagen_resultado = imagen_test.copy()
    for i, (x, y, w, h) in enumerate(coordenadas_placas[:len(regiones_extraidas)]):
        # Dibujar rectángulo en verde
        cv2.rectangle(imagen_resultado, (x, y), (x + w, y + h), (0, 255, 0), 2)
        # Agregar etiqueta
        etiqueta = f"Placa {i}"
        if i < len(textos_detectados):
            etiqueta += f": {textos_detectados[i]}"
        cv2.putText(imagen_resultado, etiqueta, (x, y - 10), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
    
    cv2.imwrite("images/samples/resultado_test.jpg", imagen_resultado)
    print("✅ Resultado guardado: images/samples/resultado_test.jpg")
    
    print("\n🎉 Test completado exitosamente!")
    print("\nArchivos generados:")
    print("- images/samples/test_image.jpg (imagen original)")
    print("- images/samples/resultado_test.jpg (imagen con detecciones)")
    for i in range(len(regiones_extraidas)):
        print(f"- images/samples/region_{i}.jpg (región extraída {i})")

if __name__ == "__main__":
    test_completo()
