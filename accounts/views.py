import re
from urllib import response

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden, JsonResponse
from .models import InvoiceItem
from django.contrib import messages
from django.db.models import Sum
from decimal import Decimal
from .models import User, Invoice, InvoiceItem, JournalEntry
from .forms import JournalEntryForm, JournalEntryLineFormSet
from .models import JournalEntryLine
from .models import Account
from django.contrib.auth.decorators import permission_required
from accounts.decorators import role_required
from django.utils import timezone
from .models import AccountingPeriod
from django.core.exceptions import ValidationError
from django.db import transaction
from django.contrib.auth.models import Group, Permission
from .models import User
from django.contrib.auth import get_user_model
from .forms import AdminUserCreateForm, AdminUserEditForm
from .decorators import role_required
from .forms import GroupForm
from .models import AccountingPeriod
from django.utils import timezone
from accounts.models import ExchangeRate
from django.http import HttpResponse
from django.template.loader import render_to_string
from .models import Invoice
from django.db import connection
from google import genai
from google.genai import types
import os
from dotenv import load_dotenv

load_dotenv()


# مفتاح Gemini API
GEMINI_API_KEY = os.environ['GEMINI_API_KEY']

if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY environment variable not set.")

# إنشاء العميل
client = genai.Client(api_key=GEMINI_API_KEY)

User = get_user_model()



from .forms import (
   JournalEntryForm,
    InvoiceForm,
    InvoiceItemFormSet
)

#  Decorator للتحقق من الدور
def role_required(*roles):
    def decorator(view_func):
        def wrapper(request, *args, **kwargs):
            if request.user.role not in roles:
                return HttpResponseForbidden("غير مصرح لك بالدخول إلى هذه الصفحة")
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


#  تسجيل الدخول
def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)

            # التحويل الصحيح حسب الدور
            if user.role == 'admin':
                return redirect('admin_user_list')

            elif user.role == 'accountant':
                return redirect('accountant_dashboard')

            elif user.role == 'data_entry':
                return redirect('data_entry_dashboard')

            elif user.role == 'manager':
                return redirect('manager_dashboard')

            else:
                return redirect('login')

        else:
            return render(request, 'accounts/login.html', {
                'error': 'اسم المستخدم أو كلمة المرور غير صحيحة'
            })

    return render(request, 'accounts/login.html')


#  لوحة مدير النظام
@login_required
@role_required('admin')
def admin_dashboard(request):
    users = User.objects.all()
    entries = JournalEntry.objects.select_related('created_by').order_by('-created_at')[:10]

    context = {
        'users_count': users.count(),
        'entries': entries,
    }
    return render(request, 'dashboard/admin/dashboard.html', context)
#قائمةالمستخدمين
@login_required
@role_required('admin')
def admin_users_list(request):
    users = User.objects.all().order_by('username')

    q = request.GET.get('q')
    role = request.GET.get('role')
    active = request.GET.get('active')

    if q:
        users = users.filter(username__icontains=q)

    if role:
        users = users.filter(role=role)

    if active == '1':
        users = users.filter(is_active=True)
    elif active == '0':
        users = users.filter(is_active=False)

    return render(request, 'dashboard/admin/admin_user_list.html', {
        'users': users,
        'roles': User.ROLE_CHOICES,
        'q': q,
        'role_filter': role,
        'active_filter': active,
    })



#اضافة مستخدم جديد
@login_required
@permission_required('auth.add_user', raise_exception=True)
def admin_user_create(request):
    form = AdminUserCreateForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, "✅ تم إنشاء المستخدم")
        return redirect('admin_edit_user')

    return render(request, 'dashboard/admin/admin_user_form.html', {
        'form': form,
        'title': 'إضافة مستخدم'
    })

#تعديل مستخدم
@login_required
@role_required('admin')
def admin_user_update(request, user_id):
    user = get_object_or_404(User, id=user_id)

    if request.method == 'POST':
        form = AdminUserEditForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, '✅ تم تحديث المستخدم بنجاح')
            return redirect('admin_user_list')
    else:
        form = AdminUserEditForm(instance=user)

    return render(request, 'dashboard/admin/admin_user_form.html', {
        'form': form,
        'title': 'تعديل مستخدم'
    })

#حذف مستخدم
@login_required
@role_required('admin')
def admin_user_delete(request, user_id):
    user = get_object_or_404(User, id=user_id)

    if request.method == 'POST':
        user.delete()
        messages.success(request, '🗑️ تم حذف المستخدم')
        return redirect('admin_user_list')

    return render(request, 'dashboard/admin/admin_user_confirm_delete.html', {
        'user': user
    })

