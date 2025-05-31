"""
Detector de placas vehiculares simplificado y funcional.
"""

import cv2
import numpy as np
from typing import List, Tuple, Optional
from .utils import preprocess_image, is_valid_plate_contour


class PlateDetectorSimple:
    """Detector de placas simplificado que funciona correctamente."""
    
    def __init__(self, min_area: int = 1000, max_area_ratio: float = 0.3):
        """
        Inicializa el detector simple.
        
        Args:
            min_area (int): Área mínima para considerar un contorno
            max_area_ratio (float): Ratio máximo del área respecto a la imagen
        """
        self.min_area = min_area
        self.max_area_ratio = max_area_ratio
    
    def detect_plates(self, image: np.ndarray) -> List[Tuple[int, int, int, int]]:
        """
        Detecta placas vehiculares en una imagen.
        
        Args:
            image (np.ndarray): Imagen de entrada
            
        Returns:
            List[Tuple[int, int, int, int]]: Lista de rectángulos (x, y, w, h)
        """
        # Asegurar que la imagen esté en escala de grises
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()
        
        # Aplicar filtro gaussiano
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        
        # Detectar bordes con Canny
        edges = cv2.Canny(blurred, 50, 150)
        
        # Operaciones morfológicas para cerrar gaps
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        closed = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel)
        
        # Encontrar contornos
        contours, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Filtrar contornos candidatos
        candidates = []
        image_area = gray.shape[0] * gray.shape[1]
        
        for contour in contours:
            # Obtener rectángulo delimitador
            x, y, w, h = cv2.boundingRect(contour)
            area = w * h
            
            # Filtros básicos
            if area < self.min_area:
                continue
            
            if area > image_area * self.max_area_ratio:
                continue
            
            # Ratio de aspecto típico de placas (entre 2:1 y 5:1)
            aspect_ratio = w / h
            if aspect_ratio < 1.5 or aspect_ratio > 6.0:
                continue
            
            # Verificar que el contorno sea suficientemente rectangular
            contour_area = cv2.contourArea(contour)
            extent = contour_area / area
            if extent < 0.6:  # Debe ocupar al menos 60% del rectángulo
                continue
            
            candidates.append((x, y, w, h))
        
        # Ordenar por área (más grandes primero)
        candidates.sort(key=lambda rect: rect[2] * rect[3], reverse=True)
        
        # Eliminar duplicados/solapamientos
        filtered = self._remove_overlapping(candidates)
        
        return filtered
    
    def _remove_overlapping(self, rectangles: List[Tuple[int, int, int, int]], 
                           overlap_threshold: float = 0.3) -> List[Tuple[int, int, int, int]]:
        """
        Elimina rectángulos que se solapan significativamente.
        
        Args:
            rectangles: Lista de rectángulos (x, y, w, h)
            overlap_threshold: Umbral de solapamiento (0.0 a 1.0)
            
        Returns:
            Lista filtrada de rectángulos
        """
        if not rectangles:
            return []
        
        filtered = []
        
        for rect in rectangles:
            x1, y1, w1, h1 = rect
            
            # Verificar si se solapa significativamente con algún rectángulo ya aceptado
            overlaps = False
            for accepted in filtered:
                x2, y2, w2, h2 = accepted
                
                # Calcular intersección
                ix1 = max(x1, x2)
                iy1 = max(y1, y2)
                ix2 = min(x1 + w1, x2 + w2)
                iy2 = min(y1 + h1, y2 + h2)
                
                if ix1 < ix2 and iy1 < iy2:
                    intersection = (ix2 - ix1) * (iy2 - iy1)
                    area1 = w1 * h1
                    area2 = w2 * h2
                    union = area1 + area2 - intersection
                    
                    if intersection / union > overlap_threshold:
                        overlaps = True
                        break
            
            if not overlaps:
                filtered.append(rect)
        
        return filtered


# Alias para compatibilidad
PlateDetector = PlateDetectorSimple
