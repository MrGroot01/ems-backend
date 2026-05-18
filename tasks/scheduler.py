"""
tasks/scheduler.py

Runs automatic task warning checks
every 5 minutes using APScheduler.
"""

from apscheduler.schedulers.background import BackgroundScheduler
from django.utils import timezone


# =========================================================
# Run Warning Check
# =========================================================
def run_task_warning_check():

    """
    Runs the management command:
    check_task_warnings
    """

    from django.core.management import call_command

    print(
        f"[Scheduler] Running task warning check at "
        f"{timezone.now()}"
    )

    try:

        call_command('check_task_warnings')

        print(
            "[Scheduler] Warning check completed"
        )

    except Exception as e:

        print(
            f"[Scheduler] Error: {e}"
        )


# =========================================================
# Start Scheduler
# =========================================================
def start():

    """
    Starts APScheduler background scheduler
    """

    scheduler = BackgroundScheduler()

    scheduler.add_job(

        run_task_warning_check,

        trigger='interval',

        minutes=5,

        id='task_warning_check',

        replace_existing=True,
    )

    scheduler.start()

    print(
        "[Scheduler] ✅ Task warning scheduler started "
        "(every 5 minutes)"
    )