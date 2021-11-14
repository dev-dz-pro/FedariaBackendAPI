from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import AuthenticationFailed
from .models import User, UserNotification
import jwt
import time
import os
import boto3
import datetime
from .utils import VifUtils
from rest_framework import status
from django.conf import settings
import requests
from threading import Thread
from urllib.parse import parse_qs
from .serializers import (UserSerializer, ChangePasswordSerializer, ResetPasswordSerializer, 
                        UpdateProfileSerializer, UpdateProfileImageSerializer, LoginSerializer, CompanySerializer)


UNAUTHONTICATED = 'Unauthenticated!'
EMAIL_VERIFICATION_MESSAGE = 'Email was sent to you, please verify your email to activate your account.'


class RegisterView(APIView): 
    def post(self, request):
        username =  VifUtils.generate_username(request.data["first_name"]) # request.data["first_name"] + request.data["last_name"] + "_" + request.data["email"].split("@")[0]
        request.data["username"] = username
        request.data["name"] = request.data["first_name"] + " " + request.data["last_name"]
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
        else:
            err = list(serializer.errors.items())
            response = {
                'status': 'error',
                'code': status.HTTP_400_BAD_REQUEST,
                'message': '(' + err[0][0] + ') ' + err[0][1][0]
            }
            return Response(response, status.HTTP_400_BAD_REQUEST)
        user_data = serializer.data
        user = User.objects.get(email=user_data["email"])
        payload = {
            'id': user.id,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=5),
            'iat': datetime.datetime.utcnow()
        }
        token = jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')
        absurl = os.environ.get("front_domain") + "/verify-email/?token=" + token # will add it to var inv
        email_body = 'Hi '+ user.name + ', Click the link below to verify your email\n' + absurl
        data = {'email_body': email_body, 'email_subject': 'Vifbox account activation', "to_email": [user.email]}
        Thread(target=VifUtils.send_email, args=(data,)).start()
        response = {
                'status': 'success',
                'code': status.HTTP_200_OK,
                'message': EMAIL_VERIFICATION_MESSAGE,
                'info': user_data
            }
        return Response(response)
        


class EmailVerifyResendView(APIView):
    def get(self, request):
        payload = permission_authontication_jwt(request)
        user = User.objects.filter(id=payload['id']).first()
        payload = {
            'id': user.id,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=5),
            'iat': datetime.datetime.utcnow()
        }
        token = jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')
        absurl = os.environ.get("front_domain") + "/verify-email/?token=" + token 
        email_body = 'Hi '+ user.name + ' Use the link below to verify your email\n' + absurl
        data = {'email_body': email_body, 'email_subject': 'Verify your email', "to_email": [user.email]}
        Thread(target=VifUtils.send_email, args=(data,)).start()
        response = {
                'status': 'success',
                'code': status.HTTP_200_OK,
                'message': EMAIL_VERIFICATION_MESSAGE
            }
        return Response(response)



class EmailVerifyView(APIView):
    def get(self, request):
        token = request.GET["token"]
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
            user = User.objects.get(id=payload["id"])
            
            if not user.is_verified:
                user.is_verified = True
                user.save()
                UserNotification.objects.create(notification_user=user, 
                                                notification_text="welcome to vifbox, your account is verified",
                                                notification_from="Vifbox", notification_url="to_url/")
                response = {
                    'status': 'success',
                    'code': status.HTTP_200_OK,
                    'message': 'Email Successfuly activated',
                    'data': []
                }
            else:
                response = {'message': 'Email already activated'}
            return Response(response)
        except jwt.DecodeError:
            response = {
                'status': 'error',
                'code': status.HTTP_403_FORBIDDEN,
                'message': 'Token Expired!'
            }
            raise AuthenticationFailed(response)
        except jwt.ExpiredSignatureError:
            response = {
                'status': 'error',
                'code': status.HTTP_403_FORBIDDEN,
                'message': UNAUTHONTICATED
            }
            raise AuthenticationFailed(response)



