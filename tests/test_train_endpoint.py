import pytest
from django.urls import reverse


@pytest.mark.django_db
def test_train_endpoint_disabled_returns_404(client, settings):
    settings.ENABLE_MODEL_TRAIN_ENDPOINT = False
    settings.MODEL_TRAIN_TOKEN = "secret"

    response = client.post(reverse("model-train"), content_type="application/json")

    assert response.status_code == 404


@pytest.mark.django_db
def test_train_endpoint_requires_token(client, settings):
    settings.ENABLE_MODEL_TRAIN_ENDPOINT = True
    settings.MODEL_TRAIN_TOKEN = "secret"

    response = client.post(reverse("model-train"), content_type="application/json")

    assert response.status_code == 401


@pytest.mark.django_db
def test_train_endpoint_trains_when_enabled_and_token_is_valid(client, settings, monkeypatch):
    settings.ENABLE_MODEL_TRAIN_ENDPOINT = True
    settings.MODEL_TRAIN_TOKEN = "secret"

    trained = {"called": False}

    def fake_call_command(*args, **kwargs):
        trained["called"] = True

    monkeypatch.setattr("scoring.views.call_command", fake_call_command)

    response = client.post(
        reverse("model-train"),
        content_type="application/json",
        HTTP_X_TRAIN_TOKEN="secret",
    )

    assert response.status_code == 202
    assert response.json()["status"] == "trained"
    assert trained["called"] is True
