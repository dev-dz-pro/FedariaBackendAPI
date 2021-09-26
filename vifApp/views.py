from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import AuthenticationFailed
from .models import User, UserNotification
import jwt
import datetime
from .utils import VifUtils
from django.contrib.sites.shortcuts import get_current_site
from django.urls import reverse
from rest_framework import status
from django.conf import settings
import requests
from threading import Thread
from .serializers import (UserSerializer, ChangePasswordSerializer, ResetPasswordSerializer, 
                        UpdateProfileSerializer, UpdateProfileImageSerializer, LoginSerializer, CompanySerializer)


class RegisterView(APIView): 
    def post(self, request):
        username = VifUtils.generate_username(request.data["first_name"])
        request.data["username"] = username
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
        # domain = get_current_site(request)
        # relativelink = reverse("email-verify")
        # absurl = 'http://'+str(domain)+relativelink+'?token='+token
        absurl = "http://vifbox.org/verify-email/?token="+token # will add it to var inv
        email_body = 'Hi '+ user.first_name + ' Use the link below to verify your email\n' + absurl
        data = {'email_body': email_body, 'email_subject': 'Verify your email', "to_email": user.email}
        Thread(target=VifUtils.send_email, args=(data,)).start()
        response = {
                'status': 'success',
                'code': status.HTTP_200_OK,
                'message': 'Email was sent to you, please verify your email to activate your account.',
                'info': user_data
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
                'message': 'Unauthenticated!'
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
            # raise AuthenticationFailed('User not found!')
            response = {
                'status': 'error',
                'code': status.HTTP_400_BAD_REQUEST,
                'message': "user not found!"
            }
            return Response(response, status.HTTP_400_BAD_REQUEST)
        if not user.check_password(password):
            # raise AuthenticationFailed('Incorrect password!')
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
        refresh_token = jwt.encode(payload_refresh, settings.SECRET_KEY, algorithm='HS256')
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
            payload = jwt.decode(refresh, settings.SECRET_KEY, algorithms=["HS256"])
        except jwt.ExpiredSignatureError:
            response = {
                'status': 'error',
                'code': status.HTTP_403_FORBIDDEN,
                'message': 'Unauthenticated!'
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
        # from botocore.client import Config
        # import boto3
        # file = request.FILES['profile_img_url']
        # client = boto3.client('s3',config=Config(signature_version='s3v4'),aws_access_key_id="AKIA4NXRCXKEC3MAIO5W", aws_secret_access_key="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")
        # client.upload_fileobj(file, "vifbox-backend", "filename.jpg")
        # url = client.generate_presigned_url('get_object', Params = {'Bucket': "vifbox-backend" , 'Key': "/"})
        # return Response({"url": url})
        payload = permission_authontication_jwt(request) # reverse('social:begin', kwargs={'backend':'github'})
        user = User.objects.filter(id=payload['id']).first()
        serializer = UserSerializer(user)
        return Response(serializer.data)



class ProfileView(APIView):
    def get(self, request):
        payload = permission_authontication_jwt(request)
        user = User.objects.filter(id=payload['id']).first()
        notification = UserNotification.objects.filter(notification_user=user)
        kys = ("from", "desc", "url", "date") 
        notf = [{kys[0]: nt.notification_from, kys[1]: nt.notification_text, kys[2]: nt.notification_url, kys[3]: nt.created_at} for nt in notification] 
        response = {
            'status': 'success',
            'code': status.HTTP_200_OK,
            'data': {
                "name": user.first_name,
                "username": user.username,
                "profile_img_url": user.profile_image.url,
                "profile_title": user.profile_title,
                "email": user.email,
                "phone_number": user.phone_number,
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
                user.first_name = user_data["name"]
                user.email = user_data["email"]
                user.username = user_data["username"]
                user.phone_number = user_data["phone"]
                user.save()
                response = {
                    'status': 'success',
                    'code': status.HTTP_200_OK,
                    'message': 'Profile info updated successfully',
                    'data': []
                }
                return Response(response)
            else:
                response = {
                    'status': 'error',
                    'code': status.HTTP_400_BAD_REQUEST,
                    'message': 'username exists'
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
        # return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



class ProfileImageUpdate(APIView):
    def put(self, request):
        payload = permission_authontication_jwt(request)
        user = User.objects.filter(id=payload['id']).first()
        serializer = UpdateProfileImageSerializer(data=request.data)
        if serializer.is_valid():
            file = request.FILES['profile_img_url']
            profile_title = request.data["profile_title"]
            user.profile_image = file
            user.profile_title = profile_title
            user.save()
            response = {
                'status': 'success',
                'code': status.HTTP_200_OK,
                'message': 'Profile image and title updated successfully',
                'data': {
                    "profile_image": user.profile_image.url,
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
        kys = ("from", "desc", "url", "date") 
        notf = [{kys[0]: nt.notification_from, kys[1]: nt.notification_text, kys[2]: nt.notification_url, kys[3]: nt.created_at} for nt in notification] 
        response = {
            'status': 'success',
            'code': status.HTTP_200_OK,
            'data': {
                "name": user.first_name,
                "username": user.username,
                "profile_img_url": user.profile_image.url,
                "is_verified": user.is_verified,
                "notification": notf
            }
        }
        return Response(response)



class SettingsInfoUpdate(APIView):
    def put(self, request):
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
        eml = request.data["email"]
        email_exist = User.objects.filter(email=eml)
        serializer = ResetPasswordSerializer(data=request.data)
        if serializer.is_valid():
            if email_exist:
                user = email_exist.first()
                payload = {
                    'id': user.id,
                    'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=5),
                    'iat': datetime.datetime.utcnow()
                }
                token = jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')
                absurl = "http://vifbox.org/new-password/?token="+token
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
    def put(self, request):
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



class GithubInfo(APIView):
    def get(self, request):
        token = request.META['HTTP_AUTHORIZATION'].split(' ')[1]
        endpoint = "https://api.github.com/user"
        headers = {"Authorization": f"token {token}"}
        githubuser_data = requests.get(endpoint, headers=headers).json()
        githubuser_id = githubuser_data["id"]
        github_user = User.objects.filter(github_id=githubuser_id)
        if not github_user:
            username = VifUtils.generate_username(githubuser_data["login"])
            user = User.objects.create_user(username=username, github_id=githubuser_id)
            if not user.is_verified:
                user.is_verified = True
                user.save()
        payload_access = {
            'id': github_user.first().id,
            'iat': datetime.datetime.utcnow(),
            'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=5)
        }
        payload_refresh = {
            'id': github_user.first().id,
            'iat': datetime.datetime.utcnow(),
            'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)
        }
        access_token = jwt.encode(payload_access, settings.SECRET_KEY, algorithm='HS256')
        refresh_token = jwt.encode(payload_refresh, settings.SECRET_KEY, algorithm='HS256')
        return Response({"access": access_token, "refresh": refresh_token})



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
                'message': 'Unauthenticated!'
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





