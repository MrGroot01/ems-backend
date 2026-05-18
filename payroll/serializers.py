from rest_framework import serializers
from .models import SalaryStructure, Payslip


class SalarySerializer(serializers.ModelSerializer):
    gross = serializers.ReadOnlyField()
    net   = serializers.ReadOnlyField()
    user_name = serializers.CharField(source='user.full_name', read_only=True)

    class Meta:
        model  = SalaryStructure
        fields = '__all__'


class PayslipSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.full_name', read_only=True)

    class Meta:
        model  = Payslip
        fields = '__all__'