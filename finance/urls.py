from django.urls import path
from . import views

urlpatterns = [
    path('payments/', views.PaymentListCreateView.as_view(), name='payment-list-create'),
    path('expenses/', views.ExpenseListCreateView.as_view(), name='expense-list-create'),
    path('reports/', views.FinancialReportView.as_view(), name='financial-report'),
]