class LoginView(APIView):
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if not serializer.is_valid():
            err = list(serializer.errors.items())
            response = {
                'status': 'error',
                'code': status.HTTP_400_BAD_REQUEST,
                'message': '(' + err[0][0] + ') ' + err[0][1][0]
            }
            return Response(response, status.HTTP_400_BAD_REQUEST)

        user_data = serializer.data
        email = user_data['email']
        password = user_data['password']

        if str(email).__contains__("@"):
            user = User.objects.filter(email=email).first()
        else:
            user = User.objects.filter(username=email).first()
        if user is None:
            response = {
                'status': 'error',
                'code': status.HTTP_400_BAD_REQUEST,
                'message': "user not found!"
            }
            return Response(response, status.HTTP_400_BAD_REQUEST)
        if not user.check_password(password):
            response = {
                'status': 'error',
                'code': status.HTTP_400_BAD_REQUEST,
                'message': "incorrect password!"
            }
            return Response(response, status.HTTP_400_BAD_REQUEST)
        payload_access = {
            'id': user.id,
            'iat': datetime.datetime.utcnow(),
            'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=5)
        }
        payload_refresh = {
            'id': user.id,
            'iat': datetime.datetime.utcnow(),
            'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)
        }
        access_token = jwt.encode(payload_access, settings.SECRET_KEY, algorithm='HS256')
        refresh_token = jwt.encode(payload_refresh, settings.SECRET_KEY+settings.SECRET_REFRESH_KEY, algorithm='HS256')
        return Response({"access": access_token, "refresh": refresh_token})



class TokenRefreshView(APIView):
    def post(self, request):
        refresh = request.data["refresh"]
        if not refresh:
            response = {
                'status': 'error',
                'code': status.HTTP_403_FORBIDDEN,
                'message': 'Please login!'
            }
            raise AuthenticationFailed(response)
        try:
            payload = jwt.decode(refresh, settings.SECRET_KEY+settings.SECRET_REFRESH_KEY, algorithms=["HS256"])
        except jwt.ExpiredSignatureError:
            response = {
                'status': 'error',
                'code': status.HTTP_403_FORBIDDEN,
                'message': UNAUTHONTICATED
            }
            raise AuthenticationFailed(response)
        except jwt.DecodeError:
            response = {
                'status': 'error',
                'code': status.HTTP_403_FORBIDDEN,
                'message': 'invalid refresh token, please login!'
            }
            raise AuthenticationFailed(response)
        payload_access = {
            'id': payload["id"],
            'iat': datetime.datetime.utcnow(),
            'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=5)
        }
        access_token = jwt.encode(payload_access, settings.SECRET_KEY, algorithm='HS256')
        return Response({"access": access_token})



class HomeView(APIView):
    def get(self, request):
        payload = permission_authontication_jwt(request) # reverse('social:begin', kwargs={'backend':'github'})
        user = User.objects.filter(id=payload['id']).first()
        serializer = UserSerializer(user)
        return Response(serializer.data)


class Github_SocAuthTest(APIView):
    def get(self, request):
        code = request.META['HTTP_AUTHORIZATION'].split(' ')[1]
        endpoint = "https://github.com/login/oauth/access_token"
        data = {"code": code,
                "client_id": settings.GITHUB_CLIENT_ID,
                "client_secret": settings.GITHUB_SECRET_KEY,
                "redirect_uri": "http://localhost:3000/social_auth"}
        social_res = requests.post(endpoint, data=data)
        if 'error' in parse_qs(social_res.text):
            response = {'status': 'error', 'code': status.HTTP_400_BAD_REQUEST, 'message': 'bad verification code'}
            return Response(response, status.HTTP_400_BAD_REQUEST)
        else:
            access_token = parse_qs(social_res.text)['access_token'][0]

        endpoint_user = "https://api.github.com/user"
        endpoint_email = "https://api.github.com/user/emails"
        headers = {"Authorization": f"token {access_token}"}
        user_info = requests.get(endpoint_user, headers=headers)
        githubuser_data = user_info.json()
        user_email = requests.get(endpoint_email, headers=headers)
        githubuser_data_email = user_email.json()[0]
        if user_info.status_code <= 200 and user_email.status_code <= 200:
            social_user = User.objects.filter(email=githubuser_data_email["email"], social_id=githubuser_data["id"]).first()
            if not social_user:
                username =  VifUtils.generate_username(githubuser_data["login"])
                try:
                    social_user = User.objects.create(email=githubuser_data_email["email"], social_id=githubuser_data["id"], 
                                                            username=username, profile_image=githubuser_data["avatar_url"],
                                                            is_verified=githubuser_data_email["verified"])
                except Exception as e:
                    response = {'status': 'error', 'code': status.HTTP_400_BAD_REQUEST, 'message': 'Email already exists, please signin.'}
                    return Response(response, status.HTTP_400_BAD_REQUEST)
            payload_access = {
                'id': social_user.id,
                'iat': datetime.datetime.utcnow(),
                'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=5)
            }
            payload_refresh = {
                'id': social_user.id,
                'iat': datetime.datetime.utcnow(),
                'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)
            }
            access_token = jwt.encode(payload_access, settings.SECRET_KEY, algorithm='HS256')
            refresh_token = jwt.encode(payload_refresh, settings.SECRET_KEY+settings.SECRET_REFRESH_KEY, algorithm='HS256')
            return Response({"access": access_token, "refresh": refresh_token})
        else:
            response = {'status': 'error', 'code': status.HTTP_400_BAD_REQUEST, 'message': 'Request is missing required authentication'}
            return Response(response, status.HTTP_400_BAD_REQUEST)

