#!/usr/bin/env python3
"""
Análisis simplificado de detección de placas vehiculares.
Versión simplificada que evita el detector avanzado mientras corregimos errores.
"""

import cv2
import numpy as np
import os
from src.detector_simple import PlateDetector
from src.extractor import PlateExtractor
from src.ocr_reader import OCRReader
from src.utils import preprocess_image, resize_image, load_image, save_image

def crear_visualizacion_resultados(imagen_original, contornos, textos):
    """Crea una visualización de los resultados de detección."""
    resultado = imagen_original.copy()
    
    for i, contorno in enumerate(contornos):
        # Dibujar contorno
        cv2.drawContours(resultado, [contorno], -1, (0, 255, 0), 3)
        
        # Obtener rectángulo del contorno
        x, y, w, h = cv2.boundingRect(contorno)
        
        # Dibujar rectángulo
        cv2.rectangle(resultado, (x, y), (x + w, y + h), (255, 0, 0), 2)
        
        # Dibujar texto si está disponible
        if i < len(textos) and textos[i]:
            texto = textos[i]
            font_scale = 0.7
            thickness = 2
            (text_w, text_h), baseline = cv2.getTextSize(texto, cv2.FONT_HERSHEY_SIMPLEX, font_scale, thickness)
            
            # Rectángulo de fondo para el texto
            cv2.rectangle(resultado, (x, y - text_h - 10), (x + text_w + 10, y), (0, 255, 0), -1)
            cv2.putText(resultado, texto, (x + 5, y - 5), cv2.FONT_HERSHEY_SIMPLEX, font_scale, (0, 0, 0), thickness)
        
        # Numeración de las detecciones
        cv2.putText(resultado, f"{i+1}", (x, y + 15), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 2)
    
    return resultado

