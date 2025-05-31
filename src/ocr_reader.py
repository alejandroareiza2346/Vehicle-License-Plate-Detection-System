"""
Lector OCR para reconocimiento de texto en placas vehiculares.

Este módulo implementa múltiples motores de OCR (Tesseract y EasyOCR)
para extraer texto de las regiones de placas detectadas.
"""

import cv2
import numpy as np
import re
from typing import List, Optional, Dict, Tuple
from abc import ABC, abstractmethod

try:
    import pytesseract
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False
    print("Advertencia: pytesseract no está instalado. Instala con: pip install pytesseract")

try:
    import easyocr
    EASYOCR_AVAILABLE = True
except ImportError:
    EASYOCR_AVAILABLE = False
    print("Advertencia: easyocr no está instalado. Instala con: pip install easyocr")


class OCREngine(ABC):
    """Clase abstracta para motores de OCR."""
    
    @abstractmethod
    def read_text(self, image: np.ndarray) -> str:
        """Lee texto de una imagen."""
        pass


class TesseractOCR(OCREngine):
    """Motor OCR usando Tesseract."""
    
    def __init__(self, config: Optional[str] = None):
        """
        Inicializa el motor Tesseract.
        
        Args:
            config (str): Configuración personalizada de Tesseract
        """
        if not TESSERACT_AVAILABLE:
            raise ImportError("pytesseract no está disponible")
        
        # Configuración optimizada para placas vehiculares
        self.config = config or (
            '--oem 3 --psm 8 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
        )
    
    def read_text(self, image: np.ndarray) -> str:
        """
        Lee texto usando Tesseract.
        
        Args:
            image (np.ndarray): Imagen de la placa
            
        Returns:
            str: Texto reconocido
        """
        try:
            text = pytesseract.image_to_string(image, config=self.config)
            return self._clean_text(text)
        except Exception as e:
            print(f"Error en Tesseract OCR: {e}")
            return ""
    
    def _clean_text(self, text: str) -> str:
        """Limpia el texto reconocido."""
        # Remover caracteres no deseados
        cleaned = re.sub(r'[^A-Z0-9]', '', text.upper())
        return cleaned


class EasyOCREngine(OCREngine):
    """Motor OCR usando EasyOCR."""
    
    def __init__(self, languages: Optional[List[str]] = None):
        """
        Inicializa el motor EasyOCR.
        
        Args:
            languages (Optional[List[str]]): Lista de idiomas a usar
        """
        if not EASYOCR_AVAILABLE:
            raise ImportError("easyocr no está disponible")
        
        self.languages = languages or ['en']
        self.reader = easyocr.Reader(self.languages)
    
    def read_text(self, image: np.ndarray) -> str:
        """
        Lee texto usando EasyOCR.
        
        Args:
            image (np.ndarray): Imagen de la placa
            
        Returns:
            str: Texto reconocido
        """
        try:
            results = self.reader.readtext(image)
            
            # Combinar todos los textos reconocidos
            text_parts = []
            for (bbox, text, confidence) in results:
                if float(confidence) > 0.5:  # Filtrar por confianza
                    text_parts.append(text)
            
            combined_text = ''.join(text_parts)
            return self._clean_text(combined_text)
        except Exception as e:
            print(f"Error en EasyOCR: {e}")
            return ""
    
    def _clean_text(self, text: str) -> str:
        """Limpia el texto reconocido."""
        # Remover caracteres no deseados
        cleaned = re.sub(r'[^A-Z0-9]', '', text.upper())
        return cleaned


