from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import AuthenticationFailed
from .serializers import UserSerializer, ChangePasswordSerializer, ResetPasswordSerializer
from .models import User
import jwt, datetime
from .utils import VifUtils
from django.contrib.sites.shortcuts import get_current_site
from django.urls import reverse
from rest_framework import status
from django.conf import settings



class RegisterView(APIView):
    def post(self, request):
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
        VifUtils.send_email(data)
        return Response(user_data)



class EmailVerifyView(APIView):
    def get(self, request):
        token = request.GET["token"]
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
            user = User.objects.get(id=payload["id"])
            if not user.is_verified:
                user.is_verified = True
                user.save()
            return Response({"email": "Successfuly activated"})
        except jwt.ExpiredSignatureError:
            raise AuthenticationFailed('Unauthenticated!')



class LoginView(APIView):
    def post(self, request):
        email = request.data['email']
        password = request.data['password']
        remember_me = request.data['remember_me']
        user = User.objects.filter(email=email).first()
        if user is None:
            raise AuthenticationFailed('User not found!')
        if not user.check_password(password):
            raise AuthenticationFailed('Incorrect password!')
        payload = {
            'id': user.id,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=90),
            'iat': datetime.datetime.utcnow()
        }
        token = jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')
        response = Response()
        if remember_me:
            response.set_cookie(key='jwt', value=token, httponly=True)
        else:
            response.delete_cookie('jwt')
        response.data = {'jwt': token}
        return response



# class HomeView(APIView):
#     def get(self, request):
#         payload = permission_authontication_jwt(request)
#         user = User.objects.filter(id=payload['id']).first()
#         serializer = UserSerializer(user)
#         return Response(serializer.data)


class ProfileView(APIView):
    def get(self, request):
        payload = permission_authontication_jwt(request)
        pass # TODO
    def post(self, request):
        payload = permission_authontication_jwt(request)
        pass # TODO


class SettingsView(APIView):
    def get(self, request):
        payload = permission_authontication_jwt(request)
        pass # TODO



class LogoutView(APIView):
    def post(self, request):
        response = Response()
        response.delete_cookie('jwt')
        response.data = {'message': 'success'}
        return response



class ChangePasswordView(APIView):
    def post(self, request):
        payload = permission_authontication_jwt(request)
        user = User.objects.filter(id=payload['id']).first()
        serializer = ChangePasswordSerializer(data=request.data)
        if serializer.is_valid():
            if not user.check_password(serializer.data.get("old_password")):
                return Response({"old_password": ["Wrong password."]}, status=status.HTTP_400_BAD_REQUEST)
            user.set_password(serializer.data.get("new_password"))
            user.save()
            response = {
                'status': 'success',
                'code': status.HTTP_200_OK,
                'message': 'Password updated successfully',
                'data': []
            }
            return Response(response)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



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
                absurl = 'http://'+str(domain)+relativelink+'?token='+token
                email_body = 'Hi '+ user.first_name + ' Use the link below to Change your password\n' + absurl
                data = {'email_body': email_body, 'email_subject': 'Verify your email', "to_email": user.email}
                VifUtils.send_email(data)
                response = {
                    'status': 'success',
                    'code': status.HTTP_200_OK,
                    'message': 'Verify your email',
                    'data': []
                }
                return Response(response)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



class ResetPassEmailVerifyView(APIView):
    def get(self, request):
        token = request.GET["token"]
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
            user = User.objects.get(id=payload["id"])
            if not user.is_verified:
                user.is_verified = True
                user.save()
            return Response({"email": "Successfuly activated"})  # you should redirect to change password page if response is sucessfull
        except jwt.ExpiredSignatureError:
            raise AuthenticationFailed('Unauthenticated!')



def permission_authontication_jwt(request):
    token = request.COOKIES.get('jwt')
    if not token:
        raise AuthenticationFailed('Unauthenticated!')
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        raise AuthenticationFailed('Unauthenticated!')
    return payload