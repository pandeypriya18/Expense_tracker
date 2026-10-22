from rest_framework import serializers
from expense.models import Category , Expense ,Budget
from rest_framework.exceptions import ValidationError

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id','category_name','owner','created_at']

    def validate_category_name(self ,value):
        if Category.objects.filter(category_name=value).exists():
            raise ValidationError("Category Already Exists.")
        return value

class ExpenseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Expense
        fields = '__all__'
        read_only_fields =['user','amount_in_base_currency']

class BudgetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Budget
        fields = ['id','user','category','month','limit_amount','created_at']
        read_only_fields = ['user','id','created_at']

    