def analizar_imagen_simplificado(imagen_path):
    """
    Realiza un análisis simplificado de la imagen.
    """
    print("🚗 ANÁLISIS SIMPLIFICADO DE DETECCIÓN DE PLACAS")
    print("=" * 50)
    
    # PASO 1: Cargar imagen original
    print("\n📁 PASO 1: Cargando imagen...")
    imagen_original = load_image(imagen_path)
    if imagen_original is None:
        print(f"❌ Error: No se pudo cargar la imagen {imagen_path}")
        return
    
    altura_orig, ancho_orig = imagen_original.shape[:2]
    print(f"✅ Imagen cargada: {ancho_orig}x{altura_orig}")
    
    # Redimensionar para trabajo
    imagen_trabajo = resize_image(imagen_original, max_width=800)
    save_image(imagen_trabajo, "results/01_imagen_original.jpg")
    
    # PASO 2: Preprocesamiento
    print("\n🔧 PASO 2: Preprocesando imagen...")
    imagen_preprocesada = preprocess_image(imagen_trabajo)
    save_image(imagen_preprocesada, "results/02_preprocesada.jpg")
    print("✅ Preprocesamiento completado")
    
    # PASO 3: Detección de placas
    print("\n🔍 PASO 3: Detectando placas...")
    detector = PlateDetector()
    contornos = detector.detect_plates(imagen_preprocesada)
    print(f"✅ Detectados {len(contornos)} candidatos")
    
    if contornos:
        # Convertir tuplas a contornos de OpenCV para visualización
        contornos_cv = []
        for (x, y, w, h) in contornos:
            contorno = np.array([
                [x, y],
                [x + w, y],
                [x + w, y + h],
                [x, y + h]
            ], dtype=np.int32)
            contornos_cv.append(contorno)
        
        vis_deteccion = crear_visualizacion_resultados(imagen_trabajo, contornos_cv, [])
        save_image(vis_deteccion, "results/03_deteccion.jpg")
    
    # PASO 4: Extracción de regiones
    print("\n✂️  PASO 4: Extrayendo regiones...")
    extractor = PlateExtractor()
    
    regiones_extraidas = []
    contornos_validos = []
    
    for i, (x, y, w, h) in enumerate(contornos):
        # Crear contorno para el extractor
        contorno = np.array([
            [x, y],
            [x + w, y],
            [x + w, y + h],
            [x, y + h]
        ], dtype=np.int32)
        
        region = extractor.extract_plate_region(imagen_trabajo, contorno)
        if region is not None:
            regiones_extraidas.append(region)
            contornos_validos.append(contorno)
            save_image(region, f"results/04_region_{len(regiones_extraidas)}.jpg")
            print(f"   ✅ Región {len(regiones_extraidas)} extraída")
    
    print(f"✅ Total regiones extraídas: {len(regiones_extraidas)}")
    
    # PASO 5: OCR
    print("\n📝 PASO 5: Reconocimiento de texto...")
    ocr_reader = OCRReader()
    
    textos_detectados = []
    for i, region in enumerate(regiones_extraidas):
        try:
            print(f"   🔍 Analizando región {i+1}...")
            
            # Probar EasyOCR primero (más confiable)
            try:
                texto = ocr_reader.read_text(region, engine='easyocr')
                if texto.strip():
                    print(f"   📋 EasyOCR: '{texto}'")
                    textos_detectados.append(texto)
                    continue
            except Exception as e:
                print(f"   ⚠️  EasyOCR error: {e}")
            
            # Si EasyOCR falla, probar Tesseract
            try:
                texto = ocr_reader.read_text(region, engine='tesseract')
                if texto.strip():
                    print(f"   📋 Tesseract: '{texto}'")
                    textos_detectados.append(texto)
                else:
                    textos_detectados.append("")
            except Exception as e:
                print(f"   ⚠️  Tesseract no disponible: {e}")
                textos_detectados.append("")
                
        except Exception as e:
            print(f"   ❌ Error en región {i+1}: {e}")
            textos_detectados.append("")
    
    # PASO 6: Resultado final
    print("\n🏁 PASO 6: Resultado final...")
    if contornos_validos and textos_detectados:
        resultado_final = crear_visualizacion_resultados(imagen_trabajo, contornos_validos, textos_detectados)
        save_image(resultado_final, "results/05_resultado_final.jpg")
        print("✅ Resultado final guardado")
    
    # RESUMEN
    print("\n" + "=" * 50)
    print("📊 RESUMEN DE RESULTADOS")
    print("=" * 50)
    print(f"📁 Imagen: {imagen_path}")
    print(f"📐 Dimensiones: {ancho_orig}x{altura_orig}")
    print(f"🔍 Candidatos detectados: {len(contornos)}")
    print(f"✂️  Regiones extraídas: {len(regiones_extraidas)}")
    print(f"📝 Textos detectados: {len([t for t in textos_detectados if t.strip()])}")
    
    print("\n🏷️  PLACAS DETECTADAS:")
    placas_validas = 0
    for i, texto in enumerate(textos_detectados):
        if texto.strip():
            print(f"   {i+1}. '{texto}'")
            placas_validas += 1
        else:
            print(f"   {i+1}. [No se pudo leer]")
    
    if placas_validas == 0:
        print("   ❌ No se detectaron placas legibles")
        print("\n💡 SUGERENCIAS:")
        print("   - Verifica que Tesseract esté instalado")
        print("   - La imagen debe tener buena calidad y la placa visible")
        print("   - Prueba con una imagen más clara o desde otro ángulo")
    
    print("\n📂 ARCHIVOS GENERADOS:")
    archivos_esperados = [
        "results/01_imagen_original.jpg",
        "results/02_preprocesada.jpg",
        "results/03_deteccion.jpg",
        "results/05_resultado_final.jpg"
    ]
    
    for i in range(len(regiones_extraidas)):
        archivos_esperados.append(f"results/04_region_{i+1}.jpg")
    
    for archivo in archivos_esperados:
        if os.path.exists(archivo):
            print(f"   ✅ {archivo}")
    
    print("\n🎉 ANÁLISIS COMPLETADO!")
    return textos_detectados

def main():
    """Función principal."""
    # Crear directorio de resultados
    os.makedirs("results", exist_ok=True)
    
    # Ruta de la imagen
    imagen_path = "images/samples/test_image.webp"
    
    if not os.path.exists(imagen_path):
        print(f"❌ Error: No se encontró la imagen {imagen_path}")
        return
    
    # Ejecutar análisis
    textos = analizar_imagen_simplificado(imagen_path)
    
    if any(t.strip() for t in textos):
        print(f"\n🎯 ¡Éxito! Se detectaron {len([t for t in textos if t.strip()])} placas")
    else:
        print(f"\n⚠️  No se pudieron leer las placas. Revisa los archivos en results/")

if __name__ == "__main__":
    main()
