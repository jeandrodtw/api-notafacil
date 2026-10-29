from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import EuView, LoginView, NotaViewSet, RegistroView

# O router cria as rotas do CRUD: /notas/ e /notas/{id}/
router = DefaultRouter()
router.register("notas", NotaViewSet, basename="nota")

urlpatterns = [
    path("auth/registro/", RegistroView.as_view(), name="registro"),
    path("auth/login/", LoginView.as_view(), name="login"),
    path("auth/eu/", EuView.as_view(), name="eu"),
    path("", include(router.urls)),
]
