from django.urls import path
from .views import (RegisterView, LoginView, LogoutView,
                    SettingsView, ProfileView, EmailVerifyView, 
                    ChangePasswordView, ResetPasswordView, 
                    ResetPassEmailVerifyView)

urlpatterns = [
    path('register/', RegisterView.as_view(), name="register"),
    path('login/', LoginView.as_view(), name="login"),
    path('profile/', ProfileView.as_view()),
    path('settings/', SettingsView.as_view()),
    path('logout/', LogoutView.as_view()),
    path('email-verify/', EmailVerifyView.as_view(), name="email-verify"),
    path('change-password/', ChangePasswordView.as_view(), name='change-password'),
    path('password_reset/', ResetPasswordView.as_view(), name='password-reset'),
    path('pass_reset_email_verify/', EmailVerifyView.as_view(), name="pass-email-verify"),
]