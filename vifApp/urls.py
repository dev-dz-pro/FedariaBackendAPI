from django.urls import path, include

from .views import (RegisterView, LoginView, LogoutView, HomeView,
                    SettingsView, ProfileView, EmailVerifyView, 
                    ResetPasswordView, NewPassView)  # ChangePasswordView Gitcredit IndexView

urlpatterns = [
    path('register/', RegisterView.as_view(), name="register"),
    path('login/', LoginView.as_view(), name="login"),
    path('home/', HomeView.as_view()),
    path('profile/', ProfileView.as_view()),
    path('settings/', SettingsView.as_view()),
    path('logout/', LogoutView.as_view()),
    path('email-verify/', EmailVerifyView.as_view(), name="email-verify"),
    
    # path('change-password/', ChangePasswordView.as_view(), name='change-password'),  # this zill chqnge the pqsszord
    path('password/reset/', ResetPasswordView.as_view(), name='password-reset'),
    path('password/reset/confirm/', NewPassView.as_view(), name="pass-email-verify"),

    path('github-auth/', include('social_django.urls', namespace='social')), 
    # path('github-auth/complete/github/', Gitcredit.as_view()),
    # path('index/', IndexView.as_view()),
]