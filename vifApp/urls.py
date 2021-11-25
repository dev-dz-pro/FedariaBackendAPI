from django.urls import path, include
from .views import (RegisterView, LoginView, HomeView,
                    SettingsView, ProfileView, EmailVerifyView, 
                    ResetPasswordView, NewPassView, ProfileInfoUpdate, EmailVerifyResendView, Google_SocAuthTest, Gitlab_SocAuthTest,
                    ProfileImageUpdate, SettingsInfoUpdate, TokenRefreshView, ProfileSetCompanyUpdate, Github_SocAuthTest)


urlpatterns = [
    path('register/', RegisterView.as_view(), name="register"),
    path('login/', LoginView.as_view(), name="login"),
    path('home/', HomeView.as_view()),

    path('token/refresh/', TokenRefreshView.as_view()),

    path('profile/', ProfileView.as_view()),
    path('profile/set_info/', ProfileInfoUpdate.as_view()), 
    path('profile/set_img/', ProfileImageUpdate.as_view()),
    path('profile/set_company/', ProfileSetCompanyUpdate.as_view()),
    
    path('settings/', SettingsView.as_view()),
    path('settings/set_info/', SettingsInfoUpdate.as_view()),
    
    path('email-verify/', EmailVerifyView.as_view(), name="email-verify"),
    path('email-verify-resend/', EmailVerifyResendView.as_view(), name="email-verify-resend"),

    path('password/reset/', ResetPasswordView.as_view(), name='password-reset'),
    path('password/reset/confirm/', NewPassView.as_view(), name="pass-email-verify"),
    
    path('social_auth_google/', Google_SocAuthTest.as_view(), name="social-auth-google"),
    path('social_auth_github/', Github_SocAuthTest.as_view(), name="social-auth-github"),
    path('social_auth_gitlab/', Gitlab_SocAuthTest.as_view(), name="social-auth-gitlab"),
    

    path('dash/', include('kanban.urls')),
] 

