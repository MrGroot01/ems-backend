from rest_framework import serializers
from .models import SalaryStructure, Payslip


class SalarySerializer(serializers.ModelSerializer):
    gross     = serializers.ReadOnlyField()
    net       = serializers.ReadOnlyField()
    user_name = serializers.CharField(source='user.full_name', read_only=True)
    user_emp_id = serializers.CharField(source='user.employee_id', read_only=True)

    class Meta:
        model  = SalaryStructure
        fields = '__all__'


class PayslipSerializer(serializers.ModelSerializer):
    user_name   = serializers.CharField(source='user.full_name',    read_only=True)
    user_email  = serializers.CharField(source='user.email',        read_only=True)
    user_emp_id = serializers.CharField(source='user.employee_id',  read_only=True)
    user_dept   = serializers.CharField(source='user.department',   read_only=True)

    class Meta:
        model  = Payslip
        fields = '__all__'