"""
tasks/management/commands/check_task_warnings.py
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta

from tasks.models import Task
from notifications.models import Notification
from users.models import User


# =========================================================
# Generate Jitsi Link
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
# Django Command
# =========================================================
class Command(BaseCommand):

    help = "Checks employees with incomplete tasks"

    def handle(self, *args, **kwargs):

        print("\n===================================")
        print("[CHECK] Running task warning system...")
        print("===================================\n")

        employees = User.objects.filter(
            role='employee',
            is_active=True
        )

        print(f"Employees Found: {employees.count()}\n")

        for employee in employees:

            print("-----------------------------------")
            print(f"Checking Employee: {employee.email}")

            # =================================================
            # Pending Tasks
            # =================================================
            pending_tasks = Task.objects.filter(
                assigned_to=employee,
                status__in=[
                    'todo',
                    'in_progress'
                ]
            )

            pending_count = pending_tasks.count()

            print(f"Pending Tasks: {pending_count}")

            # Debug task list
            for task in pending_tasks:
                print(
                    f" - {task.title} ({task.status})"
                )

            # Skip if less than 2
            if pending_count < 2:

                print("Skipped: Less than 2 tasks\n")

                continue

            # =================================================
            # Existing Warning
            # =================================================
            existing_warning = Notification.objects.filter(
                recipient=employee,
                type='warning',
                title__icontains='Task Warning'
            ).order_by('-created_at').first()

            print(
                "Existing Warning:",
                "YES" if existing_warning else "NO"
            )

            # =================================================
            # Send Warning
            # =================================================
            if not existing_warning:

                Notification.objects.create(

                    sender=None,

                    recipient=employee,

                    title='⚠️ Task Warning',

                    message=(
                        f"You currently have "
                        f"{pending_count} incomplete tasks.\n\n"

                        f"Please complete your tasks "
                        f"within 15 minutes.\n\n"

                        f"If tasks are not completed, "
                        f"a meeting will automatically "
                        f"be scheduled."
                    ),

                    type='warning'
                )

                print(
                    f"[WARNING SENT] {employee.full_name}\n"
                )

                continue

            # =================================================
            # Check Warning Time
            # =================================================
            warning_time = existing_warning.created_at

            print(
                "Warning Created At:",
                warning_time
            )

            # Wait 15 mins
            if timezone.now() < warning_time + timedelta(minutes=15):

                print(
                    "Waiting for 15 minutes...\n"
                )

                continue

            # =================================================
            # Existing Meeting
            # =================================================
            existing_meeting = Notification.objects.filter(
                recipient=employee,
                type='warning',
                title__icontains='Meeting Scheduled'
            ).exists()

            print(
                "Existing Meeting:",
                "YES" if existing_meeting else "NO"
            )

            if existing_meeting:

                print(
                    "Meeting already exists\n"
                )

                continue

            # =================================================
            # Generate Meeting
            # =================================================
            meeting_link = generate_jitsi_link(
                employee.full_name,
                employee.employee_id
            )

            task_titles = ", ".join(
                pending_tasks.values_list(
                    'title',
                    flat=True
                )[:5]
            )

            # =================================================
            # Notify Employee
            # =================================================
            Notification.objects.create(

                sender=None,

                recipient=employee,

                title='📅 Meeting Scheduled',

                message=(
                    f"A meeting has been scheduled.\n\n"

                    f"Pending Tasks:\n"
                    f"{task_titles}\n\n"

                    f"🔗 Join Meeting:\n"
                    f"{meeting_link}"
                ),

                type='warning'
            )

            print(
                f"[MEETING CREATED] {employee.full_name}"
            )

            # =================================================
            # Notify Admins
            # =================================================
            admins = User.objects.filter(
                role='admin',
                is_active=True
            )

            for admin in admins:

                Notification.objects.create(

                    sender=None,

                    recipient=admin,

                    title=(
                        f"📅 Meeting Scheduled: "
                        f"{employee.full_name}"
                    ),

                    message=(
                        f"Meeting scheduled for "
                        f"{employee.full_name}\n\n"

                        f"🔗 Meeting Link:\n"
                        f"{meeting_link}"
                    ),

                    type='warning'
                )

            print()

        print("===================================")
        print("[CHECK COMPLETED]")
        print("===================================\n")