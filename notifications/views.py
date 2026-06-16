from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from users.models import User
from .models import Notification
from .serializers import NotificationSerializer


class NotificationViewSet(viewsets.ModelViewSet):
    serializer_class   = NotificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # ── FIX: model uses 'user' not 'recipient' ──
        return Notification.objects.filter(
            user=self.request.user
        ).order_by('-created_at')

    @action(detail=True, methods=['patch'])
    def mark_read(self, request, pk=None):
        n = self.get_object()
        n.is_read = True
        n.save()
        return Response(NotificationSerializer(n).data)

    @action(detail=False, methods=['patch'])
    def mark_all_read(self, request):
        Notification.objects.filter(
            user=request.user, is_read=False
        ).update(is_read=True)
        return Response({'message': 'All marked as read'})

    @action(detail=False, methods=['post'])
    def broadcast(self, request):
        if request.user.role != 'admin':
            return Response({'error': 'Admin only'}, status=403)

        title   = request.data.get('title', '').strip()
        message = request.data.get('message', '').strip()
        ntype   = request.data.get('type', 'announcement')

        if not title or not message:
            return Response(
                {'error': 'Title and message required'}, status=400
            )

        # Send to ALL active users (including admins except sender)
        recipients = User.objects.filter(
            is_active=True
        ).exclude(id=request.user.id)

        notifs = [
            Notification(
                user=u,          # ← 'user' not 'recipient'
                title=title,
                message=message,
                type=ntype,
            )
            for u in recipients
        ]
        Notification.objects.bulk_create(notifs)
        return Response({'message': f'Sent to {len(notifs)} users'})

    @action(detail=False, methods=['get'])
    def unread_count(self, request):
        count = Notification.objects.filter(
            user=request.user, is_read=False
        ).count()
        return Response({'unread': count})