class Gitlab_SocAuthTest(APIView):
    def get(self, request):
        code = request.META['HTTP_AUTHORIZATION'].split(' ')[1]
        endpoint = "https://gitlab.com/oauth/token"
        data = {"code": code,
                "client_id": settings.GITLAB_CLIENT_ID,
                "client_secret": settings.GITLAB_SECRET_KEY,
                "grant_type": "authorization_code",
                "redirect_uri": "http://localhost:3000/social_auth"}
        social_res = requests.post(endpoint, data=data).json()
        if 'error' in social_res:
            response = {'status': 'error', 'code': status.HTTP_400_BAD_REQUEST, 'message': 'bad verification code'}
            return Response(response, status.HTTP_400_BAD_REQUEST)
        else:
            access_token = social_res["access_token"]
        endpoint_user = "https://gitlab.com/api/v4/user"
        headers = {"Authorization": f"Bearer {access_token}"}
        user_info = requests.get(endpoint_user, headers=headers)
        gitlabuser_data = user_info.json()
        if user_info.status_code <= 200:
            social_user = User.objects.filter(email=gitlabuser_data["email"], social_id=gitlabuser_data["id"]).first()
            if not social_user:
                username =  VifUtils.generate_username(gitlabuser_data["username"])
                try:
                    social_user = User.objects.create(email=gitlabuser_data["email"], social_id=gitlabuser_data["id"], 
                                                            username=username, profile_image=gitlabuser_data["avatar_url"])
                except Exception as e:
                    response = {'status': 'error', 'code': status.HTTP_400_BAD_REQUEST, 'message': 'Email already exists, please signin.'}
                    return Response(response, status.HTTP_400_BAD_REQUEST)
            payload_access = {
                'id': social_user.id,
                'iat': datetime.datetime.utcnow(),
                'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=5)
            }
            payload_refresh = {
                'id': social_user.id,
                'iat': datetime.datetime.utcnow(),
                'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)
            }
            access_token = jwt.encode(payload_access, settings.SECRET_KEY, algorithm='HS256')
            refresh_token = jwt.encode(payload_refresh, settings.SECRET_KEY+settings.SECRET_REFRESH_KEY, algorithm='HS256')
            return Response({"access": access_token, "refresh": refresh_token})
        else:
            response = {'status': 'error', 'code': status.HTTP_400_BAD_REQUEST, 'message': 'Request is missing required authentication'}
            return Response(response, status.HTTP_400_BAD_REQUEST)


class Google_SocAuthTest(APIView):
    def get(self, request):
        access_token = request.META['HTTP_AUTHORIZATION'].split(' ')[1]
        endpoint = "https://www.googleapis.com/oauth2/v2/userinfo"
        headers = {"Authorization": f"Bearer {access_token}"}
        social_res = requests.get(endpoint, headers=headers)
        githubuser_data = social_res.json()
        if social_res.status_code <= 200:
            social_user = User.objects.filter(email=githubuser_data["email"], social_id=githubuser_data["id"]).first()
            if not social_user:
                username =  VifUtils.generate_username("vifbox_GGL")
                try:
                    social_user = User.objects.create(email=githubuser_data["email"], social_id=githubuser_data["id"], 
                                                            username=username, profile_image=githubuser_data["picture"],
                                                            is_verified=githubuser_data["verified_email"])
                except Exception as e:
                    response = {'status': 'error', 'code': status.HTTP_400_BAD_REQUEST, 'message': 'Email already exists, please signin.'}
                    return Response(response, status.HTTP_400_BAD_REQUEST)
            payload_access = {
                'id': social_user.id,
                'iat': datetime.datetime.utcnow(),
                'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=5)
            }
            payload_refresh = {
                'id': social_user.id,
                'iat': datetime.datetime.utcnow(),
                'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)
            }
            access_token = jwt.encode(payload_access, settings.SECRET_KEY, algorithm='HS256')
            refresh_token = jwt.encode(payload_refresh, settings.SECRET_KEY+settings.SECRET_REFRESH_KEY, algorithm='HS256')
            return Response({"access": access_token, "refresh": refresh_token})
        else:
            response = {'status': 'error', 'code': status.HTTP_400_BAD_REQUEST, 'message': 'Request is missing required authentication credent…ogle.com/identity/sign-in/web/devconsole-project.'}
            return Response(response, status.HTTP_400_BAD_REQUEST)

