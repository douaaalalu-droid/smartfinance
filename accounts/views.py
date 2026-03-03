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
            currency = request.session.get("currency", "old_syp")

            if currency == "usd":
                exchange_rate = request.POST.get("exchange_rate")
                if not exchange_rate:
                    messages.error(request, "❌ يجب إدخال سعر الصرف للدولار")
                    return redirect('accountant_dashboard')
                entry.exchange_rate = exchange_rate
            else:
                entry.exchange_rate = None
 
            entry.save()

            formset = JournalEntryLineFormSet(request.POST, instance=entry)

            if formset.is_valid():
                lines = formset.save(commit=False)

                #  منع حفظ قيد بدون حركات
                valid_lines = [
                    line for line in lines
                    if line and not getattr(line, 'DELETE', False)
                ]

                if not valid_lines:
                    entry.delete()
                    messages.error(request, "❌ لا يمكن حفظ قيد بدون حركات")
                    return redirect('accountant_dashboard')

                # حفظ الحركات
                for line in valid_lines:
                    line.entry = entry
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

            if currency == "usd":
                exchange_rate = request.POST.get("exchange_rate")
                if not exchange_rate:
                    messages.error(request, "❌ يجب إدخال سعر الصرف للدولار")
                    return redirect('accountant_dashboard')
                entry.exchange_rate = exchange_rate
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
                lines = formset.save(commit=False)

                valid_lines = [
                    line for line in lines
                    if line and not getattr(line, 'DELETE', False)
                ]

                if not valid_lines:
                    entry.delete()
                    messages.error(request, "❌ لا يمكن حفظ قيد بدون حركات")
                    return redirect('data_entry_dashboard')

                
                for line in valid_lines:
                    line.entry = entry
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
@login_required
def set_currency(request):
    currency = request.GET.get("currency")
    exchange_rate = request.GET.get("exchange_rate")

    if currency:
        request.session["currency"] = currency

        if currency == "usd" and exchange_rate:
            request.session["exchange_rate"] = exchange_rate
        else:
            request.session["exchange_rate"] = None

        request.session.modified = True

    return redirect(request.META.get("HTTP_REFERER", "/"))
#  إنشاء فاتورة
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
                    invoice.total_amount = 0
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
                            return render(request, 'invoices/create_invoice.html', {
                                'invoice_form': invoice_form,
                                'formset': formset
                            })

                        total = 0
                        for item in items:
                            item.invoice = invoice

                            #  التحويل حسب العملة المختارة
                            currency = request.session.get("currency", "old_syp")

                            if currency == "new_syp":
                                item.unit_price = item.unit_price * 100
                                item.total_price = item.total_price * 100

                            elif currency == "usd":
                                latest_rate = ExchangeRate.objects.filter(  currency='usd').order_by('-date').first()

                                if not latest_rate:
                                    raise ValidationError("❌ لا يوجد سعر صرف معرف")
                                
                                item.unit_price = item.unit_price * latest_rate.rate
                                item.total_price = item.total_price * latest_rate.rate


                           

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
                        messages.error(request, "❌ يوجد خطأ في بنود الفاتورة")

            except ValidationError as e:
                invoice_form.add_error(None, e.messages[0])

        else:
            messages.error(request, "❌ يوجد خطأ في بيانات الفاتورة")

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
    except ValidationError as e:
        messages.error(request, e.messages[0])
        return redirect('invoice_detail', invoice.id)

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
