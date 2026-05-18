from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from .models import Attendance
from .serializers import AttendanceSerializer

class AttendanceViewSet(viewsets.ModelViewSet):
    serializer_class = AttendanceSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role == 'admin':
            return Attendance.objects.select_related('user').all()
        return Attendance.objects.filter(user=user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['post'])
    def check_in(self, request):
        today = timezone.now().date()
        now_time = timezone.now().time()
        obj, created = Attendance.objects.get_or_create(
            user=request.user, date=today,
            defaults={'check_in': now_time, 'status': 'present'}
        )
        if not created:
            return Response({'error': 'Already checked in today'}, status=400)
        return Response(AttendanceSerializer(obj).data, status=201)

    @action(detail=False, methods=['post'])
    def check_out(self, request):
        today = timezone.now().date()
        now_time = timezone.now().time()
        try:
            obj = Attendance.objects.get(user=request.user, date=today)
            if obj.check_out:
                return Response({'error': 'Already checked out'}, status=400)
            obj.check_out = now_time
            if obj.check_in:
                from datetime import datetime, date
                ci = datetime.combine(date.today(), obj.check_in)
                co = datetime.combine(date.today(), now_time)
                diff = (co - ci).seconds / 3600
                obj.working_hours = round(diff, 2)
            obj.save()
            return Response(AttendanceSerializer(obj).data)
        except Attendance.DoesNotExist:
            return Response({'error': 'No check-in found today'}, status=404)

    @action(detail=False, methods=['get'])
    def today_summary(self, request):
        today = timezone.now().date()
        total = Attendance.objects.filter(date=today).count()
        present = Attendance.objects.filter(date=today, status='present').count()
        return Response({'total': total, 'present': present,
                         'absent': total - present, 'date': str(today)})
