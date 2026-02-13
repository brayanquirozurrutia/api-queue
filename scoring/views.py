import logging
from django.conf import settings
from django.core.management import call_command
from drf_spectacular.utils import OpenApiExample, OpenApiResponse, extend_schema, inline_serializer
from rest_framework import serializers, status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView
from scoring.ml.service import model_service
from scoring.models import Prediction, UserProfile
from scoring.serializers import ScoreRequestSerializer, ScoreResponseSerializer

model_service.model_path = settings.MODEL_PATH
logger = logging.getLogger(__name__)


class HealthView(APIView):
    authentication_classes = []
    permission_classes = []

    @extend_schema(
        operation_id="health_check",
        responses={
            200: OpenApiResponse(
                response=inline_serializer(
                    name="HealthResponse",
                    fields={"status": serializers.CharField()},
                )
            )
        },
        tags=["health"],
    )
    def get(self, request):
        return Response({"status": "ok"})


class ScoreView(APIView):
    authentication_classes = []
    permission_classes = []

    @extend_schema(
        operation_id="score_user",
        request=ScoreRequestSerializer,
        responses={200: ScoreResponseSerializer},
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
            ),
            OpenApiExample(
                "Score response example",
                value={
                    "attendance_probability": 0.93,
                    "reseller_probability": 0.07,
                    "risk_label": "attendee",
                    "model_version": "v1",
                },
                response_only=True,
            ),
        ],
        tags=["scoring"],
    )
    def post(self, request):
        try:
            serializer = ScoreRequestSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            payload = serializer.validated_data

            user, _ = UserProfile.objects.update_or_create(
                email=payload["email"],
                defaults=payload,
            )

            features = {k: v for k, v in payload.items() if k != "email"}
            attendance_probability, reseller_probability, risk_label = model_service.predict(features)

            Prediction.objects.create(
                user=user,
                attendance_probability=attendance_probability,
                reseller_probability=reseller_probability,
                risk_label=risk_label,
                model_version=model_service.version,
            )

            response_payload = {
                "attendance_probability": attendance_probability,
                "reseller_probability": reseller_probability,
                "risk_label": risk_label,
                "model_version": model_service.version,
            }
            response = ScoreResponseSerializer(response_payload)
            return Response(response.data, status=status.HTTP_200_OK)
        except ValidationError:
            raise
        except Exception:
            logger.exception("Unhandled error while scoring user request")
            raise


class TrainModelView(APIView):
    authentication_classes = []
    permission_classes = []

    @extend_schema(
        operation_id="train_model",
        request=None,
        responses={
            202: OpenApiResponse(
                response=inline_serializer(
                    name="TrainModelAcceptedResponse",
                    fields={
                        "status": serializers.CharField(),
                        "model_path": serializers.CharField(),
                    },
                )
            ),
            401: OpenApiResponse(
                response=inline_serializer(
                    name="TrainModelUnauthorizedResponse",
                    fields={"detail": serializers.CharField()},
                )
            ),
            404: OpenApiResponse(
                response=inline_serializer(
                    name="TrainModelDisabledResponse",
                    fields={"detail": serializers.CharField()},
                )
            ),
        },
        tags=["operations"],
    )
    def post(self, request):
        if not settings.ENABLE_MODEL_TRAIN_ENDPOINT:
            return Response({"detail": "Training endpoint disabled."}, status=status.HTTP_404_NOT_FOUND)

        token = request.headers.get("X-Train-Token", "")
        if not settings.MODEL_TRAIN_TOKEN or token != settings.MODEL_TRAIN_TOKEN:
            return Response({"detail": "Unauthorized."}, status=status.HTTP_401_UNAUTHORIZED)

        call_command("train_model")
        model_service._model = None
        return Response({"status": "trained", "model_path": str(settings.MODEL_PATH)}, status=status.HTTP_202_ACCEPTED)