# إدارة الفترات المحاسبية 
def accounting_period_list(request):
    periods = AccountingPeriod.objects.all()

    # إضافة أو تعديل
    if request.method == "POST":
        period_id = request.POST.get("period_id")
        name = request.POST.get("name")
        start_date = request.POST.get("start_date")
        end_date = request.POST.get("end_date")

        # تعديل
        if period_id:
            period = get_object_or_404(AccountingPeriod, id=period_id)
            period.name = name
            period.start_date = start_date
            period.end_date = end_date
            period.save()
            messages.success(request, "تم تعديل الفترة بنجاح")

        # إضافة
        else:
            AccountingPeriod.objects.create(
                name=name,
                start_date=start_date,
                end_date=end_date
            )
            messages.success(request, "تم إنشاء الفترة بنجاح")

        return redirect('admin_accounting_period_list')

    # حذف
    if request.GET.get("delete"):
        period = get_object_or_404(AccountingPeriod, id=request.GET.get("delete"))
        period.delete()
        messages.success(request, "تم حذف الفترة")
        return redirect('admin_accounting_period_list')

    # إقفال
    if request.GET.get("close"):
        period = get_object_or_404(AccountingPeriod, id=request.GET.get("close"))
        period.is_closed = True
        period.closed_at = timezone.now()
        period.closed_by = request.user
        period.save()
        messages.success(request, "تم إقفال الفترة")
        return redirect('admin_accounting_period_list')

    return render(request, "dashboard/admin/accounting_period_list.html", {
        "periods": periods
    })




#  لوحة المدير المالي
from django.shortcuts import render
from django.db.models import Sum
from django.contrib.auth.decorators import login_required
from accounts.models import Invoice, JournalEntry

@login_required
def manager_dashboard(request):
    latest_invoices = Invoice.objects.order_by('-invoice_date')[:5]
    total_invoices = Invoice.objects.aggregate(total=Sum('total_amount'))['total'] or 0
    total_journal_entries = JournalEntry.objects.count()
    top_customers_query = (
        Invoice.objects
        .values('customer_name')
        .annotate(total_revenue=Sum('total_amount'))
        .order_by('-total_revenue')[:3]
    )
    top_customers = ", ".join([f"{c['customer_name']} ({c['total_revenue']})" for c in top_customers_query]) or "-"
    context = {
        "latest_invoices": latest_invoices,
        "total_invoices": total_invoices,
        "total_journal_entries": total_journal_entries,
        "top_customers": top_customers,
    }
    return render(request, "dashboard/manager.html", context)

#لوحة المحاسب
@login_required
@role_required('accountant')
def accountant_dashboard(request):

    if request.method == 'POST':
        form = JournalEntryForm(request.POST)
        formset = JournalEntryLineFormSet(request.POST)

        if form.is_valid():
            #  حفظ رأس القيد 
            entry = form.save(commit=False)
            entry.created_by = request.user
            entry.status = 'draft'
            currency = request.session.get("currency", "old_syp")
            exchange_rate = request.session.get("exchange_rate")
            
            if currency == "usd":
                if not exchange_rate:
                    messages.error(request, "❌  يجب إدخال سعر الصرف للدولار من القائمة")
                    return redirect('accountant_dashboard')
                
                entry.exchange_rate = float(exchange_rate)
            
            else:
                entry.exchange_rate = None
 
            entry.save()

            formset = JournalEntryLineFormSet(request.POST, instance=entry)

            if formset.is_valid():
                #  منع حفظ قيد بدون حركات
                valid_lines = []

                for form in formset.forms:
                    if  not form.cleaned_data:
                        continue
                    if form.cleaned_data.get("DELETE"):
                        continue
                    line = form.save(commit=False)

                                   
                        # تحويل المدين والدائن حسب العملة
                    debit = Decimal(line.debit) if line.debit is not None else Decimal(0)
                    credit = Decimal(line.credit) if line.credit is not None else Decimal(0)
                    if debit == 0 and credit == 0:
                        messages.error(request, "❌ لا يمكن أن يكون الدائن والمدين صفر معًا")
                        return redirect('accountant_dashboard')
                            

                    if currency =="usd" and exchange_rate:
                            debit = debit * Decimal(exchange_rate)
                            credit = credit *  Decimal(exchange_rate)

                    elif currency== "new_syp":
                        debit = debit * 100
                        credit = credit * 100

                    elif currency == "old_syp":
                        debit = debit
                        credit = credit

                    line.debit = debit
                    line.credit = credit
                    valid_lines.append(line)

                if not valid_lines:

                    entry.delete()
                    messages.error(request, "❌ لا يمكن حفظ قيد بدون حركات")
                    return redirect('accountant_dashboard')

                # حفظ الحركات
                for line in valid_lines:
                    line.journal_entry = entry
                    line.save()

                #  نجاح حفظ القيد 
                messages.success(request, '✅ تم حفظ القيد المحاسبي بنجاح')
                return redirect('accountant_dashboard')

            else:
                entry.delete()
                messages.error(request, '❌ يوجد خطأ في أسطر القيد')

        else:
            messages.error(request, '❌ يوجد خطأ في بيانات القيد')

    else:
        form = JournalEntryForm()
        formset = JournalEntryLineFormSet()
        
    status = request.GET.get('status')

    entries = (
        JournalEntry.objects
        .select_related('created_by')
        .prefetch_related('lines')
        .order_by('-created_at')
    )

    if status == 'approved':
        entries = entries.filter(status='approved')
    elif status == 'draft':
        entries = entries.filter(status='draft')

    return render(request, 'dashboard/accountant.html', {
        'form': form,
        'formset': formset,
        'entries': entries,
        'status': status
    })


