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
    clean_name = re.sub(r'[^a-zA-Z0-9]', '', str(employee_name).replace(' ', ''))
    import uuid
    unique_id = str(uuid.uuid4())[:8]
    room_name = f"EMS-{clean_name}-{employee_id}-{unique_id}"
    return f"https://meet.jit.si/{room_name}"


# =========================================================
# Safe notification helper
# Your Notification model fields: id, user, title, message,
# type, is_read, created_at  (NO sender field)
# =========================================================
def _notif(user, title, message, ntype='warning'):
    """Create notification using only fields your model actually has."""
    try:
        Notification.objects.create(
            user=user,
            title=title,
            message=message,
            type=ntype,
        )
        return True
    except Exception as e:
        logger.error(f'Notification.create failed for user={user.pk}: {e}')
        return False


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
    # =====================================================
    def perform_create(self, serializer):
        task = serializer.save(assigned_by=self.request.user)
        _notif(
            user=task.assigned_to,
            title='New Task Assigned',
            message=f'You have been assigned: "{task.title}" – due {task.due_date}',
            ntype='task',
        )

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
            .annotate(pending_count=Count('tasks', filter=Q(tasks__status__in=['todo', 'in_progress'])))
            .filter(pending_count__gte=2)
        )
        data = []
        for emp in at_risk:
            pending = Task.objects.filter(assigned_to=emp, status__in=['todo', 'in_progress']).values(
                'id', 'title', 'priority', 'due_date', 'status'
            )
            data.append({
                'employee_id':   emp.id,
                'employee_name': emp.full_name,
                'employee_code': getattr(emp, 'employee_id', str(emp.pk)),
                'email':         emp.email,
                'pending_count': emp.pending_count,
                'pending_tasks': list(pending),
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

        pending    = Task.objects.filter(assigned_to=employee, status__in=['todo', 'in_progress'])
        task_titles = ", ".join(pending.values_list('title', flat=True)[:3])
        emp_id     = getattr(employee, 'employee_id', None) or str(employee.pk)
        emp_name   = getattr(employee, 'full_name', None) or employee.username or str(employee.pk)
        meeting_link = generate_jitsi_link(emp_name, emp_id)

        _notif(employee, '📅 Meeting Scheduled',
            f"Meeting scheduled for your pending tasks: {task_titles}\n\n🔗 Join:\n{meeting_link}")

        for admin in User.objects.filter(role='admin', is_active=True):
            _notif(admin, f'📅 Meeting: {emp_name}',
                f"Meeting for {emp_name}\nTasks: {task_titles}\n🔗 Join:\n{meeting_link}")

        return Response({'message': f'Meeting scheduled for {emp_name}', 'meeting_link': meeting_link})

    # =====================================================
    # AUTO MEETING ON 2+ OVERDUE TASKS
    # =====================================================
    @action(detail=False, methods=['post'])
    def check_overdue_meeting(self, request):
        user  = request.user
        now   = timezone.now()
        today = now.date()

        # ── Find overdue tasks ────────────────────────────────
        overdue_qs    = Task.objects.filter(
            assigned_to=user,
            status__in=['todo', 'in_progress'],
            due_date__lt=today,
        )
        overdue_count = overdue_qs.count()

        if overdue_count < 2:
            return Response({'overdue_count': overdue_count, 'meeting_scheduled': False})

        # ── Anti-spam: check if meeting was scheduled in last 20 min ──
        # Uses 'user' field (confirmed from your model)
        try:
            recent_meeting = Notification.objects.filter(
                user=user,
                title__icontains='Meeting Scheduled',
                created_at__gte=now - timedelta(minutes=20),
            ).order_by('-created_at').first()
        except Exception as e:
            logger.error(f'recent_meeting query error: {e}')
            recent_meeting = None

        if recent_meeting:
            match = re.search(r'https://meet\.jit\.si/\S+', recent_meeting.message or '')
            return Response({
                'overdue_count':     overdue_count,
                'meeting_scheduled': False,
                'reason':            'already_scheduled',
                'meeting_link':      match.group(0) if match else None,
            })

        # ── Resolve user fields safely ────────────────────────
        emp_id = (
            getattr(user, 'employee_id', None) or
            getattr(user, 'emp_id', None) or
            str(user.pk)
        )
        emp_name = (
            getattr(user, 'full_name', None) or
            user.get_full_name() or
            user.username or
            str(user.pk)
        )

        # ── Generate meeting ──────────────────────────────────
        try:
            meeting_link = generate_jitsi_link(emp_name, emp_id)
        except Exception as e:
            import uuid
            meeting_link = f"https://meet.jit.si/EMS-{user.pk}-{uuid.uuid4().hex[:8]}"
            logger.error(f'jitsi link fallback used: {e}')

        minutes_away     = random.randint(5, 10)
        meeting_time     = now + timedelta(minutes=minutes_away)
        meeting_time_str = meeting_time.strftime('%I:%M %p')
        overdue_titles   = list(overdue_qs.values_list('title', flat=True)[:5])
        tasks_str        = ", ".join(overdue_titles)

        # ── Notify employee (uses user= field only) ───────────
        notif_ok = _notif(
            user=user,
            title='📅 Meeting Scheduled — Overdue Tasks',
            message=(
                f"You have {overdue_count} overdue tasks: {tasks_str}\n\n"
                f"A meeting has been auto-scheduled at {meeting_time_str} "
                f"(in {minutes_away} minutes).\n\n"
                f"🔗 Join Meeting:\n{meeting_link}"
            ),
            ntype='warning',
        )

        # ── Notify admins (uses user= field only) ─────────────
        admins_qs = User.objects.filter(role='admin', is_active=True)
        for admin in admins_qs:
            _notif(
                user=admin,
                title=f'📅 Meeting Scheduled: {emp_name}',
                message=(
                    f"{emp_name} has {overdue_count} overdue tasks: {tasks_str}\n\n"
                    f"Meeting at {meeting_time_str} (in {minutes_away} min).\n\n"
                    f"🔗 Meeting Link:\n{meeting_link}"
                ),
                ntype='warning',
            )

        # ── Send emails ───────────────────────────────────────
        try:
            admin_emails = list(admins_qs.values_list('email', flat=True))
            all_emails   = [e for e in ([user.email] + admin_emails) if e]
            if all_emails:
                send_mail(
                    subject=f'📅 EMS Pro — Meeting Scheduled ({overdue_count} Overdue Tasks)',
                    message=(
                        f"Hello,\n\n"
                        f"{emp_name} has {overdue_count} overdue tasks:\n"
                        f"{tasks_str}\n\n"
                        f"Meeting auto-scheduled at {meeting_time_str} "
                        f"(in {minutes_away} minutes).\n\n"
                        f"Join here:\n{meeting_link}\n\n"
                        f"— EMS Pro (automated message)"
                    ),
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=all_emails,
                    fail_silently=True,
                )
                logger.info(f'Meeting email sent to: {all_emails}')
        except Exception as e:
            logger.error(f'Meeting email error: {e}')

        return Response({
            'overdue_count':     overdue_count,
            'meeting_scheduled': True,
            'meeting_link':      meeting_link,
            'meeting_time':      meeting_time.isoformat(),
            'minutes_away':      minutes_away,
            'overdue_titles':    overdue_titles,
            'notif_created':     notif_ok,
        })