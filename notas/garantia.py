"""
Regras de garantia — espelham o arquivo utils/garantia.ts do app.

Mantendo a mesma lógica nos dois lados, o status mostrado no app
é o mesmo calculado pela API.
"""

import calendar
from datetime import date

from django.utils import timezone

# Faltando até 30 dias para vencer, a garantia está "vencendo"
DIAS_ALERTA = 30

VIGENTE = "vigente"
VENCENDO = "vencendo"
VENCIDA = "vencida"
STATUS_VALIDOS = (VIGENTE, VENCENDO, VENCIDA)


def somar_meses(data: date, meses: int) -> date:
    """Soma meses a uma data. Ex.: 31/01 + 1 mês = 28/02 (ou 29/02)."""
    total = data.month - 1 + meses
    ano = data.year + total // 12
    mes = total % 12 + 1
    ultimo_dia = calendar.monthrange(ano, mes)[1]
    return date(ano, mes, min(data.day, ultimo_dia))


def calcular_vencimento(data_compra: date, meses: int) -> date:
    """Data em que a garantia termina (compra + meses de garantia)."""
    return somar_meses(data_compra, meses)


def dias_restantes(data_compra: date, meses: int, hoje: date | None = None) -> int:
    """Dias que faltam para vencer (negativo se já venceu)."""
    hoje = hoje or timezone.localdate()
    return (calcular_vencimento(data_compra, meses) - hoje).days


def status_garantia(data_compra: date, meses: int, hoje: date | None = None) -> str:
    """Retorna "vigente", "vencendo" (≤ 30 dias) ou "vencida"."""
    dias = dias_restantes(data_compra, meses, hoje)
    if dias < 0:
        return VENCIDA
    if dias <= DIAS_ALERTA:
        return VENCENDO
    return VIGENTE
