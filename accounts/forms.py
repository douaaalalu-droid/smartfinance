from django import forms
from django.forms import inlineformset_factory
from .models import Invoice, InvoiceItem, JournalEntry, JournalEntryLine





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
    date = forms.DateField(
        widget=forms.DateInput(
            attrs={'type': 'date', 'class': 'form-control'},
            format='%Y-%m-%d'
        ),
        input_formats=['%Y-%m-%d'],
        label="تاريخ القيد"
    )

    description = forms.CharField(
        widget=forms.Textarea(
            attrs={
                'class': 'form-control',
                'rows': 2
            }
        ),
        label="وصف القيد"
    )

    class Meta:
        model = JournalEntry
        fields = [
            'date',
            'description',
        ]
    

class JournalEntryLineForm(forms.ModelForm):
    class Meta:
        model = JournalEntryLine
        fields = [
            'account',
            'debit',
            'credit',
        ]
        widgets = {
            'account': forms.Select(attrs={'class': 'form-control'}),
            'debit': forms.NumberInput(attrs={'class': 'form-control'}),
            'credit': forms.NumberInput(attrs={'class': 'form-control'}),
        }


        
JournalEntryLineFormSet = inlineformset_factory(
    JournalEntry,
    JournalEntryLine,
    form=JournalEntryLineForm,
    extra=2,
    can_delete=True
)
