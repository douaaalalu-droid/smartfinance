from django import template

register = template.Library()

@register.filter
def currency(value, currency_type):
    if value is None:
        return ""

    try:
        value = float(value)
    except:
        return value

    # معدلات التحويل
    USD_RATE = 12000  

    if currency_type == "old_syp":
        return f"{value:,.0f} ل.س قديمة"

    elif currency_type == "syp":
        return f"{value:,.0f} ل.س"

    elif currency_type == "usd":
        return f"{value / USD_RATE:,.2f} $"

    elif currency_type == "new_syp":
        return f"{value / 100:,.2f} ل.س جديدة"

    return value