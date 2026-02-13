import pytest
from django.urls import reverse
from scoring.models import Prediction, UserProfile


@pytest.mark.django_db(transaction=True)
def test_score_endpoint_returns_prediction_and_persists_data(client, monkeypatch):
    payload = {
        "email": "persona@example.com",
        "age": 29,
        "country": "CL",
        "city": "Santiago",
        "account_age_days": 950,
        "purchases_last_12_months": 8,
        "canceled_orders": 0,
        "tickets_per_order_avg": 1.4,
        "distance_to_venue_km": 12.5,
        "payment_failures_ratio": 0.02,
        "event_affinity_score": 0.91,
        "night_purchase_ratio": 0.12,
        "resale_reports_count": 0,
        "attendance_rate": 0.88,
    }

    monkeypatch.setattr("scoring.views.model_service.predict", lambda _: (0.93, 0.07, "attendee"))

    response = client.post(
        reverse("score"),
        data=payload,
        content_type="application/json",
    )

    assert response.status_code == 200
    assert response.json() == {
        "attendance_probability": 0.93,
        "reseller_probability": 0.07,
        "risk_label": "attendee",
        "model_version": "v1",
    }
    assert UserProfile.objects.filter(email="persona@example.com").exists()
    assert Prediction.objects.count() == 1


@pytest.mark.django_db(transaction=True)
def test_score_endpoint_validates_payload(client):
    payload = {
        "email": "persona@example.com",
        "age": 12,
        "country": "CL",
        "city": "Santiago",
        "account_age_days": 950,
        "purchases_last_12_months": 8,
        "canceled_orders": 0,
        "tickets_per_order_avg": 1.4,
        "distance_to_venue_km": 12.5,
        "payment_failures_ratio": 0.02,
        "event_affinity_score": 0.91,
        "night_purchase_ratio": 0.12,
        "resale_reports_count": 0,
        "attendance_rate": 0.88,
    }

    response = client.post(
        reverse("score"),
        data=payload,
        content_type="application/json",
    )

    assert response.status_code == 400
    assert "age" in response.json()


@pytest.mark.django_db(transaction=True)
def test_score_endpoint_logs_unhandled_errors(client, monkeypatch, caplog):
    payload = {
        "email": "persona@example.com",
        "age": 29,
        "country": "CL",
        "city": "Santiago",
        "account_age_days": 950,
        "purchases_last_12_months": 8,
        "canceled_orders": 0,
        "tickets_per_order_avg": 1.4,
        "distance_to_venue_km": 12.5,
        "payment_failures_ratio": 0.02,
        "event_affinity_score": 0.91,
        "night_purchase_ratio": 0.12,
        "resale_reports_count": 0,
        "attendance_rate": 0.88,
    }

    def boom(_):
        raise RuntimeError("model missing")

    monkeypatch.setattr("scoring.views.model_service.predict", boom)

    with caplog.at_level("ERROR"):
        response = client.post(
            reverse("score"),
            data=payload,
            content_type="application/json",
        )

    assert response.status_code == 500
    assert "Unhandled error while scoring user request" in caplog.text
