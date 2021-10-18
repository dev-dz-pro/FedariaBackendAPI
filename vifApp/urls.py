from django.urls import path, include
from .views import (RegisterView, LoginView, HomeView,
                    SettingsView, ProfileView, EmailVerifyView, 
                    ResetPasswordView, NewPassView, ProfileInfoUpdate, EmailVerifyResendView, SocAuthTest,
                    ProfileImageUpdate, SettingsInfoUpdate, SocialAuth, TokenRefreshView, ProfileSetCompanyUpdate)


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

    # path('github-auth/', GithubInfo.as_view(), name="github-info"),
    path('social_auth/', SocialAuth.as_view(), name="social-auth"),

    
    path('social_auth_test/', SocAuthTest.as_view(), name="social-auth-test"),
    

    path('dash/', include('kanban.urls')),
] 

