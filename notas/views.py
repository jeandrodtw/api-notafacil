from django.contrib.auth import authenticate
from django.db.models import Q
from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from rest_framework import status, viewsets
from rest_framework.authtoken.models import Token
from rest_framework.exceptions import ValidationError
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from . import garantia
from .models import Nota
from .serializers import (
    LoginSerializer,
    NotaSerializer,
    RegistroSerializer,
    TokenSerializer,
    UsuarioSerializer,
)

# ---------------------------------------------------------------------------
# Autenticação
# ---------------------------------------------------------------------------


class RegistroView(APIView):
    """Cria um usuário e já devolve o token (o app entra direto)."""

    permission_classes = [AllowAny]
    # Sem autenticação: um token antigo/inválido no header não atrapalha o registro
    authentication_classes = []

    @extend_schema(request=RegistroSerializer, responses={201: TokenSerializer})
    def post(self, request):
        serializer = RegistroSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)  # erros: {"campo": ["mensagem"]}
        usuario = serializer.save()
        token, _ = Token.objects.get_or_create(user=usuario)
        return Response({"token": token.key}, status=status.HTTP_201_CREATED)


class LoginView(APIView):
    """Confere usuário e senha e devolve o token."""

    permission_classes = [AllowAny]
    authentication_classes = []

    @extend_schema(request=LoginSerializer, responses={200: TokenSerializer})
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        usuario = authenticate(
            username=serializer.validated_data["username"],
            password=serializer.validated_data["password"],
        )
        if usuario is None:
            return Response(
                {"detail": "Usuário ou senha inválidos."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Reaproveita o token se o usuário já tiver um
        token, _ = Token.objects.get_or_create(user=usuario)
        return Response({"token": token.key})


class EuView(APIView):
    """Retorna o usuário dono do token (o app usa para validar o token salvo)."""

    @extend_schema(responses=UsuarioSerializer)
    def get(self, request):
        return Response(UsuarioSerializer(request.user).data)


# ---------------------------------------------------------------------------
# Notas
# ---------------------------------------------------------------------------


@extend_schema_view(
    list=extend_schema(
        parameters=[
            OpenApiParameter("busca", str, description="Texto na descrição ou na loja"),
            OpenApiParameter("status", str, enum=list(garantia.STATUS_VALIDOS)),
        ]
    )
)
class NotaViewSet(viewsets.ModelViewSet):
    """CRUD de notas. Cada usuário só acessa as próprias notas."""

    serializer_class = NotaSerializer
    # JSON para dados simples; multipart para enviar a foto
    parser_classes = [JSONParser, MultiPartParser, FormParser]

    def get_queryset(self):
        # O Swagger chama esta função sem usuário logado só para ler o modelo
        if getattr(self, "swagger_fake_view", False):
            return Nota.objects.none()

        # Filtrar pelo usuário garante 404 ao tentar acessar nota de outro
        notas = Nota.objects.filter(usuario=self.request.user)

        if self.action != "list":
            return notas

        busca = self.request.query_params.get("busca", "").strip()
        if busca:
            notas = notas.filter(Q(descricao_produto__icontains=busca) | Q(loja__icontains=busca))

        filtro_status = self.request.query_params.get("status", "").strip().lower()
        if filtro_status:
            if filtro_status not in garantia.STATUS_VALIDOS:
                raise ValidationError({"detail": "Status inválido. Use vigente, vencendo ou vencida."})
            # O status é calculado, então filtramos em Python
            ids = [
                nota.id
                for nota in notas
                if garantia.status_garantia(nota.data_compra, nota.tempo_garantia_meses) == filtro_status
            ]
            notas = notas.filter(id__in=ids)

        return notas

    def perform_create(self, serializer):
        # O dono da nota é sempre quem está logado
        serializer.save(usuario=self.request.user)

    def perform_destroy(self, nota):
        # Apaga o arquivo da foto antes de remover a nota
        if nota.foto:
            nota.foto.delete(save=False)
        nota.delete()
