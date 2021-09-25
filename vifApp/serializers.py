from rest_framework import serializers
from rest_framework.fields import Field
from .models import User
from rest_framework.exceptions import ValidationError


class UserSerializer(serializers.ModelSerializer):
    first_name = serializers.CharField(required=True, min_length=2)
    last_name = serializers.CharField(required=True, min_length=2)
    email = serializers.EmailField(max_length=None, min_length=None, allow_blank=False)
    password = serializers.CharField(style={'input_type': 'password'}, write_only=True, required=True, min_length=8)
    

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'password']

    def validate(self, data):
        psw = data.get('password')
        has_upper = any(n.isupper() for n in psw)
        if not has_upper:
            raise ValidationError({"password": "should have at least 1 Uppercase Charecter."})
        return data
        
    def create(self, validated_data):
        password = validated_data.pop('password', None)
        email_exists = User.objects.filter(email=validated_data["email"]).exists()
        if email_exists:
            raise ValidationError({"error": 'Email already exists, please Signin!'})
        instance = self.Meta.model(**validated_data)
        if password is not None:
            instance.set_password(password)
            instance.save()
        return instance
    


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
    email = serializers.EmailField(max_length=None, min_length=None, allow_blank=False)
    username = serializers.CharField(required=True)
    phone = serializers.CharField(allow_blank=True)



class UpdateProfileImageSerializer(serializers.Serializer):
    model = User
    profile_img_url = serializers.CharField(required=True)
    profile_title = serializers.CharField(allow_blank=True)



class ResetPasswordSerializer(serializers.Serializer):
    model = User
    email = serializers.EmailField(max_length=None, min_length=None, allow_blank=False)
