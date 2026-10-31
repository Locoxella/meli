import pytest
import requests
from melikit.exceptions import MeliAPIError, MeliAuthError, MeliError


def test_meli_api_error_formatting():
    err = MeliAPIError(
        message="Validation error",
        status_code=400,
        error_code="bad_request",
        causes=[{"code": "item.title.invalid", "message": "Title cannot be empty"}],
    )
    assert "[400]" in str(err)
    assert "bad_request:" in str(err)
    assert "Title cannot be empty" in str(err)


def test_meli_api_error_from_mock_response():
    response = requests.Response()
    response.status_code = 403
    response._content = b'{"message": "User not authorized", "error": "forbidden", "cause": ["scope_missing"]}'

    err = MeliAPIError.from_response(response)
    assert err.status_code == 403
    assert err.error_code == "forbidden"
    assert "scope_missing" in err.causes
    assert "User not authorized" in str(err)
