from rest_framework import serializers
from .models import User
from rest_framework.exceptions import ValidationError
from rest_framework import status
import re


class UserSerializer(serializers.ModelSerializer):
    first_name = serializers.CharField(required=True, min_length=2)
    last_name = serializers.CharField(required=True, min_length=2)
    email = serializers.EmailField(max_length=None, min_length=None, allow_blank=False)
    password = serializers.CharField(style={'input_type': 'password'}, write_only=True, required=True, min_length=8)
    
    class Meta:
        model = User
        fields = ['username', 'name', 'first_name', 'last_name', 'email', 'password']

    def validate(self, data):
        psw = data.get('password')
        has_upper = any(n.isupper() for n in psw)
        if not has_upper:
            raise ValidationError({"pswrd": "should have at least 1 Uppercase Charecter."})
        return data
        
    def create(self, validated_data):
        password = validated_data.pop('password', None)
        email_exists = User.objects.filter(email=validated_data["email"]).exists()
        if email_exists:
            response = {
                'status': 'error',
                'code': status.HTTP_400_BAD_REQUEST,
                'message': 'Email already exists, please Signin!'
            }
            raise ValidationError(response)
        instance = self.Meta.model(**validated_data)
        if password is not None:
            instance.set_password(password)
            instance.save()
        return instance
    

# class SocialAuthSerializer(serializers.Serializer):
#     name = serializers.CharField(required=True)
#     email = serializers.EmailField(max_length=None, min_length=None, allow_blank=False)
#     profile_image = serializers.CharField(allow_blank=True)
#     social_id = serializers.CharField(max_length=50, required=True, allow_blank=False)
class SocialAuthSerializer(serializers.Serializer):
    name = serializers.CharField(allow_null=True, allow_blank=True)
    email = serializers.EmailField(max_length=None, min_length=None, allow_blank=False)
    profile_image = serializers.CharField(allow_null=True, allow_blank=True)
    social_id = serializers.CharField(allow_null=True, allow_blank=True)


class LoginSerializer(serializers.Serializer):
    model = User
    email = serializers.CharField(required=True)
    password = serializers.CharField(required=True)



class CompanySerializer(serializers.Serializer):
    model = User
    company_email = serializers.EmailField(max_length=None, min_length=None, allow_blank=False)
    company_name = serializers.CharField(required=True)

class ChangePasswordSerializer(serializers.Serializer):
    model = User
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)
    new_password1 = serializers.CharField(required=True)



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
    model = User
    profile_img_url = serializers.FileField(max_length=None, allow_empty_file=False)
    profile_title = serializers.CharField(allow_blank=True, allow_null=True)



class ResetPasswordSerializer(serializers.Serializer):
    model = User
    email = serializers.EmailField(max_length=None, min_length=None, allow_blank=False)