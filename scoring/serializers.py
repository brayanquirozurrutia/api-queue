from rest_framework import serializers
from scoring.models import Prediction, UserProfile


class ScoreRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()
    age = serializers.IntegerField(min_value=16, max_value=100)
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


class ScoreResponseSerializer(serializers.Serializer):
    attendance_probability = serializers.FloatField()
    reseller_probability = serializers.FloatField()
    risk_label = serializers.CharField()
    model_version = serializers.CharField()


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = "__all__"


class PredictionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Prediction
        fields = "__all__"
