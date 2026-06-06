from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    RegisterView, LoginView, LogoutView, ProfileView,
    ForgotPasswordView, VerifyOTPView, ResetPasswordView,
    ChangePasswordView, ListUsersView,
    GetCaptchaView, VerifyCaptchaView,
)

urlpatterns = [
    path('register/',        RegisterView.as_view()),
    path('login/',           LoginView.as_view()),
    path('logout/',          LogoutView.as_view()),
    path('token/refresh/',   TokenRefreshView.as_view()),
    path('profile/',         ProfileView.as_view()),
    path('change-password/', ChangePasswordView.as_view()),
    path('forgot-password/', ForgotPasswordView.as_view()),
    path('verify-otp/',      VerifyOTPView.as_view()),
    path('reset-password/',  ResetPasswordView.as_view()),
    path('users/',           ListUsersView.as_view()),
    path('captcha/',         GetCaptchaView.as_view()),
    path('captcha/verify/',  VerifyCaptchaView.as_view()),
]