from django.db import models
from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db.models import Sum

class User(AbstractUser):
    ROLE_CHOICES = (
        ('admin', 'مدير النظام'),
        ('accountant', 'محاسب'),
        ('manager', 'مدير مالي'),
        ('data_entry', 'مدخل بيانات'),
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)

    def __str__(self):
        return self.username


class Invoice(models.Model):
    INVOICE_TYPES = (
        ('sale', 'فاتورة بيع'),
        ('purchase', 'فاتورة شراء'),
    )

    invoice_number = models.CharField(max_length=50, unique=True)
    invoice_type = models.CharField(max_length=10, choices=INVOICE_TYPES)
    customer_name = models.CharField(max_length=150)
    invoice_date = models.DateField()
    total_amount = models.DecimalField(max_digits=14, decimal_places=2, default=0)

    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    is_approved = models.BooleanField(default=False)

    def __str__(self):
        return self.invoice_number

class InvoiceItem(models.Model):
    invoice = models.ForeignKey(
        Invoice,
        related_name='items',
        on_delete=models.CASCADE
    )
    description = models.CharField(max_length=200)
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    total_price = models.DecimalField(max_digits=14, decimal_places=2, editable=False)

    def save(self, *args, **kwargs):
        self.total_price = self.quantity * self.unit_price
        super().save(*args, **kwargs)



class Account(models.Model):
    ACCOUNT_TYPES = (
        ('asset', 'أصول'),
        ('liability', 'خصوم'),
        ('equity', 'حقوق ملكية'),
        ('revenue', 'إيرادات'),
        ('expense', 'مصروفات'),
    )

    code = models.CharField(max_length=20, unique=True, verbose_name='رمز الحساب')
    name = models.CharField(max_length=100, verbose_name='اسم الحساب')
    account_type = models.CharField(
        max_length=20,
        choices=ACCOUNT_TYPES,
        verbose_name='نوع الحساب'
    )

    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children',
        verbose_name='الحساب الأب'
    )
    class Meta:
        permissions = [
            ("access_general_ledger", "الدخول إلى دفتر الأستاذ"),
              ("view_trial_balance", "Can view trial balance"),
        ]

    def __str__(self):
        return f"{self.code} - {self.name}"





class JournalEntry(models.Model):
    date = models.DateField()
    description = models.CharField(max_length=255)


    ENTRY_TYPES = (
        ('manual', 'قيد يدوي'),
        ('invoice', 'فاتورة'),
        ('adjustment', 'قيد تسوية'),
        ('opening', 'قيد افتتاحي'),
    )

    entry_type = models.CharField(
        max_length=20,
        choices=ENTRY_TYPES,
        default='manual'
    )


    status = models.CharField(
        max_length=10,
        choices=(('draft', 'مسودة'),
                ('approved', 'معتمد')
                ),
        default='draft'
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True
    )


    invoice = models.ForeignKey(
        Invoice,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='journal_entries'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        permissions = [
            ("view_trial_balance", "يمكنه عرض ميزان المراجعة"),
        ]




    def __str__(self):
        return f"قيد بتاريخ {self.date}"   
        



class JournalEntryLine(models.Model):
    journal_entry = models.ForeignKey(
        JournalEntry,
        on_delete=models.CASCADE,
        related_name='lines',
        verbose_name='القيد'
    )

    account = models.ForeignKey(
        Account,
        on_delete=models.PROTECT,
        verbose_name="الحساب"
    
    )

    debit = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name='مدين'
    )

    credit = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name='دائن'
    )
    
    class Meta:
        permissions = [
            ("view_general_ledger", "Can view general ledger"),
        ]

    def __str__(self):
        return f"{self.account} | مدين: {self.debit} | دائن: {self.credit}"
  

  
