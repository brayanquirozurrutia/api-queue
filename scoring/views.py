import logging
from django.conf import settings
from django.core.management import call_command
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView
from scoring.ml.service import model_service
from scoring.models import Prediction, UserProfile
from scoring.serializers import ScoreRequestSerializer, ScoreResponseSerializer

model_service.model_path = settings.MODEL_PATH
logger = logging.getLogger(__name__)


class AsyncCapableAPIView(APIView):
    pass


class HealthView(AsyncCapableAPIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request):
        return Response({"status": "ok"})


class ScoreView(AsyncCapableAPIView):
    authentication_classes = []
    permission_classes = []

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


class TrainModelView(AsyncCapableAPIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        if not settings.ENABLE_MODEL_TRAIN_ENDPOINT:
            return Response({"detail": "Training endpoint disabled."}, status=status.HTTP_404_NOT_FOUND)

        token = request.headers.get("X-Train-Token", "")
        if not settings.MODEL_TRAIN_TOKEN or token != settings.MODEL_TRAIN_TOKEN:
            return Response({"detail": "Unauthorized."}, status=status.HTTP_401_UNAUTHORIZED)

        call_command("train_model")
        model_service._model = None
        return Response({"status": "trained", "model_path": str(settings.MODEL_PATH)}, status=status.HTTP_202_ACCEPTED)
