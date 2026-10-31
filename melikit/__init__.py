"""
melikit: Herramientas y SDK para interactuar con la API oficial de Mercado Libre.
"""

from .auth import MeliAuth
from .client import MeliClient
from .exceptions import MeliError, MeliAuthError, MeliAPIError
from .ai_publisher import PublicationPipeline

__version__ = "0.2.0"

__all__ = [
    "MeliAuth",
    "MeliClient",
    "MeliError",
    "MeliAuthError",
    "MeliAPIError",
    "PublicationPipeline",
    "__version__",
]
