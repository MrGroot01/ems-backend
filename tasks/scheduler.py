from apscheduler.schedulers.background import BackgroundScheduler
from django.utils import timezone
from django.db.models import Q
import uuid


def run_task_warning_check():
    print("\n===================================", flush=True)
    print("[CHECK] Running task warning system...", flush=True)
    print("===================================", flush=True)

    try:
        from users.models import User
        from tasks.models import Task
        from notifications.models import Notification

        employees = User.objects.filter(role='employee', is_active=True)
        print(f"Employees Found: {employees.count()}", flush=True)

        for employee in employees:
            print(f"-----------------------------------", flush=True)
            print(f"Checking: {employee.full_name} ({employee.email})", flush=True)

            # Get pending tasks
            pending_tasks = Task.objects.filter(
                assigned_to=employee,
                status__in=['todo', 'in_progress']
            )
            count = pending_tasks.count()
            print(f"Pending Tasks: {count}", flush=True)

            if count >= 2:
                # Generate Jitsi meeting link
                room_name = f"EMS-{employee.employee_id}-{uuid.uuid4().hex[:6].upper()}"
                meeting_link = f"https://meet.jit.si/{room_name}"

                task_titles = ", ".join([t.title for t in pending_tasks[:5]])

                # ── Send Warning Notification ──────────────────
                already_warned = Notification.objects.filter(
                    user=employee,
                    type='warning',
                    title__contains='Task Warning',
                    created_at__date=timezone.now().date(),
                ).exists()

                if not already_warned:
                    Notification.objects.create(
                        user=employee,
                        title=f'⚠️ Task Warning — {count} Incomplete Tasks',
                        message=(
                            f'You have {count} incomplete tasks: {task_titles}. '
                            f'Please complete them immediately.'
                        ),
                        type='warning',
                    )
                    print(f"[SENT] Warning notification to {employee.full_name}", flush=True)

                # ── Send Meeting Notification ──────────────────
                already_meeting = Notification.objects.filter(
                    user=employee,
                    type='warning',
                    title__contains='Meeting',
                    created_at__date=timezone.now().date(),
                ).exists()

                if not already_meeting:
                    Notification.objects.create(
                        user=employee,
                        title=f'📅 Meeting Scheduled — Tasks Still Pending',
                        message=(
                            f'A meeting has been scheduled because you have '
                            f'{count} incomplete tasks: {task_titles}. '
                            f'Join immediately: {meeting_link}'
                        ),
                        type='warning',
                    )
                    print(f"[SENT] Meeting notification: {meeting_link}", flush=True)
                else:
                    print(f"Skipped: Already notified today", flush=True)

            else:
                print(f"Skipped: Less than 2 pending tasks", flush=True)

        print("===================================", flush=True)
        print("[COMPLETED] Task warning system done.", flush=True)
        print("===================================\n", flush=True)

    except Exception as e:
        print(f"[ERROR] Task warning check failed: {e}", flush=True)
        import traceback
        traceback.print_exc()


def start_scheduler():
    scheduler = BackgroundScheduler(timezone='Asia/Kolkata')
    scheduler.add_job(
        run_task_warning_check,
        'interval',
        minutes=5,
        id='run_task_warning_check',
        replace_existing=True,
    )
    scheduler.start()
    print("[Scheduler] ✅ Task warning scheduler started (every 5 minutes)", flush=True)
    return scheduler