# لوحة مدخل البيانات 
@login_required
@role_required('data_entry')
def data_entry_dashboard(request):

    formset = JournalEntryLineFormSet()

    if request.method == 'POST':
        form = JournalEntryForm(request.POST)

        if form.is_valid():

            entry = form.save(commit=False)
            entry.created_by = request.user
            entry.status = 'draft'
            currency = request.session.get("currency", "old_syp")
            exchange_rate = request.session.get("exchange_rate")

            entry.currency = currency

            if currency == "usd":
                if not exchange_rate:
                    messages.error(request, "❌ يجب إدخال سعر الصرف للدولار من القائمة")
                    return redirect('data_entry_dashboard')
                
                entry.exchange_rate = Decimal(exchange_rate)

            else:
                entry.exchange_rate = None
 

            try:
               
                entry.full_clean()
                entry.save()
            except ValidationError as e:
                messages.error(request, e.messages[0])
                form = JournalEntryForm()
                formset = JournalEntryLineFormSet()
                return redirect('data_entry_dashboard')

            formset = JournalEntryLineFormSet(request.POST, instance=entry)

            if formset.is_valid():
                valid_lines = []
                for form in formset.forms:
                    if  not form.cleaned_data:
                        continue
                    if form.cleaned_data.get("DELETE"):
                        continue

                    line = form.save(commit=False)
                         # تحويل المدين والدائن حسب العملة
                    debit = Decimal(line.debit) if line.debit is not None else Decimal(0)
                    credit = Decimal(line.credit) if line.credit is not None else Decimal(0)

                    if debit == 0 and credit == 0:
                            messages.error(request, "❌ لا يمكن أن يكون الدائن والمدين صفر معًا")
                            return redirect('accountant_dashboard')
                            

                    elif currency =="usd" and exchange_rate:
                            debit = debit * Decimal(exchange_rate)
                            credit = credit * Decimal(exchange_rate)

                    elif currency== "new_syp":
                        debit = debit * 100
                        credit = credit * 100

                    elif currency == "old_syp":
                         debit = debit
                         credit = credit 
                        
                    line.debit = debit
                    line.credit =credit
                    valid_lines.append(line)


                if not valid_lines:
                    entry.delete()
                    messages.error(request, "❌ لا يمكن حفظ قيد بدون حركات")
                    return redirect('data_entry_dashboard')

                
                for line in valid_lines:
                    line.journal_entry = entry
                    line.save()
                    
                messages.success(
                    request,
                    '✅ تم حفظ القيد وإرساله للمحاسب للمراجعة'
                )
                return redirect('data_entry_dashboard')

            else:
                entry.delete()
                messages.error(request, '❌ يوجد خطأ في أسطر القيد')

        else:
            messages.error(request, '❌ يوجد خطأ في بيانات القيد')

    else:
        form = JournalEntryForm()
        formset = JournalEntryLineFormSet()

    entries = (
        JournalEntry.objects
        .filter(created_by=request.user)
        .select_related('created_by')
        .prefetch_related('lines')
        .order_by('-created_at')
    )

    return render(request, 'dashboard/data_entry.html', {
        'form': form,
        'formset': formset,
        'entries': entries
    })

