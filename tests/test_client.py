import pytest
import responses
from pathlib import Path
from melikit.client import MeliClient, API_BASE_URL
from melikit.auth import MeliAuth
from melikit.exceptions import MeliAPIError


@pytest.fixture
def mock_auth(tmp_path):
    tokens_file = tmp_path / "tokens.json"
    auth = MeliAuth(tokens_path=tokens_file)
    auth.save_tokens({
        "access_token": "TEST-BEARER-TOKEN",
        "user_id": 999888777,
        "expires_at": 9999999999,
    })
    return auth


@pytest.fixture
def client(mock_auth):
    return MeliClient(auth=mock_auth, site_id="MLA")


@responses.activate
def test_predict_category(client):
    responses.add(
        responses.GET,
        f"{API_BASE_URL}/sites/MLA/domain_discovery/search",
        json=[
            {
                "domain_id": "MLA-HEADPHONES",
                "domain_name": "Auriculares",
                "category_id": "MLA3697",
                "category_name": "Auriculares",
                "attributes": [{"id": "BRAND", "name": "Marca", "value_name": "Sony"}],
            }
        ],
        status=200,
    )

    preds = client.predict_category("Auriculares Sony", limit=1)
    assert len(preds) == 1
    assert preds[0]["category_id"] == "MLA3697"


@responses.activate
def test_list_user_items(client):
    responses.add(
        responses.GET,
        f"{API_BASE_URL}/users/999888777/items/search",
        json={
            "seller_id": "999888777",
            "results": ["MLA1001", "MLA1002"],
            "paging": {"total": 2, "offset": 0, "limit": 50},
        },
        status=200,
    )

    result = client.list_user_items(status="active")
    assert result["results"] == ["MLA1001", "MLA1002"]
    assert result["paging"]["total"] == 2


@responses.activate
def test_create_item_success(client):
    responses.add(
        responses.POST,
        f"{API_BASE_URL}/items",
        json={
            "id": "MLA999999",
            "title": "Item de prueba",
            "status": "active",
            "permalink": "http://articulo.mercadolibre.com.ar/MLA-999999",
        },
        status=201,
    )

    item_data = {"title": "Item de prueba", "price": 1000}
    res = client.create_item(item_data)
    assert res["id"] == "MLA999999"
    assert res["status"] == "active"


@responses.activate
def test_create_item_api_error(client):
    responses.add(
        responses.POST,
        f"{API_BASE_URL}/items",
        json={
            "message": "Validation error",
            "error": "bad_request",
            "status": 400,
            "cause": [{"code": "item.price.invalid", "message": "Price must be positive"}],
        },
        status=400,
    )

    with pytest.raises(MeliAPIError) as exc_info:
        client.create_item({"title": "Invalido", "price": -5})

    assert exc_info.value.status_code == 400
    assert "Price must be positive" in str(exc_info.value)


@responses.activate
def test_get_and_update_description(client):
    responses.add(
        responses.GET,
        f"{API_BASE_URL}/items/MLA123/description",
        json={"plain_text": "Descripción actual"},
        status=200,
    )

    desc = client.get_item_description("MLA123")
    assert desc["plain_text"] == "Descripción actual"

    responses.add(
        responses.POST,
        f"{API_BASE_URL}/items/MLA123/description",
        json={"plain_text": "Nueva descripción actualizada"},
        status=200,
    )

    updated = client.update_item_description("MLA123", "Nueva descripción actualizada")
    assert updated["plain_text"] == "Nueva descripción actualizada"


@responses.activate
def test_upload_picture(client, tmp_path):
    img_file = tmp_path / "test.jpg"
    img_file.write_bytes(b"\xff\xd8\xff\xe0" + b"\x00" * 20)  # fake jpeg bytes

    responses.add(
        responses.POST,
        f"{API_BASE_URL}/pictures/items/upload",
        json={
            "id": "PICTURE-12345",
            "max_size": "1200x1200",
        },
        status=201,
    )

    res = client.upload_picture(img_file)
    assert res["id"] == "PICTURE-12345"
    assert res["max_size"] == "1200x1200"
