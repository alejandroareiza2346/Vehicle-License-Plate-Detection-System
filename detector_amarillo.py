#!/usr/bin/env python3
"""
Detector especializado para placas amarillas colombianas.
Se enfoca en detectar y leer específicamente los dígitos de placas amarillas.
"""

import cv2
import numpy as np
import os
import re
from src.extractor import PlateExtractor
from src.ocr_reader import OCRReader
from src.utils import resize_image, load_image, save_image

def detectar_placas_amarillas(imagen):
    """
    Detecta específicamente placas amarillas en la imagen.
    """
    # Convertir a HSV para mejor detección de color amarillo
    hsv = cv2.cvtColor(imagen, cv2.COLOR_BGR2HSV)
    
    # Rango para amarillo de placas colombianas (más amplio)
    lower_yellow1 = np.array([15, 80, 80])   # Amarillo más oscuro
    upper_yellow1 = np.array([35, 255, 255]) # Amarillo más claro
    
    # Segundo rango para capturar variaciones
    lower_yellow2 = np.array([10, 50, 100])
    upper_yellow2 = np.array([40, 255, 255])
    
    # Crear máscaras
    mask1 = cv2.inRange(hsv, lower_yellow1, upper_yellow1)
    mask2 = cv2.inRange(hsv, lower_yellow2, upper_yellow2)
    
    # Combinar máscaras
    mask_yellow = cv2.bitwise_or(mask1, mask2)
    
    # Operaciones morfológicas para limpiar la máscara
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
    mask_yellow = cv2.morphologyEx(mask_yellow, cv2.MORPH_CLOSE, kernel)
    mask_yellow = cv2.morphologyEx(mask_yellow, cv2.MORPH_OPEN, kernel)
    
    return mask_yellow

def encontrar_contornos_placa(mask_yellow, imagen_shape):
    """
    Encuentra contornos que pueden ser placas en la máscara amarilla.
    """
    altura, ancho = imagen_shape[:2]
    
    # Encontrar contornos
    contours, _ = cv2.findContours(mask_yellow, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    candidatos = []
    
    for contour in contours:
        # Calcular área
        area = cv2.contourArea(contour)
        
        # Filtros para placas colombianas
        min_area = 800   # Área mínima más pequeña
        max_area = ancho * altura * 0.15  # Máximo 15% de la imagen
        
        if area < min_area or area > max_area:
            continue
        
        # Obtener rectángulo delimitador
        x, y, w, h = cv2.boundingRect(contour)
        
        # Verificar aspect ratio (placas colombianas son rectangulares)
        aspect_ratio = w / h if h > 0 else 0
        
        # Placas colombianas tienen ratio entre 2:1 y 4:1
        if not (1.8 <= aspect_ratio <= 4.5):
            continue
        
        # Verificar que no sea demasiado pequeña en píxeles
        if w < 60 or h < 20:
            continue
        
        # Verificar que el contorno tenga forma rectangular
        perimeter = cv2.arcLength(contour, True)
        approx = cv2.approxPolyDP(contour, 0.02 * perimeter, True)
        
        # Debe tener aproximadamente 4 esquinas (rectángulo)
        if len(approx) >= 4:
            candidatos.append({
                'contour': contour,
                'bbox': (x, y, w, h),
                'area': area,
                'aspect_ratio': aspect_ratio,
                'approx_corners': len(approx)
            })
    
    # Ordenar por área (más grande primero)
    candidatos.sort(key=lambda x: x['area'], reverse=True)
    
    return candidatos

def extraer_texto_digitos(region_placa, debug_info=""):
    """
    Extrae específicamente los dígitos de una región de placa.
    """
    if region_placa is None:
        return ""
    
    # Preprocesar la región para mejorar OCR
    # 1. Convertir a escala de grises
    if len(region_placa.shape) == 3:
        gray = cv2.cvtColor(region_placa, cv2.COLOR_BGR2GRAY)
    else:
        gray = region_placa.copy()
    
    # 2. Redimensionar si es muy pequeña
    altura, ancho = gray.shape
    if ancho < 120:
        factor = 120 / ancho
        nuevo_ancho = int(ancho * factor)
        nueva_altura = int(altura * factor)
        gray = cv2.resize(gray, (nuevo_ancho, nueva_altura), interpolation=cv2.INTER_CUBIC)
    
    # 3. Mejorar contraste
    gray = cv2.equalizeHist(gray)
    
    # 4. Aplicar filtro para reducir ruido
    gray = cv2.medianBlur(gray, 3)
    
    # 5. Umbralización para obtener texto negro sobre fondo blanco
    # Probar diferentes métodos de umbralización
    thresh_methods = [
        cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1],
        cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)[1],
        cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
    ]
    
    # Guardar imágenes de debug si se especifica
    if debug_info:
        save_image(gray, f"results/debug_region_{debug_info}_gray.jpg")
        for i, thresh in enumerate(thresh_methods):
            save_image(thresh, f"results/debug_region_{debug_info}_thresh_{i}.jpg")
    
    # Intentar OCR con cada método
    ocr_reader = OCRReader()
    mejores_resultados = []
    
    for i, thresh_img in enumerate(thresh_methods):
        try:
            # Probar con EasyOCR (mejor para placas)
            try:
                texto_easy = ocr_reader.read_text(thresh_img, engine='easyocr')
                if texto_easy.strip():
                    mejores_resultados.append(texto_easy.strip())
            except:
                pass
            
            # Probar con Tesseract
            try:
                texto_tess = ocr_reader.read_text(thresh_img, engine='tesseract')
                if texto_tess.strip():
                    mejores_resultados.append(texto_tess.strip())
            except:
                pass
        except:
            continue
    
    if not mejores_resultados:
        return ""
    
    # Limpiar y filtrar resultados
    textos_limpios = []
    for texto in mejores_resultados:
        # Limpiar caracteres extraños y espacios
        texto_limpio = re.sub(r'[^A-Z0-9\s]', '', texto.upper())
        texto_limpio = re.sub(r'\s+', ' ', texto_limpio).strip()
        
        if texto_limpio and len(texto_limpio) >= 3:
            textos_limpios.append(texto_limpio)
    
    if not textos_limpios:
        return ""
    
    # Buscar el mejor resultado (el que más se parezca a una placa colombiana)
    mejor_texto = ""
    mejor_score = 0
    
    for texto in textos_limpios:
        score = 0
        
        # Bonus por tener letras y números
        if re.search(r'[A-Z]', texto):
            score += 2
        if re.search(r'[0-9]', texto):
            score += 3
        
        # Bonus por longitud apropiada (6-7 caracteres para placas colombianas)
        if 5 <= len(texto.replace(' ', '')) <= 8:
            score += 2
        
        # Penalty por caracteres extraños
        if re.search(r'[^A-Z0-9\s]', texto):
            score -= 1
        
        if score > mejor_score:
            mejor_score = score
            mejor_texto = texto
    
    return mejor_texto

