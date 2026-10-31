import json
import os
from pathlib import Path
from typing import Dict, Any, Optional, List, Union
import requests
from requests.adapters import HTTPAdapter
from urllib3.util import Retry
from dotenv import load_dotenv

from .auth import MeliAuth
from .exceptions import MeliAPIError, MeliError

load_dotenv()

API_BASE_URL = "https://api.mercadolibre.com"
DEFAULT_TIMEOUT = 20.0


def _build_session(max_retries: int = 3, backoff_factor: float = 0.5) -> requests.Session:
    """Crea una sesión de requests con reintentos para errores transitorios de red/servidor."""
    session = requests.Session()
    retry_strategy = Retry(
        total=max_retries,
        backoff_factor=backoff_factor,
        status_forcelist=[500, 502, 503, 504],
        allowed_methods=["GET", "HEAD", "OPTIONS"],
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


class MeliClient:
    def __init__(
        self,
        auth: Optional[MeliAuth] = None,
        site_id: Optional[str] = None,
        timeout: float = DEFAULT_TIMEOUT,
        session: Optional[requests.Session] = None,
    ):
        self.auth = auth or MeliAuth()
        self.site_id = site_id or os.getenv("MELI_SITE_ID", "MLA")
        self.timeout = timeout
        self.session = session or _build_session()

    def _headers(self, require_auth: bool = True, extra_headers: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        if require_auth:
            token = self.auth.get_valid_access_token()
            headers["Authorization"] = f"Bearer {token}"
        if extra_headers:
            headers.update(extra_headers)
        return headers

    def _request(
        self,
        method: str,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        files: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        require_auth: bool = True,
    ) -> requests.Response:
        url = path if path.startswith("http") else f"{API_BASE_URL}{path}"
        req_headers = headers if headers is not None else self._headers(require_auth=require_auth)

        try:
            resp = self.session.request(
                method=method,
                url=url,
                params=params,
                json=json_data,
                files=files,
                headers=req_headers,
                timeout=self.timeout,
            )
        except requests.RequestException as e:
            raise MeliError(f"Error de conexión con Mercado Libre: {e}") from e

        if not resp.ok:
            raise MeliAPIError.from_response(resp)

        return resp

    # --- Métodos de Usuario ---
    def get_me(self) -> Dict[str, Any]:
        """Obtiene los datos del usuario autenticado."""
        resp = self._request("GET", "/users/me", require_auth=True)
        return resp.json()

    # --- Categorías y Atributos ---
    def predict_category(self, title: str, limit: int = 3) -> List[Dict[str, Any]]:
        """Predice las categorías más probables usando domain_discovery."""
        resp = self._request(
            "GET",
            f"/sites/{self.site_id}/domain_discovery/search",
            params={"q": title, "limit": limit},
            require_auth=False,
        )
        return resp.json()

    def get_category_attributes(self, category_id: str) -> List[Dict[str, Any]]:
        """Obtiene los atributos requeridos y opcionales para una categoría."""
        resp = self._request("GET", f"/categories/{category_id}/attributes", require_auth=False)
        return resp.json()

    def get_category_info(self, category_id: str) -> Dict[str, Any]:
        """Obtiene detalles y ruta de una categoría."""
        resp = self._request("GET", f"/categories/{category_id}", require_auth=False)
        return resp.json()

    # --- Gestión de Publicaciones (Items) ---
    def list_user_items(
        self,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
        user_id: Optional[Union[str, int]] = None,
    ) -> Dict[str, Any]:
        """
        Lista las publicaciones del usuario (por ID o usuario actual).
        Permite filtrar por estado ('active', 'paused', 'closed', etc.).
        """
        if not user_id:
            tokens = self.auth.load_tokens()
            if tokens and tokens.get("user_id"):
                user_id = tokens["user_id"]
            else:
                me = self.get_me()
                user_id = me.get("id")

        params: Dict[str, Any] = {"limit": limit, "offset": offset}
        if status:
            params["status"] = status

        resp = self._request("GET", f"/users/{user_id}/items/search", params=params, require_auth=True)
        return resp.json()

    def validate_item(self, item_data: Dict[str, Any]) -> Dict[str, Any]:
        """Valida una publicación con la API sin crearla realmente."""
        url = f"{API_BASE_URL}/items/validate"
        try:
            resp = self.session.post(
                url,
                headers=self._headers(require_auth=True),
                json=item_data,
                timeout=self.timeout,
            )
            if resp.status_code in (200, 204):
                return {"valid": True, "message": "Estructura del item valida"}
            data = resp.json() if resp.text else {}
            causes = data.get("cause", [])
            errors = [c for c in causes if c.get("type") == "error"]
            if causes and not errors:
                return {
                    "valid": True,
                    "message": "Estructura del item valida (con advertencias informativas)",
                    "warnings": causes,
                }
            return {
                "valid": False,
                "status_code": resp.status_code,
                "error": data or resp.text,
            }
        except requests.RequestException as e:
            raise MeliError(f"Error de red al validar publicación: {e}") from e

    def create_item(self, item_data: Dict[str, Any]) -> Dict[str, Any]:
        """Crea una nueva publicación en Mercado Libre."""
        resp = self._request("POST", "/items", json_data=item_data, require_auth=True)
        return resp.json()

    def get_item(self, item_id: str) -> Dict[str, Any]:
        """Consulta los datos de una publicación."""
        resp = self._request("GET", f"/items/{item_id}", require_auth=True)
        return resp.json()

    def update_item(self, item_id: str, update_data: Dict[str, Any]) -> Dict[str, Any]:
        """Actualiza atributos, precio o estado de una publicación."""
        resp = self._request("PUT", f"/items/{item_id}", json_data=update_data, require_auth=True)
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

    # --- Descripción del Ítem ---
    def get_item_description(self, item_id: str) -> Dict[str, Any]:
        """Obtiene la descripción en texto plano de una publicación."""
        resp = self._request("GET", f"/items/{item_id}/description", require_auth=True)
        return resp.json()

    def update_item_description(self, item_id: str, plain_text: str) -> Dict[str, Any]:
        """
        Crea o actualiza la descripción de una publicación.
        Mercado Libre utiliza el endpoint POST o PUT /items/{item_id}/description.
        """
        payload = {"plain_text": plain_text}
        try:
            resp = self._request("POST", f"/items/{item_id}/description", json_data=payload, require_auth=True)
        except MeliAPIError as e:
            # Si ya existía y MeLi requiere PUT:
            if e.status_code == 400 or "already_has_description" in str(e):
                resp = self._request("PUT", f"/items/{item_id}/description", json_data=payload, require_auth=True)
            else:
                raise
        return resp.json()

    # --- Subida de Imágenes ---
    def upload_picture(self, image_path: Union[str, Path]) -> Dict[str, Any]:
        """
        Sube un archivo de imagen directamente a los servidores de Mercado Libre.
        Retorna el objeto con 'id' y 'variations' que puede ser usado en pictures del item.
        """
        path = Path(image_path)
        if not path.exists():
            raise FileNotFoundError(f"No se encontró el archivo de imagen: {path}")

        token = self.auth.get_valid_access_token()
        headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {token}",
        }

        with open(path, "rb") as img_file:
            files = {"file": (path.name, img_file, "image/jpeg")}
            resp = self._request(
                "POST",
                "/pictures/items/upload",
                files=files,
                headers=headers,
                require_auth=True,
            )
        return resp.json()