#لتغيير العملة 
def set_currency(request):

    if request.method == "POST":

        currency = request.POST.get("currency")
        rate = request.POST.get("exchange_rate")

        request.session["currency"] = currency

        if currency == "usd" and rate:
            request.session["exchange_rate"] = rate
        else:
            request.session["exchange_rate"] = None

    return redirect(request.META.get("HTTP_REFERER", "/"))
# إنشاء فاتورة
@login_required
@role_required('accountant', 'data_entry')
def create_invoice(request):

    if "currency" not in request.session:
        request.session["currency"] = "old_syp"

    invoice_form = InvoiceForm()
    formset = InvoiceItemFormSet(queryset=InvoiceItem.objects.none())

    if request.method == 'POST':
        invoice_form = InvoiceForm(request.POST)

        if invoice_form.is_valid():
            invoice = invoice_form.save(commit=False)

            try:
                with transaction.atomic():

                    invoice.created_by = request.user
                    invoice.save()

                    formset = InvoiceItemFormSet(request.POST, instance=invoice)

                    if formset.is_valid():
                        items = formset.save(commit=False)

                        valid_items = [
                            item for item in items
                            if item and not getattr(item, 'DELETE', False)
                        ]

                        if not valid_items:
                            invoice.delete()
                            messages.error(request, "❌ لا يمكن حفظ فاتورة بدون بنود")
                            context = {
                                'invoice_form': invoice_form,
                                'formset': formset,
                                'hide_currency_selector': True
                            }
                            return render(request, 'invoices/create_invoice.html', context)

                        original_total = Decimal('0.00')

                        for item in valid_items:
                            item.invoice = invoice
                            item.save()
                            original_total += item.total_price

                        invoice.original_total = original_total
                        currency = request.session.get("currency", "old_syp")
                        invoice.currency = currency
                        invoice.original_currency = currency
                        invoice.original_amount = original_total

                        if currency == "old_syp":
                            invoice.exchange_rate = Decimal('1')
                            invoice.total_amount = original_total

                        elif currency == "new_syp":
                            invoice.exchange_rate = Decimal('1')
                            invoice.total_amount = original_total 

                        elif currency == "usd":
                            user_rate = request.POST.get("exchange_rate")

                            if user_rate:
                                invoice.exchange_rate = Decimal(user_rate)

                            else:
                                rate = ExchangeRate.objects.filter(
                                    currency='usd',
                                    date__lte=invoice.invoice_date
                                ).order_by('-date').first()

                                if not rate:
                                    raise ValidationError("❌ لا يوجد سعر صرف معرف لهذا التاريخ")

                                invoice.exchange_rate = rate.rate

                            invoice.total_amount = original_total

                        invoice.save(update_fields=[
                            'original_total',
                            'currency',
                            'exchange_rate',
                            'total_amount'
                        ])

                        messages.success(request, "✅ تم حفظ الفاتورة بنجاح")

                        if request.user.role == 'accountant':
                            return redirect('accountant_invoices')
                        else:
                            return redirect('data_entry_dashboard')

                    else:
                        messages.error(request, "❌ يوجد خطأ في بنود الفاتورة")

            except ValidationError as e:
                invoice_form.add_error(None, e.messages[0])

        else:
            messages.error(request, "❌ يوجد خطأ في بيانات الفاتورة")
            if not invoice_form.is_valid():
              print(invoice_form.errors)

    context = {
        'invoice_form': invoice_form,
        'formset': formset,
        'hide_currency_selector': True
    }

    return render(request, 'invoices/create_invoice.html', context)

#  قائمة الفواتير
@login_required
@role_required('accountant')
def accountant_invoices(request):
    status = request.GET.get('status')

    invoices = Invoice.objects.all().order_by('-created_at')

    if status == 'approved':
        invoices = invoices.filter(is_approved=True)
    elif status == 'pending':
        invoices = invoices.filter(is_approved=False)

    return render(request, 'invoices/accountant_invoices.html', {
        'invoices': invoices,
        'status': status
    })


#  تفاصيل الفاتورة
@login_required
@role_required('accountant')
def invoice_detail(request, invoice_id):
    invoice = Invoice.objects.get(pk=invoice_id)
    items = invoice.items.all()
    entries = JournalEntry.objects.filter(invoice=invoice)

    return render(request, "invoices/invoice_detail.html", {
        "invoice": invoice,
        "items": items,
        "entries": entries
    })
