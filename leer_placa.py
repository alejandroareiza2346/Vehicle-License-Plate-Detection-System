#!/usr/bin/env python3
"""
Detector simple de placas amarillas - Muestra resultado en terminal y guarda imágenes
"""

import cv2
import numpy as np
import os
from src.ocr_reader import OCRReader
from src.utils import load_image, resize_image, save_image

def leer_placa_amarilla(imagen_path):
    """
    Lee únicamente la placa amarilla, muestra el resultado y guarda imágenes del proceso.
    """
    # Crear directorio de resultados
    os.makedirs("results", exist_ok=True)
    
    print("🔍 Buscando placa amarilla...")
    
    # Cargar imagen
    imagen = load_image(imagen_path)
    if imagen is None:
        print("❌ Error: No se pudo cargar la imagen")
        return None
    
    # Redimensionar para mejor procesamiento
    imagen = resize_image(imagen, max_width=800)
    altura_img, ancho_img = imagen.shape[:2]
    
    # Guardar imagen original redimensionada
    save_image(imagen, "results/01_imagen_original.jpg")
    
    # Convertir a HSV para detectar amarillo
    hsv = cv2.cvtColor(imagen, cv2.COLOR_BGR2HSV)
    
    # Rango para detectar amarillo (placas colombianas)
    lower_yellow = np.array([15, 100, 100])
    upper_yellow = np.array([35, 255, 255])
    
    # Crear máscara para áreas amarillas
    mask_yellow = cv2.inRange(hsv, lower_yellow, upper_yellow)
    
    # Guardar máscara amarilla
    save_image(mask_yellow, "results/02_mascara_amarilla.jpg")
    
    # Operaciones morfológicas para limpiar la máscara
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
    mask_yellow = cv2.morphologyEx(mask_yellow, cv2.MORPH_CLOSE, kernel)
    mask_yellow = cv2.morphologyEx(mask_yellow, cv2.MORPH_OPEN, kernel)
    
    # Guardar máscara procesada
    save_image(mask_yellow, "results/03_mascara_procesada.jpg")
    
    # Encontrar contornos en las áreas amarillas
    contours, _ = cv2.findContours(mask_yellow, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    # Crear imagen para mostrar todos los contornos encontrados
    imagen_contornos = imagen.copy()
    cv2.drawContours(imagen_contornos, contours, -1, (0, 255, 0), 2)
    save_image(imagen_contornos, "results/04_contornos_encontrados.jpg")
    
    # Filtrar contornos que pueden ser placas
    candidatos = []
    
    for i, contour in enumerate(contours):
        area = cv2.contourArea(contour)
        
        # Filtrar por área mínima
        if area < 800:
            continue
            
        # Obtener rectángulo del contorno
        x, y, w, h = cv2.boundingRect(contour)
        
        # Verificar aspect ratio (placas colombianas son ~3:1)
        aspect_ratio = w / h if h > 0 else 0
        if not (2.0 <= aspect_ratio <= 4.5):
            continue
            
        # Verificar que no sea demasiado grande ni pequeña
        if w < 80 or h < 20 or w > ancho_img * 0.8 or h > altura_img * 0.3:
            continue
            
        candidatos.append((x, y, w, h, area))
    
    if not candidatos:
        print("❌ No se detectó ninguna placa amarilla")
        return None
    
    # Ordenar por área (la placa más grande probablemente sea la correcta)
    candidatos.sort(key=lambda x: x[4], reverse=True)
    
    # Crear imagen mostrando candidatos filtrados
    imagen_candidatos = imagen.copy()
    for i, (x, y, w, h, area) in enumerate(candidatos):
        cv2.rectangle(imagen_candidatos, (x, y), (x + w, y + h), (255, 0, 0), 2)
        cv2.putText(imagen_candidatos, f"Candidato {i+1}", (x, y - 10), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 2)
    save_image(imagen_candidatos, "results/05_candidatos_placa.jpg")
    
    # Procesar el mejor candidato
    x, y, w, h, area = candidatos[0]
    
    print(f"✅ Placa detectada en posición: ({x}, {y}) con tamaño: {w}x{h}")
    
    # IMAGEN 1: Crear imagen con recuadro identificando la placa
    imagen_detectada = imagen.copy()
    cv2.rectangle(imagen_detectada, (x, y), (x + w, y + h), (0, 255, 0), 3)
    cv2.putText(imagen_detectada, "PLACA DETECTADA", (x, y - 10), 
               cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
    save_image(imagen_detectada, "results/06_placa_identificada.jpg")
    
    # Extraer región de la placa con un poco de margen
    margin = 5
    x1 = max(0, x - margin)
    y1 = max(0, y - margin)
    x2 = min(ancho_img, x + w + margin)
    y2 = min(altura_img, y + h + margin)
    
    region_placa = imagen[y1:y2, x1:x2]
    
    if region_placa.size == 0:
        print("❌ Error al extraer la región de la placa")
        return None
    
    # IMAGEN 2: Guardar solo la región de la placa extraída
    save_image(region_placa, "results/07_solo_placa.jpg")
    
    print("📸 Imágenes guardadas en results/")
    
    # Usar OCR para leer el texto
    print("🔍 Analizando texto de la placa...")
    ocr_reader = OCRReader()
    
    try:
        # Usar el método estándar del OCRReader
        texto_placa = ocr_reader.read_text(region_placa)
    except Exception as e:
        print(f"❌ Error en OCR: {e}")
        return None
    
    # Limpiar el texto (solo letras y números)
    import re
    texto_limpio = re.sub(r'[^A-Z0-9]', '', texto_placa.upper().strip())
    
    if texto_limpio:
        # RESULTADO FINAL: Crear imagen con la placa y el texto detectado
        imagen_final = imagen.copy()
        cv2.rectangle(imagen_final, (x, y), (x + w, y + h), (0, 255, 0), 3)
        cv2.putText(imagen_final, f"PLACA: {texto_limpio}", (x, y - 15), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
        save_image(imagen_final, "results/08_resultado_final.jpg")
        
        print(f"🎯 La placa es: {texto_limpio}")
        return texto_limpio
    else:
        print("❌ No se pudo leer el texto de la placa")
        return None

def main():
    """Función principal."""
    imagen_path = "images/samples/test_image.webp"
    
    if not os.path.exists(imagen_path):
        print(f"❌ Error: No se encontró la imagen {imagen_path}")
        return
    
    print("🔍 Buscando placa amarilla...")
    placa = leer_placa_amarilla(imagen_path)
    
    if not placa:
        print("\n💡 Sugerencias:")
        print("   - Verifica que la imagen tenga una placa amarilla visible")
        print("   - Asegúrate de que EasyOCR o Tesseract estén instalados")
        print("   - La placa debe tener buen contraste y no estar muy inclinada")

if __name__ == "__main__":
    main()
