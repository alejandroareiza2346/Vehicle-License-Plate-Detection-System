# Directorio de Imágenes de Muestra

Este directorio contiene imágenes de ejemplo para probar el sistema de detección de placas vehiculares.

## Estructura

- `samples/`: Imágenes de muestra para pruebas
- `test_results/`: Resultados de las pruebas (se genera automáticamente)

## Formato de Imágenes Soportadas

- JPEG (.jpg, .jpeg)
- PNG (.png)
- BMP (.bmp)
- TIFF (.tif, .tiff)

## Uso

Coloca tus imágenes de prueba en el directorio `samples/` y ejecuta los scripts de ejemplo:

```bash
# Procesar una imagen específica
python examples/basic_detection.py --image images/samples/tu_imagen.jpg

# Procesar todas las imágenes del directorio
python examples/batch_processing.py --input images/samples/
```

## Imágenes de Prueba

Para obtener mejores resultados, usa imágenes que tengan:

- **Buena iluminación**: Evita imágenes muy oscuras o con sombras fuertes
- **Resolución adecuada**: Mínimo 640x480 píxeles
- **Placas visibles**: Las placas deben ser claramente visibles y no estar obstruidas
- **Contraste suficiente**: Buena diferencia entre el fondo y la placa

## Consejos para Mejores Resultados

1. **Ángulo frontal**: Las placas frontales dan mejores resultados que las laterales
2. **Distancia apropiada**: Ni muy cerca (pixelado) ni muy lejos (pequeña)
3. **Sin reflejos**: Evita reflejos de luz en la placa
4. **Placa completa**: Asegúrate de que toda la placa esté visible

## Ejemplos de Nombres de Archivos

- `carro_frontal_01.jpg`
- `vehiculo_estacionado.png`
- `trafico_urbano.jpg`
- `moto_lateral.jpg`

## Nota Importante

Este directorio está configurado para ignorar archivos de imagen en el control de versiones (.gitignore) para evitar subir archivos grandes al repositorio. Solo se incluyen archivos de configuración y documentación.
