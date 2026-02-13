from drf_spectacular.utils import OpenApiExample, extend_schema_serializer
from rest_framework import serializers

from scoring.models import Prediction, UserProfile


@extend_schema_serializer(
    examples=[
        OpenApiExample(
            "Score request example",
            value={
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
            },
            request_only=True,
        )
    ]
)
class ScoreRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()
    age = serializers.IntegerField(min_value=13, max_value=100)
    country = serializers.CharField(max_length=64)
    city = serializers.CharField(max_length=128)
    account_age_days = serializers.IntegerField(min_value=0)
    purchases_last_12_months = serializers.IntegerField(min_value=0)
    canceled_orders = serializers.IntegerField(min_value=0)
    tickets_per_order_avg = serializers.FloatField(min_value=0)
    distance_to_venue_km = serializers.FloatField(min_value=0)
    payment_failures_ratio = serializers.FloatField(min_value=0, max_value=1)
    event_affinity_score = serializers.FloatField(min_value=0, max_value=1)
    night_purchase_ratio = serializers.FloatField(min_value=0, max_value=1)
    resale_reports_count = serializers.IntegerField(min_value=0)
    attendance_rate = serializers.FloatField(min_value=0, max_value=1)


@extend_schema_serializer(
    examples=[
        OpenApiExample(
            "Score response example",
            value={
                "attendance_probability": 0.93,
                "reseller_probability": 0.07,
                "risk_label": "attendee",
                "model_version": "v1",
            },
            response_only=True,
            status_codes=["200"],
        )
    ]
)
class ScoreResponseSerializer(serializers.Serializer):
    attendance_probability = serializers.FloatField()
    reseller_probability = serializers.FloatField()
    risk_label = serializers.CharField()
    model_version = serializers.CharField()


@extend_schema_serializer(
    examples=[
        OpenApiExample(
            "Validation error example",
            value={"age": ["Ensure this value is greater than or equal to 13."]},
            response_only=True,
            status_codes=["400"],
        )
    ]
)
class ValidationErrorResponseSerializer(serializers.Serializer):
    age = serializers.ListField(child=serializers.CharField(), required=False)


@extend_schema_serializer(
    examples=[
        OpenApiExample(
            "Detail error example",
            value={"detail": "Unauthorized."},
            response_only=True,
        )
    ]
)
class DetailResponseSerializer(serializers.Serializer):
    detail = serializers.CharField()


@extend_schema_serializer(
    examples=[
        OpenApiExample(
            "Training accepted example",
            value={"status": "trained", "model_path": "/app/.data/attendance_model.joblib"},
            response_only=True,
            status_codes=["202"],
        )
    ]
)
class TrainModelResponseSerializer(serializers.Serializer):
    status = serializers.CharField()
    model_path = serializers.CharField()


@extend_schema_serializer(
    examples=[
        OpenApiExample(
            "Health response example",
            value={"status": "ok"},
            response_only=True,
            status_codes=["200"],
        )
    ]
)
class HealthResponseSerializer(serializers.Serializer):
    status = serializers.CharField()


class EmptyRequestSerializer(serializers.Serializer):
    pass


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = "__all__"


class PredictionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Prediction
        fields = "__all__"
