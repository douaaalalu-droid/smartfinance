from django.core.exceptions import ValidationError

def close_accounting_period(period):
    if period.journal_entries.filter(posted=False).exists():
        raise ValidationError(
            "لا يمكن إقفال الفترة، يوجد قيود غير مرحلة"
        )

    period.is_closed = True
    period.save()
