from django.http import response
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import AuthenticationFailed
from .serializers import (UserSerializer, ChangePasswordSerializer, ResetPasswordSerializer, 
                            UpdateProfileSerializer, UpdateProfileImageSerializer, LoginSerializer)
from .models import User, UserNotification
import jwt, datetime
from .utils import VifUtils
from django.contrib.sites.shortcuts import get_current_site
from django.urls import reverse
from rest_framework import status
from django.conf import settings
import requests
import random
from threading import Thread

class RegisterView(APIView):
    def post(self, request):
        username = generate_username(request.data["first_name"])
        request.data["username"] = username
        
        serializer = UserSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        user_data = serializer.data
        user = User.objects.get(email=user_data["email"])
        payload = {
            'id': user.id,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=5),
            'iat': datetime.datetime.utcnow()
        }
        token = jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')
        domain = get_current_site(request)
        relativelink = reverse("email-verify")
        absurl = 'http://'+str(domain)+relativelink+'?token='+token
        email_body = 'Hi '+ user.first_name + ' Use the link below to verify your email\n' + absurl
        data = {'email_body': email_body, 'email_subject': 'Verify your email', "to_email": user.email}
        Thread(target=VifUtils.send_email, args=(data,)).start()
        response = {
                'status': 'success',
                'code': status.HTTP_200_OK,
                'message': 'Email was sent to you, please verify your email to activate your account.',
                'data': [user_data]
            }
        return Response(response)


class EmailVerifyView(APIView):
    def get(self, request):
        token = request.GET["token"]
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
            user = User.objects.get(id=payload["id"])
            UserNotification.objects.create(notification_user=user, notification_text="welcome to vifbox, your account is verified",
                                        notification_from="Vifbox", notification_url="to_url/")
            if not user.is_verified:
                user.is_verified = True
                user.save()
            response = {
                'status': 'success',
                'code': status.HTTP_200_OK,
                'message': 'Email Successfuly activated',
                'data': []
            }
            return Response(response)
        except jwt.ExpiredSignatureError:
            raise AuthenticationFailed('Token expired!')



class LoginView(APIView):
    def post(self, request):

        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user_data = serializer.data
        email = user_data['email']
        password = user_data['password']
        remember_me = user_data['remember_me']

        if str(email).__contains__("@"):
            user = User.objects.filter(email=email).first()
        else:
            user = User.objects.filter(username=email).first()
        if user is None:
            raise AuthenticationFailed('User not found!')
        if not user.check_password(password):
            raise AuthenticationFailed('Incorrect password!')
        payload = {
            'id': user.id,
            'iat': datetime.datetime.utcnow()
        }
        response = Response()
        if remember_me: 
            payload['exp'] = datetime.datetime.utcnow() + datetime.timedelta(days=7)
        else:
            payload['exp'] = datetime.datetime.utcnow() + datetime.timedelta(minutes=90)
        token = jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')
        response.set_cookie(key='jwt', value=token, httponly=True)
        response.data = {'jwt': token}
        return response



class HomeView(APIView):
    def get(self, request):
        payload = permission_authontication_jwt(request) # print(reverse('social:begin', kwargs={'backend':'github'}))
        user = User.objects.filter(id=payload['id']).first()
        serializer = UserSerializer(user)
        return Response(serializer.data)



class ProfileView(APIView):

    def get(self, request):
        payload = permission_authontication_jwt(request)
        user = User.objects.filter(id=payload['id']).first()
        notification = UserNotification.objects.filter(notification_user=user)
        kys = ("from", "desc", "url", "date") 
        notf = [{kys[0]: f"{nt.notification_from}", kys[1]: f"{nt.notification_text}", kys[2]: f"{nt.notification_url}", kys[3]: f"{nt.created_at}"} for nt in notification] 
        response = {
            'status': 'success',
            'code': status.HTTP_200_OK,
            'data': {
                "name": f"{user.first_name}",
                "username": f"{user.username}",
                "profile_img_url": f"{user.profile_image}",
                "email": f"{user.email}",
                "phone_number": f"{user.phone_number}",
                "notification": notf
            }
        }
        return Response(response)


