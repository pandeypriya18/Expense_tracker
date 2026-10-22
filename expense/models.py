from django.utils import timezone
from django.core.exceptions import ValidationError
from django.db import models
from account.models import MyUser
from django.core.validators import MinValueValidator , RegexValidator
from .integrations.currency import convert_to_base_currency

currency_validator = RegexValidator(
    r"^[A-Z]{3}$", "Use a 3-letter code like USD, INR, EUR."
)

class Category(models.Model):
    category_name = models.CharField(max_length=100)
    owner = models.ForeignKey(MyUser, on_delete=models.CASCADE ,null = True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.category_name

def validate_not_future(value):
    if value > timezone.localdate():
        raise ValidationError("Date cannot be in the future.")
    
class Expense(models.Model):
    user = models.ForeignKey(MyUser , on_delete=models.CASCADE)
    category = models.ForeignKey(Category , on_delete=models.PROTECT)
    amount = models.DecimalField(max_digits=12,decimal_places=2, validators=[MinValueValidator(0.01)])
    currency = models.CharField(max_length=3,validators=[currency_validator])
    amount_in_base_currency = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        editable=False,
        null=True,
        blank=True,
    )
    description = models.TextField(blank=True)
    date = models.DateField(validators=[validate_not_future])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        self.amount_in_base_currency = convert_to_base_currency(
            amount=self.amount,
            from_currency=self.currency,
            base_currency="INR",
        )

        super().save(*args, **kwargs)

class Budget(models.Model):
    user = models.ForeignKey(MyUser,on_delete=models.CASCADE)
    category = models.ForeignKey(Category,on_delete=models.CASCADE)
    month = models.CharField(max_length=7, validators=[RegexValidator(r"^\d{4}-(0[1-9]|1[0-2])$", "Month must be in YYYY-MM format, e.g. 2026-09.")])
    limit_amount = models.DecimalField(max_digits=12,decimal_places=2,validators=[MinValueValidator(0.01)],)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user} - {self.category} - {self.month}"


class ExchangeRate(models.Model):
    base_currency = models.CharField(max_length=3, validators=[currency_validator])
    target_currency = models.CharField(max_length=3, validators=[currency_validator])
    rate = models.DecimalField(max_digits=18, decimal_places=6)
    fetched_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"1 {self.base_currency} = {self.rate} {self.target_currency}"
