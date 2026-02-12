from django.urls import path
from scoring.views import HealthView, ScoreView, TrainModelView

urlpatterns = [
    path("health/", HealthView.as_view(), name="health"),
    path("score/", ScoreView.as_view(), name="score"),
    path("model/train/", TrainModelView.as_view(), name="model-train"),
]
