from django.urls import path, include
from . import views


urlpatterns = [
    path('register/', views.RegisterView.as_view(), name="register"),
    path('login/', views.LoginView.as_view(), name="login"),
    path('home/', views.HomeView.as_view()),

    path('user/notifications/', views.GetUserNotifications.as_view(), name="user-notification"),
    path('user/change_status/', views.ChangeUserStatus.as_view(), name="change-status"),
    path('user/update_account/', views.UpdateAccount.as_view()),
    path('user/update_pic/', views.AccountImageUpdate.as_view()),
    
    path('user/account/', views.AccountView.as_view()),

    path('token/refresh/', views.TokenRefreshView.as_view()),

    path('profile/', views.ProfileView.as_view()),
    path('profile/set_info/', views.ProfileInfoUpdate.as_view()), 
    path('profile/set_img/', views.ProfileImageUpdate.as_view()),
    path('profile/set_company/', views.ProfileSetCompanyUpdate.as_view()),
    
    path('settings/', views.SettingsView.as_view()),
    path('settings/set_info/', views.SettingsInfoUpdate.as_view()),

    
    
    path('email-verify/', views.EmailVerifyView.as_view(), name="email-verify"),
    path('email-verify-resend/', views.EmailVerifyResendView.as_view(), name="email-verify-resend"),

    path('password/reset/', views.ResetPasswordView.as_view(), name='password-reset'),
    path('password/reset/confirm/', views.NewPassView.as_view(), name="pass-email-verify"),
    
    path('social_auth_google/', views.Google_SocAuthTest.as_view(), name="social-auth-google"),
    path('social_auth_github/', views.Github_SocAuthTest.as_view(), name="social-auth-github"),
    path('social_auth_gitlab/', views.Gitlab_SocAuthTest.as_view(), name="social-auth-gitlab"),
    

    path('dash/', include('kanban.urls')),
] 

