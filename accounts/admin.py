from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, FinancialEntry, Invoice, InvoiceItem


# 👤 المستخدم
@admin.register(User)
class CustomUserAdmin(UserAdmin):
    model = User
    list_display = ('username', 'email', 'role', 'is_active', 'is_staff')
    list_filter = ('role', 'is_active')
    fieldsets = UserAdmin.fieldsets + (
        ('الدور الوظيفي', {'fields': ('role',)}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('الدور الوظيفي', {'fields': ('role',)}),
    )


# 📒 القيود المحاسبية
@admin.register(FinancialEntry)
class FinancialEntryAdmin(admin.ModelAdmin):
    list_display = (
        'entry_type',
        'amount',
        'account_name',
        'status',
        'created_by',
        'created_at',
    )
    list_filter = ('entry_type', 'status', 'created_at')
    search_fields = ('account_name', 'description')


# 🧾 الفواتير
@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = (
        'invoice_number',
        'invoice_type',
        'total_amount',
        'is_approved',
        'created_by',
        'created_at',
    )
    list_filter = ('invoice_type', 'is_approved', 'created_at')
    search_fields = ('invoice_number',)


# 📦 بنود الفاتورة
@admin.register(InvoiceItem)
class InvoiceItemAdmin(admin.ModelAdmin):
    list_display = (
        'invoice',
        'description',  
        'quantity',
        'unit_price',
        'total_price',
    )

