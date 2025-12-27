from django.urls import path
from . import views
urlpatterns = [
    path('', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('manager-dashboard/', views.manager_dashboard, name='manager_dashboard'),
    path('accountant-dashboard/', views.accountant_dashboard, name='accountant_dashboard'),
    path('data-entry-dashboard/', views.data_entry_dashboard, name='data_entry_dashboard'),

    path('create-invoice/', views.create_invoice, name='create_invoice'),
    path('accountant-invoices/', views.accountant_invoices, name='accountant_invoices'),

    path('invoice/<int:invoice_id>/', views.invoice_detail, name='invoice_detail'),
    path('approve-invoice/<int:invoice_id>/', views.approve_invoice, name='approve_invoice'),
]
