from django import forms
from django.forms import inlineformset_factory
from .models import Invoice, InvoiceItem, JournalEntry, JournalEntryLine
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.contrib.auth.models import  User, Group, Permission
from django.contrib.auth import get_user_model




class InvoiceForm(forms.ModelForm):
    invoice_date = forms.DateTimeField(
        widget=forms.DateTimeInput(
            attrs={
                'type': 'datetime-local',
                'class': 'form-control'
            },
            format='%Y-%m-%dT%H:%M'
        ),
        input_formats=['%Y-%m-%dT%H:%M'],
        error_messages={
            'invalid': '❌ الرجاء إدخال تاريخ ووقت صحيح'
        }
    )

    class Meta:
        model = Invoice
        fields = [
            'invoice_number',
            'invoice_type',
            'customer_name',
            'invoice_date',
            'currency'
    
        ]

    def clean_invoice_number(self):
        number = self.cleaned_data.get('invoice_number')

        if Invoice.objects.filter(invoice_number=number).exists():
            raise forms.ValidationError("❌ رقم الفاتورة مستخدم مسبقاً")

        return number
    def clean(self):
        cleaned_data = super().clean()
        period = cleaned_data.get('period')

        if period and period.is_closed:
            raise forms.ValidationError(
                  '❌ هذه الفترة المحاسبية مقفلة، لا يمكن إنشاء فاتورة داخلها'   
            )
        return cleaned_data


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
    def clean(self):
        cleaned_data = super().clean()
        period = cleaned_data.get('period')

        if period and period.is_closed:
            raise forms.ValidationError(
                '❌ لا يمكن إدخال قيد في فترة محاسبية مقفلة'
            )

        return cleaned_data

  
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



User = get_user_model()


class AdminUserCreateForm(UserCreationForm):
    groups = forms.ModelMultipleChoiceField(
        queryset=Group.objects.all(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label="المجموعات"
    )

    user_permissions = forms.ModelMultipleChoiceField(
        queryset=Permission.objects.all(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label="الصلاحيات"
    )

    class Meta:
        model = User
        fields = (
            'username',
            'email',
            'is_active',
            'is_staff',
            'is_superuser',
            'groups',
            'user_permissions',
        )


class AdminUserEditForm(UserChangeForm):
    password = None  # إخفاء كلمة المرور

    groups = forms.ModelMultipleChoiceField(
        queryset=Group.objects.all(),
        required=False,
        widget=forms.CheckboxSelectMultiple
    )

    user_permissions = forms.ModelMultipleChoiceField(
        queryset=Permission.objects.all(),
        required=False,
        widget=forms.CheckboxSelectMultiple
    )

    class Meta:
        model = User
        fields = (
            'username',
            'email',
            'is_active',
            'is_staff',
            'is_superuser',
            'groups',
            'user_permissions',
        )



User = get_user_model()

class AdminUserForm(forms.ModelForm):
    groups = forms.ModelMultipleChoiceField(
        queryset=Group.objects.all(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label="الصلاحيات (المجموعات)"
    )

    password = forms.CharField(
        required=False,
        widget=forms.PasswordInput,
        label="كلمة المرور"
    )

    class Meta:
        model = User
        fields = [
            'username',
            'first_name',
            'last_name',
            'email',
            'is_active',
            'groups',
        ]

    def save(self, commit=True):
        user = super().save(commit=False)

        if self.cleaned_data.get('password'):
            user.set_password(self.cleaned_data['password'])

        if commit:
            user.save()
            self.save_m2m()

        return user
    


class GroupForm(forms.ModelForm):
    permissions = forms.ModelMultipleChoiceField(
        queryset=Permission.objects.all().order_by('content_type__app_label'),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="الصلاحيات"
    )

    class Meta:
        model = Group
        fields = ['name', 'permissions']

