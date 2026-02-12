import pytest
from django.urls import reverse


@pytest.mark.django_db
def test_openapi_schema_endpoint_is_available(client):
    response = client.get(reverse("schema"))

    assert response.status_code == 200
    assert response["Content-Type"].startswith("application/vnd.oai.openapi")


@pytest.mark.django_db
def test_swagger_ui_endpoint_is_available(client):
    response = client.get(reverse("swagger-ui"))

    assert response.status_code == 200
    assert b"swagger-ui" in response.content.lower()
