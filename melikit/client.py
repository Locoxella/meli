import json
import os
from typing import Dict, Any, Optional, List
import requests
from dotenv import load_dotenv
from .auth import MeliAuth

load_dotenv()

API_BASE_URL = "https://api.mercadolibre.com"


class MeliClient:
    def __init__(self, auth: Optional[MeliAuth] = None, site_id: Optional[str] = None):
        self.auth = auth or MeliAuth()
        self.site_id = site_id or os.getenv("MELI_SITE_ID", "MLA")

    def _headers(self, require_auth: bool = True) -> Dict[str, str]:
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        if require_auth:
            token = self.auth.get_valid_access_token()
            headers["Authorization"] = f"Bearer {token}"
        return headers

    # --- Métodos de Usuario ---
    def get_me(self) -> Dict[str, Any]:
        """Obtiene los datos del usuario autenticado."""
        resp = requests.get(f"{API_BASE_URL}/users/me", headers=self._headers())
        resp.raise_for_status()
        return resp.json()

    # --- Categorías y Atributos ---
    def predict_category(self, title: str, limit: int = 3) -> List[Dict[str, Any]]:
        """Predice las categorías más probables usando domain_discovery."""
        url = f"{API_BASE_URL}/sites/{self.site_id}/domain_discovery/search"
        resp = requests.get(
            url,
            params={"q": title, "limit": limit},
            headers=self._headers(require_auth=False),
        )
        resp.raise_for_status()
        return resp.json()

    def get_category_attributes(self, category_id: str) -> List[Dict[str, Any]]:
        """Obtiene los atributos requeridos y opcionales para una categoría."""
        url = f"{API_BASE_URL}/categories/{category_id}/attributes"
        resp = requests.get(url, headers=self._headers(require_auth=False))
        resp.raise_for_status()
        return resp.json()

    def get_category_info(self, category_id: str) -> Dict[str, Any]:
        """Obtiene detalles y ruta de una categoría."""
        url = f"{API_BASE_URL}/categories/{category_id}"
        resp = requests.get(url, headers=self._headers(require_auth=False))
        resp.raise_for_status()
        return resp.json()

    # --- Gestión de Publicaciones (Items) ---
    def validate_item(self, item_data: Dict[str, Any]) -> Dict[str, Any]:
        """Valida una publicación con la API sin crearla realmente."""
        url = f"{API_BASE_URL}/items/validate"
        resp = requests.post(url, headers=self._headers(), json=item_data)
        if resp.status_code in (200, 204):
            return {"valid": True, "message": "Estructura del item valida"}
        return {
            "valid": False,
            "status_code": resp.status_code,
            "error": resp.json() if resp.text else resp.text,
        }

    def create_item(self, item_data: Dict[str, Any]) -> Dict[str, Any]:
        """Crea una nueva publicación en Mercado Libre."""
        url = f"{API_BASE_URL}/items"
        resp = requests.post(url, headers=self._headers(), json=item_data)
        if resp.status_code not in (200, 201):
            raise RuntimeError(f"Error al crear publicación ({resp.status_code}): {resp.text}")
        return resp.json()

    def get_item(self, item_id: str) -> Dict[str, Any]:
        """Consulta los datos de una publicación."""
        url = f"{API_BASE_URL}/items/{item_id}"
        resp = requests.get(url, headers=self._headers(require_auth=False))
        resp.raise_for_status()
        return resp.json()

    def update_item(self, item_id: str, update_data: Dict[str, Any]) -> Dict[str, Any]:
        """Actualiza atributos, precio o estado de una publicación."""
        url = f"{API_BASE_URL}/items/{item_id}"
        resp = requests.put(url, headers=self._headers(), json=update_data)
        if resp.status_code != 200:
            raise RuntimeError(f"Error al actualizar item ({resp.status_code}): {resp.text}")
        return resp.json()

    def change_status(self, item_id: str, status: str) -> Dict[str, Any]:
        """Cambia el estado del item ('active', 'paused', 'closed')."""
        valid_statuses = ["active", "paused", "closed"]
        if status not in valid_statuses:
            raise ValueError(f"Estado invalido: {status}. Opciones: {valid_statuses}")
        return self.update_item(item_id, {"status": status})

    def update_stock(self, item_id: str, available_quantity: int) -> Dict[str, Any]:
        """Actualiza el stock disponible."""
        return self.update_item(item_id, {"available_quantity": available_quantity})

    def update_price(self, item_id: str, price: float) -> Dict[str, Any]:
        """Actualiza el precio de la publicación."""
        return self.update_item(item_id, {"price": price})
