import pytest
from django.urls import path
from rest_framework.response import Response

from scoring.views import AsyncCapableAPIView


class CoroutineReturningView(AsyncCapableAPIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        async def build_response():
            return Response({"ok": True})

        return build_response()


urlpatterns = [
    path("test-coroutine-response/", CoroutineReturningView.as_view(), name="test-coroutine-response"),
]


@pytest.mark.django_db(transaction=True)
def test_async_capable_api_view_resolves_coroutine_response(client, settings):
    settings.ROOT_URLCONF = __name__

    response = client.post("/test-coroutine-response/", data={}, content_type="application/json")

    assert response.status_code == 200
    assert response.json() == {"ok": True}
