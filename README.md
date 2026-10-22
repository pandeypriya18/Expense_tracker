# Expense Tracker API

A Django REST Framework (DRF) REST API for managing daily expenses, organizing categories, setting monthly budgets, and converting expense amounts into a base currency (INR) using exchange rates.

> **Project status:** Authentication, category, expense, and budget APIs have been developed and tested with Postman. Final end-to-end verification of currency conversion and exchange-rate caching is still required.

## Features

### Authentication and Password Management

- User registration and login
- JWT-based authentication for protected endpoints
- Logout
- Change password
- Forgot password and password reset

### Category Management

- Create and retrieve categories
- Support for global and user-specific categories
- Role-based access and ownership checks
- Category deletion according to project permission rules

### Expense Management

- Create, list, and retrieve expenses
- Update expenses with `PUT`
- Partially update expenses with `PATCH`
- Delete expenses
- Pagination for the expense list
- Preserve the original amount and currency
- Convert expenses into INR using exchange rates

### Budget Management

- Create and retrieve monthly budgets
- Update budgets with `PUT` or `PATCH`
- Delete budgets

### Currency Conversion

- Retrieve exchange rates from an external provider
- Store exchange rates in the database
- Cache rates for a configurable period (currently intended to be six hours)
- Return whether a rate came from cache or a live API request
- Intended fallback to a cached rate when the provider is unavailable

> The cached-rate fallback and complete expense-conversion workflow should be verified with end-to-end tests before being considered complete.

## Technology Stack

- **Language:** Python
- **Framework:** Django
- **API framework:** Django REST Framework
- **Authentication:** JWT (Simple JWT)
- **HTTP requests:** `requests`
- **Database:** `SQLite`(Default)
- **API testing:** Postman
- **Financial calculations:** Python `Decimal`

## Project Structure

```text
Expense_tracker/
├── account/
│   ├── models.py
│   ├── serializers.py
│   ├── views.py
│   └── urls.py
├── expense/
│   ├── models.py
│   ├── serializers.py
│   ├── views.py
│   └── urls.py
|   |__integrations/
│      ├── __init__.py
│      └── currency.py
├── expense_tracker
|       |___settings.py
|       |___urls.py
├──manage.py
|__README.md
|__requirements.txt

```

The `integrations/currency.py` module is a suggested location for external currency-provider calls, exchange-rate caching, and related error handling. Keep the existing app and file names if your project uses a different structure.

## API Endpoints

| Module | Method | Endpoint | Purpose |
|---|---|---|---|
| Authentication | `POST` | `/api/register/` | Register a user |
| Authentication | `POST` | `/api/login/` | Log in |
| Authentication | `POST` | `/api/logout/` | Log out |
| Authentication | `POST` | `/api/change-password/` | Change password |
| Authentication | `POST` | `/api/forgot-password/` | Request a password reset |
| Authentication | `GET` / `POST` | Reset-password URL | Validate a reset link and set a new password |
| Category | `GET`, `POST` | `/api/category/` | List and create categories |
| Expense | `GET`, `POST` | `/api/expense/` | List and create expenses |
| Single expense | `GET`, `PUT`, `PATCH`, `DELETE` | `/api/expense/<int:id>/` | Retrieve, update, or delete an expense |
| Budget | `GET`, `POST` | `/api/budget/` | List and create budgets |
| Single budget | `PUT`, `PATCH`, `DELETE` | `/api/budget/<int:id>/` | Update or delete a budget |
| Exchange rates | `GET` | Check the configured exchange-rate URL | Retrieve a currency exchange rate |
| Monthly Report | `GET` | Monthly report Total spend,category breakdown %,Budget remaining,Overspend |
| Spending Trend | `GET` | Month-over-Month total spend comparision |

## Authentication

Protected endpoints require valid authentication. With JWT authentication, obtain tokens from the login endpoint and send the access token in the request header:

```http
Authorization: Bearer {{json_web_token_12tt}}
```
## Currency Conversion

The intended currency-conversion workflow is:

1. An authenticated user submits an expense with its amount, currency, category, and date.
2. The API validates the submitted data.
3. The application retrieves the relevant exchange rate from the database cache or external provider.
4. The amount is converted into INR using `Decimal` arithmetic.
5. The original amount, original currency, and converted amount are saved.
6. The API returns the expense details.

The exchange-rate endpoint checks currency-code format, checks for a fresh cached rate, and can request rates from the Open Exchange Rates API endpoint used in this project:

```text
https://open.er-api.com/v6/latest/<SOURCE_CURRENCY>
```

For example, use `USD` as the source currency to retrieve rates including INR.

### Currency conversion implementation checklist

- [ ] Store each source/target currency pair with a unique constraint where appropriate.
- [ ] Reuse cached rates while they are fresh.
- [ ] Refresh rates older than the configured cache duration.
- [ ] Fall back to a cached rate if the provider fails and a usable cached rate exists.
- [ ] Return a clear `502` or `503` response if no usable rate is available.
- [ ] Avoid saving a partially processed expense when conversion fails.
- [ ] Update the rate's `fetched_at` timestamp when refreshing an existing record.
- [ ] Test cache hits, stale-cache refreshes, and provider failures.
- [ ] Keep currency-provider logic separate from API views, for example in `integrations/currency.py`.

## Permissions and Access Control

The project uses a custom `MyUser` model with a `role` field such as `admin` and `user`.

The intended access rules include:

- Regular users can access their own expenses and budgets, subject to endpoint-specific rules.
- Admin access is controlled by the permissions implemented for each endpoint.
- Users can access global categories and their own categories.
- Users should not be able to access other users' private records.
- Under the intended category deletion policy, admins must not delete user-owned categories.

## Installation and Setup
1. Clone or copy the project and navigate to the directory containing `manage.py`.
2. Create and activate a virtual environment.
3. Install the project's dependencies.
4. Configure environment variables.
5. Apply database migrations.
6. Start the development server.

Commands for Windows PowerShell:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install django djangorestframework djangorestframework-simplejwt requests
python manage.py makemigrations
python manage.py migrate
python manage.py runserver
```

This repository contains `requirements.txt` install dependencies from it:

```powershell
pip install -r requirements.txt
```

## Testing with Postman

Use Postman to test each endpoint. For protected endpoints, include the JWT access token.

Recommended test cases:
- Successful registration and login
- Invalid credentials and invalid input
- Logout and password-management flows
- Category creation, listing, and deletion permissions
- Expense creation, retrieval, update, and deletion
- Access to another user's expense
- Expense-list pagination
- Budget CRUD operations and ownership checks
- Fresh cache hit
- Stale cache refresh
- External API timeout or error
- Cached-rate fallback when the provider is unavailable
- Failure without a usable cached rate

## Current Project Status

Completed and tested with Postman:

- Registration, login, logout, change-password, and forgot-password APIs
- Category CRUD functionality implemented for the required endpoints
- Expense CRUD functionality
- Budget CRUD functionality
- Pagination on the expense list API

Currency conversion, cache refresh, fallback behavior, and full expense-creation integration should be verified end to end.
