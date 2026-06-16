from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Leave
from .serializers import LeaveSerializer
from notifications.models import Notification


class LeaveViewSet(viewsets.ModelViewSet):
    serializer_class   = LeaveSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        qs   = Leave.objects.select_related('user', 'approved_by').all()
        if user.role != 'admin':
            qs = qs.filter(user=user)
        s = self.request.query_params.get('status')
        if s:
            qs = qs.filter(status=s)
        return qs.order_by('-applied_on')

    def perform_create(self, serializer):
        leave = serializer.save(user=self.request.user)
        # Notify all admins — use 'user' field not 'recipient'
        from users.models import User
        admins = User.objects.filter(role='admin', is_active=True)
        Notification.objects.bulk_create([
            Notification(
                user=admin,          # ← fixed: 'user' not 'recipient'
                title='New Leave Request',
                message=f'{self.request.user.full_name} applied for '
                        f'{leave.leave_type} leave ({leave.days} days)',
                type='leave',
            ) for admin in admins
        ])

    @action(detail=True, methods=['patch'])
    def update_status(self, request, pk=None):
        if request.user.role != 'admin':
            return Response({'error': 'Admin only'}, status=403)

        leave      = self.get_object()
        new_status = request.data.get('status')

        if new_status not in ['approved', 'rejected', 'cancelled']:
            return Response(
                {'error': 'Status must be approved, rejected or cancelled'},
                status=400
            )

        leave.status      = new_status
        leave.approved_by = request.user
        if new_status == 'rejected':
            leave.reject_reason = request.data.get('reason', '').strip()
        leave.save()

        # Notify the employee — use 'user' field not 'recipient'
        Notification.objects.create(
            user=leave.user,         # ← fixed: 'user' not 'recipient'
            title=f'Leave {new_status.capitalize()}',
            message=(
                f'Your {leave.leave_type} leave request '
                f'({leave.start_date} → {leave.end_date}) '
                f'has been {new_status}.'
                + (f' Reason: {leave.reject_reason}' if leave.reject_reason else '')
            ),
            type='leave',
        )
        return Response(LeaveSerializer(leave).data)