"""
Management command to test order email notifications
Usage: python manage.py test_order_email
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from orders.models import Order, OrderLine
from catalogue.models import Product
from cart.views import send_order_notification_email, send_customer_confirmation_email


class Command(BaseCommand):
    help = 'Create a test order and send notification email'

    def add_arguments(self, parser):
        parser.add_argument(
            '--user',
            type=str,
            help='Username to create order for (defaults to first user)',
        )
        parser.add_argument(
            '--no-email',
            action='store_true',
            help='Create order but do not send email',
        )

    def handle(self, *args, **options):
        # Get user
        username = options.get('user')
        if username:
            try:
                user = User.objects.get(username=username)
            except User.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'User "{username}" not found'))
                return
        else:
            user = User.objects.first()
            if not user:
                self.stdout.write(self.style.ERROR('No users found in database'))
                return

        # Get some available products
        products = Product.objects.filter(available=True)[:3]
        if not products:
            self.stdout.write(self.style.ERROR('No available products found'))
            return

        # Create test order
        order = Order.objects.create(
            customer=user,
            status='new',
            notes='This is a test order created for email testing'
        )

        # Add products to order
        for i, product in enumerate(products, 1):
            OrderLine.objects.create(
                order=order,
                product=product,
                quantity=i,  # 1, 2, 3...
                unit_price_ex_gst=product.price_ex_gst,
                unit_price_inc_gst=product.price_inc_gst
            )

        self.stdout.write(self.style.SUCCESS(f'✓ Test order #{order.id} created'))
        self.stdout.write(f'  Customer: {user.username} ({user.email})')
        self.stdout.write(f'  Items: {order.lines.count()}')
        self.stdout.write(f'  Total: A$ {order.get_total_inc_gst():.2f}')

        # Send email unless --no-email flag is used
        if not options.get('no_email'):
            try:
                self.stdout.write('')
                self.stdout.write('Sending admin notification email...')
                send_order_notification_email(order)
                self.stdout.write(self.style.SUCCESS('✓ Admin notification sent to mpbenti@gmail.com and mpbenti2@gmail.com'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'✗ Failed to send admin email: {e}'))

            try:
                self.stdout.write('')
                self.stdout.write('Sending customer confirmation email...')
                send_customer_confirmation_email(order)
                self.stdout.write(self.style.SUCCESS(f'✓ Customer confirmation sent to {user.email}'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'✗ Failed to send customer email: {e}'))

            self.stdout.write('')
            self.stdout.write(self.style.WARNING('Check your email output:'))
            self.stdout.write('  - Console: Check terminal output above')
            self.stdout.write('  - File: Check EMAIL_FILE_PATH directory')
            self.stdout.write('  - SMTP: Check recipient inbox or Mailtrap/Mailhog')
        else:
            self.stdout.write('Email sending skipped (--no-email flag used)')

        self.stdout.write('')
        self.stdout.write(f'View order at: http://localhost:8000/dashboard/orders/{order.id}/')

