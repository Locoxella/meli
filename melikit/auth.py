import json
import os
import re
import time
import urllib.parse
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Dict, Any, Optional
import requests
from dotenv import load_dotenv

load_dotenv()

DEFAULT_AUTH_URL = "https://auth.mercadolibre.com.ar/authorization"
TOKEN_URL = "https://api.mercadolibre.com/oauth/token"
TOKENS_FILE = Path(".meli_tokens.json")


class OAuthCallbackHandler(BaseHTTPRequestHandler):
    code: Optional[str] = None
    error: Optional[str] = None

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)

        if "code" in params:
            OAuthCallbackHandler.code = params["code"][0]
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(
                b"<h1>Autorizacion Exitosa!</h1><p>Ya puedes volver a la terminal.</p>"
            )
        elif "error" in params:
            OAuthCallbackHandler.error = params.get("error_description", params["error"])[0]
            self.send_response(400)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(
                f"<h1>Error de Autorizacion</h1><p>{OAuthCallbackHandler.error}</p>".encode("utf-8")
            )
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        return


class MeliAuth:
    def __init__(
        self,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        redirect_uri: Optional[str] = None,
        tokens_path: Path = TOKENS_FILE,
    ):
        self.client_id = client_id or os.getenv("MELI_APP_ID")
        self.client_secret = client_secret or os.getenv("MELI_CLIENT_SECRET")
        self.redirect_uri = redirect_uri or os.getenv("MELI_REDIRECT_URI", "https://localhost/callback")
        self.tokens_path = tokens_path

    @staticmethod
    def extract_code(raw_value: str) -> str:
        """Extrae el parámetro code si el usuario pegó la URL completa."""
        if "code=" in raw_value:
            match = re.search(r"code=([^&]+)", raw_value)
            if match:
                return match.group(1)
        return raw_value.strip()

    def get_auth_url(self, state: str = "meli_login") -> str:
        if not self.client_id:
            raise ValueError("MELI_APP_ID no esta configurado en tu archivo .env")
        params = {
            "response_type": "code",
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "state": state,
        }
        return f"{DEFAULT_AUTH_URL}?{urllib.parse.urlencode(params)}"

    def exchange_code_for_token(self, code: str) -> Dict[str, Any]:
        if not self.client_id or not self.client_secret:
            raise ValueError("Faltan MELI_APP_ID o MELI_CLIENT_SECRET en tu archivo .env")

        clean_code = self.extract_code(code)
        payload = {
            "grant_type": "authorization_code",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "code": clean_code,
            "redirect_uri": self.redirect_uri,
        }
        headers = {
            "accept": "application/json",
            "content-type": "application/x-www-form-urlencoded",
        }

        resp = requests.post(TOKEN_URL, data=payload, headers=headers)
        if resp.status_code != 200:
            raise RuntimeError(f"Error al obtener token ({resp.status_code}): {resp.text}")

        data = resp.json()
        data["expires_at"] = time.time() + data.get("expires_in", 21600)
        self.save_tokens(data)
        return data

    def refresh_access_token(self, refresh_token: str) -> Dict[str, Any]:
        if not self.client_id or not self.client_secret:
            raise ValueError("Faltan MELI_APP_ID o MELI_CLIENT_SECRET en tu archivo .env")

        payload = {
            "grant_type": "refresh_token",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "refresh_token": refresh_token,
        }
        headers = {
            "accept": "application/json",
            "content-type": "application/x-www-form-urlencoded",
        }

        resp = requests.post(TOKEN_URL, data=payload, headers=headers)
        if resp.status_code != 200:
            raise RuntimeError(f"Error al refrescar token ({resp.status_code}): {resp.text}")

        data = resp.json()
        data["expires_at"] = time.time() + data.get("expires_in", 21600)
        self.save_tokens(data)
        return data

    def save_tokens(self, tokens: Dict[str, Any]) -> None:
        with open(self.tokens_path, "w", encoding="utf-8") as f:
            json.dump(tokens, f, indent=2)

    def load_tokens(self) -> Optional[Dict[str, Any]]:
        if not self.tokens_path.exists():
            return None
        try:
            with open(self.tokens_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return None

    def get_valid_access_token(self) -> str:
        tokens = self.load_tokens()
        if not tokens or "access_token" not in tokens:
            raise RuntimeError(
                "No hay sesion activa. Genera el token primero con 'python -m melikit auth url' o 'login'."
            )

        expires_at = tokens.get("expires_at", 0)
        if time.time() >= (expires_at - 300):
            refresh_tok = tokens.get("refresh_token")
            if not refresh_tok:
                raise RuntimeError("El token expiro y no hay refresh_token disponible.")
            tokens = self.refresh_access_token(refresh_tok)

        return tokens["access_token"]

    def start_local_login_flow(self, port: int = 8080) -> Dict[str, Any]:
        parsed = urllib.parse.urlparse(self.redirect_uri)
        target_port = parsed.port or port

        auth_url = self.get_auth_url()
        print("\n" + "=" * 60)
        print("INSTRUCCIONES DE AUTORIZACION (MERCADO LIBRE)")
        print("=" * 60)
        print("1. Abre la siguiente URL en tu navegador:")
        print(f"\n   {auth_url}\n")
        print(f"2. Inicia sesion y autoriza la aplicacion.")
        print(f"3. Esperando redireccion en {self.redirect_uri}...")
        print("=" * 60 + "\n")

        OAuthCallbackHandler.code = None
        OAuthCallbackHandler.error = None

        server = HTTPServer(("localhost", target_port), OAuthCallbackHandler)
        while OAuthCallbackHandler.code is None and OAuthCallbackHandler.error is None:
            server.handle_request()

        if OAuthCallbackHandler.error:
            raise RuntimeError(f"Error devuelto por MeLi: {OAuthCallbackHandler.error}")

        code = OAuthCallbackHandler.code
        print(f"Codigo de autorizacion recibido con exito.")
        print("Intercambiando codigo por access_token y refresh_token...")
        tokens = self.exchange_code_for_token(code)
        print("Tokens guardados exitosamente en", self.tokens_path)
        return tokens
