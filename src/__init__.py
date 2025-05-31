"""
Archivo de inicialización del paquete src.

Este archivo permite importar las clases principales del proyecto
de manera más conveniente.
"""

from .detector import PlateDetector, AdvancedPlateDetector
from .extractor import PlateExtractor, AdvancedPlateExtractor
from .ocr_reader import OCRReader, TesseractOCR, EasyOCREngine, PlateTextProcessor
from .utils import (
    load_image, resize_image, preprocess_image, 
    is_valid_plate_contour, draw_rectangle, 
    display_images, save_image, validate_image_format, Config
)

__version__ = "1.0.0"
__author__ = "Proyecto Placas Vehiculares"

# Configuración de importaciones principales
__all__ = [
    # Detectores
    'PlateDetector',
    'AdvancedPlateDetector',
    
    # Extractores
    'PlateExtractor', 
    'AdvancedPlateExtractor',
    
    # OCR
    'OCRReader',
    'TesseractOCR',
    'EasyOCREngine',
    'PlateTextProcessor',
    
    # Utilidades
    'load_image',
    'resize_image', 
    'preprocess_image',
    'is_valid_plate_contour',
    'draw_rectangle',
    'display_images',
    'save_image',
    'validate_image_format',
    'Config'
]
