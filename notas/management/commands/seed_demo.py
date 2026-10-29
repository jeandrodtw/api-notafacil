"""
Cria dados de demonstração: usuário "aluno" (senha "senac123") e 6 notas.

As datas são calculadas a partir de hoje, assim sempre aparecem
os três status: vigente, vencendo e vencida.

Uso: python manage.py seed_demo
"""

from datetime import timedelta

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.utils import timezone
from rest_framework.authtoken.models import Token

from notas import garantia
from notas.models import Nota

USUARIO = "aluno"
SENHA = "senac123"

# (produto, loja, dias desde a compra, meses de garantia, assistência técnica)
NOTAS = [
    ('Smart TV Samsung 55" 4K Crystal UHD', "Magazine Luiza", 90, 12, "Assistência autorizada Samsung"),
    ("Notebook Dell Inspiron 15 i5 16GB", "Kabum", 60, 24, "Dell Suporte (atendimento on-site)"),
    ("Geladeira Brastemp Frost Free 375L", "Casas Bahia", 350, 12, "Brastemp Serviços"),
    ("Máquina de Lavar Electrolux 12kg", "Carrefour", 170, 6, "Electrolux Assistência"),
    ("iPhone 13 128GB", "Fast Shop", 400, 12, "Apple Authorized Service Provider"),
    ("Fone de Ouvido JBL Tune 510BT", "Mercado Livre", 120, 3, ""),
]


class Command(BaseCommand):
    help = "Cria o usuário 'aluno' e 6 notas de exemplo (vigente, vencendo e vencida)."

    def handle(self, *args, **options):
        usuario, criado = User.objects.get_or_create(username=USUARIO)
        usuario.set_password(SENHA)  # garante a senha mesmo se o usuário já existia
        usuario.save()

        # Recria as notas do zero para o comando poder rodar várias vezes
        Nota.objects.filter(usuario=usuario).delete()

        hoje = timezone.localdate()
        for produto, loja, dias, meses, assistencia in NOTAS:
            nota = Nota.objects.create(
                usuario=usuario,
                descricao_produto=produto,
                data_compra=hoje - timedelta(days=dias),
                tempo_garantia_meses=meses,
                loja=loja,
                assistencia_tecnica=assistencia,
            )
            situacao = garantia.status_garantia(nota.data_compra, nota.tempo_garantia_meses)
            self.stdout.write(f"  - {produto}: {situacao}")

        token, _ = Token.objects.get_or_create(user=usuario)
        acao = "criado" if criado else "atualizado"
        self.stdout.write(self.style.SUCCESS(f"Usuário '{USUARIO}' {acao} (senha: {SENHA})."))
        self.stdout.write(self.style.SUCCESS(f"{len(NOTAS)} notas criadas. Token: {token.key}"))