def analizar_placa_amarilla(imagen_path):
    """
    Análisis completo enfocado en placas amarillas.
    """
    print("🟡 DETECTOR ESPECIALIZADO DE PLACAS AMARILLAS COLOMBIANAS")
    print("=" * 60)
    
    # Cargar imagen
    print("\n📁 Cargando imagen...")
    imagen_original = load_image(imagen_path)
    if imagen_original is None:
        print(f"❌ Error al cargar {imagen_path}")
        return []
    
    altura_orig, ancho_orig = imagen_original.shape[:2]
    print(f"✅ Imagen cargada: {ancho_orig}x{altura_orig}")
    
    # Redimensionar si es necesario
    imagen_trabajo = resize_image(imagen_original, max_width=1000)  # Mantener más resolución
    save_image(imagen_trabajo, "results/yellow_01_original.jpg")
    
    # PASO 1: Detectar color amarillo
    print("\n🟡 PASO 1: Detectando regiones amarillas...")
    mask_yellow = detectar_placas_amarillas(imagen_trabajo)
    save_image(mask_yellow, "results/yellow_02_mask.jpg")
    
    # Aplicar máscara a imagen original
    imagen_amarilla = cv2.bitwise_and(imagen_trabajo, imagen_trabajo, mask=mask_yellow)
    save_image(imagen_amarilla, "results/yellow_03_yellow_regions.jpg")
    
    # PASO 2: Encontrar contornos de placas
    print("\n📐 PASO 2: Buscando contornos de placas...")
    candidatos = encontrar_contornos_placa(mask_yellow, imagen_trabajo.shape)
    
    print(f"✅ Encontrados {len(candidatos)} candidatos de placas amarillas")
    
    if not candidatos:
        print("❌ No se encontraron placas amarillas")
        return []
    
    # Visualizar candidatos
    vis_candidatos = imagen_trabajo.copy()
    for i, candidato in enumerate(candidatos):
        x, y, w, h = candidato['bbox']
        area = candidato['area']
        ratio = candidato['aspect_ratio']
        
        # Dibujar rectángulo
        cv2.rectangle(vis_candidatos, (x, y), (x + w, y + h), (0, 255, 0), 3)
        
        # Información del candidato
        texto_info = f"#{i+1}: {area:.0f}px, {ratio:.1f}:1"
        cv2.putText(vis_candidatos, texto_info, (x, y - 10), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        
        print(f"   Candidato {i+1}: área={area:.0f}, ratio={ratio:.2f}, pos=({x},{y}), tam=({w}x{h})")
    
    save_image(vis_candidatos, "results/yellow_04_candidates.jpg")
    
    # PASO 3: Extraer y analizar cada región
    print("\n✂️  PASO 3: Extrayendo regiones de placas...")
    extractor = PlateExtractor()
    
    placas_detectadas = []
    
    for i, candidato in enumerate(candidatos):
        print(f"\n   🔍 Analizando candidato {i+1}...")
        
        # Extraer región
        x, y, w, h = candidato['bbox']
        
        # Expandir ligeramente la región para capturar mejor la placa
        margen = 5
        x_exp = max(0, x - margen)
        y_exp = max(0, y - margen)
        w_exp = min(imagen_trabajo.shape[1] - x_exp, w + 2*margen)
        h_exp = min(imagen_trabajo.shape[0] - y_exp, h + 2*margen)
        
        region_expandida = imagen_trabajo[y_exp:y_exp+h_exp, x_exp:x_exp+w_exp]
        
        if region_expandida.size == 0:
            continue
        
        save_image(region_expandida, f"results/yellow_05_region_{i+1}.jpg")
        
        # Extraer texto
        print(f"      📝 Extrayendo texto...")
        texto_detectado = extraer_texto_digitos(region_expandida, f"{i+1}")
        
        if texto_detectado:
            print(f"      ✅ Texto detectado: '{texto_detectado}'")
            
            placas_detectadas.append({
                'texto': texto_detectado,
                'bbox': candidato['bbox'],
                'confianza': candidato['area']  # Usar área como medida de confianza
            })
        else:
            print(f"      ❌ No se pudo extraer texto")
    
    # PASO 4: Resultado final
    print("\n🏁 PASO 4: Resultado final...")
    
    if placas_detectadas:
        # Visualizar resultado final
        resultado_final = imagen_trabajo.copy()
        
        for i, placa in enumerate(placas_detectadas):
            x, y, w, h = placa['bbox']
            texto = placa['texto']
            
            # Dibujar rectángulo verde
            cv2.rectangle(resultado_final, (x, y), (x + w, y + h), (0, 255, 0), 3)
            
            # Dibujar texto detectado
            font_scale = 1.0
            thickness = 2
            (text_w, text_h), baseline = cv2.getTextSize(texto, cv2.FONT_HERSHEY_SIMPLEX, font_scale, thickness)
            
            # Fondo para el texto
            cv2.rectangle(resultado_final, (x, y - text_h - 15), 
                         (x + text_w + 10, y - 5), (0, 255, 0), -1)
            
            # Texto
            cv2.putText(resultado_final, texto, (x + 5, y - 10), 
                       cv2.FONT_HERSHEY_SIMPLEX, font_scale, (0, 0, 0), thickness)
        
        save_image(resultado_final, "results/yellow_06_final_result.jpg")
    
    # RESUMEN
    print("\n" + "=" * 60)
    print("📊 RESUMEN - PLACAS AMARILLAS DETECTADAS")
    print("=" * 60)
    
    if placas_detectadas:
        print(f"🎯 ¡ÉXITO! Se detectaron {len(placas_detectadas)} placas amarillas:")
        for i, placa in enumerate(placas_detectadas):
            print(f"   {i+1}. {placa['texto']}")
        
        # Mostrar solo los dígitos si se requiere
        print(f"\n🔢 SOLO DÍGITOS:")
        for i, placa in enumerate(placas_detectadas):
            digitos = re.findall(r'\d+', placa['texto'])
            if digitos:
                print(f"   {i+1}. {''.join(digitos)}")
            else:
                print(f"   {i+1}. [Sin dígitos claros]")
    else:
        print("❌ No se detectaron placas amarillas legibles")
        print("\n💡 SUGERENCIAS:")
        print("   - Verifica que la imagen tenga una placa amarilla visible")
        print("   - La placa debe tener buen contraste y no estar muy inclinada")
        print("   - Revisa los archivos en results/ para ver el proceso")
    
    print(f"\n📂 ARCHIVOS GENERADOS EN results/:")
    archivos_yellow = [
        "yellow_01_original.jpg",
        "yellow_02_mask.jpg", 
        "yellow_03_yellow_regions.jpg",
        "yellow_04_candidates.jpg",
        "yellow_06_final_result.jpg"
    ]
    
    for archivo in archivos_yellow:
        if os.path.exists(f"results/{archivo}"):
            print(f"   ✅ {archivo}")
    
    print(f"\n🎉 ANÁLISIS COMPLETADO!")
    
    return [placa['texto'] for placa in placas_detectadas]

def main():
    """Función principal."""
    os.makedirs("results", exist_ok=True)
    
    imagen_path = "images/samples/test_image.webp"
    
    if not os.path.exists(imagen_path):
        print(f"❌ Error: No se encontró {imagen_path}")
        return
    
    placas = analizar_placa_amarilla(imagen_path)
    
    if placas:
        print(f"\n🏆 RESULTADO FINAL:")
        for i, placa in enumerate(placas):
            print(f"Placa {i+1}: {placa}")
            
            # Extraer solo números
            numeros = re.findall(r'\d+', placa)
            if numeros:
                print(f"Dígitos: {''.join(numeros)}")

if __name__ == "__main__":
    main()
