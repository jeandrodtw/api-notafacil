from django.contrib.auth.models import User
from rest_framework import serializers

from . import garantia
from .models import Nota

TAMANHO_MAX_FOTO = 5 * 1024 * 1024  # 5 MB


# ---------------------------------------------------------------------------
# Autenticação
# ---------------------------------------------------------------------------


class RegistroSerializer(serializers.Serializer):
    """Valida usuário e senha com regras simples (sem os validadores do Django)."""

    username = serializers.CharField(max_length=150)
    password = serializers.CharField(write_only=True)

    def validate_username(self, valor):
        if len(valor) < 3:
            raise serializers.ValidationError("O usuário deve ter ao menos 3 caracteres.")
        if User.objects.filter(username__iexact=valor).exists():
            raise serializers.ValidationError("Este usuário já existe.")
        return valor

    def validate_password(self, valor):
        if len(valor) < 6:
            raise serializers.ValidationError("A senha deve ter ao menos 6 caracteres.")
        return valor

    def create(self, dados):
        # create_user grava a senha com hash (nunca em texto puro)
        return User.objects.create_user(username=dados["username"], password=dados["password"])


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)


class TokenSerializer(serializers.Serializer):
    """Usado só para documentar a resposta {"token": "..."} no Swagger."""

    token = serializers.CharField()


class UsuarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username"]


# ---------------------------------------------------------------------------
# Notas
# ---------------------------------------------------------------------------


class FotoField(serializers.ImageField):
    """
    Na leitura devolve a URL absoluta da foto; na escrita aceita um arquivo.

    Se o app reenviar a própria URL (texto) num PUT/PATCH em JSON,
    o campo é ignorado e a foto atual é mantida. Enviar null remove a foto.
    """

    def to_internal_value(self, dado):
        if isinstance(dado, str):
            raise serializers.SkipField()
        return super().to_internal_value(dado)


class NotaSerializer(serializers.ModelSerializer):
    # Nomes em camelCase (contrato com o app) apontando para os campos do modelo
    descricaoProduto = serializers.CharField(source="descricao_produto", max_length=200)
    fotoUri = FotoField(source="foto", required=False, allow_null=True)
    dataCompra = serializers.DateField(
        source="data_compra",
        format="%d/%m/%Y",  # resposta sempre em dd/mm/aaaa
        input_formats=["%d/%m/%Y", "%Y-%m-%d"],  # aceita os dois formatos
    )
    tempoGarantiaMeses = serializers.IntegerField(
        source="tempo_garantia_meses",
        min_value=0,
        required=False,
        default=0,
        error_messages={"min_value": "A garantia não pode ser negativa."},
    )
    loja = serializers.CharField(max_length=150)
    assistenciaTecnica = serializers.CharField(
        source="assistencia_tecnica",
        max_length=200,
        required=False,
        allow_blank=True,
        default="",
    )

    # Campos calculados (somente leitura) — regras em notas/garantia.py
    dataVencimento = serializers.SerializerMethodField()
    statusGarantia = serializers.SerializerMethodField()

    class Meta:
        model = Nota
        fields = [
            "id",
            "descricaoProduto",
            "fotoUri",
            "dataCompra",
            "tempoGarantiaMeses",
            "loja",
            "assistenciaTecnica",
            "dataVencimento",
            "statusGarantia",
        ]

    def get_dataVencimento(self, nota) -> str:
        vencimento = garantia.calcular_vencimento(nota.data_compra, nota.tempo_garantia_meses)
        return vencimento.strftime("%d/%m/%Y")

    def get_statusGarantia(self, nota) -> str:
        return garantia.status_garantia(nota.data_compra, nota.tempo_garantia_meses)

    def validate_fotoUri(self, foto):
        if foto and foto.size > TAMANHO_MAX_FOTO:
            raise serializers.ValidationError("A imagem deve ter no máximo 5 MB.")
        return foto

    def update(self, nota, dados):
        # Se a foto foi trocada ou removida, apaga o arquivo antigo do disco
        foto_antiga = nota.foto.name if nota.foto else None
        nota = super().update(nota, dados)
        if foto_antiga and "foto" in dados and nota.foto.name != foto_antiga:
            nota.foto.storage.delete(foto_antiga)
        return nota
