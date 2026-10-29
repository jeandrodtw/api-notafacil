from django.contrib import admin

from .models import Nota


@admin.register(Nota)
class NotaAdmin(admin.ModelAdmin):
    list_display = ["id", "descricao_produto", "loja", "data_compra", "tempo_garantia_meses", "usuario"]
    list_filter = ["loja"]
    search_fields = ["descricao_produto", "loja"]
