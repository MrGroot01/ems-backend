from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import SalaryStructure, Payslip
from .serializers import SalarySerializer, PayslipSerializer


class SalaryViewSet(viewsets.ModelViewSet):
    serializer_class   = SalarySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role == 'admin':
            return SalaryStructure.objects.select_related('user').all()
        return SalaryStructure.objects.filter(user=user)


class PayslipViewSet(viewsets.ModelViewSet):
    serializer_class   = PayslipSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role == 'admin':
            return Payslip.objects.select_related('user').all()
        return Payslip.objects.filter(user=user)