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
            if not exchange_rate:
                return value
            rate = Decimal(exchange_rate)
            if rate == 0:
                return value
            return round(value / rate, 2)
        except (InvalidOperation, TypeError):
            return value

    # الليرة الجديدة
    if currency == "new_syp":
        return round(value / Decimal("100"), 2)

    # الليرة القديمة
    return value


@register.filter
def div(value, arg):
    try:
        value = Decimal(value)
        arg = Decimal(arg)
        if arg == 0:
            return 0
        return value / arg
    except:
        return 0


@register.filter
def mul(value, arg):
    try:
        value = Decimal(value)
        arg = Decimal(arg)
        return value * arg
    except:
        return 0