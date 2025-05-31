"""
Utilidades generales para el proyecto de detección de placas vehiculares.

Este módulo contiene funciones auxiliares para procesamiento de imágenes,
validación y configuración.
"""

import cv2
import numpy as np
import os
from typing import Tuple, List, Optional
import matplotlib.pyplot as plt


def load_image(image_path: str) -> Optional[np.ndarray]:
    """
    Carga una imagen desde el archivo especificado.
    
    Args:
        image_path (str): Ruta al archivo de imagen
        
    Returns:
        Optional[np.ndarray]: Imagen cargada o None si hay error
    """
    if not os.path.exists(image_path):
        print(f"Error: El archivo {image_path} no existe.")
        return None
    
    try:
        image = cv2.imread(image_path)
        if image is None:
            print(f"Error: No se pudo cargar la imagen {image_path}")
            return None
        return image
    except Exception as e:
        print(f"Error al cargar la imagen: {e}")
        return None


def resize_image(image: np.ndarray, max_width: int = 800) -> np.ndarray:
    """
    Redimensiona una imagen manteniendo la proporción.
    
    Args:
        image (np.ndarray): Imagen original
        max_width (int): Ancho máximo deseado
        
    Returns:
        np.ndarray: Imagen redimensionada
    """
    height, width = image.shape[:2]
    
    if width > max_width:
        # Calcular nueva altura manteniendo proporción
        new_height = int((max_width * height) / width)
        image = cv2.resize(image, (max_width, new_height))
    
    return image


def preprocess_image(image: np.ndarray) -> np.ndarray:
    """
    Preprocesa una imagen para mejorar la detección de placas.
    
    Args:
        image (np.ndarray): Imagen original (color o escala de grises)
        
    Returns:
        np.ndarray: Imagen preprocesada en escala de grises
    """
    # Convertir a escala de grises si es necesario
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image.copy()
    
    # Aplicar filtro gaussiano para reducir ruido
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    
    # Ecualización de histograma para mejorar contraste
    equalized = cv2.equalizeHist(blurred)
    
    return equalized


def is_valid_plate_contour(contour: np.ndarray, image_area: int) -> bool:
    """
    Valida si un contorno puede ser una placa vehicular.
    
    Args:
        contour (np.ndarray): Contorno a validar
        image_area (int): Área total de la imagen
        
    Returns:
        bool: True si el contorno es válido para una placa
    """
    # Obtener rectángulo delimitador
    x, y, w, h = cv2.boundingRect(contour)
    
    # Calcular área del contorno
    area = cv2.contourArea(contour)
    
    # Filtros de validación
    
    # 1. Área mínima y máxima
    min_area = 500
    max_area = image_area * 0.1  # Máximo 10% del área de la imagen
    if area < min_area or area > max_area:
        return False
    
    # 2. Proporción ancho/alto (placas suelen ser rectangulares)
    aspect_ratio = w / h if h > 0 else 0
    if aspect_ratio < 2 or aspect_ratio > 5:
        return False
    
    # 3. Solidez del contorno (área del contorno / área del rectángulo)
    rect_area = w * h
    solidity = area / rect_area if rect_area > 0 else 0
    if solidity < 0.3:
        return False
    
    # 4. Verificar que el contorno sea aproximadamente rectangular
    epsilon = 0.02 * cv2.arcLength(contour, True)
    approx = cv2.approxPolyDP(contour, epsilon, True)
    
    # Una placa debe tener aproximadamente 4 esquinas
    if len(approx) < 4 or len(approx) > 8:
        return False
    
    return True


def draw_rectangle(image: np.ndarray, x: int, y: int, w: int, h: int, 
                  color: Tuple[int, int, int] = (0, 255, 0), thickness: int = 2) -> np.ndarray:
    """
    Dibuja un rectángulo en la imagen.
    
    Args:
        image (np.ndarray): Imagen donde dibujar
        x, y, w, h (int): Coordenadas y dimensiones del rectángulo
        color (Tuple[int, int, int]): Color BGR del rectángulo
        thickness (int): Grosor de las líneas
        
    Returns:
        np.ndarray: Imagen con el rectángulo dibujado
    """
    result = image.copy()
    cv2.rectangle(result, (x, y), (x + w, y + h), color, thickness)
    return result


def display_images(images: List[np.ndarray], titles: List[str], 
                  figsize: Tuple[int, int] = (15, 5)) -> None:
    """
    Muestra múltiples imágenes en una sola figura.
    
    Args:
        images (List[np.ndarray]): Lista de imágenes a mostrar
        titles (List[str]): Lista de títulos para cada imagen
        figsize (Tuple[int, int]): Tamaño de la figura
    """
    plt.figure(figsize=figsize)
    
    for i, (image, title) in enumerate(zip(images, titles)):
        plt.subplot(1, len(images), i + 1)
        
        # Convertir de BGR a RGB si es necesario
        if len(image.shape) == 3:
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            plt.imshow(image_rgb)
        else:
            plt.imshow(image, cmap='gray')
        
        plt.title(title)
        plt.axis('off')
    
    plt.tight_layout()
    plt.show()


def save_image(image: np.ndarray, output_path: str) -> bool:
    """
    Guarda una imagen en el archivo especificado.
    
    Args:
        image (np.ndarray): Imagen a guardar
        output_path (str): Ruta donde guardar la imagen
        
    Returns:
        bool: True si se guardó correctamente
    """
    try:
        # Crear directorio si no existe
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Guardar imagen
        success = cv2.imwrite(output_path, image)
        if success:
            print(f"Imagen guardada en: {output_path}")
            return True
        else:
            print(f"Error al guardar la imagen en: {output_path}")
            return False
    except Exception as e:
        print(f"Error al guardar la imagen: {e}")
        return False


def validate_image_format(image_path: str) -> bool:
    """
    Valida si el archivo tiene un formato de imagen válido.
    
    Args:
        image_path (str): Ruta al archivo de imagen
        
    Returns:
        bool: True si el formato es válido
    """
    valid_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif'}
    _, ext = os.path.splitext(image_path.lower())
    return ext in valid_extensions


class Config:
    """Configuración global del proyecto."""
    
    # Parámetros de detección
    MIN_PLATE_AREA = 500
    MAX_PLATE_AREA_RATIO = 0.1
    MIN_ASPECT_RATIO = 2.0
    MAX_ASPECT_RATIO = 5.0
    MIN_SOLIDITY = 0.3
    
    # Parámetros de preprocesamiento
    GAUSSIAN_KERNEL_SIZE = (5, 5)
    CANNY_THRESHOLD1 = 100
    CANNY_THRESHOLD2 = 200
    
    # Parámetros de visualización
    RECTANGLE_COLOR = (0, 255, 0)  # Verde
    RECTANGLE_THICKNESS = 2
    MAX_DISPLAY_WIDTH = 800
