import json
import os
import stat
import time
import pytest
import responses
from pathlib import Path
from melikit.auth import MeliAuth, TOKEN_URL
from melikit.exceptions import MeliAuthError, MeliAPIError


def test_extract_code():
    assert MeliAuth.extract_code("TG-123456789") == "TG-123456789"
    assert (
        MeliAuth.extract_code("https://localhost:8080/callback?code=TG-987654321&state=login")
        == "TG-987654321"
    )
    assert (
        MeliAuth.extract_code("http://meli.example.com/callback?code=TG-ABCDEF")
        == "TG-ABCDEF"
    )


def test_save_and_load_tokens(tmp_path):
    tokens_file = tmp_path / ".meli_tokens.json"
    auth = MeliAuth(tokens_path=tokens_file)

    test_data = {
        "access_token": "APP_USR-12345",
        "refresh_token": "TG-REFRESH-12345",
        "expires_in": 21600,
        "expires_at": time.time() + 21600,
    }

    auth.save_tokens(test_data)
    assert tokens_file.exists()

    # Check file permissions on POSIX
    file_stat = tokens_file.stat()
    permissions = stat.S_IMODE(file_stat.st_mode)
    assert permissions == 0o600

    loaded = auth.load_tokens()
    assert loaded == test_data


def test_get_valid_access_token_unexpired(tmp_path):
    tokens_file = tmp_path / ".tokens.json"
    auth = MeliAuth(tokens_path=tokens_file)
    auth.save_tokens({
        "access_token": "VALID-TOKEN-123",
        "expires_at": time.time() + 3600,
    })

    token = auth.get_valid_access_token()
    assert token == "VALID-TOKEN-123"


@responses.activate
def test_get_valid_access_token_auto_refresh(tmp_path):
    tokens_file = tmp_path / ".tokens.json"
    auth = MeliAuth(
        client_id="123456",
        client_secret="secret",
        tokens_path=tokens_file,
    )
    auth.save_tokens({
        "access_token": "EXPIRED-TOKEN",
        "refresh_token": "REFRESH-TOKEN-XYZ",
        "expires_at": time.time() - 100,  # Expired
    })

    responses.add(
        responses.POST,
        TOKEN_URL,
        json={
            "access_token": "NEW-VALID-TOKEN",
            "refresh_token": "NEW-REFRESH-TOKEN",
            "expires_in": 21600,
        },
        status=200,
    )

    token = auth.get_valid_access_token()
    assert token == "NEW-VALID-TOKEN"

    updated_tokens = auth.load_tokens()
    assert updated_tokens["access_token"] == "NEW-VALID-TOKEN"
    assert updated_tokens["refresh_token"] == "NEW-REFRESH-TOKEN"


def test_no_active_session_raises(tmp_path):
    tokens_file = tmp_path / "non_existent.json"
    auth = MeliAuth(tokens_path=tokens_file)
    with pytest.raises(MeliAuthError, match="No hay sesion activa"):
        auth.get_valid_access_token()
