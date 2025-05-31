"""
Detector de placas vehiculares usando técnicas de procesamiento de imágenes.

Este módulo implementa algoritmos para detectar automáticamente placas
vehiculares en imágenes utilizando OpenCV.
"""

import cv2
import numpy as np
from typing import List, Tuple, Optional
from .utils import preprocess_image, is_valid_plate_contour, Config


class PlateDetector:
    """
    Clase para detectar placas vehiculares en imágenes.
    
    Utiliza técnicas de procesamiento de imágenes como detección de bordes,
    análisis de contornos y filtrado geométrico.
    """
    
    def __init__(self, min_area: Optional[int] = None, max_area_ratio: Optional[float] = None):
        """
        Inicializa el detector de placas.
        
        Args:
            min_area (int): Área mínima para considerar un contorno
            max_area_ratio (float): Ratio máximo del área respecto a la imagen
        """
        self.min_area = min_area or Config.MIN_PLATE_AREA
        self.max_area_ratio = max_area_ratio or Config.MAX_PLATE_AREA_RATIO
        
    def detect_plates(self, image: np.ndarray) -> List[Tuple[int, int, int, int]]:
        """
        Detecta placas vehiculares en una imagen.
        
        Args:
            image (np.ndarray): Imagen de entrada en formato BGR
            
        Returns:
            List[Tuple[int, int, int, int]]: Lista de rectángulos (x, y, w, h)
                                           que contienen las placas detectadas
        """
        # Preprocesar imagen
        processed = preprocess_image(image)
        
        # Detectar bordes
        edges = self._detect_edges(processed)
        
        # Encontrar contornos
        contours = self._find_contours(edges)
        
        # Filtrar contornos válidos
        plate_contours = self._filter_plate_contours(list(contours), image.shape[:2])
        
        # Convertir contornos a rectángulos
        plates = []
        for contour in plate_contours:
            x, y, w, h = cv2.boundingRect(contour)
            plates.append((x, y, w, h))
        
        return plates
    
    def _detect_edges(self, image: np.ndarray) -> np.ndarray:
        """
        Detecta bordes en la imagen usando el algoritmo Canny.
        
        Args:
            image (np.ndarray): Imagen en escala de grises
            
        Returns:
            np.ndarray: Imagen binaria con bordes detectados
        """
        # Aplicar detector de bordes Canny
        edges = cv2.Canny(
            image, 
            Config.CANNY_THRESHOLD1, 
            Config.CANNY_THRESHOLD2
        )
        
        # Operaciones morfológicas para conectar bordes
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        edges = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel)
        edges = cv2.morphologyEx(edges, cv2.MORPH_DILATE, kernel)
        
        return edges
    
    def _find_contours(self, edges: np.ndarray) -> List[np.ndarray]:
        """
        Encuentra contornos en la imagen de bordes.
        
        Args:
            edges (np.ndarray): Imagen binaria con bordes
            
        Returns:
            List[np.ndarray]: Lista de contornos encontrados
        """
        contours, _ = cv2.findContours(
            edges, 
            cv2.RETR_EXTERNAL, 
            cv2.CHAIN_APPROX_SIMPLE
        )
        
        return list(contours)
    
    def _filter_plate_contours(self, contours: List[np.ndarray], 
                              image_shape: Tuple[int, int]) -> List[np.ndarray]:
        """
        Filtra contornos que pueden ser placas vehiculares.
        
        Args:
            contours (List[np.ndarray]): Lista de contornos
            image_shape (Tuple[int, int]): Forma de la imagen (height, width)
            
        Returns:
            List[np.ndarray]: Contornos filtrados que pueden ser placas
        """
        height, width = image_shape
        image_area = height * width
        
        valid_contours = []
        
        for contour in contours:
            if is_valid_plate_contour(contour, image_area):
                valid_contours.append(contour)
        
        # Ordenar por área (mayor a menor)
        valid_contours.sort(key=cv2.contourArea, reverse=True)
        
        # Retornar solo los mejores candidatos (máximo 5)
        return valid_contours[:5]
    
    def detect_with_morphology(self, image: np.ndarray) -> List[Tuple[int, int, int, int]]:
        """
        Método alternativo usando operaciones morfológicas avanzadas.
        
        Args:
            image (np.ndarray): Imagen de entrada en formato BGR
            
        Returns:
            List[Tuple[int, int, int, int]]: Lista de rectángulos detectados
        """        # Preprocesar imagen
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()
        
        # Aplicar filtro bilateral para preservar bordes
        bilateral = cv2.bilateralFilter(gray, 9, 75, 75)
        
        # Detectar bordes
        edges = cv2.Canny(bilateral, 50, 150)
        
        # Operaciones morfológicas para formar rectángulos
        kernel_rect = cv2.getStructuringElement(cv2.MORPH_RECT, (15, 5))
        morphed = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel_rect)
        
        # Dilatar para unir componentes
        kernel_dilate = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        morphed = cv2.dilate(morphed, kernel_dilate, iterations=2)
        
        # Encontrar contornos
        contours, _ = cv2.findContours(
            morphed, 
            cv2.RETR_EXTERNAL, 
            cv2.CHAIN_APPROX_SIMPLE
        )
        
        # Filtrar contornos
        plate_contours = self._filter_plate_contours(list(contours), image.shape[:2])
        
        # Convertir a rectángulos
        plates = []
        for contour in plate_contours:
            x, y, w, h = cv2.boundingRect(contour)
            plates.append((x, y, w, h))
        
        return plates
    
    def visualize_detection_process(self, image: np.ndarray) -> List[np.ndarray]:
        """
        Visualiza el proceso de detección paso a paso.
        
        Args:
            image (np.ndarray): Imagen original
            
        Returns:
            List[np.ndarray]: Lista de imágenes mostrando cada paso
        """
        steps = []
        
        # Imagen original
        steps.append(image.copy())
        
        # Preprocesamiento
        processed = preprocess_image(image)
        steps.append(cv2.cvtColor(processed, cv2.COLOR_GRAY2BGR))
        
        # Detección de bordes
        edges = self._detect_edges(processed)
        steps.append(cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR))
        
        # Contornos detectados
        contours = self._find_contours(edges)
        contour_image = image.copy()
        cv2.drawContours(contour_image, contours, -1, (0, 255, 255), 2)
        steps.append(contour_image)
        
        # Placas detectadas
        plates = self.detect_plates(image)
        result = image.copy()
        for x, y, w, h in plates:
            cv2.rectangle(result, (x, y), (x + w, y + h), (0, 255, 0), 2)
        steps.append(result)
        
        return steps


