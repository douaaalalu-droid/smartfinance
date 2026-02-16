from django import template
from decimal import Decimal, ROUND_HALF_UP

register = template.Library()

@register.filter
def currency(value, currency_type):
    if value is None:
        return value

    value = Decimal(value)

    if currency_type == 'new_syp':
        return (value / Decimal('100')).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

    elif currency_type == 'usd':
        #  لإضافة سعر صرف لاحقاً)
        return value.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

    return value.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
