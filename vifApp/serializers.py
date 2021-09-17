from rest_framework import serializers
from .models import User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'password']
        extra_kwargs = {
            'password': {'write_only': True}
        }

    def create(self, validated_data):
        # validated_data["name"] = "testname" # to play with the validated data genarate a username and save it
        password = validated_data.pop('password', None)
        instance = self.Meta.model(**validated_data)
        if password is not None:
            instance.set_password(password)
        instance.save()
        return instance



class ChangePasswordSerializer(serializers.Serializer):
    model = User
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)
    new_password1 = serializers.CharField(required=True)


class UpdateProfileSerializer(serializers.Serializer):
    model = User
    name = serializers.CharField(required=True)
    username = serializers.CharField(required=True)
    phone = serializers.CharField(required=True)


class ResetPasswordSerializer(serializers.Serializer):
    model = User
    email = serializers.CharField(required=True)