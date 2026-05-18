from django.apps import AppConfig


class TasksConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'tasks'

    def ready(self):
        """
        Start APScheduler automatically
        when Django server starts.
        """

        import sys

        # Prevent duplicate scheduler runs
        if 'runserver' in sys.argv:
            try:
                from tasks.scheduler import start
                start()
            except Exception as e:
                print("Scheduler startup error:", e)