class AdvancedPlateDetector(PlateDetector):
    """
    Detector avanzado con múltiples algoritmos y validaciones adicionales.
    """
    
    def __init__(self, use_adaptive_threshold: bool = True):
        super().__init__()
        self.use_adaptive_threshold = use_adaptive_threshold
    
    def detect_plates(self, image: np.ndarray) -> List[Tuple[int, int, int, int]]:
        """
        Detecta placas usando múltiples métodos y combina resultados.
        """
        # Método 1: Detección estándar
        plates1 = super().detect_plates(image)
        
        # Método 2: Detección con morfología
        plates2 = self.detect_with_morphology(image)
        
        # Método 3: Detección con umbralización adaptativa
        plates3 = self._detect_with_adaptive_threshold(image)
          # Combinar y filtrar resultados
        all_plates = plates1 + plates2 + plates3
        
        # Eliminar duplicados y superpuestos
        filtered_plates = self._remove_overlapping_plates(all_plates)
        return filtered_plates
    
    def _detect_with_adaptive_threshold(self, image: np.ndarray) -> List[Tuple[int, int, int, int]]:
        """
        Detección usando umbralización adaptativa.
        """
        if not self.use_adaptive_threshold:
            return []
        
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()
        
        # Umbralización adaptativa
        adaptive = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
            cv2.THRESH_BINARY, 11, 2
        )
        
        # Invertir si es necesario
        adaptive = cv2.bitwise_not(adaptive)
        
        # Operaciones morfológicas
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (10, 3))
        morphed = cv2.morphologyEx(adaptive, cv2.MORPH_CLOSE, kernel)
        
        # Encontrar contornos
        contours, _ = cv2.findContours(
            morphed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )
        
        # Filtrar contornos
        plate_contours = self._filter_plate_contours(list(contours), image.shape[:2])
        
        plates = []
        for contour in plate_contours:
            x, y, w, h = cv2.boundingRect(contour)
            plates.append((x, y, w, h))
        
        return plates
    
    def _remove_overlapping_plates(self, plates: List[Tuple[int, int, int, int]], 
                                  overlap_threshold: float = 0.5) -> List[Tuple[int, int, int, int]]:
        """
        Elimina placas superpuestas manteniendo las de mayor área.
        """
        if not plates:
            return []
        
        # Ordenar por área (mayor a menor)
        plates_with_area = []
        for x, y, w, h in plates:
            area = w * h
            plates_with_area.append((x, y, w, h, area))
        
        plates_with_area.sort(key=lambda x: x[4], reverse=True)
        
        # Filtrar superpuestos
        filtered = []
        
        for i, (x1, y1, w1, h1, area1) in enumerate(plates_with_area):
            is_overlapping = False
            
            for x2, y2, w2, h2 in filtered:
                # Calcular intersección
                x_left = max(x1, x2)
                y_top = max(y1, y2)
                x_right = min(x1 + w1, x2 + w2)
                y_bottom = min(y1 + h1, y2 + h2)
                
                if x_left < x_right and y_top < y_bottom:
                    intersection_area = (x_right - x_left) * (y_bottom - y_top)
                    union_area = w1 * h1 + w2 * h2 - intersection_area
                    
                    if intersection_area / union_area > overlap_threshold:
                        is_overlapping = True
                        break
            
            if not is_overlapping:
                filtered.append((x1, y1, w1, h1))
        
        return filtered
