from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Invoice, InvoiceItem, JournalEntry, JournalEntryLine
from django.core.exceptions import ValidationError
from django.db.models import Sum
from .models import Account
from .models import AccountingPeriod
from .services import close_accounting_period
from django.contrib import messages



# المستخدم
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
    
#  الفواتير
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
    def save_model(self, request, obj, form, change):
        if obj.period and obj.period.is_closed:
            raise ValidationError("لا يمكن حفظ فاتورة في فترة محاسبية مقفلة")
        super().save_model(request, obj, form, change)


#  بنود الفاتورة
@admin.register(InvoiceItem)
class InvoiceItemAdmin(admin.ModelAdmin):
    list_display = (
        'invoice',
        'description',  
        'quantity',
        'unit_price',
        'total_price',
    )

# #دفتر القيود 

class JournalEntryLineInline(admin.TabularInline):
    model = JournalEntryLine
    extra = 2
    def save_model(self, request, obj, form, change):
        if obj.period and obj.period.is_closed:
            raise ValidationError("لا يمكن حفظ فاتورة في فترة محاسبية مقفلة")
        super().save_model(request, obj, form, change)


#رأس القيد
@admin.register(JournalEntry)
class JournalEntryAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'date',
        'description',
        'status',
        'created_by',
       

    )
    list_filter = ('status', 'date')
    search_fields = ('description',)
    readonly_fields = ('created_at',)

    inlines = [JournalEntryLineInline]
    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)

        entry = form.instance

        total_debit = entry.lines.aggregate(total=Sum('debit'))['total'] or 0
        total_credit = entry.lines.aggregate(total=Sum('credit'))['total'] or 0

        if total_debit != total_credit:
            raise ValidationError(
                f"❌ القيد غير متوازن: المدين = {total_debit} ، الدائن = {total_credit}"
            )
    def save_model(self, request, obj, form, change):
        if obj.period and obj.period.is_closed:
            raise ValidationError("لا يمكن حفظ فاتورة في فترة محاسبية مقفلة")
        super().save_model(request, obj, form, change)

#اسطر القيد
@admin.register(JournalEntryLine)
class JournalEntryLineAdmin(admin.ModelAdmin):
    list_display = (
        'journal_entry', 
        'account',
        'debit',
        'credit',
    )
    list_filter = ('account',)
    def save_model(self, request, obj, form, change):
        if obj.period and obj.period.is_closed:
            raise ValidationError("لا يمكن حفظ فاتورة في فترة محاسبية مقفلة")
        super().save_model(request, obj, form, change)


@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = (
        'code',
        'name',
        'account_type',
        'parent',
    
    )
    list_filter = (
        'account_type',
        )
    search_fields = ('code', 'name')


    @admin.register(AccountingPeriod)
    class AccountingPeriodAdmin(admin.ModelAdmin):
     list_display = ("name", "start_date", "end_date", "is_closed")
     actions = ["close_period"]

    def close_period(self, request, queryset):
        for period in queryset:
            try:
                close_accounting_period(period)
                messages.success(
                    request,
                    f"تم إقفال الفترة {period.name}"
                )
            except ValidationError as e:
                messages.error(request, str(e))

    close_period.short_description = "إقفال الفترات المحددة"




