from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
from .models import Employee
from .serializers import EmployeeReadSerializer, EmployeeCreateSerializer, EmployeeUpdateSerializer


class EmployeeViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def list(self, request):
        qs     = Employee.objects.select_related('user').all()
        dept   = request.query_params.get('department')
        stat   = request.query_params.get('status')
        search = request.query_params.get('search')

        if dept:   qs = qs.filter(department=dept.lower())
        if stat:   qs = qs.filter(status=stat.lower())
        if search:
            qs = qs.filter(
                Q(user__full_name__icontains=search) |
                Q(user__email__icontains=search)     |
                Q(user__employee_id__icontains=search)
            )
        return Response(EmployeeReadSerializer(qs, many=True).data)

    def create(self, request):
        s = EmployeeCreateSerializer(data=request.data)
        if s.is_valid():
            try:
                employee = s.save()
                return Response({
                    'message':        f'Employee {employee.user.full_name} created! '
                                      f'Login: {employee.user.email} / Employee@123',
                    'employee':       EmployeeReadSerializer(employee).data,
                    'login_email':    employee.user.email,
                    'login_password': 'Employee@123',
                }, status=201)
            except Exception as exc:
                return Response({'error': str(exc)}, status=400)
        return Response(s.errors, status=400)

    def retrieve(self, request, pk=None):
        try:
            emp = Employee.objects.select_related('user').get(pk=pk)
            return Response(EmployeeReadSerializer(emp).data)
        except Employee.DoesNotExist:
            return Response({'error': 'Not found'}, status=404)

    def update(self, request, pk=None):
        try:
            emp = Employee.objects.get(pk=pk)
            s   = EmployeeUpdateSerializer(emp, data=request.data, partial=True)
            if s.is_valid():
                s.save()
                emp.refresh_from_db()
                return Response(EmployeeReadSerializer(emp).data)
            return Response(s.errors, status=400)
        except Employee.DoesNotExist:
            return Response({'error': 'Not found'}, status=404)

    def destroy(self, request, pk=None):
        try:
            emp = Employee.objects.get(pk=pk)
            emp.user.delete()
            return Response({'message': 'Deleted'}, status=204)
        except Employee.DoesNotExist:
            return Response({'error': 'Not found'}, status=404)


class DashboardStatsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from leaves.models import Leave
        from tasks.models import Task
        from attendance.models import Attendance
        from django.utils import timezone

        today = timezone.now().date()

        return Response({
            'total_employees': Employee.objects.filter(status='active').count(),
            'present_today':   Attendance.objects.filter(date=today, status='present').count(),
            'on_leave':        Leave.objects.filter(status='approved',
                                   start_date__lte=today, end_date__gte=today).count(),
            'pending_leaves':  Leave.objects.filter(status='pending').count(),
            'active_tasks':    Task.objects.filter(status__in=['todo', 'in_progress']).count(),
            'salary_expense':  '4.65L',
        })