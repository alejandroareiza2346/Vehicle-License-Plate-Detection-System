#!/usr/bin/env python3
"""
Análisis completo de detección de placas vehiculares con imagen real.
Este programa procesa la imagen del carro y muestra cada paso del proceso.
"""

import cv2
import numpy as np
import os
from src.detector import PlateDetector, AdvancedPlateDetector
from src.extractor import PlateExtractor, AdvancedPlateExtractor
from src.ocr_reader import OCRReader
from src.utils import preprocess_image, resize_image, load_image, save_image

def crear_visualizacion_resultados(imagen_original, contornos, textos, paso_num):
    """Crea una visualización de los resultados de detección."""
    resultado = imagen_original.copy()
    
    for i, contorno in enumerate(contornos):
        # Dibujar contorno
        cv2.drawContours(resultado, [contorno], -1, (0, 255, 0), 3)
        
        # Obtener rectángulo del contorno
        x, y, w, h = cv2.boundingRect(contorno)
        
        # Dibujar texto si está disponible
        if i < len(textos) and textos[i]:
            # Fondo para el texto
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

def analizar_imagen_completa(imagen_path):
    """
    Realiza un análisis completo de la imagen paso a paso.
    """
    print("🚗 ANÁLISIS COMPLETO DE DETECCIÓN DE PLACAS VEHICULARES")
    print("=" * 60)
    
    # PASO 1: Cargar imagen original
    print("\n📁 PASO 1: Cargando imagen original...")
    imagen_original = load_image(imagen_path)
    if imagen_original is None:
        print(f"❌ Error: No se pudo cargar la imagen {imagen_path}")
        return
    
    altura_orig, ancho_orig = imagen_original.shape[:2]
    print(f"✅ Imagen cargada exitosamente")
    print(f"   Dimensiones originales: {ancho_orig}x{altura_orig}")
    print(f"   Formato: {imagen_original.dtype}")
    
    # Guardar imagen original redimensionada para análisis
    imagen_trabajo = resize_image(imagen_original, max_width=800)
    save_image(imagen_trabajo, "results/paso1_original.jpg")
    
    # PASO 2: Preprocesamiento
    print("\n🔧 PASO 2: Preprocesando imagen...")
    imagen_preprocesada = preprocess_image(imagen_trabajo)
    print("✅ Preprocesamiento completado")
    print("   - Conversión a escala de grises")
    print("   - Reducción de ruido")
    print("   - Mejora de contraste")
    save_image(imagen_preprocesada, "results/paso2_preprocesada.jpg")
    
    # PASO 3: Detección básica de placas
    print("\n🔍 PASO 3: Detección básica de placas...")
    detector_basico = PlateDetector()
    contornos_basicos = detector_basico.detect_plates(imagen_preprocesada)
    print(f"✅ Detectados {len(contornos_basicos)} candidatos con método básico")
    
    # Crear visualización de detección básica
    if contornos_basicos:
        vis_basica = crear_visualizacion_resultados(imagen_trabajo, contornos_basicos, [], 3)
        save_image(vis_basica, "results/paso3_deteccion_basica.jpg")
    
    # PASO 4: Detección avanzada
    print("\n🎯 PASO 4: Detección avanzada de placas...")
    detector_avanzado = AdvancedPlateDetector()
    contornos_avanzados = detector_avanzado.detect_plates(imagen_preprocesada)
    print(f"✅ Detectados {len(contornos_avanzados)} candidatos con método avanzado")
    
    # Crear visualización de detección avanzada
    if contornos_avanzados:
        vis_avanzada = crear_visualizacion_resultados(imagen_trabajo, contornos_avanzados, [], 4)
        save_image(vis_avanzada, "results/paso4_deteccion_avanzada.jpg")
    
    # Usar los mejores contornos (combinar ambos métodos)
    todos_contornos = contornos_basicos + contornos_avanzados
    
    # PASO 5: Extracción de regiones
    print("\n✂️  PASO 5: Extrayendo regiones de placas...")
    extractor_basico = PlateExtractor()
    extractor_avanzado = AdvancedPlateExtractor()
    
    regiones_extraidas = []
    contornos_validos = []
    
    for i, contorno in enumerate(todos_contornos):
        # Probar extractor básico primero
        region = extractor_basico.extract_plate_region(imagen_trabajo, contorno)
        if region is None:
            # Si falla, probar extractor avanzado
            region = extractor_avanzado.extract_plate_region(imagen_trabajo, contorno)
        
        if region is not None:
            regiones_extraidas.append(region)
            contornos_validos.append(contorno)
            save_image(region, f"results/paso5_region_{len(regiones_extraidas)}.jpg")
            print(f"   ✅ Región {len(regiones_extraidas)} extraída y guardada")
    
    print(f"✅ Total de regiones válidas extraídas: {len(regiones_extraidas)}")
    
    # PASO 6: Reconocimiento de texto (OCR)
    print("\n📝 PASO 6: Reconocimiento de texto (OCR)...")
    ocr_reader = OCRReader()
    
    textos_detectados = []
    for i, region in enumerate(regiones_extraidas):
        try:
            print(f"   🔍 Analizando región {i+1}...")
            
            # Probar con diferentes motores OCR
            texto_tesseract = ""
            texto_easyocr = ""
            
            try:
                texto_tesseract = ocr_reader.read_text(region)
                print(f"   📋 Tesseract: '{texto_tesseract}'")
            except Exception as e:
                print(f"   ⚠️  Tesseract no disponible: {e}")
            
            try:
                texto_easyocr = ocr_reader.read_text(region)
                print(f"   📋 EasyOCR: '{texto_easyocr}'")
            except Exception as e:
                print(f"   ⚠️  EasyOCR error: {e}")
            
            # Usar el mejor resultado
            texto_final = texto_tesseract if texto_tesseract else texto_easyocr
            textos_detectados.append(texto_final)
            
            if texto_final:
                print(f"   ✅ Texto final detectado: '{texto_final}'")
            else:
                print(f"   ❌ No se pudo extraer texto de la región {i+1}")
                
        except Exception as e:
            print(f"   ❌ Error en OCR para región {i+1}: {e}")
            textos_detectados.append("")
    
    # PASO 7: Resultado final
    print("\n🏁 PASO 7: Generando resultado final...")
    if contornos_validos:
        resultado_final = crear_visualizacion_resultados(imagen_trabajo, contornos_validos, textos_detectados, 7)
        save_image(resultado_final, "results/paso7_resultado_final.jpg")
        print("✅ Resultado final guardado")
    
    # RESUMEN FINAL
    print("\n" + "=" * 60)
    print("📊 RESUMEN DE RESULTADOS")
    print("=" * 60)
    print(f"📁 Imagen analizada: {imagen_path}")
    print(f"📐 Dimensiones: {ancho_orig}x{altura_orig}")
    print(f"🔍 Contornos detectados (básico): {len(contornos_basicos)}")
    print(f"🎯 Contornos detectados (avanzado): {len(contornos_avanzados)}")
    print(f"✂️  Regiones extraídas: {len(regiones_extraidas)}")
    print(f"📝 Textos detectados: {len([t for t in textos_detectados if t])}")
    
    print("\n🏷️  PLACAS DETECTADAS:")
    for i, texto in enumerate(textos_detectados):
        if texto:
            print(f"   {i+1}. {texto}")
        else:
            print(f"   {i+1}. [No se pudo leer]")
    
    print("\n📂 ARCHIVOS GENERADOS:")
    archivos = [
        "results/paso1_original.jpg",
        "results/paso2_preprocesada.jpg",
        "results/paso3_deteccion_basica.jpg",
        "results/paso4_deteccion_avanzada.jpg",
    ]
    
    for i in range(len(regiones_extraidas)):
        archivos.append(f"results/paso5_region_{i+1}.jpg")
    
    archivos.append("results/paso7_resultado_final.jpg")
    
    for archivo in archivos:
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
        print("Asegúrate de que la imagen esté en la ubicación correcta.")
        return
    
    # Ejecutar análisis completo
    textos = analizar_imagen_completa(imagen_path)
    
    print(f"\n🔚 Programa terminado. Revisa los archivos en la carpeta 'results/'")

if __name__ == "__main__":
    main()
