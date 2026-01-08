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

#  لوحة المحاسب
@login_required
@role_required('accountant')
def accountant_dashboard(request):
    form = JournalEntryForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        entry = form.save(commit=False)

        entry.created_by = request.user
        entry.status = 'draft'
        entry.save()
        return redirect('accountant_dashboard')

    entries = JournalEntry.objects.all().order_by('-created_at')

    return render(request, 'dashboard/accountant.html', {
        'form': form,
        'entries': entries
    })


#  لوحة المدير المالي

@login_required
@role_required('manager')
def manager_dashboard(request):
    income = JournalEntry.objects.filter(entry_type='income').aggregate(total=Sum('amount'))['total'] or 0
    expense = JournalEntry.objects.filter(entry_type='expense').aggregate(total=Sum('amount'))['total'] or 0

    context = {
        'income': income,
        'expense': expense,
        'profit': income - expense
    }
    return render(request, 'dashboard/manager.html', context)

# لوحة مدخل البيانات مع دفتر القيود
@login_required
@role_required('data_entry')
def data_entry_dashboard(request):
    form = JournalEntryForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        entry = form.save(commit=False)
        entry.created_by = request.user
        entry.status = 'draft'
        entry.save()
        return redirect('data_entry_dashboard')

    entries = JournalEntry.objects.filter(
        created_by=request.user
    ).order_by('-created_at')

    return render(request, 'dashboard/data_entry.html', {
        'form': form,
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
            with transaction.atomic():
                invoice = invoice_form.save(commit=False)
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
                    invoice.save()

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
    invoices = Invoice.objects.all().order_by('-created_at')
    return render(request, 'invoices/accountant_invoices.html', {
        'invoices': invoices
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
    amount = invoice.total_amount

    JournalEntry.objects.create(
            date=invoice.invoice_date,
            description=f"قيد تلقائي للفاتورة{invoice.invoice_number}",
            account_name=(
                "المبيعات"if invoice.invoice_type == 'sale' else "المشتريات"
            ),
    debit=amount if invoice.invoice_type == 'purchase' else Decimal('0'),
    credit=amount if invoice.invoice_type == 'sale' else Decimal('0'),
    amount=amount,
    entry_type=(
        'income' if invoice.invoice_type == 'sale' else 'expense'
    ),
    created_by=request.user,
    status='approved',
    invoice=invoice 
 )
    invoice.is_approved = True
    invoice.save()
    return redirect('invoice_detail', invoice.id)


#  تسجيل الخروج
@login_required
def logout_view(request):
    logout(request)
    return redirect('login')
