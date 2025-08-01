from django.apps import AppConfig
from django.db.utils import OperationalError, ProgrammingError

class TrackerConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'tracker'

    def ready(self):
        from django.contrib.auth import get_user_model
        User = get_user_model()
        try:
            if not User.objects.filter(username='admin').exists():
                User.objects.create_superuser(
                    username='admin',
                    email='admin@example.com',
                    password='password123@@',
                    department='Admin'
                )
                print("✅ Default admin user created.")
        except (OperationalError, ProgrammingError):
            # This avoids issues before migrations are applied
            pass
