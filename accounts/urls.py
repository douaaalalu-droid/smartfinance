from django.urls import path
from . import views

urlpatterns = [
    path('', views.login_view, name='login'),


    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('accountant-dashboard/', views.accountant_dashboard, name='accountant_dashboard'),
    path('manager-dashboard/', views.manager_dashboard, name='manager_dashboard'),
    path('data-entry-dashboard/', views.data_entry_dashboard, name='data_entry_dashboard'),

    path('logout/', views.logout_view, name='logout'),

    # الفواتير
    path('invoices/create/', views.create_invoice, name='create_invoice'),
    path('accountant/invoices/', views.accountant_invoices, name='accountant_invoices'),
    path('invoice/<int:invoice_id>/', views.invoice_detail, name='invoice_detail'),
    path('invoice/<int:invoice_id>/approve/', views.approve_invoice, name='approve_invoice'),

    path('general-ledger/', views.general_ledger, name='general_ledger'),


    path('trial-balance/', views.trial_balance, name='trial_balance'),
    path(
    'journal-entry/<int:entry_id>/approve/',
    views.approve_journal_entry,
    name='approve_journal_entry'
),


]
