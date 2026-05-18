from rest_framework import serializers
from users.models import User
from users.serializers import UserProfileSerializer
from .models import Employee


class EmployeeReadSerializer(serializers.ModelSerializer):
    user = UserProfileSerializer(read_only=True)

    class Meta:
        model  = Employee
        fields = '__all__'


class EmployeeCreateSerializer(serializers.Serializer):
    # User fields
    full_name   = serializers.CharField(max_length=150)
    email       = serializers.EmailField()
    employee_id = serializers.CharField(max_length=20)
    phone       = serializers.CharField(max_length=15, required=False, allow_blank=True, default='')
    password    = serializers.CharField(max_length=128, required=False, default='Employee@123')

    # Employee profile fields
    designation = serializers.CharField(max_length=100)
    department  = serializers.CharField(max_length=50)
    date_joined = serializers.DateField()
    address     = serializers.CharField(required=False, allow_blank=True, default='')
    status      = serializers.CharField(max_length=20, required=False, default='active')

    def validate_email(self, value):
        value = value.lower().strip()
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError('An account with this email already exists.')
        return value

    def validate_employee_id(self, value):
        value = value.strip()
        if User.objects.filter(employee_id=value).exists():
            raise serializers.ValidationError('This Employee ID already exists.')
        return value

    def validate_department(self, value):
        # Accept any capitalisation — normalise to lowercase
        VALID = ['engineering', 'hr', 'finance', 'marketing',
                 'operations', 'design', 'sales']
        normalised = value.lower().strip()
        if normalised not in VALID:
            normalised = 'engineering'
        return normalised

    def validate_status(self, value):
        VALID = ['active', 'inactive', 'on_leave']
        v = value.lower().strip()
        return v if v in VALID else 'active'

    def create(self, validated_data):
        password = validated_data.pop('password', 'Employee@123')

        user = User(
            email       = validated_data['email'],
            full_name   = validated_data['full_name'],
            employee_id = validated_data['employee_id'],
            phone       = validated_data.get('phone', ''),
            department  = validated_data['department'],
            role        = 'employee',
            is_active   = True,
        )
        user.set_password(password)
        user.save()

        employee = Employee.objects.create(
            user        = user,
            designation = validated_data['designation'],
            department  = validated_data['department'],
            date_joined = validated_data['date_joined'],
            address     = validated_data.get('address', ''),
            status      = validated_data.get('status', 'active'),
        )
        return employee


class EmployeeUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Employee
        fields = ['designation', 'department', 'date_joined',
                  'address', 'status', 'emergency_contact']