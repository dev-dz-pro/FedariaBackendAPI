from rest_framework import serializers
from .models import User, UserNotification
from rest_framework.exceptions import ValidationError
from rest_framework import status
import re



class UserSerializer(serializers.Serializer):
    first_name = serializers.CharField(required=True, min_length=2)
    last_name = serializers.CharField(required=True, min_length=2)
    email = serializers.EmailField(max_length=None, min_length=None, allow_blank=False)
    password = serializers.CharField(style={'input_type': 'password'}, required=True, min_length=8)
    

    def validate(self, data):
        psw = data.get('password')
        has_upper = any(n.isupper() for n in psw)
        if not has_upper:
            raise ValidationError({"pswrd": "should have at least 1 Uppercase Charecter."})
        return data
        

# class UserSerializer(serializers.ModelSerializer):
#     first_name = serializers.CharField(required=True, min_length=2)
#     last_name = serializers.CharField(required=True, min_length=2)
#     email = serializers.EmailField(max_length=None, min_length=None, allow_blank=False)
#     password = serializers.CharField(style={'input_type': 'password'}, write_only=True, required=True, min_length=8)
    
#     class Meta:
#         model = User
#         fields = ['username', 'name', 'first_name', 'last_name', 'email', 'password']

#     def validate(self, data):
#         psw = data.get('password')
#         has_upper = any(n.isupper() for n in psw)
#         if not has_upper:
#             raise ValidationError({"pswrd": "should have at least 1 Uppercase Charecter."})
#         return data
        
#     def create(self, validated_data):
#         password = validated_data.pop('password', None)
#         email_exists = User.objects.filter(email=validated_data["email"]).exists()
#         if email_exists:
#             response = {
#                 'status': 'error',
#                 'code': status.HTTP_400_BAD_REQUEST,
#                 'message': 'Email already exists, please Signin!'
#             }
#             raise ValidationError(response)
#         instance = self.Meta.model(**validated_data)
#         if password is not None:
#             instance.set_password(password)
#             instance.save()
#         return instance



class JwtTokenSerializer(serializers.Serializer):
    refresh = serializers.CharField(required=True, max_length=600)


class LoginSerializer(serializers.Serializer):
    model = User
    email = serializers.CharField(required=True)
    password = serializers.CharField(required=True)


class UserStatusSerializer(serializers.Serializer):
    status = serializers.CharField(required=True)
    def validate(self, data):
        stts = data.get('status')
        if not stts in ['Available', 'Busy', 'Do not disturb', 'Away']:
            raise ValidationError({"status": "should be ('Available', 'Busy', 'Do not disturb' or 'Away')"})
        return data

class CompanySerializer(serializers.Serializer):
    model = User
    company_email = serializers.EmailField(max_length=None, min_length=None, allow_blank=False)
    company_name = serializers.CharField(required=True)



class UpdateAccountSerializer(serializers.Serializer):
    model = User
    company_email = serializers.EmailField(max_length=None, min_length=None, allow_blank=True)
    company_name = serializers.CharField(required=False, allow_blank=True)
    job_title = serializers.CharField(required=False, allow_blank=True)
    name = serializers.CharField(required=True)
    phone = serializers.CharField(allow_blank=True)
    def validate(self, data):
        value = data.get('phone')
        if value:
            reg = re.compile(r'^\+?1?\d{9,15}$')
            if reg.match(value):  
                return data
            else:
                raise ValidationError({"Phone number": "must be entered in the format: '+999999999'. Up to 15 digits allowed."})
        else:
            return data



class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, min_length=8)
    new_password1 = serializers.CharField(required=True, min_length=8)
    def validate(self, data):
        psw = data.get('new_password')
        has_upper = any(n.isupper() for n in psw)
        if not has_upper:
            raise ValidationError({"pswrd": "should have at least 1 Uppercase Charecter."})
        return data


class UpdateProfileSerializer(serializers.Serializer):
    model = User
    name = serializers.CharField(required=True)
    username = serializers.CharField(required=True)
    phone = serializers.CharField(allow_blank=True)

    def validate(self, data):
        value = data.get('phone')
        reg = re.compile(r'^\+?1?\d{9,15}$')
        if reg.match(value):  
            return data
        else:
            raise ValidationError({"Phone number": "must be entered in the format: '+999999999'. Up to 15 digits allowed."})


class UpdateProfileImageSerializer(serializers.Serializer):
    profile_img_url = serializers.FileField(max_length=None, allow_empty_file=False)


class ResetPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField(max_length=None, min_length=None, allow_blank=False)


class NewPassSerializer(serializers.Serializer):
    new_pass = serializers.CharField(required=True, min_length=8)
    confirm_new_pass = serializers.CharField(required=True, min_length=8)

    def validate(self, data):
        psw = data.get('new_pass')
        has_upper = any(n.isupper() for n in psw)
        if not has_upper:
            raise ValidationError({"pswrd": "should have at least 1 Uppercase Charecter."})
        return data


class UserNotificationSerializer(serializers.ModelSerializer):
    notification_from = serializers.CharField(read_only=True, source="notification_from.name")
    class Meta:
        model = UserNotification
        fields = ("notification_from", "notification_text", "notification_url", "created_at")

