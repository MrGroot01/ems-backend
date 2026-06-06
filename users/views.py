from rest_framework import generics
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from django.conf import settings
from django.utils import timezone
from captcha.models import CaptchaStore
from captcha.helpers import captcha_image_url
from .models import User
from .serializers import (
    RegisterSerializer, LoginSerializer, UserProfileSerializer,
    ForgotPasswordSerializer, VerifyOTPSerializer, ResetPasswordSerializer,
    ChangePasswordSerializer
)
from .aws_services import send_otp_email


def get_tokens(user):
    r = RefreshToken.for_user(user)
    return {'access': str(r.access_token), 'refresh': str(r)}


class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        s = RegisterSerializer(data=request.data)
        if s.is_valid():
            user = s.save()
            return Response({
                'message': 'Registration successful',
                'user':    UserProfileSerializer(user).data,
                'tokens':  get_tokens(user)
            }, status=201)
        return Response(s.errors, status=400)


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        s = LoginSerializer(data=request.data)
        if s.is_valid():
            user = s.validated_data['user']
            return Response({
                'message': 'Login successful',
                'user':    UserProfileSerializer(user).data,
                'tokens':  get_tokens(user)
            })
        return Response(s.errors, status=401)


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            token = RefreshToken(request.data.get('refresh'))
            token.blacklist()
            return Response({'message': 'Logged out successfully'})
        except TokenError:
            return Response({'error': 'Invalid token'}, status=400)


class ProfileView(generics.RetrieveUpdateAPIView):
    serializer_class   = UserProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user


class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        s = ChangePasswordSerializer(data=request.data)
        if s.is_valid():
            user = request.user
            if not user.check_password(s.validated_data['old_password']):
                return Response(
                    {'error': 'Current password is incorrect'},
                    status=400
                )
            user.set_password(s.validated_data['new_password'])
            user.save()
            return Response({'message': 'Password changed successfully'})
        return Response(s.errors, status=400)


class ForgotPasswordView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        s = ForgotPasswordSerializer(data=request.data)
        if s.is_valid():
            email = s.validated_data['email']
            try:
                user = User.objects.get(email=email)
                otp  = user.generate_otp()
                print(f"[OTP CODE] Email:{email} OTP:{otp}", flush=True)
                try:
                    sent = send_otp_email(email, otp, user.full_name)
                    if sent:
                        print(f"[OTP EMAIL OK] {email}", flush=True)
                    else:
                        print(f"[OTP EMAIL FAILED] {email}", flush=True)
                except Exception as e:
                    print(f"[OTP EMAIL ERROR] {email}: {str(e)}", flush=True)
                return Response({'message': 'OTP sent to your email'})
            except User.DoesNotExist:
                return Response(
                    {'error': 'No account with this email'},
                    status=404
                )
        return Response(s.errors, status=400)


class VerifyOTPView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        s = VerifyOTPSerializer(data=request.data)
        if s.is_valid():
            email = s.validated_data['email']
            otp   = s.validated_data['otp']
            try:
                user = User.objects.get(email=email)
                if user.is_otp_valid(otp):
                    return Response({'message': 'OTP verified'})
                return Response(
                    {'error': 'Invalid or expired OTP'},
                    status=400
                )
            except User.DoesNotExist:
                return Response({'error': 'User not found'}, status=404)
        return Response(s.errors, status=400)


class ResetPasswordView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        s = ResetPasswordSerializer(data=request.data)
        if s.is_valid():
            email = s.validated_data['email']
            otp   = s.validated_data['otp']
            try:
                user = User.objects.get(email=email)
                if not user.is_otp_valid(otp):
                    return Response(
                        {'error': 'Invalid or expired OTP'},
                        status=400
                    )
                user.set_password(s.validated_data['new_password'])
                user.save()
                user.clear_otp()
                return Response({'message': 'Password reset successful'})
            except User.DoesNotExist:
                return Response({'error': 'User not found'}, status=404)
        return Response(s.errors, status=400)


class ListUsersView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        users = User.objects.filter(role='employee', is_active=True)
        return Response(UserProfileSerializer(users, many=True).data)


# ── CAPTCHA VIEWS ──────────────────────────────────────────

class GetCaptchaView(APIView):
    """Generate captcha — returns key + image URL"""
    permission_classes = [AllowAny]

    def get(self, request):
        key       = CaptchaStore.generate_key()
        image_url = request.build_absolute_uri(captcha_image_url(key))
        return Response({
            'captcha_key':       key,
            'captcha_image_url': image_url,
        })


class VerifyCaptchaView(APIView):
    """Verify captcha value"""
    permission_classes = [AllowAny]

    def post(self, request):
        key   = request.data.get('captcha_key', '')
        value = request.data.get('captcha_value', '').strip().upper()

        if not key or not value:
            return Response(
                {'error': 'Captcha key and value required'},
                status=400
            )
        try:
            captcha = CaptchaStore.objects.get(
                hashkey=key,
                expiration__gt=timezone.now()
            )
            if captcha.response.upper() == value:
                captcha.delete()
                return Response({'valid': True, 'message': 'Captcha verified'})
            else:
                return Response(
                    {'valid': False, 'error': 'Wrong captcha! Try again.'},
                    status=400
                )
        except CaptchaStore.DoesNotExist:
            return Response(
                {'valid': False, 'error': 'Captcha expired. Please refresh.'},
                status=400
            )