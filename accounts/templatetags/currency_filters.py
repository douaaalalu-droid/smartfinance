from django import template
from decimal import Decimal, InvalidOperation

register = template.Library()

@register.filter
def currency_display(value, request):

    if value is None:
        return value

    currency = request.session.get("currency", "old_syp")
    exchange_rate = request.session.get("exchange_rate")

    try:
        value = Decimal(value)
    except:
        return value

    # الدولار
    if currency == "usd":
        try:
            rate = Decimal(exchange_rate)
            return round(value / rate, 2)
        except (InvalidOperation, TypeError):
            return value

    # الليرة الجديدة
    if currency == "new_syp":
        return round(value / Decimal("100"), 2)

    # الليرة القديمة
    return value