from scoring.serializers import ScoreRequestSerializer


def test_score_request_serializer_valid_payload():
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

    serializer = ScoreRequestSerializer(data=payload)

    assert serializer.is_valid()
