"""
Detección de placas vehiculares en video en tiempo real.

Este script procesa un archivo de video o la cámara web para detectar
placas vehiculares frame por frame.
"""

import os
import sys
import argparse
import cv2
import time
from collections import deque

# Agregar el directorio src al path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from src.detector import PlateDetector
from src.extractor import PlateExtractor
from src.ocr_reader import OCRReader
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'utils'))
try:
    from utils.resize_image import resize_image # type: ignore
except ModuleNotFoundError:
    print("❌ Error: El módulo 'resize_image' no se encuentra en 'utils'. Verifica su existencia.")
    sys.exit(1)


class VideoPlateDetector:
    """
    Detector de placas para video en tiempo real.
    """
    
    def __init__(self, confidence_frames: int = 5):
        """
        Inicializa el detector de video.
        
        Args:
            confidence_frames (int): Frames necesarios para confirmar una placa
        """
        self.detector = PlateDetector()
        self.extractor = PlateExtractor()
        self.ocr_reader = OCRReader()
        
        # Buffer para estabilizar detecciones
        self.confidence_frames = confidence_frames
        self.detected_plates_buffer = deque(maxlen=confidence_frames)
        self.confirmed_plates = set()
        
        # Estadísticas
        self.total_frames = 0
        self.frames_with_plates = 0
        self.processing_times = deque(maxlen=30)  # Últimos 30 frames
    
    def process_frame(self, frame):
        """
        Procesa un frame del video.
        
        Args:
            frame: Frame del video
            
        Returns:
            tuple: (frame_procesado, placas_detectadas, textos_reconocidos)
        """
        start_time = time.time()
        
        # Redimensionar frame para mejor rendimiento
        processed_frame = resize_image(frame, max_width=640)
        
        # Detectar placas
        plates = self.detector.detect_plates(processed_frame)
        
        # Actualizar estadísticas
        self.total_frames += 1
        if plates:
            self.frames_with_plates += 1
        
        # Buffer para estabilizar detecciones
        self.detected_plates_buffer.append(plates)
        
        # Procesar placas estables
        stable_plates = self._get_stable_plates()
        
        # Reconocer texto en placas estables
        recognized_texts = []
        for plate_coords in stable_plates:
            region = self.extractor.extract_plate_region(processed_frame, plate_coords)
            if region is not None:
                enhanced_versions = self.extractor.preprocess_for_ocr(region)
                text = self.ocr_reader.read_text_multiple_versions(enhanced_versions)
                if text:
                    recognized_texts.append(text)
                    self.confirmed_plates.add(text)
        
        # Dibujar resultados en el frame
        result_frame = self._draw_results(processed_frame, stable_plates, recognized_texts)
        
        # Calcular tiempo de procesamiento
        processing_time = time.time() - start_time
        self.processing_times.append(processing_time)
        
        return result_frame, stable_plates, recognized_texts
    
    def _get_stable_plates(self):
        """
        Obtiene placas que han sido detectadas consistentemente.
        """
        if len(self.detected_plates_buffer) < self.confidence_frames:
            return []
        
        # Contar detecciones por posición aproximada
        position_counts = {}
        
        for frame_plates in self.detected_plates_buffer:
            for x, y, w, h in frame_plates:
                # Crear una clave basada en posición aproximada
                pos_key = (x // 20, y // 20, w // 10, h // 10)  # Cuantizar posición
                
                if pos_key not in position_counts:
                    position_counts[pos_key] = []
                position_counts[pos_key].append((x, y, w, h))
        
        # Seleccionar placas que aparecen en suficientes frames
        stable_plates = []
        threshold = self.confidence_frames * 0.6  # 60% de los frames
        
        for pos_key, detections in position_counts.items():
            if len(detections) >= threshold:
                # Usar la detección más reciente
                stable_plates.append(detections[-1])
        
        return stable_plates
    
    def _draw_results(self, frame, plates, texts):
        """
        Dibuja los resultados en el frame.
        """
        result_frame = frame.copy()
        
        # Dibujar placas detectadas
        for i, (x, y, w, h) in enumerate(plates):
            # Color verde para placas con texto, amarillo sin texto
            color = (0, 255, 0) if i < len(texts) else (0, 255, 255)
            cv2.rectangle(result_frame, (x, y), (x + w, y + h), color, 2)
            
            # Agregar texto si está disponible
            if i < len(texts):
                cv2.putText(
                    result_frame,
                    texts[i],
                    (x, y - 10),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    color,
                    2
                )
        
        # Agregar información del sistema
        self._draw_system_info(result_frame)
        
        return result_frame
    
    def _draw_system_info(self, frame):
        """
        Dibuja información del sistema en el frame.
        """
        height, width = frame.shape[:2]
        
        # Fondo semi-transparente para el texto
        overlay = frame.copy()
        cv2.rectangle(overlay, (10, 10), (300, 120), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.7, frame, 0.3, 0, frame)
        
        # Información del sistema
        info_lines = [
            f"Frames procesados: {self.total_frames}",
            f"Frames con placas: {self.frames_with_plates}",
            f"Placas confirmadas: {len(self.confirmed_plates)}",
        ]
        
        # FPS
        if self.processing_times:
            avg_time = sum(self.processing_times) / len(self.processing_times)
            fps = 1.0 / avg_time if avg_time > 0 else 0
            info_lines.append(f"FPS: {fps:.1f}")
        
        # Dibujar líneas de información
        for i, line in enumerate(info_lines):
            y_pos = 30 + (i * 20)
            cv2.putText(
                frame,
                line,
                (15, y_pos),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (255, 255, 255),
                1
            )
    
    def get_statistics(self):
        """
        Obtiene estadísticas del procesamiento.
        """
        detection_rate = self.frames_with_plates / max(self.total_frames, 1)
        avg_fps = 1.0 / (sum(self.processing_times) / max(len(self.processing_times), 1))
        
        return {
            'total_frames': self.total_frames,
            'frames_with_plates': self.frames_with_plates,
            'detection_rate': detection_rate,
            'confirmed_plates': list(self.confirmed_plates),
            'average_fps': avg_fps
        }


def process_video(video_source, output_path=None, show_video=True):
    """
    Procesa un video para detección de placas.
    
    Args:
        video_source: Ruta al video o índice de cámara (0 para webcam)
        output_path: Ruta para guardar video de salida
        show_video: Mostrar video en tiempo real
    """
    print(f"🎥 Iniciando procesamiento de video...")
    
    # Abrir fuente de video
    if isinstance(video_source, str):
        cap = cv2.VideoCapture(video_source)
        print(f"📁 Fuente: {video_source}")
    else:
        cap = cv2.VideoCapture(video_source)
        print(f"📹 Fuente: Cámara {video_source}")
    
    if not cap.isOpened():
        print("❌ Error: No se pudo abrir la fuente de video")
        return
    
    # Configuración del video de salida
    fourcc = None
    out = None
    
    if output_path:
        fourcc = cv2.VideoWriter.fourcc(*'XVID')
        fps = int(cap.get(cv2.CAP_PROP_FPS)) or 30
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        # Ajustar dimensiones si se redimensiona
        if width > 640:
            height = int((640 * height) / width)
            width = 640
        
        out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
        print(f"💾 Guardando resultado en: {output_path}")
    
    # Inicializar detector
    video_detector = VideoPlateDetector()
    
    print("🚀 Procesamiento iniciado. Presiona 'q' para salir.")
    
    frame_count = 0
    
    try:
        while True:
            ret, frame = cap.read()
            
            if not ret:
                print("📹 Fin del video o error al leer frame")
                break
            
            frame_count += 1
            
            # Procesar frame
            result_frame, plates, texts = video_detector.process_frame(frame)
            
            # Guardar frame si es necesario
            if out is not None:
                out.write(result_frame)
            
            # Mostrar video
            if show_video:
                cv2.imshow('Detección de Placas - Presiona Q para salir', result_frame)
                
                # Verificar si se presionó 'q'
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    print("⏹️  Procesamiento detenido por el usuario")
                    break
            
            # Mostrar progreso cada 100 frames
            if frame_count % 100 == 0:
                stats = video_detector.get_statistics()
                print(f"Frame {frame_count}: FPS={stats['average_fps']:.1f}, "
                      f"Placas confirmadas={len(stats['confirmed_plates'])}")
    
    except KeyboardInterrupt:
        print("\n⏹️  Procesamiento interrumpido por el usuario")
    
    finally:
        # Liberar recursos
        cap.release()
        if out is not None:
            out.release()
        if show_video:
            cv2.destroyAllWindows()
        
        # Mostrar estadísticas finales
        stats = video_detector.get_statistics()
        print("\n" + "="*50)
        print("📊 ESTADÍSTICAS FINALES")
        print("="*50)
        print(f"Frames procesados: {stats['total_frames']}")
        print(f"Frames con placas: {stats['frames_with_plates']}")
        print(f"Tasa de detección: {stats['detection_rate']:.2%}")
        print(f"FPS promedio: {stats['average_fps']:.1f}")
        print(f"Placas confirmadas: {len(stats['confirmed_plates'])}")
        
        if stats['confirmed_plates']:
            print("\n📋 PLACAS RECONOCIDAS:")
            for plate in stats['confirmed_plates']:
                print(f"   • {plate}")


def main():
    """Función principal del script."""
    parser = argparse.ArgumentParser(
        description="Detección de placas vehiculares en video",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos de uso:
  python video_detection.py --camera 0                    # Usar webcam
  python video_detection.py --video ../videos/traffic.mp4 # Procesar video
  python video_detection.py --video ../videos/traffic.mp4 --output resultado.avi
  python video_detection.py --camera 0 --no-display      # Sin mostrar video
        """
    )
    
    # Grupo mutuamente exclusivo para fuente de video
    source_group = parser.add_mutually_exclusive_group(required=True)
    source_group.add_argument(
        '--video', '-v',
        help='Ruta al archivo de video'
    )
    source_group.add_argument(
        '--camera', '-c',
        type=int,
        help='Índice de la cámara (0 para webcam principal)'
    )
    
    parser.add_argument(
        '--output', '-o',
        help='Ruta para guardar video de salida'
    )
    
    parser.add_argument(
        '--no-display',
        action='store_true',
        help='No mostrar video durante el procesamiento'
    )
    
    args = parser.parse_args()
    
    # Determinar fuente de video
    if args.video:
        if not os.path.exists(args.video):
            print(f"❌ Error: El archivo {args.video} no existe")
            return
        video_source = args.video
    else:
        video_source = args.camera
    
    # Procesar video
    process_video(
        video_source=video_source,
        output_path=args.output,
        show_video=not args.no_display
    )


if __name__ == "__main__":
    main()