#  اعتماد فاتورة
@login_required
@role_required('accountant')
def approve_invoice(request, invoice_id):
    invoice = get_object_or_404(Invoice, id=invoice_id)

    if invoice.is_approved:
        return redirect('invoice_detail', invoice.id)
    if invoice.currency == "usd":
     if not invoice.exchange_rate:
        raise ValueError("يجب إدخال سعر الصرف قبل اعتماد الفاتورة")
    if invoice.period and invoice.period.is_closed:
        messages.error(
            request,
              "❌ لا يمكن اعتماد فاتورة في فترة محاسبية مقفلة"
        )
        return redirect('invoice_detail', invoice.id)
    amount = invoice.total_amount

    try:

      with transaction.atomic():


        #  إنشاء رأس القيد
        entry = JournalEntry.objects.create(
            date=invoice.invoice_date,
            description=f"قيد تلقائي للفاتورة {invoice.invoice_number}",
            created_by=request.user,
            status='approved',
            invoice=invoice,
            period=invoice.period,
            currency=invoice.currency,
            exchange_rate=invoice.exchange_rate
        )

        if invoice.invoice_type == 'sale':
            debit_account =  Account.objects.filter(name="العملاء").first()
            credit_account =  Account.objects.filter(name="إيرادات المبيعات").first()
        else:
            debit_account = Account.objects.filter(name="المصروفات").first()
            credit_account = Account.objects.filter(name="الموردون").first()

        #  تأكد أن الحسابات موجودة
        if not debit_account or not credit_account:
            raise ValueError("الحسابات المحاسبية غير مكتملة")

        #  سطر مدين
        JournalEntryLine.objects.create(
            journal_entry=entry,
            account=debit_account,
            debit=amount,
            credit=Decimal('0')
        )

        #  سطر دائن
        JournalEntryLine.objects.create(
            journal_entry=entry,
            account=credit_account,
            debit=Decimal('0'),
            credit=amount
        )

        # اعتماد الفاتورة
        invoice.is_approved = True
        invoice.save(update_fields=['is_approved'])
    except ValidationError as e:
        messages.error(request, e.messages[0])
        return redirect('invoice_detail', invoice.id)
    invoice.exchange_rate_date = timezone.now()
    invoice.save()

    messages.success(request, "✅ تم اعتماد الفاتورة وإنشاء القيد المحاسبي بنجاح")
    return redirect('invoice_detail', invoice.id)

@login_required
@role_required('accountant')
def approve_journal_entry(request, entry_id):
    entry = get_object_or_404(JournalEntry, id=entry_id)

    if entry.status == 'approved':
        return redirect('accountant_dashboard')

    # منع اعتماد قيد في فترة مقفلة
    if entry.period and entry.period.is_closed:
        messages.error(
            request,
            "❌ لا يمكن اعتماد قيد في فترة محاسبية مقفلة"
        )
        return redirect('accountant_dashboard')

    entry.status = 'approved'
    entry.posted = True
    entry.save(update_fields=['status', 'posted'])

    messages.success(request, "✅ تم اعتماد القيد المحاسبي بنجاح")
    return redirect('accountant_dashboard')





#دفتر الأستاذ
@login_required
@permission_required('accounts.access_general_ledger', raise_exception=True)
def general_ledger(request):
    current_currency = request.session.get("currency", "old_syp")
    account_id = request.GET.get('account')

    account = None
    lines = []
    running_balance = 0

    if account_id:
        account = Account.objects.get(id=account_id)

        lines = (
            JournalEntryLine.objects
            .filter(account=account, journal_entry__status='approved')
            .select_related('journal_entry')
            .order_by('journal_entry__date', 'id')
        )

        for line in lines:
            running_balance = running_balance + (line.debit - line.credit)
            line.running_balance = running_balance

    accounts = Account.objects.all()

    return render(request, 'accounts/general_ledger.html', {
        'accounts': accounts,
        'selected_account': account,
        'lines': lines,
    })


#ميزان المراجعة

@login_required
@permission_required('accounts.view_trial_balance', raise_exception=True)
def trial_balance(request):
    rows = []
    total_debit = 0
    total_credit = 0

    accounts = Account.objects.all()

    for account in accounts:
        debit = JournalEntryLine.objects.filter(account=account,journal_entry__status='approved').aggregate(
            total=Sum('debit')
        )['total'] or 0

        credit =JournalEntryLine.objects.filter( account=account, journal_entry__status='approved').aggregate(
            total=Sum('credit')
        )['total'] or 0

        if debit != 0 or credit != 0:
            rows.append({
                'account': account,
                'debit': debit,
                'credit': credit
            })
            total_debit += debit
            total_credit += credit

    context = {
        'rows': rows,
        'total_debit': total_debit,
        'total_credit': total_credit,
    }

    return render(request, 'accounts/trial_balance.html', context)

