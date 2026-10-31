"""
Excepciones personalizadas para melikit.
"""

from typing import Optional, List, Dict, Any


class MeliError(Exception):
    """Excepción base para melikit."""
    pass


class MeliAuthError(MeliError):
    """Excepción para errores en el flujo de autenticación o refresco de tokens."""
    pass


class MeliAPIError(MeliError):
    """
    Excepción lanzada cuando la API de Mercado Libre responde con un error HTTP.
    Parsea automáticamente campos comunes como message, error y causes.
    """

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        error_code: Optional[str] = None,
        causes: Optional[List[Any]] = None,
        raw_response: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.causes = causes or []
        self.raw_response = raw_response or {}

    @classmethod
    def from_response(cls, response) -> "MeliAPIError":
        """Construye un MeliAPIError detallado a partir de un objeto requests.Response."""
        status_code = response.status_code
        error_code = None
        causes = []
        raw_json = {}

        try:
            raw_json = response.json()
            message = raw_json.get("message") or raw_json.get("error_description") or response.text
            error_code = raw_json.get("error")
            causes = raw_json.get("cause") or []
            if isinstance(causes, dict):
                causes = [causes]
        except Exception:
            message = response.text or f"HTTP Error {status_code}"

        return cls(
            message=message,
            status_code=status_code,
            error_code=error_code,
            causes=causes,
            raw_response=raw_json,
        )

    def __str__(self) -> str:
        parts = []
        if self.status_code:
            parts.append(f"[{self.status_code}]")
        if self.error_code and self.error_code != self.message:
            parts.append(f"{self.error_code}:")
        parts.append(self.message)

        if self.causes:
            details = []
            for c in self.causes:
                if isinstance(c, dict):
                    msg = c.get("message") or c.get("code") or str(c)
                    details.append(msg)
                else:
                    details.append(str(c))
            parts.append(f"- Detalles: {', '.join(details)}")

        return " ".join(parts)
