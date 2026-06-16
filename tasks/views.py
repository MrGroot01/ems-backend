import logging
import random
import re
from datetime import timedelta

from django.conf import settings
from django.core.mail import send_mail
from django.db.models import Count, Q
from django.utils import timezone

from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from notifications.models import Notification
from users.models import User

from .models import Task
from .serializers import TaskSerializer

logger = logging.getLogger(__name__)


# =========================================================
# Generate Jitsi Meet Link
# =========================================================
def generate_jitsi_link(employee_name, employee_id):
    import uuid
    clean_name = re.sub(r'[^a-zA-Z0-9]', '', employee_name.replace(' ', ''))
    unique_id  = str(uuid.uuid4())[:8]
    room_name  = f"EMS-{clean_name}-{employee_id}-{unique_id}"
    return f"https://meet.jit.si/{room_name}"


# =========================================================
# Task ViewSet
# =========================================================
class TaskViewSet(viewsets.ModelViewSet):

    serializer_class   = TaskSerializer
    permission_classes = [IsAuthenticated]

    # =====================================================
    # GET TASKS
    # =====================================================
    def get_queryset(self):
        user = self.request.user
        if user.role == 'admin':
            return Task.objects.select_related('assigned_to', 'assigned_by').all()
        return Task.objects.filter(assigned_to=user).select_related('assigned_to', 'assigned_by')

    # =====================================================
    # CREATE TASK
    # ── task saves even if notification fails ──
    # =====================================================
    def perform_create(self, serializer):
        task = serializer.save(assigned_by=self.request.user)

        try:
            Notification.objects.create(
                recipient=task.assigned_to,
                sender=self.request.user,
                title='New Task Assigned',
                message=(
                    f'You have been assigned: '
                    f'"{task.title}" – due {task.due_date}'
                ),
                type='task',
            )
        except Exception as e:
            # Log but never fail the task creation because of a notification error
            logger.error(f'Notification failed for task {task.id}: {e}')

    # =====================================================
    # UPDATE PROGRESS
    # =====================================================
    @action(detail=True, methods=['patch'])
    def update_progress(self, request, pk=None):
        task     = self.get_object()
        progress = int(request.data.get('progress', task.progress))
        s_status = request.data.get('status', task.status)

        task.progress = min(100, max(0, progress))
        task.status   = s_status

        if task.progress == 100:
            task.status       = 'completed'
            task.completed_at = timezone.now()

        task.save()
        return Response(TaskSerializer(task).data)

    # =====================================================
    # MANUAL WARNING CHECK (admin)
    # =====================================================
    @action(detail=False, methods=['post'])
    def trigger_warning_check(self, request):
        if request.user.role != 'admin':
            return Response({'error': 'Admin only'}, status=403)

        from django.core.management import call_command
        try:
            call_command('check_task_warnings')
            return Response({'message': 'Warning check completed successfully'})
        except Exception as e:
            return Response({'error': str(e)}, status=500)

    # =====================================================
    # AT-RISK EMPLOYEES (admin)
    # =====================================================
    @action(detail=False, methods=['get'])
    def at_risk_employees(self, request):
        if request.user.role != 'admin':
            return Response({'error': 'Admin only'}, status=403)

        at_risk = (
            User.objects
            .filter(role='employee', is_active=True)
            .annotate(
                pending_count=Count(
                    'tasks',
                    filter=Q(tasks__status__in=['todo', 'in_progress'])
                )
            )
            .filter(pending_count__gte=2)
        )

        data = []
        for emp in at_risk:
            pending_tasks = Task.objects.filter(
                assigned_to=emp,
                status__in=['todo', 'in_progress']
            ).values('id', 'title', 'priority', 'due_date', 'status')

            data.append({
                'employee_id':   emp.id,
                'employee_name': emp.full_name,
                'employee_code': emp.employee_id,
                'email':         emp.email,
                'pending_count': emp.pending_count,
                'pending_tasks': list(pending_tasks),
            })

        return Response(data)

    # =====================================================
    # MANUAL MEETING SCHEDULER (admin-triggered)
    # =====================================================
    @action(detail=False, methods=['post'])
    def schedule_meeting(self, request):
        if request.user.role != 'admin':
            return Response({'error': 'Admin only'}, status=403)

        employee_id = request.data.get('employee_id')
        if not employee_id:
            return Response({'error': 'employee_id required'}, status=400)

        try:
            employee = User.objects.get(id=employee_id, role='employee')
        except User.DoesNotExist:
            return Response({'error': 'Employee not found'}, status=404)

        pending_tasks = Task.objects.filter(
            assigned_to=employee,
            status__in=['todo', 'in_progress']
        )
        task_titles  = ", ".join(pending_tasks.values_list('title', flat=True)[:3])
        meeting_link = generate_jitsi_link(employee.full_name, employee.employee_id)

        # Notify employee
        try:
            Notification.objects.create(
                recipient=employee,
                sender=request.user,
                title='📅 Meeting Scheduled',
                message=(
                    f"A meeting has been scheduled regarding your pending tasks: "
                    f"{task_titles}\n\n"
                    f"🔗 Join Meeting:\n{meeting_link}\n\n"
                    f"Please join at the scheduled time."
                ),
                type='warning',
            )
        except Exception as e:
            logger.error(f'Employee meeting notification failed: {e}')

        # Notify admins
        admins = User.objects.filter(role='admin', is_active=True)
        for admin in admins:
            try:
                Notification.objects.create(
                    recipient=admin,
                    sender=request.user,
                    title=f'📅 Meeting Scheduled: {employee.full_name}',
                    message=(
                        f"Meeting scheduled for {employee.full_name}\n\n"
                        f"Pending Tasks: {task_titles}\n\n"
                        f"🔗 Meeting Link:\n{meeting_link}"
                    ),
                    type='warning',
                )
            except Exception as e:
                logger.error(f'Admin meeting notification failed: {e}')

        return Response({
            'message':      f'Meeting scheduled for {employee.full_name}',
            'meeting_link': meeting_link,
            'employee':     employee.full_name,
            'tasks':        task_titles,
        })

    # =====================================================
    # AUTO MEETING ON 2+ OVERDUE TASKS
    # (called every 60s by TaskWarningBanner)
    # =====================================================
    @action(detail=False, methods=['post'])
    def check_overdue_meeting(self, request):
        user  = request.user
        now   = timezone.now()
        today = now.date()

        # Find OVERDUE tasks (not completed, due date in the past)
        overdue_qs    = Task.objects.filter(
            assigned_to=user,
            status__in=['todo', 'in_progress'],
            due_date__lt=today,
        )
        overdue_count = overdue_qs.count()

        if overdue_count < 2:
            return Response({
                'overdue_count':     overdue_count,
                'meeting_scheduled': False,
            })

        # Don't spam: skip if meeting was already scheduled in last 20 min
        recent_meeting = Notification.objects.filter(
            recipient=user,
            title__icontains='Meeting Scheduled',
            created_at__gte=now - timedelta(minutes=20),
        ).order_by('-created_at').first()

        if recent_meeting:
            match = re.search(r'https://meet\.jit\.si/\S+', recent_meeting.message)
            return Response({
                'overdue_count':     overdue_count,
                'meeting_scheduled': False,
                'reason':            'already_scheduled',
                'meeting_link':      match.group(0) if match else None,
            })

        # Generate meeting
        meeting_link     = generate_jitsi_link(user.full_name, user.employee_id)
        minutes_away     = random.randint(5, 10)
        meeting_time     = now + timedelta(minutes=minutes_away)
        meeting_time_str = meeting_time.strftime('%I:%M %p')
        overdue_titles   = list(overdue_qs.values_list('title', flat=True)[:5])
        tasks_list_str   = ", ".join(overdue_titles)

        # Notify employee
        try:
            Notification.objects.create(
                recipient=user,
                sender=None,
                title='📅 Meeting Scheduled — Overdue Tasks',
                message=(
                    f"You currently have {overdue_count} overdue tasks: "
                    f"{tasks_list_str}\n\n"
                    f"A meeting with your manager has been automatically "
                    f"scheduled at {meeting_time_str} (in {minutes_away} minutes).\n\n"
                    f"🔗 Join Meeting:\n{meeting_link}"
                ),
                type='warning',
            )
        except Exception as e:
            logger.error(f'Overdue meeting employee notification failed: {e}')

        # Notify admins
        admins = User.objects.filter(role='admin', is_active=True)
        for admin in admins:
            try:
                Notification.objects.create(
                    recipient=admin,
                    sender=user,
                    title=f'📅 Meeting Scheduled: {user.full_name}',
                    message=(
                        f"{user.full_name} ({user.employee_id}) has "
                        f"{overdue_count} overdue tasks: {tasks_list_str}\n\n"
                        f"A meeting has been auto-scheduled at "
                        f"{meeting_time_str} (in {minutes_away} minutes).\n\n"
                        f"🔗 Meeting Link:\n{meeting_link}"
                    ),
                    type='warning',
                )
            except Exception as e:
                logger.error(f'Overdue meeting admin notification failed: {e}')

        # Send emails
        recipient_emails = [user.email] + list(admins.values_list('email', flat=True))
        recipient_emails = [e for e in recipient_emails if e]

        if recipient_emails:
            try:
                send_mail(
                    subject=f'📅 EMS Pro — Meeting Scheduled ({overdue_count} Overdue Tasks)',
                    message=(
                        f"Hello,\n\n"
                        f"{user.full_name} currently has {overdue_count} overdue tasks:\n"
                        f"{tasks_list_str}\n\n"
                        f"A meeting has been automatically scheduled at "
                        f"{meeting_time_str} (in {minutes_away} minutes).\n\n"
                        f"Join here:\n{meeting_link}\n\n"
                        f"— EMS Pro (automated message)"
                    ),
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=recipient_emails,
                    fail_silently=True,
                )
            except Exception as e:
                logger.error(f'Meeting email error: {e}')

        return Response({
            'overdue_count':     overdue_count,
            'meeting_scheduled': True,
            'meeting_link':      meeting_link,
            'meeting_time':      meeting_time.isoformat(),
            'minutes_away':      minutes_away,
            'overdue_titles':    overdue_titles,
        })