#عرض المجموعات
@login_required
@role_required('admin')
def admin_group_list(request):
    groups = Group.objects.all()
    return render(request, 'dashboard/admin/admin_group_list.html', {
        'groups': groups
    })

@login_required
@role_required('admin')
def admin_group_create(request):
    if request.method == 'POST':
        form = GroupForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "✅ تم إنشاء المجموعة")
            return redirect('admin_group_list')
    else:
        form = GroupForm()

    return render(request, 'dashboard/admin/group_form.html', {
        'form': form,
        'title': 'إضافة مجموعة'
    })

@login_required
@role_required('admin')
def admin_group_update(request, group_id):
    group = get_object_or_404(Group, id=group_id)

    if request.method == 'POST':
        form = GroupForm(request.POST, instance=group)
        if form.is_valid():
            form.save()
            messages.success(request, "✅ تم تحديث المجموعة")
            return redirect('admin_group_list')
    else:
        form = GroupForm(instance=group)

    return render(request, 'dashboard/admin/group_form.html', {
        'form': form,
        'title': 'تعديل مجموعة'
    })

@login_required
@role_required('admin')
def admin_group_delete(request, group_id):
    group = get_object_or_404(Group, id=group_id)

    if request.method == 'POST':
        group.delete()
        messages.success(request, "🗑 تم حذف المجموعة")
        return redirect('admin_group_list')

    return render(request, 'dashboard/admin/group_confirm_delete.html', {
        'group': group
    })


#  تسجيل الخروج
@login_required
def logout_view(request):
    logout(request)
    return redirect('login')

#تابع مشترك لجلب البيانات
def generate_report_text(request):
    """
    Endpoint لإرجاع البيانات المالية المهمة بصيغة تحليلية احترافية (plain text)
    جاهزة لإدخالها في نموذج ذكاء اصطناعي
    """

    report_text = ""

    with connection.cursor() as cursor:

        # ========================
        # الفواتير - تحليل احترافي
        # ========================
        cursor.execute("""
        SELECT
            i.invoice_number,
            i.customer_name,
            i.invoice_date,
            i.total_amount,
            ii.description AS item_description,
            ii.quantity,
            ii.unit_price,
            ii.total_price,
            i.is_approved,
            i.currency,
            i.exchange_rate
        FROM accounts_invoice i
        JOIN accounts_invoiceitem ii
            ON i.id = ii.invoice_id
        """)
        invoices = cursor.fetchall()

        report_text += "تقرير الفواتير (تحليل احترافي):\n"
        report_text += "===============================\n"

        # تجميع الفواتير حسب رقم الفاتورة
        invoice_summary = {}
        for row in invoices:
            invoice_number, customer_name, invoice_date, total_amount, item_desc, qty, unit_price, total_price, is_approved, currency, exchange_rate = row
            if invoice_number not in invoice_summary:
                invoice_summary[invoice_number] = {
                    "customer": customer_name,
                    "date": str(invoice_date),
                    "total": total_amount,
                    "currency": currency,
                    "exchange_rate": exchange_rate,
                    "approved": is_approved,
                    "items": []
                }
            invoice_summary[invoice_number]["items"].append(f"{item_desc} (الكمية: {qty}, سعر الوحدة: {unit_price}, الإجمالي: {total_price})")

        for inv_num, info in invoice_summary.items():
            report_text += f"- فاتورة رقم {inv_num} للعميل {info['customer']} بتاريخ {info['date']}, إجمالي المبلغ: {info['total']} {info['currency']}"
            if info['currency'] != "USD" and info['exchange_rate']:
                report_text += f" (سعر الصرف: {info['exchange_rate']})"
            report_text += f", حالة الاعتماد: {'معتمدة' if info['approved'] else 'غير معتمدة'}.\n"
            report_text += "  البنود: " + "; ".join(info["items"]) + ".\n"

        # ========================
        # القيود المحاسبية - تحليل احترافي
        # ========================
        cursor.execute("""
        SELECT
            je.id AS entry_id,
            je.date,
            je.description,
            a.code AS account_code,
            a.name AS account_name,
            a.account_type,
            jl.debit,
            jl.credit,
            je.posted
        FROM accounts_journalentry je
        JOIN accounts_journalentryline jl
            ON je.id = jl.journal_entry_id
        JOIN accounts_account a
            ON jl.account_id = a.id
        """)
        entries = cursor.fetchall()

        report_text += "\nتقرير القيود المحاسبية (تحليل احترافي):\n"
        report_text += "=====================================\n"

        # تجميع القيود حسب رقم القيد
        entry_summary = {}
        for row in entries:
            entry_id, date, desc, acc_code, acc_name, acc_type, debit, credit, posted = row
            if entry_id not in entry_summary:
                entry_summary[entry_id] = {
                    "date": str(date),
                    "description": desc,
                    "posted": posted,
                    "accounts": []
                }
            entry_summary[entry_id]["accounts"].append({
                "code": acc_code,
                "name": acc_name,
                "type": acc_type,
                "debit": debit,
                "credit": credit
            })

        for eid, info in entry_summary.items():
            report_text += f"- القيد رقم {eid} بتاريخ {info['date']}, {'معتمد' if info['posted'] else 'غير معتمد'}.\n"
            report_text += f"  وصف القيد: {info['description']}\n"
            for acc in info["accounts"]:
                report_text += f"    الحساب: {acc['code']} - {acc['name']} ({acc['type']}), مدين: {acc['debit']}, دائن: {acc['credit']}\n"

        # ========================
        # دفتر الأستاذ - تحليل احترافي
        # ========================
        cursor.execute("""
        SELECT
            a.code,
            a.name,
            a.account_type,
            SUM(jl.debit) AS total_debit,
            SUM(jl.credit) AS total_credit,
            SUM(jl.debit - jl.credit) AS balance
        FROM accounts_account a
        LEFT JOIN accounts_journalentryline jl
            ON a.id = jl.account_id
        GROUP BY a.code, a.name, a.account_type
        """)
        ledger = cursor.fetchall()

        report_text += "\nتقرير دفتر الأستاذ (ملخص الحسابات):\n"
        report_text += "==================================\n"
        for code, name, acc_type, debit, credit, balance in ledger:
            report_text += f"- الحساب {code} - {name} ({acc_type}): إجمالي المدين = {debit}, إجمالي الدائن = {credit}, الرصيد = {balance}\n"

        # ========================
        # ميزان المراجعة - تحليل احترافي
        # ========================
        cursor.execute("""
        SELECT
            a.code,
            a.name,
            SUM(jl.debit) AS debit,
            SUM(jl.credit) AS credit
        FROM accounts_account a
        LEFT JOIN accounts_journalentryline jl
            ON a.id = jl.account_id
        GROUP BY a.code, a.name
        ORDER BY a.code
        """)
        trial_balance = cursor.fetchall()

        report_text += "\nتقرير ميزان المراجعة:\n"
        report_text += "======================\n"
        for code, name, debit, credit in trial_balance:
            report_text += f"- الحساب {code} - {name}: مدين = {debit}, دائن = {credit}\n"
            return report_text
