from django.urls import path
from scoring.views import HealthView, ScoreView

urlpatterns = [
    path("health/", HealthView.as_view(), name="health"),
    path("score/", ScoreView.as_view(), name="score"),
]
