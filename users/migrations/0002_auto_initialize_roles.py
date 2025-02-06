from django.db import migrations
from django.contrib.auth.models import User
from users.models import Profile

def initialize_roles_and_admin(apps, schema_editor):
    # Check if the admin user already exists
    if not User.objects.filter(username='admin').exists():
        admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@gmail.com',
            password='Admin@1234'
        )
        # Create a Profile for the admin user
        Profile.objects.create(user=admin_user, role='admin')

class Migration(migrations.Migration):
    dependencies = [
        ('users', '0001_initial'),  # Ensure this matches your previous migration file
    ]

    operations = [
        migrations.RunPython(initialize_roles_and_admin),
    ]
