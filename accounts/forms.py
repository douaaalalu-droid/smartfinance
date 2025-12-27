from django import forms
from django.forms import inlineformset_factory
from .models import Invoice, InvoiceItem, FinancialEntry


class InvoiceForm(forms.ModelForm):
    class Meta:
        model = Invoice
        fields = ['invoice_number', 'invoice_type', 'customer_name', 'invoice_date']


InvoiceItemFormSet = inlineformset_factory(
    Invoice,
    InvoiceItem,
    fields=('description', 'quantity', 'unit_price'),
    extra=1,
    can_delete=False
)


class FinancialEntryForm(forms.ModelForm):
    class Meta:
        model = FinancialEntry
        fields = ['entry_type', 'amount', 'account_name', 'description']