class ProfileView(APIView):
    def get(self, request):
        payload = permission_authontication_jwt(request)
        user = User.objects.filter(id=payload['id']).first()
        notification = UserNotification.objects.filter(notification_user=user)
        prf_img = user.get_presigned_url_img() 
        if user.profile_image != prf_img:
            user.profile_image = prf_img
            user.save()
        kys = ("from", "desc", "url", "date") 
        notf = [{kys[0]: nt.notification_from, kys[1]: nt.notification_text, kys[2]: nt.notification_url, kys[3]: nt.created_at} for nt in notification] 
        response = {
            'status': 'success',
            'code': status.HTTP_200_OK,
            'data': {
                "name": user.name,
                "username": user.username,
                "profile_img_url": prf_img,
                "profile_title": user.profile_title,
                "email": user.email,
                "phone_number": str(user.phone_number),
                "company_email": user.company_email,
                "company_name": user.company_name,
                "notification": notf
            }
        }
        return Response(response)


class ProfileInfoUpdate(APIView):
    def put(self, request):
        payload = permission_authontication_jwt(request)
        user = User.objects.filter(id=payload['id']).first()
        serializer = UpdateProfileSerializer(data=request.data)
        if serializer.is_valid():
            user_data = serializer.data
            user_exist = User.objects.filter(username=user_data["username"])
            if not user_exist:
                user.name = user_data["name"]
                user.username = user_data["username"]
                user.phone_number = user_data["phone"]
                user.save()
                response = {'status': 'success', 'code': status.HTTP_200_OK, 'message': 'Profile info updated successfully'}
                return Response(response)
            elif user.username == user_exist.first().username:
                user.name = user_data["name"]
                user.phone_number = user_data["phone"]
                user.save()
                response = {'status': 'success', 'code': status.HTTP_200_OK, 'message': 'Profile info updated successfully'}
                return Response(response)
            else:
                response = {'status': 'error', 'code': status.HTTP_400_BAD_REQUEST, 'message': 'username or email already exists!'}
                return Response(response, status.HTTP_400_BAD_REQUEST)
        else:
            err = list(serializer.errors.items())
            response = {'status': 'error', 'code': status.HTTP_400_BAD_REQUEST, 'message': '(' + err[0][0] + ') ' + err[0][1][0]}
            return Response(response, status.HTTP_400_BAD_REQUEST)



class ProfileImageUpdate(APIView):
    def put(self, request):
        payload = permission_authontication_jwt(request)
        user = User.objects.filter(id=payload['id']).first()
        serializer = UpdateProfileImageSerializer(data=request.data)
        if serializer.is_valid():

            file = request.FILES['profile_img_url']
            utls_cls = VifUtils()
            img_url = utls_cls.aws_upload_file(user=user, file=file)

            profile_title = request.data["profile_title"]
            user.profile_image = img_url
            user.profile_title = profile_title
            user.save()
            response = {
                'status': 'success',
                'code': status.HTTP_200_OK,
                'message': 'Profile image and title updated successfully',
                'data': {
                    "profile_image": img_url,
                    "profile_title": user.profile_title
                }
            }
            return Response(response)
        else:
            err = list(serializer.errors.items())
            response = {
                    'status': 'error',
                    'code': status.HTTP_400_BAD_REQUEST,
                    'message': '(' + err[0][0] + ') ' + err[0][1][0]
                }
            return Response(response, status.HTTP_400_BAD_REQUEST)


