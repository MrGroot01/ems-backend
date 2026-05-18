from rest_framework import status, generics
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from django.core.mail import send_mail
from django.conf import settings
from .models import User
from .serializers import (
    RegisterSerializer, LoginSerializer, UserProfileSerializer,
    ForgotPasswordSerializer, VerifyOTPSerializer, ResetPasswordSerializer,
    ChangePasswordSerializer
)


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
                'user': UserProfileSerializer(user).data,
                'tokens': get_tokens(user)
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
                'user': UserProfileSerializer(user).data,
                'tokens': get_tokens(user)
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
    serializer_class = UserProfileSerializer
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
                return Response({'error': 'Current password is incorrect'}, status=400)
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
                # Try to send email, fall back to console
                try:
                    send_mail(
                        subject='EMS Pro – Your Password Reset OTP',
                        message=f'Your OTP is: {otp}\nValid for 5 minutes.',
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[email],
                        fail_silently=False,
                    )
                except Exception:
                    pass  # console backend will print it
                print(f"[OTP] {email}: {otp}")   # always log to console for dev
                return Response({'message': 'OTP sent to your email'})
            except User.DoesNotExist:
                return Response({'error': 'No account with this email'}, status=404)
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
                return Response({'error': 'Invalid or expired OTP'}, status=400)
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
                    return Response({'error': 'Invalid or expired OTP'}, status=400)
                user.set_password(s.validated_data['new_password'])
                user.clear_otp()
                return Response({'message': 'Password reset successful'})
            except User.DoesNotExist:
                return Response({'error': 'User not found'}, status=404)
        return Response(s.errors, status=400)


class ListUsersView(APIView):
    """Admin: list all users for dropdowns"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        users = User.objects.filter(role='employee', is_active=True)
        return Response(UserProfileSerializer(users, many=True).data)
