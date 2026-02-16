def currency_context(request):
    currency = request.session.get("currency", "old_syp")
    return {
        "current_currency": currency
    }
