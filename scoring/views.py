import logging

from django.conf import settings
from django.core.management import call_command
from drf_spectacular.utils import OpenApiParameter, OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from scoring.ml.service import model_service
from scoring.models import Prediction, UserProfile
from scoring.serializers import (
    DetailResponseSerializer,
    HealthResponseSerializer,
    ScoreRequestSerializer,
    ScoreResponseSerializer,
    TrainModelResponseSerializer,
    ValidationErrorResponseSerializer,
    EmptyRequestSerializer,
)

model_service.model_path = settings.MODEL_PATH
logger = logging.getLogger(__name__)


class HealthView(APIView):
    authentication_classes = []
    permission_classes = []

    @extend_schema(
        operation_id="healthCheck",
        summary="Health check",
        description="Returns service liveness status.",
        responses={
            200: OpenApiResponse(
                response=HealthResponseSerializer,
                description="Service is up.",
            )
        },
    )
    def get(self, request):
        return Response({"status": "ok"})


class ScoreView(APIView):
    authentication_classes = []
    permission_classes = []

    @extend_schema(
        operation_id="scoreUser",
        summary="Score user risk",
        description="Computes attendance and reseller risk probabilities from user behavioral features.",
        request=ScoreRequestSerializer,
        responses={
            200: OpenApiResponse(response=ScoreResponseSerializer, description="Scoring completed."),
            400: OpenApiResponse(response=ValidationErrorResponseSerializer, description="Invalid request payload."),
            500: OpenApiResponse(description="Unhandled server error."),
        },
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
        operation_id="trainModel",
        summary="Trigger model training",
        description="Triggers synchronous model retraining when endpoint is enabled and token is valid.",
        request=EmptyRequestSerializer,
        parameters=[
            OpenApiParameter(
                name="X-Train-Token",
                required=True,
                type=str,
                location=OpenApiParameter.HEADER,
                description="Training authorization token.",
            )
        ],
        responses={
            202: OpenApiResponse(response=TrainModelResponseSerializer, description="Model retraining triggered."),
            401: OpenApiResponse(response=DetailResponseSerializer, description="Invalid or missing token."),
            404: OpenApiResponse(response=DetailResponseSerializer, description="Training endpoint disabled."),
        },
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