#تقرير شامل         
def get_ai_report_summary(request):
    report_text = generate_report_text(request)
    user_prompt ="هذه البيانات مأخوذة من نظام محاسبي وتشمل القيود المحاسبية والفواتير ودفتر الأستاذ وميزان المراجعة. الهدف هو إعداد تقرير مالي احترافي مختصر موجه للإدارة يدعم اتخاذ القرار. ابدأ بـ ملخص تنفيذي ذكي يتضمن: إجمالي الفواتير، إجمالي القيود، وأبرز الأرصدة، مع أهم الملاحظات والمخاطر والفرص. يتضمن التقرير: ملخص مالي: إجمالي القيود والفواتير مع توزيع مختصر حسب العملاء والعملات وتحليل مختصر لدفتر الأستاذ (إجمالي المدين والدائن والنتيجة العامة) وتحليل ميزان المراجعة مع نتيجة مختصرة دون عرض الميزان وتحليل الأداء كتحديد اتجاه الإيرادات والمصروفات (نمو، انخفاض، استقرار) وأهم الحسابات المؤثرة، مع كشف الأرصدة غير الطبيعية يتضمن كشف التنبيهات: فواتير بدون قيود، قيود غير معتمدة، فواتير مرتفعة مقارنة بمتوسط العميل، اختلاف العملة قم باستخراج أهم الأنماط والتغيرات المالية، مع عرض التنبيهات حسب الأولوية. أضف قائمة مختصرة بأهم الملاحظات، ثم قدم توصيات واضحة ومختصرة تهدف إلى تحسين الربحية، تقليل المصاريف، وتعزيز الرقابة المالية. يجب أن يكون التقرير منسق، واضح، مختصر، وجاهز للإدارة دون ذكر أي تفاصيل تقنية"
    full_prompt = report_text + user_prompt + "أريد أن يكون التقرير هو نص HTML فقط فيه تنسيق كافي لعرض البيانات والجداول بشكل أنيق شبيه بتنسق ملفات ال word وملفات ال pdf لا تضيف في البداية ```html وقم بوضع dir='rtl' وأيضًا lang='ar'"
    response = client.models.generate_content(
        model="gemma-3-27b-it",
        contents=full_prompt,
        config=types.GenerateContentConfig(
            response_modalities=["TEXT"]
        )
    )

    output_text = ""
    for part in response.parts:
        if part.text:
            output_text += part.text

    output_text = re.sub(r'^```html\s*|\s*```$', '', output_text.strip())

    return HttpResponse(output_text, content_type="text/html; charset=utf-8")



 #تقرير العملاء      