class OCRReader:
    """
    Lector principal que combina múltiples motores de OCR.
    
    Utiliza tanto Tesseract como EasyOCR para mejorar la precisión
    del reconocimiento de texto en placas vehiculares.
    """
    
    def __init__(self, use_tesseract: bool = True, use_easyocr: bool = True):
        """
        Inicializa el lector OCR.
        
        Args:
            use_tesseract (bool): Usar Tesseract OCR
            use_easyocr (bool): Usar EasyOCR
        """
        self.engines = []
        
        # Inicializar motores disponibles
        if use_tesseract and TESSERACT_AVAILABLE:
            try:
                self.engines.append(TesseractOCR())
            except Exception as e:
                print(f"No se pudo inicializar Tesseract: {e}")
        
        if use_easyocr and EASYOCR_AVAILABLE:
            try:
                self.engines.append(EasyOCREngine())
            except Exception as e:
                print(f"No se pudo inicializar EasyOCR: {e}")
        
        if not self.engines:
            print("Advertencia: No hay motores OCR disponibles")
    
    def read_text(self, image: np.ndarray) -> str:
        """
        Lee texto de una imagen usando todos los motores disponibles.
        
        Args:
            image (np.ndarray): Imagen de la placa
            
        Returns:
            str: Mejor texto reconocido
        """
        if not self.engines:
            return ""
        
        results = []
        
        # Ejecutar todos los motores
        for engine in self.engines:
            text = engine.read_text(image)
            if text:
                results.append(text)
        
        if not results:
            return ""
        
        # Seleccionar el mejor resultado
        return self._select_best_result(results)
    
    def read_text_multiple_versions(self, image_versions: List[np.ndarray]) -> str:
        """
        Lee texto de múltiples versiones procesadas de una imagen.
        
        Args:
            image_versions (List[np.ndarray]): Lista de versiones procesadas
            
        Returns:
            str: Mejor texto reconocido
        """
        all_results = []
        
        for image in image_versions:
            text = self.read_text(image)
            if text:
                all_results.append(text)
        
        if not all_results:
            return ""
        
        return self._select_best_result(all_results)
    
    def _select_best_result(self, results: List[str]) -> str:
        """
        Selecciona el mejor resultado entre múltiples opciones.
        
        Args:
            results (List[str]): Lista de textos reconocidos
            
        Returns:
            str: Mejor resultado
        """
        if not results:
            return ""
        
        if len(results) == 1:
            return results[0]
        
        # Evaluar calidad de cada resultado
        scored_results = []
        
        for text in results:
            score = self._calculate_text_quality_score(text)
            scored_results.append((text, score))
        
        # Ordenar por puntuación (mayor es mejor)
        scored_results.sort(key=lambda x: x[1], reverse=True)
        
        return scored_results[0][0]
    
    def _calculate_text_quality_score(self, text: str) -> float:
        """
        Calcula una puntuación de calidad para un texto reconocido.
        
        Args:
            text (str): Texto a evaluar
            
        Returns:
            float: Puntuación de calidad
        """
        score = 0.0
        
        # Longitud apropiada para placas (6-8 caracteres típicamente)
        length = len(text)
        if 5 <= length <= 9:
            score += 2.0
        elif 3 <= length <= 10:
            score += 1.0
        
        # Proporción de letras vs números
        letters = sum(1 for c in text if c.isalpha())
        numbers = sum(1 for c in text if c.isdigit())
        
        # Placas típicas tienen mezcla de letras y números
        if letters > 0 and numbers > 0:
            score += 1.5
        
        # Penalizar caracteres especiales o espacios
        special_chars = sum(1 for c in text if not c.isalnum())
        score -= special_chars * 0.5
        
        # Bonificar patrones comunes de placas
        if self._matches_plate_pattern(text):
            score += 1.0
        
        return score
    
    def _matches_plate_pattern(self, text: str) -> bool:
        """
        Verifica si el texto coincide con patrones comunes de placas.
        
        Args:
            text (str): Texto a verificar
            
        Returns:
            bool: True si coincide con un patrón común
        """
        # Patrones comunes (ajustar según el país/región)
        patterns = [
            r'^[A-Z]{3}[0-9]{3}$',  # AAA123
            r'^[A-Z]{3}[0-9]{4}$',  # AAA1234
            r'^[A-Z]{2}[0-9]{3}[A-Z]{2}$',  # AA123BB
            r'^[0-9]{3}[A-Z]{3}$',  # 123AAA
            r'^[A-Z]{1}[0-9]{3}[A-Z]{3}$',  # A123BBB
        ]
        
        for pattern in patterns:
            if re.match(pattern, text):
                return True
        
        return False
    
    def get_detailed_results(self, image: np.ndarray) -> Dict[str, str]:
        """
        Obtiene resultados detallados de todos los motores OCR.
        
        Args:
            image (np.ndarray): Imagen de la placa
            
        Returns:
            Dict[str, str]: Resultados por motor
        """
        results = {}
        
        for i, engine in enumerate(self.engines):
            engine_name = type(engine).__name__
            text = engine.read_text(image)
            results[engine_name] = text
        
        return results
    
    def validate_plate_text(self, text: str) -> bool:
        """
        Valida si un texto reconocido es válido para una placa.
        
        Args:
            text (str): Texto a validar
            
        Returns:
            bool: True si es válido
        """
        if not text:
            return False
        
        # Longitud mínima y máxima
        if len(text) < 4 or len(text) > 10:
            return False
        
        # Solo letras y números
        if not text.isalnum():
            return False
        
        # Debe tener al menos un número o una letra
        has_letter = any(c.isalpha() for c in text)
        has_number = any(c.isdigit() for c in text)
        
        if not (has_letter or has_number):
            return False
        
        return True


class PlateTextProcessor:
    """
    Procesador especializado para texto de placas vehiculares.
    """
    
    def __init__(self):
        self.common_corrections = {
            # Correcciones comunes OCR -> carácter correcto
            'O': '0', 'I': '1', 'S': '5', 'B': '8',
            'Z': '2', 'G': '6', 'T': '7', 'A': '4'
        }
    
    def correct_common_ocr_errors(self, text: str) -> str:
        """
        Corrige errores comunes de OCR en placas.
        
        Args:
            text (str): Texto original
            
        Returns:
            str: Texto corregido
        """
        corrected = text
        
        # Aplicar correcciones comunes en contexto numérico
        for wrong, correct in self.common_corrections.items():
            # Solo corregir si está en posición de número
            corrected = self._contextual_replace(corrected, wrong, correct)
        
        return corrected
    
    def _contextual_replace(self, text: str, wrong: str, correct: str) -> str:
        """
        Reemplaza caracteres considerando el contexto.
        """
        # Esta función podría implementar lógica más sofisticada
        # basada en patrones de placas específicos del país
        return text.replace(wrong, correct)
    
    def format_plate_text(self, text: str) -> str:
        """
        Formatea el texto de la placa según convenciones.
        
        Args:
            text (str): Texto sin formato
            
        Returns:
            str: Texto formateado
        """
        # Remover espacios y caracteres especiales
        clean = re.sub(r'[^A-Z0-9]', '', text.upper())
        
        # Aplicar formato específico según patrones comunes
        # (esto puede personalizarse según el país)
        
        if len(clean) == 6:
            # Formato ABC123
            return f"{clean[:3]}{clean[3:]}"
        elif len(clean) == 7:
            # Formato ABC1234
            return f"{clean[:3]}{clean[3:]}"
        
        return clean
