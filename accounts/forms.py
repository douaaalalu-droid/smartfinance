from django import forms
from django.forms import inlineformset_factory
from .models import Invoice, InvoiceItem, FinancialEntry


class InvoiceForm(forms.ModelForm):
    invoice_date = forms.DateField(
        widget=forms.DateInput(
            attrs={
                'type': 'date',
                'class': 'form-control'
            },
            format='%Y-%m-%d'
        ),
        input_formats=['%Y-%m-%d'],
        error_messages={
            'invalid': '❌ الرجاء إدخال تاريخ صحيح بالصيغة YYYY-MM-DD'
        }
    )

    class Meta:
        model = Invoice
        fields = [
            'invoice_number',
            'invoice_type',
            'customer_name',
            'invoice_date',
        ]
    def clean_invoice_number(self):
        number = self.cleaned_data.get('invoice_number')

        if Invoice.objects.filter(invoice_number=number).exists():
            raise forms.ValidationError("❌ رقم الفاتورة مستخدم مسبقاً")

        return number
    

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
