from django.urls import path
from .views import CategoryView,ExpenseView,ExpenseDetailView,BudgetView,BudgetDetailView,MonthlyReportView,SpendingTrendView,ExchangeRateView

urlpatterns = [
    path("category/", CategoryView.as_view()),
    path("category/<int:id>/", CategoryView.as_view()),
    path('expense/',ExpenseView.as_view()),
    path('expense/<int:pk>/',ExpenseDetailView.as_view()),
    path('budget/',BudgetView.as_view()),
    path('budget/<int:pk>/',BudgetDetailView.as_view()),
    path("reports/monthly/",MonthlyReportView.as_view()),
    path("reports/trend/",SpendingTrendView.as_view()),
    path("exchange-rate/",ExchangeRateView.as_view()),
]

