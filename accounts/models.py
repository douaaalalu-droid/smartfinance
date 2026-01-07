from django.db import models
from django.conf import settings
from django.contrib.auth.models import AbstractUser


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
class JournalEntry(models.Model):
    ENTRY_TYPES = (
        ('income', 'إيراد'),
        ('expense', 'مصروف'),
    )

    ENTRY_STATUS = (
        ('draft', 'مسودة'),
        ('approved', 'معتمد'),
    )

    date = models.DateField()
    description = models.CharField(max_length=255)

    debit = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    credit = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    account_name = models.CharField(max_length=100)

    entry_type = models.CharField(
        max_length=10,
        choices=ENTRY_TYPES
    )

    amount = models.DecimalField(max_digits=14, decimal_places=2)

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

    status = models.CharField(
        max_length=10,
        choices=ENTRY_STATUS,
        default='draft'
    )

    created_at = models.DateTimeField(auto_now_add=True)
