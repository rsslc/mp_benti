from django.core.management.base import BaseCommand
from django.contrib.auth.models import User


class Command(BaseCommand):
    help = 'Grant staff access to a user for dashboard access'

    def add_arguments(self, parser):
        parser.add_argument('username', type=str, help='Username to grant staff access')
        parser.add_argument(
            '--superuser',
            action='store_true',
            help='Also grant superuser privileges',
        )

    def handle(self, *args, **options):
        username = options['username']
        make_superuser = options['superuser']

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'User "{username}" does not exist'))
            return

        user.is_staff = True
        if make_superuser:
            user.is_superuser = True
        user.save()

        self.stdout.write(self.style.SUCCESS(f'✓ Successfully granted staff access to {username}'))
        if make_superuser:
            self.stdout.write(self.style.SUCCESS(f'✓ Successfully granted superuser access to {username}'))

        self.stdout.write(self.style.WARNING('\nUser permissions:'))
        self.stdout.write(f'  is_staff: {user.is_staff}')
        self.stdout.write(f'  is_superuser: {user.is_superuser}')
        self.stdout.write(f'  Dashboard access: {"✓ Granted" if user.is_staff else "✗ Denied"}')
