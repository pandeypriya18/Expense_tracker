from django.urls import path
from account.views import RegisterView,LoginView,LogoutView,ChangePasswordView ,ForgetPasswordView ,MeView,ResetPasswordView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('change-password/',ChangePasswordView.as_view() , name="change-password"),
    path('forget-password/',ForgetPasswordView.as_view(),name='forget-password'),
    path('me/',MeView.as_view() ,name='me'),
    path('reset-password/<str:uid>/<str:token>/',ResetPasswordView.as_view(),name="reset-password"),
    path("token/",TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("token/refresh/",TokenRefreshView.as_view(), name="token_refresh"),
]

