from django.urls import path, include
from . import views


urlpatterns = [
    path('accounts/register/', views.RegisterView.as_view(), name="register"),
    path('accounts/login/', views.LoginView.as_view(), name="login"),
    path('accounts/social_auth_google/', views.Google_SocAuthTest.as_view(), name="social-auth-google"),
    path('accounts/social_auth_github/', views.Github_SocAuthTest.as_view(), name="social-auth-github"),
    path('accounts/social_auth_gitlab/', views.Gitlab_SocAuthTest.as_view(), name="social-auth-gitlab"),


    path('user/notifications/', views.GetUserNotifications.as_view(), name="user-notification"),
    path('user/change_status/', views.ChangeUserStatus.as_view(), name="change-status"),
    path('user/update_account/', views.UpdateAccount.as_view()),
    path('user/update_settings/', views.UpdateSettings.as_view()),
    path('user/update_pic/', views.AccountImageUpdate.as_view()),
    path('user/account/', views.AccountView.as_view()),


    path('user/account/inbox/', views.EmailInboxList.as_view()),
    path('user/account/inbox/message/', views.EmailInbox.as_view()),
    path('user/account/inbox/send/', views.SendEmailInbox.as_view()),

    path('user/account/minbox/', views.MEmailInboxList.as_view()), 
    path('user/account/minbox/message/', views.MEmailInbox.as_view()), 
    path('user/account/minbox/send/', views.MSendEmailInbox.as_view()),
    


    path('token/refresh/', views.TokenRefreshView.as_view()),

    
    path('email_verify/', views.EmailVerify.as_view(), name="email-verify"),
    path('email_verify/resend/', views.EmailVerifyResend.as_view(), name="email-verify-resend"),

    path('reset_password/verify_email/', views.ResetPasswordMailLinkVerify.as_view(), name='password-reset-email-verify'),
    path('reset_password/', views.NewPass.as_view(), name="reset-password"),
    

    path('dash/', include('kanban.urls')),
] 



# path('home/', views.HomeView.as_view()),
# path('profile/', views.ProfileView.as_view()),
# path('profile/set_info/', views.ProfileInfoUpdate.as_view()), 
# path('profile/set_img/', views.ProfileImageUpdate.as_view()),
# path('profile/set_company/', views.ProfileSetCompanyUpdate.as_view()),
# path('settings/', views.SettingsView.as_view()),