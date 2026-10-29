from django.conf import settings
from django.db import models


class Nota(models.Model):
    """Nota fiscal de um produto, com os dados da garantia."""

    # Cada nota pertence a um usuário (ele só enxerga as suas)
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notas",
    )
    descricao_produto = models.CharField("descrição do produto", max_length=200)
    foto = models.ImageField(upload_to="notas/", null=True, blank=True)
    data_compra = models.DateField("data da compra")
    tempo_garantia_meses = models.PositiveIntegerField("garantia (meses)", default=0)
    loja = models.CharField(max_length=150)
    assistencia_tecnica = models.CharField("assistência técnica", max_length=200, blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-id"]  # mais recentes primeiro
        verbose_name = "nota"
        verbose_name_plural = "notas"

    def __str__(self):
        return f"{self.descricao_produto} ({self.loja})"