def get_ai_report_customers(request):
    report_text = generate_report_text(request)
    user_prompt ="هذه البيانات مأخوذة من نظام محاسبي وتشمل الفواتير والقيود المحاسبية المرتبطة بالعملاء الهدف هو إعداد تقرير احترافي مختصر لتحليل العملاء يدعم الإدارة في اتخاذ قرارات فعالة ابدأ بملخص تنفيذي ذكي يتضمن أعلى العملاء مساهمة في الإيرادات ونسبة تركّز الإيرادات هل تعتمد الشركة على عدد محدود من العملاء ويتضمن التقرير تصنيف العملاء إلى عملاء رئيسيين متوسطين منخفضي النشاط بناء على تحليل الفواتير وتحليل تكرار التعامل عملاء دائمون مقابل عملاء عرضيين وتحليل متوسط قيمة الفاتورة لكل عميل تحديد العملاء غير النشطين أو المتوقفين واستخراج أهم الأنماط في سلوك العملاء والتغيرات في مساهمة العملاء بمرور الوقت وقائمة مختصرة بأهم الملاحظات وتوصيات واضحة لزيادة الإيرادات من العملاء الحاليين واستخدم الخوارزميات الصحيحة ويجب أن يكون التقرير مختصر واضح إداري وخالي من التفاصيل التقنية والخوارزميات المستخدمة"
    full_prompt = report_text + user_prompt + "أريد أن يكون التقرير هو نص HTML فقط فيه تنسيق كافي لعرض البيانات والجداول بشكل أنيق شبيه بتنسق ملفات ال word وملفات ال pdf لا تضيف في البداية ```html وقم بوضع dir='rtl' وأيضًا lang='ar'"
    response = client.models.generate_content(
        model="gemma-3-27b-it",
        contents=full_prompt,

    )

    output =  "".join([p.text for p in response.parts if p.text])

    return HttpResponse(output, content_type="text/html; charset=utf-8")




#كشف المخاطر والتنبيهات المالية     
def get_ai_report_risks(request):
    report_text = generate_report_text(request)
    user_prompt ="""هذه البيانات مأخوذة من نظام محاسبي وتشمل القيود المحاسبية والفواتير ودفتر الأستاذ وميزان المراجعة الهدف إعداد تقرير احترافي يركز على كشف المخاطر المالية والحالات غير الطبيعية لدعم الرقابة المالية يشمل التقرير ملخص عام للحالة المالية وتحليل التوازن بين المدين والدائن عبر ميزان المراجعة وتحليل الأرصدة في دفتر الأستاذ ويركز على كشف الحالات غير الطبيعية مثل فواتير بدون قيود قيود بدون ارتباط واضح قيود أو فواتير غير معتمدة اختلاف العملات أو بيانات ناقصة واكتشاف القيم المرتفعة مقارنة بالمتوسط العام أو متوسط العميل وتحديد التغيرات المفاجئة في المصروفات أو الإيرادات وتحليل العمليات عالية المخاطر وتصنيف التنبيهات حسب درجة الخطورة وإبراز الحالات التي تتطلب تدخل فوري مع تقديم توصيات للإدارة لتحسين الرقابة المالية تقليل الأخطاء تعزيز دقة البيانات وتطوير نظام التنبيهات المبكر يجب عرض التقرير منسق واضح وموجه لاتخاذ القرار دون ذكر أي خوارزميات أو تفاصيل تقنية"""
    full_prompt = report_text + user_prompt + "أريد أن يكون التقرير هو نص HTML فقط فيه تنسيق كافي لعرض البيانات والجداول بشكل أنيق شبيه بتنسق ملفات ال word وملفات ال pdf لا تضيف في البداية ```html وقم بوضع dir='rtl' وأيضًا lang='ar'"
    response = client.models.generate_content(
        model="gemma-3-27b-it",
        contents=full_prompt,
    )

    output = "".join([p.text for p in response.parts if p.text])

    return HttpResponse(output, content_type="text/html; charset=utf-8")