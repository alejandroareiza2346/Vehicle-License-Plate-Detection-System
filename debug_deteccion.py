#!/usr/bin/env python3
"""
Análisis de depuración para entender por qué no se detectan placas.
"""

import cv2
import numpy as np
import os
from src.detector import PlateDetector
from src.extractor import PlateExtractor
from src.utils import preprocess_image, resize_image, load_image, save_image

def analizar_con_debug(imagen_path):
    """
    Análisis detallado con información de depuración.
    """
    print("🔍 ANÁLISIS DE DEPURACIÓN PARA DETECCIÓN DE PLACAS")
    print("=" * 60)
    
    # Cargar imagen
    print("\n📁 Cargando imagen...")
    imagen_original = load_image(imagen_path)
    if imagen_original is None:
        print(f"❌ Error: No se pudo cargar {imagen_path}")
        return
    
    altura_orig, ancho_orig = imagen_original.shape[:2]
    print(f"✅ Imagen cargada: {ancho_orig}x{altura_orig}")
    print(f"   Tipo: {imagen_original.dtype}")
    print(f"   Canales: {len(imagen_original.shape)}")
    
    # Redimensionar
    imagen_trabajo = resize_image(imagen_original, max_width=800)
    altura_work, ancho_work = imagen_trabajo.shape[:2]
    print(f"   Redimensionada a: {ancho_work}x{altura_work}")
    
    # Preprocesamiento con múltiples técnicas
    print("\n🔧 Probando diferentes técnicas de preprocesamiento...")
    
    # 1. Preprocesamiento estándar
    gray_std = preprocess_image(imagen_trabajo)
    save_image(gray_std, "results/debug_01_gray_standard.jpg")
    print("   ✅ Preprocesamiento estándar guardado")
    
    # 2. Solo escala de grises
    if len(imagen_trabajo.shape) == 3:
        gray_simple = cv2.cvtColor(imagen_trabajo, cv2.COLOR_BGR2GRAY)
    else:
        gray_simple = imagen_trabajo.copy()
    save_image(gray_simple, "results/debug_02_gray_simple.jpg")
    print("   ✅ Escala de grises simple guardado")
    
    # 3. Con filtro bilateral
    bilateral = cv2.bilateralFilter(gray_simple, 9, 75, 75)
    save_image(bilateral, "results/debug_03_bilateral.jpg")
    print("   ✅ Filtro bilateral guardado")
    
    # 4. Detección de bordes con diferentes parámetros
    print("\n🔍 Probando detección de bordes...")
    
    # Canny con parámetros bajos
    edges_low = cv2.Canny(gray_simple, 30, 100)
    save_image(edges_low, "results/debug_04_edges_low.jpg")
    print("   ✅ Bordes (umbral bajo) guardado")
    
    # Canny con parámetros altos
    edges_high = cv2.Canny(gray_simple, 100, 200)
    save_image(edges_high, "results/debug_05_edges_high.jpg")
    print("   ✅ Bordes (umbral alto) guardado")
    
    # Canny automático
    sigma = 0.33
    v = np.median(gray_simple)
    lower = int(max(0, (1.0 - sigma) * v))
    upper = int(min(255, (1.0 + sigma) * v))
    edges_auto = cv2.Canny(gray_simple, lower, upper)
    save_image(edges_auto, "results/debug_06_edges_auto.jpg")
    print(f"   ✅ Bordes automáticos (umbrales: {lower}-{upper}) guardado")
    
    # 5. Detección de contornos
    print("\n📐 Analizando contornos...")
    
    for i, (name, edges) in enumerate([
        ("low", edges_low),
        ("high", edges_high), 
        ("auto", edges_auto)
    ]):
        # Operaciones morfológicas
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        morphed = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel)
        morphed = cv2.morphologyEx(morphed, cv2.MORPH_DILATE, kernel)
        
        # Encontrar contornos
        contours, _ = cv2.findContours(morphed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        print(f"   📊 Método {name}: {len(contours)} contornos encontrados")
        
        # Analizar contornos por tamaño
        areas = [cv2.contourArea(c) for c in contours]
        if areas:
            print(f"      - Área mínima: {min(areas):.0f}")
            print(f"      - Área máxima: {max(areas):.0f}")
            print(f"      - Área promedio: {np.mean(areas):.0f}")
        
        # Visualizar todos los contornos
        vis_all = imagen_trabajo.copy()
        cv2.drawContours(vis_all, contours, -1, (0, 255, 0), 2)
        save_image(vis_all, f"results/debug_07_contours_{name}.jpg")
        
        # Filtrar contornos por área
        min_area = 500  # Área mínima para una placa
        max_area = ancho_work * altura_work * 0.1  # Máximo 10% de la imagen
        
        filtered_contours = []
        for contour in contours:
            area = cv2.contourArea(contour)
            if min_area <= area <= max_area:
                # Verificar aspect ratio
                x, y, w, h = cv2.boundingRect(contour)
                aspect_ratio = w / h if h > 0 else 0
                
                # Las placas colombianas tienen aspect ratio entre 2:1 y 4:1
                if 1.5 <= aspect_ratio <= 5.0:
                    filtered_contours.append(contour)
        
        print(f"      - Contornos filtrados: {len(filtered_contours)}")
        
        if filtered_contours:
            # Visualizar contornos filtrados
            vis_filtered = imagen_trabajo.copy()
            for j, contour in enumerate(filtered_contours):
                # Dibujar contorno
                cv2.drawContours(vis_filtered, [contour], -1, (0, 255, 0), 3)
                
                # Dibujar rectángulo
                x, y, w, h = cv2.boundingRect(contour)
                cv2.rectangle(vis_filtered, (x, y), (x + w, y + h), (255, 0, 0), 2)
                
                # Información del contorno
                area = cv2.contourArea(contour)
                aspect_ratio = w / h if h > 0 else 0
                
                # Texto informativo
                text = f"{j+1}: {area:.0f}px, {aspect_ratio:.1f}:1"
                cv2.putText(vis_filtered, text, (x, y - 10), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 2)
                
                print(f"         Candidato {j+1}: área={area:.0f}, ratio={aspect_ratio:.2f}, pos=({x},{y}), tam=({w}x{h})")
            
            save_image(vis_filtered, f"results/debug_08_filtered_{name}.jpg")
    
    # 6. Probar detector oficial
    print("\n🤖 Probando detector oficial...")
    detector = PlateDetector()
    
    try:
        placas_detectadas = detector.detect_plates(imagen_trabajo)
        print(f"   📊 Detector oficial: {len(placas_detectadas)} placas detectadas")
        
        if placas_detectadas:
            vis_oficial = imagen_trabajo.copy()
            for i, (x, y, w, h) in enumerate(placas_detectadas):
                cv2.rectangle(vis_oficial, (x, y), (x + w, y + h), (0, 255, 0), 3)
                cv2.putText(vis_oficial, f"Placa {i+1}", (x, y - 10), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                print(f"      Placa {i+1}: pos=({x},{y}), tam=({w}x{h})")
            
            save_image(vis_oficial, "results/debug_09_detector_oficial.jpg")
    except Exception as e:
        print(f"   ❌ Error en detector oficial: {e}")
    
    # 7. Análisis de colores
    print("\n🎨 Analizando colores de la imagen...")
    
    # Convertir a HSV para análisis de color
    hsv = cv2.cvtColor(imagen_trabajo, cv2.COLOR_BGR2HSV)
    
    # Buscar colores típicos de placas (amarillo, blanco)
    # Amarillo en HSV
    lower_yellow = np.array([15, 50, 50])
    upper_yellow = np.array([35, 255, 255])
    mask_yellow = cv2.inRange(hsv, lower_yellow, upper_yellow)
    
    # Blanco en HSV
    lower_white = np.array([0, 0, 200])
    upper_white = np.array([180, 30, 255])
    mask_white = cv2.inRange(hsv, lower_white, upper_white)
    
    # Combinar máscaras
    mask_combined = cv2.bitwise_or(mask_yellow, mask_white)
    
    save_image(mask_yellow, "results/debug_10_mask_yellow.jpg")
    save_image(mask_white, "results/debug_11_mask_white.jpg")
    save_image(mask_combined, "results/debug_12_mask_combined.jpg")
    
    # Aplicar máscara a la imagen original
    result_masked = cv2.bitwise_and(imagen_trabajo, imagen_trabajo, mask=mask_combined)
    save_image(result_masked, "results/debug_13_color_filtered.jpg")
    
    print("   ✅ Análisis de colores completado")
    
    # Resumen
    print("\n" + "=" * 60)
    print("📋 RESUMEN DEL ANÁLISIS DE DEPURACIÓN")
    print("=" * 60)
    print(f"📁 Imagen analizada: {imagen_path}")
    print(f"📐 Dimensiones originales: {ancho_orig}x{altura_orig}")
    print(f"📐 Dimensiones de trabajo: {ancho_work}x{altura_work}")
    
    print("\n📂 ARCHIVOS DE DEPURACIÓN GENERADOS:")
    debug_files = [
        "debug_01_gray_standard.jpg",
        "debug_02_gray_simple.jpg", 
        "debug_03_bilateral.jpg",
        "debug_04_edges_low.jpg",
        "debug_05_edges_high.jpg",
        "debug_06_edges_auto.jpg",
        "debug_07_contours_low.jpg",
        "debug_07_contours_high.jpg",
        "debug_07_contours_auto.jpg",
        "debug_08_filtered_low.jpg",
        "debug_08_filtered_high.jpg",
        "debug_08_filtered_auto.jpg",
        "debug_09_detector_oficial.jpg",
        "debug_10_mask_yellow.jpg",
        "debug_11_mask_white.jpg",
        "debug_12_mask_combined.jpg",
        "debug_13_color_filtered.jpg"
    ]
    
    for archivo in debug_files:
        ruta_completa = f"results/{archivo}"
        if os.path.exists(ruta_completa):
            print(f"   ✅ {archivo}")
    
    print(f"\n🎯 RECOMENDACIONES:")
    print("   1. Revisa los archivos debug_07_contours_*.jpg para ver si se detectan contornos")
    print("   2. Revisa debug_08_filtered_*.jpg para ver candidatos filtrados")
    print("   3. Si no hay detecciones, la placa puede ser muy pequeña o poco contrastada")
    print("   4. Revisa debug_12_mask_combined.jpg para ver si se detectan colores de placa")
    
    print(f"\n🏁 Análisis de depuración completado!")

def main():
    """Función principal."""
    os.makedirs("results", exist_ok=True)
    
    imagen_path = "images/samples/test_image.webp"
    
    if not os.path.exists(imagen_path):
        print(f"❌ Error: No se encontró {imagen_path}")
        return
    
    analizar_con_debug(imagen_path)

if __name__ == "__main__":
    main()
