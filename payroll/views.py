from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
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

    def create(self, request, *args, **kwargs):
        """
        Admin sets salary for an employee.
        If salary already exists for that user → update it.
        """
        user_id = request.data.get('user')
        if not user_id:
            return Response({'error': 'Employee (user) is required'}, status=400)

        # Check if salary already exists → update instead of create
        existing = SalaryStructure.objects.filter(user_id=user_id).first()
        if existing:
            s = SalarySerializer(existing, data=request.data, partial=True)
            if s.is_valid():
                s.save()
                return Response(s.data)
            return Response(s.errors, status=400)

        # Create new
        s = SalarySerializer(data=request.data)
        if s.is_valid():
            s.save()
            return Response(s.data, status=201)
        return Response(s.errors, status=400)


class PayslipViewSet(viewsets.ModelViewSet):
    serializer_class   = PayslipSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role == 'admin':
            return Payslip.objects.select_related('user').all()
        return Payslip.objects.filter(user=user)

    def create(self, request, *args, **kwargs):
        """
        Generate payslip for an employee.
        Automatically pulls salary structure and calculates gross/net.
        Body: { user: <id>, month: 1-12, year: 2026, days_worked: 22 }
        """
        if request.user.role != 'admin':
            return Response({'error': 'Admin only'}, status=403)

        user_id     = request.data.get('user')
        month       = request.data.get('month')
        year        = request.data.get('year')
        days_worked = int(request.data.get('days_worked', 22))

        if not all([user_id, month, year]):
            return Response({'error': 'user, month, and year are required'}, status=400)

        # Check salary structure exists
        try:
            salary = SalaryStructure.objects.get(user_id=user_id)
        except SalaryStructure.DoesNotExist:
            return Response({
                'error': 'No salary structure found for this employee. '
                         'Please set their salary first using "Set Salary".'
            }, status=400)

        # Check if payslip already exists for this month/year
        existing = Payslip.objects.filter(user_id=user_id, month=month, year=year).first()
        if existing:
            return Response({
                'error': f'Payslip for {month}/{year} already generated for this employee.'
            }, status=400)

        # Calculate values
        gross      = salary.gross
        deductions = float(salary.pf_deduction) + float(salary.tax_deduction) + float(salary.other_deductions)
        net        = gross - deductions

        # Pro-rate if days_worked < 26 (standard working days)
        if days_worked < 26:
            ratio = days_worked / 26
            net   = net * ratio

        payslip = Payslip.objects.create(
            user             = salary.user,
            month            = month,
            year             = year,
            basic            = salary.basic,
            hra              = salary.hra,
            transport        = salary.transport,
            medical          = salary.medical,
            other_allowances = salary.other_allowances,
            pf_deduction     = salary.pf_deduction,
            tax_deduction    = salary.tax_deduction,
            other_deductions = salary.other_deductions,
            gross            = round(gross, 2),
            deductions       = round(deductions, 2),
            net              = round(net, 2),
            days_worked      = days_worked,
        )

        # Send notification to employee
        try:
            from notifications.models import Notification
            Notification.objects.create(
                recipient = salary.user,
                sender    = request.user,
                title     = f'💰 Payslip Generated – {payslip.get_month_display()} {year}',
                message   = (
                    f'Your payslip for month {month}/{year} has been generated. '
                    f'Net salary: ₹{net:,.2f}. '
                    f'Days worked: {days_worked}. Check the Payroll section.'
                ),
                type = 'payroll',
            )
        except Exception:
            pass

        return Response(PayslipSerializer(payslip).data, status=201)

    @action(detail=True, methods=['patch'])
    def mark_paid(self, request, pk=None):
        """Admin marks payslip as paid"""
        if request.user.role != 'admin':
            return Response({'error': 'Admin only'}, status=403)
        payslip      = self.get_object()
        payslip.paid = True
        payslip.save()
        return Response(PayslipSerializer(payslip).data)