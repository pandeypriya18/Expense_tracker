from django.contrib import admin

from .models import Budget, Category, ExchangeRate, Expense


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("id","category_name", "owner", "created_at")
    list_filter = ("owner",)
    search_fields = ("category_name",)


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ("id","user", "category", "amount", "currency","amount_in_base_currency", "date")
    list_filter = ("currency", "category", "date")
    search_fields = ("description", "user__username")
    readonly_fields = ("amount_in_base_currency", "created_at", "updated_at")


@admin.register(Budget)
class BudgetAdmin(admin.ModelAdmin):
    list_display = ("id","user", "category", "month", "limit_amount")
    list_filter = ("month",)


@admin.register(ExchangeRate)
class ExchangeRateAdmin(admin.ModelAdmin):
    list_display = ("base_currency", "target_currency", "rate", "fetched_at")
