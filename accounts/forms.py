from django import forms
from django.forms import inlineformset_factory
from .models import Invoice, InvoiceItem, JournalEntry


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
    


InvoiceItemFormSet = inlineformset_factory(
    Invoice,
    InvoiceItem,
    fields=('description', 'quantity', 'unit_price'),
    extra=1,
    can_delete=False
)

from django import forms
from django.forms import inlineformset_factory
from .models import Invoice, InvoiceItem, JournalEntry


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


InvoiceItemFormSet = inlineformset_factory(
    Invoice,
    InvoiceItem,
    fields=('description', 'quantity', 'unit_price'),
    extra=1,
    can_delete=False
)

class JournalEntryForm(forms.ModelForm):

    ENTRY_SIDE = (
        ('debit', 'مدين'),
        ('credit', 'دائن'),
    )

    entry_side = forms.ChoiceField(
        choices=ENTRY_SIDE,
        widget=forms.RadioSelect,
        label='نوع القيد'
    )

    amount = forms.DecimalField(
        label="المبلغ",
        min_value=0,
        decimal_places=2
    )

    date = forms.DateField(
        widget=forms.DateInput(
            attrs={'type': 'date', 'class': 'form-control'},
            format='%Y-%m-%d'
        ),
        input_formats=['%Y-%m-%d'],
        label="تاريخ القيد"
    )

    class Meta:
        model = JournalEntry
        fields = [
            'date',
            'account_name',
            'description',
        ]

        widgets = {
            'account_name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control'}),
        }

    def save(self, commit=True):
        entry = super().save(commit=False)

        side = self.cleaned_data['entry_side']
        amount = self.cleaned_data['amount']

        if side == 'debit':
            entry.debit = amount
            entry.credit = 0
        else:
            entry.credit = amount 
            entry.debit = 0
        entry.amount = amount

        if commit:
            entry.save()

        return entry
