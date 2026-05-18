import re
from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import User


class RegisterSerializer(serializers.ModelSerializer):
    password         = serializers.CharField(write_only=True, min_length=8)
    confirm_password = serializers.CharField(write_only=True)

    class Meta:
        model  = User
        fields = ['full_name','employee_id','email','phone','department',
                  'role','password','confirm_password','profile_image']

    def validate_password(self, v):
        if not re.search(r'[A-Z]', v): raise serializers.ValidationError('Need uppercase letter')
        if not re.search(r'[a-z]', v): raise serializers.ValidationError('Need lowercase letter')
        if not re.search(r'\d',   v):  raise serializers.ValidationError('Need a number')
        if not re.search(r'[!@#$%^&*]', v): raise serializers.ValidationError('Need special char')
        return v

    def validate(self, data):
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError({'confirm_password': 'Passwords do not match'})
        return data

    def create(self, validated_data):
        validated_data.pop('confirm_password')
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


class LoginSerializer(serializers.Serializer):
    email    = serializers.EmailField()
    password = serializers.CharField()
    role     = serializers.ChoiceField(choices=['admin','employee'])

    def validate(self, data):
        user = authenticate(email=data['email'], password=data['password'])
        if not user:           raise serializers.ValidationError('Invalid email or password')
        if not user.is_active: raise serializers.ValidationError('Account is disabled')
        if user.role != data['role']:
            raise serializers.ValidationError(f'This account is not registered as {data["role"]}')
        data['user'] = user
        return data


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model  = User
        fields = ['id','full_name','employee_id','email','phone',
                  'department','role','profile_image','date_joined']
        read_only_fields = ['id','email','employee_id','date_joined']


class AdminCreateUserSerializer(serializers.ModelSerializer):
    """Used by admin to create employee user + profile in one shot"""
    password = serializers.CharField(write_only=True, default='Employee@123')

    class Meta:
        model  = User
        fields = ['full_name','employee_id','email','phone','department','role','password']

    def create(self, validated_data):
        password = validated_data.pop('password', 'Employee@123')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()


class VerifyOTPSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp   = serializers.CharField(max_length=6)


class ResetPasswordSerializer(serializers.Serializer):
    email            = serializers.EmailField()
    otp              = serializers.CharField(max_length=6)
    new_password     = serializers.CharField(min_length=8)
    confirm_password = serializers.CharField()

    def validate(self, data):
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError({'confirm_password': 'Passwords do not match'})
        return data


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField()
    new_password = serializers.CharField(min_length=8)

    def validate_new_password(self, v):
        if not re.search(r'[A-Z]', v): raise serializers.ValidationError('Need uppercase')
        if not re.search(r'\d',   v):  raise serializers.ValidationError('Need a digit')
        return v
