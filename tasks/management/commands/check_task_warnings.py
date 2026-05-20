"""
tasks/management/commands/check_task_warnings.py

RUN:   python manage.py check_task_warnings
CRON:  */15 * * * * /path/to/venv/bin/python /path/to/manage.py check_task_warnings
"""

import re
import uuid
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from tasks.models import Task
from notifications.models import Notification
from users.models import User


def generate_jitsi_link(full_name, employee_id):
    clean_name = re.sub(r'[^a-zA-Z0-9]', '', full_name.replace(' ', ''))
    unique_id  = str(uuid.uuid4())[:8]
    room_name  = f"EMS-{clean_name}-{employee_id}-{unique_id}"
    return f"https://meet.jit.si/{room_name}"


class Command(BaseCommand):
    help = "Check employees with incomplete tasks and auto-schedule meetings"

    def handle(self, *args, **kwargs):
        self.stdout.write("\n===================================")
        self.stdout.write("[CHECK] Running task warning system...")
        self.stdout.write("===================================\n")

        # ── All active employees (role='employee') ─────────────
        employees = User.objects.filter(
            role='employee',
            is_active=True,
        )
        self.stdout.write(f"Employees Found: {employees.count()}\n")

        for employee in employees:
            self.stdout.write("-----------------------------------")
            self.stdout.write(
                f"Checking: {employee.full_name} ({employee.email})"
            )

            # ── Pending Tasks ──────────────────────────────────
            pending_tasks = Task.objects.filter(
                assigned_to=employee,
                status__in=['todo', 'in_progress', 'pending'],
            )
            pending_count = pending_tasks.count()
            self.stdout.write(f"Pending Tasks: {pending_count}")

            for task in pending_tasks:
                self.stdout.write(f"  - {task.title} [{task.status}]")

            # Skip if less than 2
            if pending_count < 2:
                self.stdout.write("Skipped: Less than 2 pending tasks\n")
                continue

            # ── Check existing warning ─────────────────────────
            existing_warning = Notification.objects.filter(
                recipient=employee,
                type='warning',
                title__icontains='Task Warning',
            ).order_by('-created_at').first()

            self.stdout.write(
                f"Existing Warning: {'YES' if existing_warning else 'NO'}"
            )

            # ── Send first warning ─────────────────────────────
            if not existing_warning:
                Notification.objects.create(
                    sender=None,
                    recipient=employee,
                    title='⚠️ Task Warning',
                    message=(
                        f"Hi {employee.full_name},\n\n"
                        f"You currently have {pending_count} incomplete tasks.\n\n"
                        f"Please complete your tasks within 15 minutes.\n\n"
                        f"If tasks are not completed, a meeting will be "
                        f"automatically scheduled with your manager."
                    ),
                    type='warning',
                )
                self.stdout.write(
                    self.style.WARNING(f"[WARNING SENT] {employee.full_name}\n")
                )
                continue

            # ── Check 15-minute window ─────────────────────────
            warning_time = existing_warning.created_at
            self.stdout.write(f"Warning Created At: {warning_time}")

            if timezone.now() < warning_time + timedelta(minutes=15):
                self.stdout.write("Still within 15-minute window. Waiting...\n")
                continue

            # ── Check if meeting already scheduled ────────────
            existing_meeting = Notification.objects.filter(
                recipient=employee,
                type='warning',
                title__icontains='Meeting Scheduled',
            ).exists()

            self.stdout.write(
                f"Existing Meeting: {'YES' if existing_meeting else 'NO'}"
            )

            if existing_meeting:
                self.stdout.write("Meeting already scheduled. Skipping.\n")
                continue

            # ── Generate Jitsi link ────────────────────────────
            meeting_link = generate_jitsi_link(
                employee.full_name,
                employee.employee_id,
            )

            task_titles = "\n".join(
                f"• {t}" for t in
                pending_tasks.values_list('title', flat=True)[:5]
            )

            # ── Notify Employee ────────────────────────────────
            Notification.objects.create(
                sender=None,
                recipient=employee,
                title='📅 Meeting Scheduled',
                message=(
                    f"Hi {employee.full_name},\n\n"
                    f"A meeting has been scheduled because you have "
                    f"{pending_count} incomplete tasks.\n\n"
                    f"Pending Tasks:\n{task_titles}\n\n"
                    f"🔗 Join Meeting:\n{meeting_link}"
                ),
                type='warning',
            )
            self.stdout.write(
                self.style.SUCCESS(
                    f"[MEETING CREATED] {employee.full_name}"
                )
            )

            # ── Notify All Admins ──────────────────────────────
            admins = User.objects.filter(
                role='admin',
                is_active=True,
            )
            admin_count = 0
            for admin in admins:
                Notification.objects.create(
                    sender=None,
                    recipient=admin,
                    title=f'📅 Meeting Scheduled: {employee.full_name}',
                    message=(
                        f"Auto-meeting scheduled for "
                        f"{employee.full_name} ({employee.email})\n"
                        f"Department: {employee.department or 'N/A'}\n"
                        f"Employee ID: {employee.employee_id}\n\n"
                        f"Reason: {pending_count} incomplete tasks.\n\n"
                        f"Pending Tasks:\n{task_titles}\n\n"
                        f"🔗 Meeting Link:\n{meeting_link}"
                    ),
                    type='warning',
                )
                admin_count += 1

            self.stdout.write(f"Admins Notified: {admin_count}\n")

        self.stdout.write("===================================")
        self.stdout.write(
            self.style.SUCCESS("[COMPLETED] Task warning system done.")
        )
        self.stdout.write("===================================\n")