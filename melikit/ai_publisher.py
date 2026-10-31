"""
Pipeline automatizado para preparar publicaciones usando IA y visión por computadora:
- Remoción y unificación de fondo a blanco puro (estándar Mercado Libre)
- Identificación de producto y extracción de especificaciones
- Predicción de categoría y atributos requeridos
- Generación de payload JSON listo para publicar
"""

from pathlib import Path
from typing import Dict, Any, Union, Optional
from .client import MeliClient

try:
    from PIL import Image
    from rembg import remove
    AI_DEPS_AVAILABLE = True
except ImportError:
    AI_DEPS_AVAILABLE = False


def check_ai_dependencies():
    if not AI_DEPS_AVAILABLE:
        raise ImportError(
            "Las dependencias para procesamiento de imagen (Pillow y rembg) no están instaladas.\n"
            "Instálalas ejecutando: pip install 'melikit[ai]' o pip install pillow rembg"
        )


class PublicationPipeline:
    def __init__(self, output_dir: Union[str, Path] = "processed_images", client: Optional[MeliClient] = None):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.client = client or MeliClient()

    def process_image(self, input_path: Union[str, Path], filename_prefix: str = "item") -> Path:
        """Remueve el fondo y centra la imagen en un lienzo blanco puro de 1200x1200."""
        check_ai_dependencies()

        input_file = Path(input_path)
        if not input_file.exists():
            raise FileNotFoundError(f"Imagen no encontrada: {input_file}")

        inp = Image.open(input_file)
        no_bg = remove(inp)

        # Redimensionar conservando proporción
        no_bg.thumbnail((1100, 1100), Image.Resampling.LANCZOS)

        canvas = Image.new("RGB", (1200, 1200), (255, 255, 255))
        offset = ((1200 - no_bg.width) // 2, (1200 - no_bg.height) // 2)
        canvas.paste(no_bg, offset, no_bg)

        target_path = self.output_dir / f"{filename_prefix}_white_bg.jpg"
        canvas.save(target_path, "JPEG", quality=95)
        return target_path

    def process_and_upload(self, input_path: Union[str, Path], filename_prefix: str = "item") -> Dict[str, Any]:
        """Procesa la imagen a fondo blanco puro y la sube directamente a Mercado Libre."""
        clean_path = self.process_image(input_path, filename_prefix=filename_prefix)
        upload_res = self.client.upload_picture(clean_path)
        return {
            "local_path": str(clean_path),
            "picture_id": upload_res.get("id"),
            "meli_response": upload_res,
        }

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
            "suggested_attributes": cat.get("attributes", []),
        }