class ProfileSetCompanyUpdate(APIView):
    def put(self, request):
        payload = permission_authontication_jwt(request)
        user = User.objects.filter(id=payload['id']).first()
        serializer = CompanySerializer(data=request.data)
        if serializer.is_valid():
            user_data = serializer.data
            user.company_email = user_data["company_email"]
            user.company_name = user_data["company_name"]
            user.save()
            response = {
                'status': 'success',
                'code': status.HTTP_200_OK,
                'message': 'Profile image updated successfully',
                'data': []
            }
            return Response(response)
        else:
            err = list(serializer.errors.items())
            response = {
                    'status': 'error',
                    'code': status.HTTP_400_BAD_REQUEST,
                    'message': '(' + err[0][0] + ') ' + err[0][1][0]
                }
            return Response(response, status.HTTP_400_BAD_REQUEST)
        


class SettingsView(APIView):
    def get(self, request):
        payload = permission_authontication_jwt(request)
        user = User.objects.filter(id=payload['id']).first()
        notification = UserNotification.objects.filter(notification_user=user)
        prf_img = user.get_presigned_url_img() 
        if user.profile_image != prf_img:
            user.profile_image = prf_img
            user.save()
        kys = ("from", "desc", "url", "date") 
        notf = [{kys[0]: nt.notification_from, kys[1]: nt.notification_text, kys[2]: nt.notification_url, kys[3]: nt.created_at} for nt in notification] 
        response = {
            'status': 'success',
            'code': status.HTTP_200_OK,
            'data': {
                "name": user.name,
                "username": user.username,
                "profile_img_url": prf_img,
                "is_verified": user.is_verified,
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
                response = {
                    'status': 'error',
                    'code': status.HTTP_400_BAD_REQUEST,
                    'message': "Wrong password, please enter your old password correctly!"
                }
                return Response(response, status=status.HTTP_400_BAD_REQUEST)
            if serializer.data.get("new_password") == serializer.data.get("new_password1"):
                user.set_password(serializer.data.get("new_password"))
                user.save()
            else:
                response = {
                    'status': 'error',
                    'code': status.HTTP_400_BAD_REQUEST,
                    'message': "passwords not match"
                }
                return Response(response, status=status.HTTP_400_BAD_REQUEST)
            response = {
                'status': 'success',
                'code': status.HTTP_200_OK,
                'message': 'Password updated successfully',
                'data': []
            }
            return Response(response)
        else:
            err = list(serializer.errors.items())
            response = {
                    'status': 'error',
                    'code': status.HTTP_400_BAD_REQUEST,
                    'message': '(' + err[0][0] + ') ' + err[0][1][0]
            }
            return Response(response, status.HTTP_400_BAD_REQUEST)



class ResetPasswordView(APIView):
    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        if serializer.is_valid():
            eml = request.data["email"]
            email_exist = User.objects.filter(email=eml)
            if email_exist:
                user = email_exist.first()
                payload = {
                    'id': user.id,
                    'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=5),
                    'iat': datetime.datetime.utcnow()
                }
                token = jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')
                absurl = os.environ.get("front_domain") + "/new-password/?token=" + token
                email_body = 'Hi '+ user.name + ' Use the link below to Change your password\n' + absurl
                data = {'email_body': email_body, 'email_subject': 'Vifbox Reset password', "to_email": [user.email]}
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
                    'code': status.HTTP_400_BAD_REQUEST,
                    'message': 'Email not exists, Please enter your email or SignUP'
                }
                return Response(response, status.HTTP_400_BAD_REQUEST)
        else:
            err = list(serializer.errors.items())
            response = {
                    'status': 'error',
                    'code': status.HTTP_400_BAD_REQUEST,
                    'message': '(' + err[0][0] + ') ' + err[0][1][0]
                }
            return Response(response, status.HTTP_400_BAD_REQUEST)
        



class NewPassView(APIView):
    def post(self, request):
        try:
            token = request.GET["token"]
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
                response = {
                    'status': 'error',
                    'code': status.HTTP_400_BAD_REQUEST,
                    'message': "Passwords not match"
                }
                return Response(response, status.HTTP_400_BAD_REQUEST)
        except jwt.ExpiredSignatureError:
            response = {
                'status': 'error',
                'code': status.HTTP_403_FORBIDDEN,
                'message': 'Token expired!'
            }
            raise AuthenticationFailed(response)



def permission_authontication_jwt(request):
    try:
        token = request.META['HTTP_AUTHORIZATION'].split(' ')[1]
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
    except jwt.DecodeError:
        response = {
                'status': 'error',
                'code': status.HTTP_403_FORBIDDEN,
                'message': 'Token Expired!'
            }
        raise AuthenticationFailed(response)
    except jwt.ExpiredSignatureError:
        response = {
                'status': 'error',
                'code': status.HTTP_403_FORBIDDEN,
                'message': UNAUTHONTICATED
            }
        raise AuthenticationFailed(response)
    except KeyError:
        response = {
                'status': 'error',
                'code': status.HTTP_403_FORBIDDEN,
                'message': 'Invalid AUTHORIZATION!'
            }
        raise AuthenticationFailed(response)
    return payload

















# class SocialAuth(APIView):
#     def post(self, request):
#         serializer = SocialAuthSerializer(data=request.data)
#         if serializer.is_valid():
#             social_user = User.objects.filter(email=request.data["email"])
#             if social_user:
#                 payload_access = {
#                     'id': social_user.first().id,
#                     'iat': datetime.datetime.utcnow(),
#                     'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=5)
#                 }
#                 payload_refresh = {
#                     'id': social_user.first().id,
#                     'iat': datetime.datetime.utcnow(),
#                     'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)
#                 }
#                 access_token = jwt.encode(payload_access, settings.SECRET_KEY, algorithm='HS256')
#                 refresh_token = jwt.encode(payload_refresh, settings.SECRET_KEY, algorithm='HS256')
#                 return Response({"type": "signin", "access": access_token, "refresh": refresh_token})
#             else:
#                 try:
#                     user_data = serializer.data
#                     username =  VifUtils.generate_username(request.data["name"])
#                     if user_data["profile_image"] == "" or user_data["profile_image"] is None:
#                         user_data["profile_image"] = "https://vifbox.org/api/media/default.jpg"
#                     user = User.objects.create(username=username, email=user_data["email"], name=request.data["name"], profile_image=user_data["profile_image"], social_id=user_data["social_id"])
#                     payload_access = {
#                         'id': user.id,
#                         'iat': datetime.datetime.utcnow(),
#                         'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=5)
#                     }
#                     payload_refresh = {
#                         'id': user.id,
#                         'iat': datetime.datetime.utcnow(),
#                         'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)
#                     }
#                     access_token = jwt.encode(payload_access, settings.SECRET_KEY, algorithm='HS256')
#                     refresh_token = jwt.encode(payload_refresh, settings.SECRET_KEY, algorithm='HS256')
#                     return Response({"type": "signup", "access": access_token, "refresh": refresh_token})
#                 except:
#                     response = {
#                         'status': 'error',
#                         'code': status.HTTP_400_BAD_REQUEST,
#                         'message': 'Bad request.'
#                     }
#                     return Response(response, status.HTTP_400_BAD_REQUEST)
#         else:
#             err = list(serializer.errors.items())
#             response = {
#                 'status': 'error',
#                 'code': status.HTTP_400_BAD_REQUEST,
#                 'message': '(' + err[0][0] + ') ' + err[0][1][0]
#             }
#             return Response(response, status.HTTP_400_BAD_REQUEST)


# class GithubInfo(APIView):
#     def get(self, request):
#         token = request.META['HTTP_AUTHORIZATION'].split(' ')[1]
#         endpoint = "https://api.github.com/user"
#         headers = {"Authorization": f"token {token}"}
#         githubuser_data = requests.get(endpoint, headers=headers).json()
#         try:
#             githubuser_id = githubuser_data["id"]
#         except KeyError:
#             return Response(githubuser_data, status.HTTP_400_BAD_REQUEST)
#         github_user = User.objects.filter(github_id=githubuser_id)
#         if not github_user:
#             username = VifUtils.generate_username(githubuser_data["login"]) # githubuser_data["login"] + "_G" 
#             user = User.objects.create_user(username=username, github_id=githubuser_id)
#             if not user.is_verified:
#                 user.is_verified = True
#                 user.save()
#                 UserNotification.objects.create(notification_user=user, 
#                                                 notification_text="welcome to vifbox",
#                                                 notification_from="Vifbox", notification_url="to_url/")
#         payload_access = {
#             'id': github_user.first().id,
#             'iat': datetime.datetime.utcnow(),
#             'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=5)
#         }
#         payload_refresh = {
#             'id': github_user.first().id,
#             'iat': datetime.datetime.utcnow(),
#             'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)
#         }
#         access_token = jwt.encode(payload_access, settings.SECRET_KEY, algorithm='HS256')
#         refresh_token = jwt.encode(payload_refresh, settings.SECRET_KEY, algorithm='HS256')
#         return Response({"access": access_token, "refresh": refresh_token})