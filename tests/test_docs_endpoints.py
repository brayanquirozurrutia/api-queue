import pytest
from django.urls import reverse


@pytest.mark.django_db
def test_openapi_schema_endpoint_is_available(client):
    response = client.get(reverse("schema"), {"format": "json"})

    assert response.status_code == 200
    assert response["Content-Type"].startswith("application/vnd.oai.openapi")


@pytest.mark.django_db
def test_swagger_ui_endpoint_is_available(client):
    response = client.get(reverse("swagger-ui"))

    assert response.status_code == 200
    assert b"swagger-ui" in response.content.lower()


@pytest.mark.django_db
def test_score_schema_includes_examples_and_response_models(client):
    response = client.get(reverse("schema"), {"format": "json"})
    schema = response.json()

    score_post = schema["paths"]["/api/v1/score/"]["post"]
    content = score_post["requestBody"]["content"]["application/json"]
    responses = score_post["responses"]

    assert "examples" in content
    assert "200" in responses
    assert "400" in responses
    assert "500" in responses


@pytest.mark.django_db
def test_train_schema_includes_header_and_error_responses(client):
    response = client.get(reverse("schema"), {"format": "json"})
    schema = response.json()

    train_post = schema["paths"]["/api/v1/model/train/"]["post"]
    parameters = train_post["parameters"]
    responses = train_post["responses"]

    assert any(p["name"] == "X-Train-Token" and p["in"] == "header" for p in parameters)
    assert "202" in responses
    assert "401" in responses
    assert "404" in responses
