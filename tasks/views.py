from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from django.utils import timezone
from django.db.models import Count, Q

from .models import Task
from .serializers import TaskSerializer

from notifications.models import Notification
from users.models import User


# =========================================================
# Generate Jitsi Meet Link
# =========================================================
def generate_jitsi_link(employee_name, employee_id):

    import re
    import uuid

    clean_name = re.sub(
        r'[^a-zA-Z0-9]',
        '',
        employee_name.replace(' ', '')
    )

    unique_id = str(uuid.uuid4())[:8]

    room_name = f"EMS-{clean_name}-{employee_id}-{unique_id}"

    return f"https://meet.jit.si/{room_name}"


# =========================================================
# Task ViewSet
# =========================================================
class TaskViewSet(viewsets.ModelViewSet):

    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated]

    # =====================================================
    # GET TASKS (YOUR OLD CODE KEPT)
    # =====================================================
    def get_queryset(self):

        user = self.request.user

        # OLD CODE
        if user.role == 'admin':
            return Task.objects.select_related(
                'assigned_to',
                'assigned_by'
            ).all()

        return Task.objects.filter(
            assigned_to=user
        ).select_related(
            'assigned_to',
            'assigned_by'
        )

    # =====================================================
    # CREATE TASK (YOUR OLD CODE KEPT)
    # =====================================================
    def perform_create(self, serializer):

        # OLD CODE
        task = serializer.save(
            assigned_by=self.request.user
        )

        # OLD CODE
        Notification.objects.create(
            recipient=task.assigned_to,
            sender=self.request.user,

            title='New Task Assigned',

            message=(
                f'You have been assigned: '
                f'"{task.title}" – due {task.due_date}'
            ),

            type='task'
        )

    # =====================================================
    # UPDATE PROGRESS (YOUR OLD CODE KEPT)
    # =====================================================
    @action(detail=True, methods=['patch'])
    def update_progress(self, request, pk=None):

        # OLD CODE
        task = self.get_object()

        progress = int(
            request.data.get(
                'progress',
                task.progress
            )
        )

        s_status = request.data.get(
            'status',
            task.status
        )

        task.progress = min(
            100,
            max(0, progress)
        )

        task.status = s_status

        # OLD CODE
        if task.progress == 100:
            task.status = 'completed'
            task.completed_at = timezone.now()

        task.save()

        return Response(
            TaskSerializer(task).data
        )

    # =====================================================
    # NEW FEATURE:
    # MANUAL WARNING CHECK
    # =====================================================
    @action(detail=False, methods=['post'])
    def trigger_warning_check(self, request):

        if request.user.role != 'admin':
            return Response(
                {'error': 'Admin only'},
                status=403
            )

        from django.core.management import call_command

        try:

            call_command('check_task_warnings')

            return Response({
                'message':
                'Warning check completed successfully'
            })

        except Exception as e:

            return Response(
                {'error': str(e)},
                status=500
            )

    # =====================================================
    # NEW FEATURE:
    # GET EMPLOYEES WITH 2+ TASKS
    # =====================================================
    @action(detail=False, methods=['get'])
    def at_risk_employees(self, request):

        if request.user.role != 'admin':
            return Response(
                {'error': 'Admin only'},
                status=403
            )

        at_risk_employees = (

            User.objects

            .filter(
                role='employee',
                is_active=True
            )

            .annotate(
                pending_count=Count(
                    'tasks',
                    filter=Q(
                        tasks__status__in=[
                            'todo',
                            'in_progress'
                        ]
                    )
                )
            )

            .filter(
                pending_count__gte=2
            )
        )

        data = []

        for employee in at_risk_employees:

            pending_tasks = Task.objects.filter(
                assigned_to=employee,
                status__in=[
                    'todo',
                    'in_progress'
                ]
            ).values(
                'id',
                'title',
                'priority',
                'due_date',
                'status'
            )

            data.append({

                'employee_id': employee.id,

                'employee_name': employee.full_name,

                'employee_code': employee.employee_id,

                'email': employee.email,

                'pending_count': employee.pending_count,

                'pending_tasks': list(pending_tasks),
            })

        return Response(data)

    # =====================================================
    # NEW FEATURE:
    # MANUAL MEETING SCHEDULER
    # =====================================================
    @action(detail=False, methods=['post'])
    def schedule_meeting(self, request):

        if request.user.role != 'admin':
            return Response(
                {'error': 'Admin only'},
                status=403
            )

        employee_id = request.data.get('employee_id')

        if not employee_id:
            return Response(
                {'error': 'employee_id required'},
                status=400
            )

        # Find employee
        try:

            employee = User.objects.get(
                id=employee_id,
                role='employee'
            )

        except User.DoesNotExist:

            return Response(
                {'error': 'Employee not found'},
                status=404
            )

        # Pending tasks
        pending_tasks = Task.objects.filter(
            assigned_to=employee,
            status__in=[
                'todo',
                'in_progress'
            ]
        )

        task_titles = ", ".join(

            pending_tasks.values_list(
                'title',
                flat=True
            )[:3]
        )

        # Generate meeting link
        meeting_link = generate_jitsi_link(
            employee.full_name,
            employee.employee_id
        )

        # Notify employee
        Notification.objects.create(

            recipient=employee,

            sender=request.user,

            title='📅 Meeting Scheduled',

            message=(
                f"A meeting has been scheduled "
                f"regarding your pending tasks: "
                f"{task_titles}\n\n"

                f"🔗 Join Meeting:\n"
                f"{meeting_link}\n\n"

                f"Please join at the scheduled time."
            ),

            type='warning',
        )

        # Notify admins
        admins = User.objects.filter(
            role='admin',
            is_active=True
        )

        for admin in admins:

            Notification.objects.create(

                recipient=admin,

                sender=request.user,

                title=(
                    f'📅 Meeting Scheduled: '
                    f'{employee.full_name}'
                ),

                message=(
                    f"Meeting scheduled for "
                    f"{employee.full_name}\n\n"

                    f"Pending Tasks: "
                    f"{task_titles}\n\n"

                    f"🔗 Meeting Link:\n"
                    f"{meeting_link}"
                ),

                type='warning',
            )

        return Response({

            'message':
            f'Meeting scheduled for '
            f'{employee.full_name}',

            'meeting_link': meeting_link,

            'employee': employee.full_name,

            'tasks': task_titles,
        })