class ProfileInfoUpdate(APIView):
    def post(self, request):
        payload = permission_authontication_jwt(request)
        user = User.objects.filter(id=payload['id']).first()
        serializer = UpdateProfileSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            user_data = serializer.data
            user.first_name = user_data["name"]
            user_exist = User.objects.filter(username=user_data["username"])
            if not user_exist:
                user.username = user_data["username"]
                user.phone_number = user_data["phone"]
                user.save()
                response = {
                    'status': 'success',
                    'code': status.HTTP_200_OK,
                    'message': 'Profile info updated successfully',
                    'data': []
                }
            else:
                response = {
                    'code': status.HTTP_500_INTERNAL_SERVER_ERROR,
                    'message': 'username exists'
                }
            return Response(response)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ProfileImageUpdate(APIView):
    def post(self, request):
        payload = permission_authontication_jwt(request)
        user = User.objects.filter(id=payload['id']).first()
        serializer = UpdateProfileImageSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            user_data = serializer.data
            user.profile_image = user_data["profile_img_url"]
            user.profile_title = user_data["profile_title"]
            user.save()
            response = {
                'status': 'success',
                'code': status.HTTP_200_OK,
                'message': 'Profile image updated successfully',
                'data': []
            }
            return Response(response)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



class SettingsView(APIView):
    def get(self, request):
        payload = permission_authontication_jwt(request)
        user = User.objects.filter(id=payload['id']).first()
        notification = UserNotification.objects.filter(notification_user=user)
        kys = ("from", "desc", "url", "date") 
        notf = [{kys[0]: f"{nt.notification_from}", kys[1]: f"{nt.notification_text}", kys[2]: f"{nt.notification_url}", kys[3]: f"{nt.created_at}"} for nt in notification] 
        response = {
            'status': 'success',
            'code': status.HTTP_200_OK,
            'data': {
                "name": f"{user.first_name}",
                "username": f"{user.username}",
                "profile_img_url": f"{user.profile_image}",
                "is_verified": f"{user.is_verified}",
                "notification": notf
            }
        }
        return Response(response)


class SettingsInfoUpdate(APIView):
    def post(self, request):
        payload = permission_authontication_jwt(request)
        user = User.objects.filter(id=payload['id']).first()
        serializer = ChangePasswordSerializer(data=request.data)
        if serializer.is_valid():
            if not user.check_password(serializer.data.get("old_password")):
                return Response({"old_password": ["Wrong password."]}, status=status.HTTP_400_BAD_REQUEST)
            if serializer.data.get("new_password") == serializer.data.get("new_password1"):
                user.set_password(serializer.data.get("new_password"))
                user.save()
            else:
                return Response({"error": "password not match"})
            response = {
                'status': 'success',
                'code': status.HTTP_200_OK,
                'message': 'Password updated successfully',
                'data': []
            }
            return Response(response)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



class LogoutView(APIView):
    def post(self, request):
        response = Response()
        response.delete_cookie('jwt')
        response.data = {
            'status': 'success',
            'code': status.HTTP_200_OK,
            'message': 'Logged out successfully',
            'data': []
        }
        return response


class ResetPasswordView(APIView):
    def post(self, request):
        payload = permission_authontication_jwt(request)
        user = User.objects.filter(id=payload['id']).first()
        serializer = ResetPasswordSerializer(data=request.data)
        if serializer.is_valid():
            if request.data["email"] == user.email:
                payload = {
                    'id': user.id,
                    'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=5),
                    'iat': datetime.datetime.utcnow()
                }
                token = jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')
                domain = get_current_site(request)
                relativelink = reverse("pass-email-verify")
                absurl = 'http://'+str(domain)+relativelink+'?token='+token  # route for front end (view of new pass and its confirmation)
                email_body = 'Hi '+ user.first_name + ' Use the link below to Change your password\n' + absurl
                data = {'email_body': email_body, 'email_subject': 'Verify your email', "to_email": user.email}
                Thread(target=VifUtils.send_email, args=(data,)).start()
                response = {
                    'status': 'success',
                    'code': status.HTTP_200_OK,
                    'message': 'email sent to reset password, will expire after 5 min',
                    'data': []
                }
                return Response(response)
            else:
                response = {
                    'status': 'error',
                    'message': 'Please enter your email'
                }
                return Response(response)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class NewPassView(APIView):
    def post(self, request):
        token = request.GET["token"]
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
            user = User.objects.get(id=payload["id"])
            new_pass = request.data["new_pass"]
            confirm_pass = request.data["confirm_new_pass"]
            if new_pass == confirm_pass:
                user.set_password(confirm_pass)
                user.save()
                response = {
                        'status': 'success',
                        'code': status.HTTP_200_OK,
                        'message': 'Password updated'
                }
                return Response(response) 
            else:
                return Response({"error": "Passwords not match"})
        except jwt.ExpiredSignatureError:
            raise AuthenticationFailed('Token expired!')
    

