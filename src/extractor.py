"""
Extractor de regiones de placas vehiculares.

Este módulo se encarga de extraer y procesar las regiones específicas
donde se detectaron las placas para optimizar el reconocimiento OCR.
"""

import cv2
import numpy as np
from typing import List, Tuple, Optional
from .utils import Config


class PlateExtractor:
    """
    Clase para extraer y procesar regiones de placas detectadas.
    
    Mejora la calidad de las regiones extraídas para optimizar
    el reconocimiento de texto mediante OCR.
    """
    
    def __init__(self, padding: int = 5):
        """
        Inicializa el extractor de placas.
        
        Args:
            padding (int): Píxeles adicionales alrededor de la región detectada
        """
        self.padding = padding
    
    def extract_plate_region(self, image: np.ndarray, 
                           plate_coords: Tuple[int, int, int, int]) -> Optional[np.ndarray]:
        """
        Extrae la región de la placa de la imagen original.
        
        Args:
            image (np.ndarray): Imagen original
            plate_coords (Tuple[int, int, int, int]): Coordenadas (x, y, w, h)
            
        Returns:
            Optional[np.ndarray]: Región extraída o None si hay error
        """
        x, y, w, h = plate_coords
        
        # Agregar padding
        x_start = max(0, x - self.padding)
        y_start = max(0, y - self.padding)
        x_end = min(image.shape[1], x + w + self.padding)
        y_end = min(image.shape[0], y + h + self.padding)
        
        # Extraer región
        try:
            plate_region = image[y_start:y_end, x_start:x_end]
            
            if plate_region.size == 0:
                return None
            
            return plate_region
        except Exception as e:
            print(f"Error al extraer región de placa: {e}")
            return None
    
    def extract_all_plates(self, image: np.ndarray, 
                          plates_coords: List[Tuple[int, int, int, int]]) -> List[np.ndarray]:
        """
        Extrae todas las regiones de placas detectadas.
        
        Args:
            image (np.ndarray): Imagen original
            plates_coords (List[Tuple[int, int, int, int]]): Lista de coordenadas
            
        Returns:
            List[np.ndarray]: Lista de regiones extraídas
        """
        plate_regions = []
        
        for coords in plates_coords:
            region = self.extract_plate_region(image, coords)
            if region is not None:
                plate_regions.append(region)
        
        return plate_regions
    
    def enhance_plate_region(self, plate_region: np.ndarray) -> np.ndarray:
        """
        Mejora la calidad de una región de placa para OCR.
        
        Args:
            plate_region (np.ndarray): Región de placa extraída
            
        Returns:
            np.ndarray: Región mejorada
        """
        # Convertir a escala de grises si es necesario
        if len(plate_region.shape) == 3:
            gray = cv2.cvtColor(plate_region, cv2.COLOR_BGR2GRAY)
        else:
            gray = plate_region.copy()
        
        # Redimensionar si es muy pequeña
        enhanced = self._resize_if_small(gray)
        
        # Mejorar contraste
        enhanced = self._enhance_contrast(enhanced)
        
        # Reducir ruido
        enhanced = self._reduce_noise(enhanced)
        
        # Binarización
        enhanced = self._binarize_image(enhanced)
        
        return enhanced
    
    def _resize_if_small(self, image: np.ndarray, min_height: int = 30) -> np.ndarray:
        """
        Redimensiona la imagen si es muy pequeña para mejorar OCR.
        """
        height, width = image.shape[:2]
        
        if height < min_height:
            scale_factor = min_height / height
            new_width = int(width * scale_factor)
            new_height = min_height
            
            # Usar interpolación bicúbica para mejor calidad
            resized = cv2.resize(
                image, 
                (new_width, new_height), 
                interpolation=cv2.INTER_CUBIC
            )
            return resized
        
        return image
    
    def _enhance_contrast(self, image: np.ndarray) -> np.ndarray:
        """
        Mejora el contraste de la imagen.
        """
        # CLAHE (Contrast Limited Adaptive Histogram Equalization)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(image)
        
        return enhanced
    
    def _reduce_noise(self, image: np.ndarray) -> np.ndarray:
        """
        Reduce el ruido en la imagen.
        """
        # Filtro bilateral para reducir ruido preservando bordes
        denoised = cv2.bilateralFilter(image, 9, 75, 75)
        
        return denoised
    
    def _binarize_image(self, image: np.ndarray) -> np.ndarray:
        """
        Binariza la imagen para mejorar el reconocimiento de texto.
        """
        # Probar diferentes métodos de umbralización
        
        # Método 1: Otsu
        _, binary1 = cv2.threshold(image, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # Método 2: Umbralización adaptativa
        binary2 = cv2.adaptiveThreshold(
            image, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
            cv2.THRESH_BINARY, 11, 2
        )
        
        # Método 3: Umbralización adaptativa con media
        binary3 = cv2.adaptiveThreshold(
            image, 255, cv2.ADAPTIVE_THRESH_MEAN_C, 
            cv2.THRESH_BINARY, 11, 2
        )        # Seleccionar el mejor resultado basado en la varianza
        # (mayor varianza indica mejor separación)
        variances = [
            binary1.var(),
            binary2.var(),
            binary3.var()
        ]
        
        best_method = np.argmax(variances)
        
        if best_method == 0:
            return binary1
        elif best_method == 1:
            return binary2
        else:
            return binary3
    
    def preprocess_for_ocr(self, plate_region: np.ndarray) -> List[np.ndarray]:
        """
        Preprocesa una región de placa generando múltiples versiones para OCR.
        
        Args:
            plate_region (np.ndarray): Región de placa original
            
        Returns:
            List[np.ndarray]: Lista de versiones procesadas
        """
        processed_versions = []
        
        # Versión 1: Procesamiento estándar
        enhanced = self.enhance_plate_region(plate_region)
        processed_versions.append(enhanced)
        
        # Versión 2: Invertida (texto blanco sobre fondo oscuro)
        inverted = cv2.bitwise_not(enhanced)
        processed_versions.append(inverted)
        
        # Versión 3: Con operaciones morfológicas para limpiar
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
        cleaned = cv2.morphologyEx(enhanced, cv2.MORPH_CLOSE, kernel)
        processed_versions.append(cleaned)
        
        # Versión 4: Dilatada para conectar caracteres fragmentados
        dilated = cv2.dilate(enhanced, kernel, iterations=1)
        processed_versions.append(dilated)
        
        # Versión 5: Erosionada para separar caracteres unidos
        eroded = cv2.erode(enhanced, kernel, iterations=1)
        processed_versions.append(eroded)
        
        return processed_versions
    
    def extract_and_enhance_all(self, image: np.ndarray, 
                               plates_coords: List[Tuple[int, int, int, int]]) -> List[List[np.ndarray]]:
        """
        Extrae y mejora todas las regiones de placas.
        
        Args:
            image (np.ndarray): Imagen original
            plates_coords (List[Tuple[int, int, int, int]]): Coordenadas de placas
            
        Returns:
            List[List[np.ndarray]]: Lista de listas con versiones procesadas de cada placa
        """
        all_processed = []
        
        for coords in plates_coords:
            # Extraer región
            region = self.extract_plate_region(image, coords)
            
            if region is not None:
                # Generar versiones procesadas
                processed_versions = self.preprocess_for_ocr(region)
                all_processed.append(processed_versions)
        
        return all_processed
    
    def validate_plate_region(self, plate_region: np.ndarray) -> bool:
        """
        Valida si una región extraída es válida para OCR.
        
        Args:
            plate_region (np.ndarray): Región de placa
            
        Returns:
            bool: True si la región es válida
        """
        if plate_region is None or plate_region.size == 0:
            return False
        
        height, width = plate_region.shape[:2]
        
        # Verificar dimensiones mínimas
        if height < 15 or width < 30:
            return False
        
        # Verificar proporción
        aspect_ratio = width / height
        if aspect_ratio < 1.5 or aspect_ratio > 8:
            return False
          # Verificar que no sea completamente negro o blanco
        if len(plate_region.shape) == 3:
            gray = cv2.cvtColor(plate_region, cv2.COLOR_BGR2GRAY)
        else:
            gray = plate_region
        
        mean_intensity = gray.mean()
        if mean_intensity < 10 or mean_intensity > 245:
            return False
        
        # Verificar varianza (debe tener suficiente contraste)
        if gray.var() < 100:
            return False
        
        return True


class AdvancedPlateExtractor(PlateExtractor):
    """
    Extractor avanzado con técnicas adicionales de mejora de imagen.
    """
    
    def __init__(self, padding: int = 5, use_perspective_correction: bool = True):
        super().__init__(padding)
        self.use_perspective_correction = use_perspective_correction
    
    def extract_with_perspective_correction(self, image: np.ndarray, 
                                          contour: np.ndarray) -> Optional[np.ndarray]:
        """
        Extrae región aplicando corrección de perspectiva.
        
        Args:
            image (np.ndarray): Imagen original
            contour (np.ndarray): Contorno de la placa
            
        Returns:
            Optional[np.ndarray]: Región corregida o None
        """
        if not self.use_perspective_correction:
            return None
        
        # Aproximar contorno a un polígono
        epsilon = 0.02 * cv2.arcLength(contour, True)
        approx = cv2.approxPolyDP(contour, epsilon, True)
        
        if len(approx) == 4:
            # Ordenar puntos para transformación de perspectiva
            points = self._order_points(approx.reshape(4, 2))
            
            # Definir puntos de destino
            width = 300
            height = 100
            dst_points = np.array([
                [0, 0],
                [width - 1, 0],
                [width - 1, height - 1],
                [0, height - 1]
            ], dtype=np.float32)
            
            # Calcular matriz de transformación
            matrix = cv2.getPerspectiveTransform(points, dst_points)
            
            # Aplicar transformación
            corrected = cv2.warpPerspective(image, matrix, (width, height))
            
            return corrected
        
        return None
    
    def _order_points(self, pts: np.ndarray) -> np.ndarray:
        """
        Ordena puntos en el orden: top-left, top-right, bottom-right, bottom-left.
        """
        # Inicializar lista de coordenadas ordenadas
        rect = np.zeros((4, 2), dtype=np.float32)
        
        # Top-left tendrá la menor suma
        # Bottom-right tendrá la mayor suma
        s = pts.sum(axis=1)
        rect[0] = pts[np.argmin(s)]
        rect[2] = pts[np.argmax(s)]
        
        # Top-right tendrá la menor diferencia
        # Bottom-left tendrá la mayor diferencia
        diff = np.diff(pts, axis=1)
        rect[1] = pts[np.argmin(diff)]
        rect[3] = pts[np.argmax(diff)]
        
        return rect
