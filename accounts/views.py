from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.db import transaction
from .models import InvoiceItem
from django.contrib import messages
from django.db.models import Sum
from decimal import Decimal
from .models import User, Invoice, InvoiceItem, JournalEntry
from .forms import JournalEntryForm, JournalEntryLineFormSet
from accounts.forms import JournalEntryLine
from .models import Account
from django.contrib.auth.decorators import permission_required
from accounts.decorators import role_required
from django.utils import timezone
from .models import AccountingPeriod




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
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)

        if user:
            login(request, user)

            if user.role == 'admin':
                return redirect('admin_dashboard')
            elif user.role == 'accountant':
                return redirect('accountant_dashboard')
            elif user.role == 'manager':
                return redirect('manager_dashboard')
            elif user.role == 'data_entry':
                return redirect('data_entry_dashboard')

        return render(request, 'login.html', {
            'error': 'بيانات الدخول غير صحيحة'
        })

    return render(request, 'login.html')


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
    return render(request, 'dashboard/admin.html', context)




#  لوحة المدير المالي


@login_required
@role_required('manager')
def manager_dashboard(request):

    income = (
        JournalEntryLine.objects
        .filter(
            account__account_type='revenue',
            journal_entry__status='approved'
        )
        .aggregate(total=Sum('credit'))['total'] or 0
    )

    expense = (
        JournalEntryLine.objects
        .filter(
            account__account_type='expense',
            journal_entry__status='approved'
        )
        .aggregate(total=Sum('debit'))['total'] or 0
    )


    profit = income - expense

    context = {
        'income': income,
        'expense': expense,
        'profit': profit,
    }

    return render(request, 'dashboard/manager.html', context)

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
            entry.save()

            formset = JournalEntryLineFormSet(request.POST, instance=entry)

            if formset.is_valid():
                formset.save()

                #  التحقق من توازن القيد
                total_debit = entry.lines.aggregate(
                    total=Sum('debit')
                )['total'] or 0

                total_credit = entry.lines.aggregate(
                    total=Sum('credit')
                )['total'] or 0

                if total_debit != total_credit:
                    entry.delete()
                    messages.error(
                        request,
                        f"❌ القيد غير متوازن: مدين {total_debit} ≠ دائن {total_credit}"
                    )
                    return redirect('accountant_dashboard')

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

    if request.method == 'POST':
        form = JournalEntryForm(request.POST)

        if form.is_valid():
         
            entry = form.save(commit=False)
            entry.created_by = request.user
            entry.status = 'draft'
            entry.save() 

            formset = JournalEntryLineFormSet(request.POST, instance=entry)

            if formset.is_valid():
                formset.save()

        
                total_debit = entry.lines.aggregate(
                    total=Sum('debit')
                )['total'] or 0

                total_credit = entry.lines.aggregate(
                    total=Sum('credit')
                )['total'] or 0

                if total_debit != total_credit:
                    entry.delete()
                    messages.error(
                        request,
                        f"❌ القيد غير متوازن: مدين {total_debit} ≠ دائن {total_credit}"
                    )
                    return redirect('data_entry_dashboard')

              
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
    .select_related('created_by')
    .prefetch_related('lines')
    .order_by('-created_at')
)


    return render(request, 'dashboard/data_entry.html', {
        'form': form,
        'formset': formset,
        'entries': entries
    })



#  إنشاء فاتورة
@login_required
@role_required('accountant', 'data_entry')
def create_invoice(request):
    invoice_form = InvoiceForm()
    formset = InvoiceItemFormSet(queryset=InvoiceItem.objects.none())

    if request.method == 'POST':
        invoice_form = InvoiceForm(request.POST)

        if invoice_form.is_valid():
            invoice = invoice_form.save(commit=False)
            if invoice.period and invoice.period.is_closed:
                invoice_form.add_error(
                    'period',
                    '❌ لا يمكن إنشاء فاتورة في فترة محاسبية مقفلة'
                )
            else:
                with transaction.atomic():
                    invoice.created_by = request.user
                    invoice.total_amount = 0
                    invoice.save()

                    formset = InvoiceItemFormSet(request.POST, instance=invoice)

                    if formset.is_valid():
                        items = formset.save(commit=False)

                        total = 0
                        for item in items:
                            item.invoice = invoice
                            item.save()
                            total += item.total_price

                        invoice.total_amount = total
                        invoice.save(update_fields=['total_amount'])

                        messages.success(request, "✅ تم حفظ الفاتورة بنجاح")

                        if request.user.role == 'accountant':
                            return redirect('accountant_invoices')
                        else:
                            return redirect('data_entry_dashboard')

                    else:
                        print("Formset errors:", formset.errors)

        else:
            print("Invoice errors:", invoice_form.errors)

    return render(request, 'invoices/create_invoice.html', {
        'invoice_form': invoice_form,
        'formset': formset
    })


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
    invoice = get_object_or_404(Invoice, id=invoice_id)
    items = invoice.items.all()

    return render(request, 'invoices/invoice_detail.html', {
        'invoice': invoice,
        'items': items
    })


#  اعتماد فاتورة
@login_required
@role_required('accountant')
def approve_invoice(request, invoice_id):
    invoice = get_object_or_404(Invoice, id=invoice_id)

    if invoice.is_approved:
        return redirect('invoice_detail', invoice.id)
    if invoice.period and invoice.period.is_closed:
        messages.error(
            request,
              "❌ لا يمكن اعتماد فاتورة في فترة محاسبية مقفلة"
        )
        return redirect('invoice_detail', invoice.id)

    if invoice.is_approved:
        return redirect('invoice_detail', invoice.id)

    amount = invoice.total_amount

    with transaction.atomic():

        #  إنشاء رأس القيد
        entry = JournalEntry.objects.create(
            date=invoice.invoice_date,
            description=f"قيد تلقائي للفاتورة {invoice.invoice_number}",
            created_by=request.user,
            status='approved',
            invoice=invoice,
            period=invoice.period
        )

        #  جلب الحسابات
        if invoice.invoice_type == 'sale':
            debit_account = Account.objects.filter(account_type='asset').first()
            credit_account = Account.objects.filter(account_type='revenue').first()
        else:
            debit_account = Account.objects.filter(account_type='expense').first()
            credit_account = Account.objects.filter(account_type='liability').first()

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
    account_id = request.GET.get('account')

    account = None
    lines = []
    running_balance = 0

    if account_id:
        account = Account.objects.get(id=account_id)

        lines = (
            JournalEntryLine.objects
            .filter(account=account)
            .select_related('journal_entry')
            .order_by('journal_entry__date', 'id')
        )

        for line in lines:
            running_balance += line.debit - line.credit
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
        debit = account.journalentryline_set.aggregate(
            total=Sum('debit')
        )['total'] or 0

        credit = account.journalentryline_set.aggregate(
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




#الإقفال المحاسبي
@permission_required('accounts.close_accounting_period', raise_exception=True)
def close_accounting_period(request, period_id):
    period = get_object_or_404(AccountingPeriod, id=period_id)

    period.is_closed = True
    period.closed_at = timezone.now()
    period.closed_by = request.user
    period.save()

    return redirect('accounting_period_list')

#  تسجيل الخروج
@login_required
def logout_view(request):
    logout(request)
    return redirect('login')