class GithubInfo(APIView):
    def get(self, request):
        token = request.COOKIES.get('gitsk')
        endpoint = "https://api.github.com/user"
        headers = {"Authorization": f"Bearer {token}"}
        githubuser_data = requests.get(endpoint, headers=headers).json()
        githubuser_id = githubuser_data["id"]
        github_user = User.objects.filter(github_id=githubuser_id)
        if not github_user:
            username = generate_username(githubuser_data["login"])
            user = User.objects.create_user(username=username, github_id=githubuser_id)
            if not user.is_verified:
                user.is_verified = True
                user.save()
        payload = {
            'id': github_user.first().id,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=90),
            'iat': datetime.datetime.utcnow()
        }
        token = jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')
        response = Response()
        response.set_cookie(key='jwt', value=token, httponly=True)
        response.data = {'jwt': token}
        return response  


def permission_authontication_jwt(request):
    token = request.COOKIES.get('jwt')
    if not token:
        raise AuthenticationFailed('Unauthenticated!')
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        raise AuthenticationFailed('Unauthenticated!')
    return payload


def generate_username(name):
    return name + str(random.randint(10000, 99999))







# def permission_authontication_jwt_reset_pass(request):
#     token = request.COOKIES.get('jwttoken')
#     if not token:
#         raise AuthenticationFailed('Unauthenticated!')
#     try:
#         payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
#     except jwt.ExpiredSignatureError:
#         raise AuthenticationFailed('Unauthenticated!')
#     return payload


# class NewPassView(APIView):
# def get(self, request):
#     token = request.GET["token"]
#     try:
#         payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
#         user = User.objects.get(id=payload["id"])
#         if not user.is_verified:
#             user.is_verified = True
#             user.save()
#         response = {
#                 'status': 'success',
#                 'code': status.HTTP_200_OK,
#                 'message': 'Email Verified for changing password',
#                 'data': []
#         }
#         return Response(response)  # you should redirect to change password page if response is sucessfull
#     except jwt.ExpiredSignatureError:
#         raise AuthenticationFailed('Unauthenticated!')

# class ResetPasswordView(APIView):
#     def post(self, request):
#         payload = permission_authontication_jwt(request)
#         user = User.objects.filter(id=payload['id']).first()
#         serializer = ResetPasswordSerializer(data=request.data)
#         if serializer.is_valid():
#             if request.data["email"] == user.email:
#                 payload = {
#                     'id': user.id,
#                     'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=5),
#                     'iat': datetime.datetime.utcnow()
#                 }
#                 token = jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')
#                 response = Response()
#                 response.set_cookie(key='jwt-conf-pass', value=token, httponly=True)
#                 response = {
#                     'status': 'success',
#                     'code': status.HTTP_200_OK
#                 }
#                 return Response(response)
#             else:
#                 return Response({"error": "email not match"})
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# class NewPassView(APIView):
#     def post(self, request):
#         payload = permission_authontication_jwt(request)
#         user = User.objects.filter(id=payload['id']).first()
#         new_pass = request.data["new_pass"]
#         confirm_pass = request.data["confirm_new_pass"]
#         if new_pass == confirm_pass:
#             user.set_password(confirm_pass)
#             user.save()
#             response = {
#                     'status': 'success',
#                     'code': status.HTTP_200_OK,
#                     'message': 'Password updated'
#             }
#             return Response(response) 
#         else:
#             return Response({"error": "Passwords not match"})

# class ChangePasswordView(APIView):
#     def post(self, request):
#         payload = permission_authontication_jwt(request)
#         user = User.objects.filter(id=payload['id']).first()
#         serializer = ChangePasswordSerializer(data=request.data)
#         if serializer.is_valid():
#             if not user.check_password(serializer.data.get("old_password")):
#                 return Response({"old_password": ["Wrong password."]}, status=status.HTTP_400_BAD_REQUEST)
#             user.set_password(serializer.data.get("new_password"))
#             user.save()
#             response = {
#                 'status': 'success',
#                 'code': status.HTTP_200_OK,
#                 'message': 'Password updated successfully',
#                 'data': []
#             }
#             return Response(response)
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# class IndexView(APIView):
#     def get(self, request):
#         token = request.COOKIES.get('dotcom_user')
#         print(token)
#         return Response({})

# class AUTHORIZE(APIView):
#     def get(self, request):
#         print(request.data)
#         return Response({})
   