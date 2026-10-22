from datetime import date
from django.utils import timezone
from decimal import Decimal
import re
from django.db.models.aggregates import Sum
from django.db.models.functions import TruncMonth
import requests
from expense.integrations.currency import CurrencyConversionError
from expense.serializers import CategorySerializer,ExpenseSerializer,BudgetSerializer
from rest_framework.response import Response
from rest_framework.views import APIView
from expense.models import Category, ExchangeRate ,Expense,Budget
from rest_framework import permissions
from rest_framework import status
from django.shortcuts import get_object_or_404
from rest_framework.pagination import PageNumberPagination

class CategoryView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def get(self, request):
        if request.user.role == "admin":
            categories = Category.objects.all()
        else:
            categories = Category.objects.filter(owner__role="admin") | Category.objects.filter(owner=request.user)

        serializer = CategorySerializer(categories, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = CategorySerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(owner=request.user)
            return Response({"message":"Category created successfully."}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors ,status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, id):
       try:  
         category = get_object_or_404(Category, id=id)
       except Exception:
         return Response({"error":"Category doesn't exists."} , status=status.HTTP_400_BAD_REQUEST)

       if request.user.role == "admin":
            if category.owner is not None:
                return Response({"message": "Admin cannot delete a user's category."},status=status.HTTP_403_FORBIDDEN)
       else:
            if category.owner != request.user:
                return Response({"message": "You cannot delete this category."},status=status.HTTP_403_FORBIDDEN)
       category.delete()
       return Response({"message": "Category deleted successfully."},status=status.HTTP_200_OK)

class ExpenseView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    #Post:create
    def post(self, request):
        serializer = ExpenseSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            serializer.save(user=request.user)
        except CurrencyConversionError as exc:
            return Response({"error": str(exc)},status=status.HTTP_503_SERVICE_UNAVAILABLE)

        return Response(serializer.data,status=status.HTTP_201_CREATED)

    def get(self, request):
        expenses = Expense.objects.filter(user=request.user)
        search = request.query_params.get("search")
        if search:
            expenses = expenses.filter(category__category_name__icontains=search)
        paginator = PageNumberPagination()
        paginator.page_size = 10
        paginated_expenses = paginator.paginate_queryset(expenses, request, view=self)
        serializer = ExpenseSerializer(paginated_expenses, many=True)
        return paginator.get_paginated_response(serializer.data)

def check_expense_permission(request, expense):
    if request.user.role == "admin":
     if expense.user is not None:
        return Response({"message": "No Permission."},status=status.HTTP_403_FORBIDDEN)
    else:
        if expense.user != request.user:
         return Response({"message": "No Permission."},status=status.HTTP_403_FORBIDDEN)
    return None

class ExpenseDetailView(APIView):

    def get_object(self, request, pk):
        if request.user.role == "admin":
            return Expense.objects.filter(pk=pk).first()

        return Expense.objects.filter(pk=pk,user=request.user).first()

    # GET: Single expense
    def get(self, request, pk):
        expense = self.get_object(request, pk)
        if expense is None:
            return Response({"error": "Expense not found."},status=status.HTTP_404_NOT_FOUND)
        serializer = ExpenseSerializer(expense)
        return Response(serializer.data, status=status.HTTP_200_OK)

    # PUT: Complete update
    def put(self, request, pk):
        expense = self.get_object(request, pk)

        permission_response = check_expense_permission(request, expense)

        if permission_response:
           return permission_response

        if expense is None:
            return Response({"error": "Expense not found."},status=status.HTTP_404_NOT_FOUND)

        serializer = ExpenseSerializer(expense,data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    # PATCH: Partial update
    def patch(self, request, pk):
        expense = self.get_object(request, pk)

        permission_response = check_expense_permission(request, expense)

        if permission_response:
           return permission_response

        if expense is None:
            return Response({"error": "Expense not found."},status=status.HTTP_404_NOT_FOUND)

        serializer = ExpenseSerializer(expense,data=request.data,partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data, status=status.HTTP_200_OK)

    # DELETE: Remove expense
    def delete(self, request, pk):
        expense = self.get_object(request, pk)

        permission_response = check_expense_permission(request, expense)
        if permission_response:
           return permission_response

        if expense is None:
            return Response({"error": "Expense not found."},status=status.HTTP_404_NOT_FOUND)
        expense.delete()

        return Response({"message": "Expense deleted successfully."}, status=status.HTTP_200_OK)

class BudgetView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    # POST: Create budget
    def post(self, request):
        serializer = BudgetSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(user=request.user)
        return Response(serializer.data,status=status.HTTP_201_CREATED)

    # GET: List budgets
    def get(self, request):
        if request.user.role == "admin":
            budgets = Budget.objects.all()
        else:
            budgets = Budget.objects.filter(user=request.user)

        serializer = BudgetSerializer(budgets, many=True)
        return Response(serializer.data,status=status.HTTP_200_OK)

def check_budget_permission(request, budget):
    if request.user.role == "admin":
     if budget.user is not None:
        return Response({"message": "No Permission."},status=status.HTTP_403_FORBIDDEN)
    else:
        if budget.user != request.user:
         return Response({"message": "No Permission."},status=status.HTTP_403_FORBIDDEN)
    return None

class BudgetDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self, request, pk):
        if request.user.role == "admin":
            return Budget.objects.filter(pk=pk).first()
        return Budget.objects.filter(pk=pk,user=request.user).first()

    # PUT: Complete update
    def put(self, request, pk):
        budget = self.get_object(request, pk)

        permission_response = check_budget_permission(request, budget)
        if permission_response:
           return permission_response

        if budget is None:
            return Response({"error": "Budget not found."},status=status.HTTP_404_NOT_FOUND)

        serializer = BudgetSerializer(budget,data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data,status=status.HTTP_200_OK)

    # PATCH: Partial update
    def patch(self, request, pk):
        budget = self.get_object(request, pk)

        permission_response = check_budget_permission(request, budget)
        if permission_response:
           return permission_response

        if budget is None:
            return Response({"error": "Budget not found."},status=status.HTTP_404_NOT_FOUND)
        serializer = BudgetSerializer(budget,data=request.data,partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data,status=status.HTTP_200_OK)

    # DELETE: Delete budget
    def delete(self, request, pk):
        budget = self.get_object(request, pk)        
        
        permission_response = check_budget_permission(request, budget)
        if permission_response:
           return permission_response

        if budget is None:
            return Response({"error": "Budget not found."},status=status.HTTP_404_NOT_FOUND)
        budget.delete()
        return Response({"message": "Budget deleted successfully."},status=status.HTTP_200_OK)

class MonthlyReportView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        month = request.query_params.get("month")

        if not month or not re.fullmatch(r"\d{4}-(0[1-9]|1[0-2])", month):
            return Response({"error": "Provide month in YYYY-MM format, e.g. 2026-09."},status=status.HTTP_400_BAD_REQUEST,)

        year, month_number = map(int, month.split("-"))
        start_date = date(year, month_number, 1)
        if month_number == 12:
            end_date = date(year + 1, 1, 1)
        else:
            end_date = date(year, month_number + 1, 1)

        # Only the logged-in user's expenses
        expenses = Expense.objects.filter(user=request.user,date__gte=start_date,date__lt=end_date,)
        total_spend = (expenses.aggregate(total=Sum("amount_in_base_currency"))["total"] or Decimal("0.00"))

        # Category-wise spending
        category_totals = (
            expenses.values("category_id","category__category_name",).annotate(total=Sum("amount_in_base_currency")).order_by("category__category_name"))
        category_breakdown = []
        for item in category_totals:
            category_spend = item["total"] or Decimal("0.00")

            percentage = (category_spend * Decimal("100") / total_spend
                if total_spend else Decimal("0.00")
            )

            # Budget for this category and month
            budget = Budget.objects.filter(user=request.user,category_id=item["category_id"],month=month,).first()

            # Assumes Budget has an `amount` field
            budget_amount = (budget.amount if budget else Decimal("0.00"))
            remaining = budget_amount - category_spend
            category_breakdown.append({
                "category_id": item["category_id"],
                "category_name": item["category__category_name"],
                "total_spend": str(category_spend),
                "spend_percentage": round(percentage, 2),
                "budget": str(budget_amount),
                "remaining": str(max(remaining, Decimal("0.00"))),
                "overspend": str(max(-remaining, Decimal("0.00"))),
                "status": (
                    "no_budget" if budget is None
                    else "overspent" if remaining < 0
                    else "within_budget"
                ),})

        return Response({"month": month,"base_currency": "INR","total_spend": str(total_spend),"category_breakdown": category_breakdown,})

class SpendingTrendView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def get(self, request):
        try:
            months = int(request.query_params.get("months", 3))
        except (TypeError, ValueError):
            return Response({"error": "months must be a valid integer."},status=status.HTTP_400_BAD_REQUEST,)
        if not 1 <= months <= 24:
            return Response({"error": "months must be between 1 and 24."},status=status.HTTP_400_BAD_REQUEST,)

        today = timezone.localdate()

        # Include current month and previous months
        start_year = today.year
        start_month = today.month - months + 1

        while start_month <= 0:
            start_month += 12
            start_year -= 1

        start_date = date(start_year, start_month, 1)
        expenses = Expense.objects.filter(user=request.user,date__gte=start_date,date__lt=date(
                today.year + (1 if today.month == 12 else 0),
                1 if today.month == 12 else today.month + 1,
                1,
            ), )
        totals = (
            expenses.annotate(month_date=TruncMonth("date"))
            .values("month_date")
            .annotate(total=Sum("amount_in_base_currency"))
            .order_by("month_date") )
        
        # Map months to totals; missing months become zero
        totals_map = {
            item["month_date"].strftime("%Y-%m"):
                item["total"] or Decimal("0.00")
            for item in totals
        }
        monthly_data = []
        year, month = start_year, start_month
        for _ in range(months):
            month_key = f"{year:04d}-{month:02d}"
            monthly_data.append({
                "month": month_key,
                "total_spend": totals_map.get(
                    month_key, Decimal("0.00")
                ),})
            month += 1
            if month == 13:
                month = 1
                year += 1

        for index, item in enumerate(monthly_data):
            current = Decimal(str(item["total_spend"]))

            if index == 0:
                change = None
                change_percentage = None
            else:
                previous = Decimal(str(monthly_data[index - 1]["total_spend"]))

                change = current - previous

                if previous != 0:
                    change_percentage = round(
                        (change / previous) * 100, 2
                    )
                else:
                    change_percentage = None

            item["total_spend"] = str(current)

            item["change_from_previous_month"] = (
                str(change) if change is not None else None
            )

            item["change_percentage"] = change_percentage


        return Response({"months": months,"base_currency": "INR","trend": monthly_data,})

class ExchangeRateView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    CACHE_HOURS = 6

    def get(self, request):
        from_currency = request.query_params.get("from", "").upper()
        to_currency = request.query_params.get("to", "").upper()

        if not re.fullmatch(r"[A-Z]{3}", from_currency) or not re.fullmatch(
            r"[A-Z]{3}", to_currency
        ):
            return Response(
                {"error": "Provide valid 3-letter currency codes, e.g. USD and INR."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if from_currency == to_currency:
            return Response({
                "from": from_currency,
                "to": to_currency,
                "rate": "1",
                "source": "same_currency",
            })

        cached = ExchangeRate.objects.filter(
            base_currency=from_currency,
            target_currency=to_currency,
        ).first()

        if cached and (
            timezone.now() - cached.fetched_at
        ).total_seconds() < self.CACHE_HOURS * 3600:
            return Response({"from": from_currency,"to": to_currency,"rate": str(cached.rate),"source": "cache","fetched_at": cached.fetched_at,})
        try:
            url = (
                f"https://open.er-api.com/v6/latest/{from_currency}"
            )
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()

            if data.get("result") != "success":
                return Response({"error": "Currency provider could not return the rate."},status=status.HTTP_502_BAD_GATEWAY,)

            rate = data.get("rates", {}).get(to_currency)
            if rate is None:
                return Response({"error": f"Rate for {to_currency} is unavailable."},status=status.HTTP_502_BAD_GATEWAY)

            rate = Decimal(str(rate))
            exchange_rate, _ = ExchangeRate.objects.update_or_create(
                base_currency=from_currency,
                target_currency=to_currency,
                defaults={"rate": rate},)

            return Response({"from": from_currency,"to": to_currency,"rate": str(exchange_rate.rate),"source": "live_api","fetched_at": exchange_rate.fetched_at,})
        except (requests.RequestException, ValueError):
            return Response({"error": "Unable to fetch the exchange rate right now."},status=status.HTTP_502_BAD_GATEWAY)
