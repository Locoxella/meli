"""
Pipeline automatizado para preparar publicaciones usando IA y visión por computadora:
- Remoción y unificación de fondo a blanco puro (estándar Mercado Libre)
- Identificación de producto y extracción de especificaciones
- Predicción de categoría y atributos requeridos
- Generación de payload JSON listo para publicar
"""

import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from PIL import Image
from rembg import remove
from .client import MeliClient


class PublicationPipeline:
    def __init__(self, output_dir: str = "processed_images"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.client = MeliClient()

    def process_image(self, input_path: str, filename_prefix: str = "item") -> Path:
        """Remueve el fondo y centra la imagen en un lienzo blanco puro de 1200x1200."""
        inp = Image.open(input_path)
        no_bg = remove(inp)
        
        # Redimensionar conservando proporción
        no_bg.thumbnail((1100, 1100), Image.Resampling.LANCZOS)
        
        canvas = Image.new("RGB", (1200, 1200), (255, 255, 255))
        offset = ((1200 - no_bg.width) // 2, (1200 - no_bg.height) // 2)
        canvas.paste(no_bg, offset, no_bg)
        
        target_path = self.output_dir / f"{filename_prefix}_white_bg.jpg"
        canvas.save(target_path, "JPEG", quality=95)
        return target_path

    def inspect_category(self, title: str) -> Dict[str, Any]:
        """Predice categoría y obtiene los atributos obligatorios automáticamente."""
        predictions = self.client.predict_category(title, limit=1)
        if not predictions:
            raise ValueError(f"No se pudo determinar categoría para '{title}'")
        
        cat = predictions[0]
        cat_id = cat.get("category_id")
        attrs = self.client.get_category_attributes(cat_id)
        required_attrs = [a for a in attrs if a.get("tags", {}).get("required")]
        
        return {
            "category_id": cat_id,
            "category_name": cat.get("category_name"),
            "domain_name": cat.get("domain_name"),
            "required_attributes": required_attrs,
            "suggested_attributes": cat.get("attributes", [])
        }
