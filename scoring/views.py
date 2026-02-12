import asyncio
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from scoring.ml.service import model_service
from scoring.models import Prediction, UserProfile
from scoring.serializers import ScoreRequestSerializer, ScoreResponseSerializer


class HealthView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request):
        return Response({"status": "ok"})


class ScoreView(APIView):
    authentication_classes = []
    permission_classes = []

    async def post(self, request):
        serializer = ScoreRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payload = serializer.validated_data

        user, _ = await UserProfile.objects.aupdate_or_create(
            email=payload["email"],
            defaults=payload,
        )

        features = {k: v for k, v in payload.items() if k != "email"}
        attendance_probability, reseller_probability, risk_label = await asyncio.to_thread(
            model_service.predict,
            features,
        )

        await Prediction.objects.acreate(
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
