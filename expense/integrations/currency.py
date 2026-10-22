
import requests
from decimal import Decimal
from datetime import timedelta
from django.utils import timezone

CACHE_HOURS = 6

class CurrencyConversionError(Exception):
    """Raised when currency conversion cannot be completed."""
    pass


def fetch_live_rate(from_currency, to_currency):
    url = f"https://open.er-api.com/v6/latest/{from_currency}"

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()

        if data.get("result") != "success":
            raise CurrencyConversionError(
                "Currency exchange API returned an unsuccessful result."
            )

        rate = data.get("rates", {}).get(to_currency)

        if rate is None:
            raise CurrencyConversionError(
                f"Exchange rate for {to_currency} is unavailable."
            )

        rate = Decimal(str(rate))

        if not rate.is_finite() or rate <= 0:
            raise CurrencyConversionError(
                "The exchange API returned an invalid rate."
            )

        return rate

    except (requests.RequestException, ValueError, TypeError) as exc:
        raise CurrencyConversionError(
            "Currency conversion service is unavailable."
        ) from exc


def get_exchange_rate(from_currency, to_currency):
    from expense.models import ExchangeRate
    # Step 1: Check database cache
    cached_rate = ExchangeRate.objects.filter(
        base_currency=from_currency,
        target_currency=to_currency,
    ).first()

    # Step 2: Return cached rate if it is less than 6 hours old
    if cached_rate:
        cache_expiry = timezone.now() - timedelta(hours=CACHE_HOURS)

        if cached_rate.fetched_at >= cache_expiry:
            return cached_rate.rate, "cache"

    # Step 3: Cache missing or expired; try fetching a live rate
    try:
        live_rate = fetch_live_rate(from_currency, to_currency)

    except CurrencyConversionError:
        # Step 4: Fallback to an existing cached rate
        if cached_rate is not None:
            return cached_rate.rate, "fallback"

        # No cached rate: conversion cannot proceed
        raise

    # Step 5: Save the newly fetched rate
    ExchangeRate.objects.update_or_create(
        base_currency=from_currency,
        target_currency=to_currency,
        defaults={"rate": live_rate},
    )

    return live_rate, "live"


def convert_to_base_currency(amount, from_currency, base_currency="INR"):
    amount = Decimal(str(amount))
    from_currency = from_currency.upper()
    base_currency = base_currency.upper()

    # No API required when currencies are identical
    if from_currency == base_currency:
        return amount.quantize(Decimal("0.01"))

    rate, source = get_exchange_rate(from_currency, base_currency)

    converted_amount = amount * rate

    # Log whether the rate came from cache, live API or fallback
    print(
        f"Currency conversion: {from_currency} -> {base_currency}; "
        f"rate source={source}"
    )

    return converted_amount.quantize(Decimal("0.01"))
