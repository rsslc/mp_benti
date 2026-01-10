# Email Testing Guide

## Overview
When a customer completes an order (checkout), the system sends two types of emails:

1. **Admin Notification Email**: Sent to `mpbenti@gmail.com` and `mpbenti2@gmail.com` with order details
2. **Customer Confirmation Email**: Sent to the customer who placed the order

The email sending functionality is located in:
- **File**: `cart/views.py`
- **Functions**: 
  - `send_order_notification_email()` - Sends to admin/owner
  - `send_customer_confirmation_email()` - Sends to customer
- **Triggered from**: `checkout()` view when order is created

### Email Templates
- **Admin notification**: `templates/cart/order_notification_email.txt`
- **Customer confirmation**: `templates/cart/customer_confirmation_email.txt`

## Current Email Configuration

Your email settings are configured in `core/settings.py`:

```python
EMAIL_BACKEND = env('EMAIL_BACKEND', default='django.core.mail.backends.console.EmailBackend')
EMAIL_HOST = env('EMAIL_HOST', default='')
EMAIL_PORT = env.int('EMAIL_PORT', default=587)
EMAIL_USE_TLS = env.bool('EMAIL_USE_TLS', default=True)
EMAIL_HOST_USER = env('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = env('DEFAULT_FROM_EMAIL', default='noreply@mpbenti.com.au')
```

**Default behavior**: Emails are sent to the **console** (terminal output), not to actual email addresses.

---

## Testing Methods

### Method 1: Console Backend (Default - Currently Active)

**Best for**: Quick development testing without email setup

The current configuration prints emails to your terminal/console where the Django development server is running.

**How to test**:
1. Start your development server:
   ```bash
   python manage.py runserver
   ```

2. Place a test order:
   - Login as a customer
   - Add products to cart
   - Go to checkout: http://localhost:8000/cart/checkout/
   - Submit the order

3. Check your terminal where the server is running - you'll see both email contents printed there:
   ```
   Content-Type: text/plain; charset="utf-8"
   MIME-Version: 1.0
   Content-Transfer-Encoding: 7bit
   Subject: New Order #123 from testuser
   From: noreply@mpbenti.com.au
   To: mpbenti@gmail.com, mpbenti2@gmail.com
   Date: ...
   
   New Order Received - Order #123
   ...
   ```
   
   Followed by:
   ```
   Subject: Order Confirmation - Order #123
   From: noreply@mpbenti.com.au
   To: customer@example.com
   Date: ...
   
   Order Confirmation - MP Benti
   ...
   ```

**No configuration needed** - this is your current setup!

---

### Method 2: File Backend

**Best for**: Saving emails as files to review later

**Setup**:
Add to your `.env` file:
```env
EMAIL_BACKEND=django.core.mail.backends.filebased.EmailBackend
EMAIL_FILE_PATH=/tmp/app-emails
```

**How to test**:
1. Create the directory:
   ```bash
   mkdir -p /tmp/app-emails
   ```

2. Restart your server and place an order

3. Check the email files:
   ```bash
   ls -la /tmp/app-emails/
   cat /tmp/app-emails/[filename]
   ```

---

### Method 3: Gmail SMTP (Real Emails)

**Best for**: Testing actual email delivery

**Setup**:

1. **Enable 2-Factor Authentication** on your Gmail account

2. **Create an App Password**:
   - Go to: https://myaccount.google.com/apppasswords
   - Select "Mail" and your device
   - Copy the generated 16-character password

3. **Update your `.env` file**:
   ```env
   EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
   EMAIL_HOST=smtp.gmail.com
   EMAIL_PORT=587
   EMAIL_USE_TLS=True
   EMAIL_HOST_USER=your-email@gmail.com
   EMAIL_HOST_PASSWORD=your-app-password-here
   DEFAULT_FROM_EMAIL=your-email@gmail.com
   ```

4. **Restart your server**

**How to test**:
1. Place a test order through checkout
2. Check `mpbenti@gmail.com` and `mpbenti2@gmail.com` inboxes for the admin notification
3. Check the customer's email inbox for the confirmation email

**Note**: For testing, you might want to temporarily change the recipient email addresses in `cart/views.py` to your own email address.

---

### Method 4: Mailtrap / Mailhog (Fake SMTP)

**Best for**: Testing email design and content without sending real emails

**Mailtrap** (online service):
1. Sign up at https://mailtrap.io (free tier available)
2. Get SMTP credentials from your inbox
3. Update `.env`:
   ```env
   EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
   EMAIL_HOST=smtp.mailtrap.io
   EMAIL_PORT=2525
   EMAIL_USE_TLS=True
   EMAIL_HOST_USER=your-mailtrap-username
   EMAIL_HOST_PASSWORD=your-mailtrap-password
   ```

**Mailhog** (local service):
1. Install with Homebrew:
   ```bash
   brew install mailhog
   ```

2. Start Mailhog:
   ```bash
   mailhog
   ```

3. Update `.env`:
   ```env
   EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
   EMAIL_HOST=localhost
   EMAIL_PORT=1025
   EMAIL_USE_TLS=False
   ```

4. View emails at: http://localhost:8025

---

## Quick Test Script

You can also test emails directly from Django shell:

```bash
python manage.py shell
```

```python
from django.core.mail import send_mail
from django.conf import settings

send_mail(
    'Test Email',
    'This is a test email from MP Benti.',
    settings.DEFAULT_FROM_EMAIL,
    ['mpbenti@gmail.com'],
    fail_silently=False,
)
```

---

## Testing Order Email Specifically

### Option 1: Place a Real Order
1. Login as a test customer
2. Add products to cart
3. Go through checkout
4. Check email output (console/file/inbox depending on backend)

### Option 2: Test Email Function Directly

Create a test script `test_order_email.py`:

```python
from django.contrib.auth.models import User
from orders.models import Order, OrderLine
from catalogue.models import Product
from cart.views import send_order_notification_email, send_customer_confirmation_email

# Get or create a test user
user = User.objects.first()

# Get some products
products = Product.objects.filter(available=True)[:2]

# Create a test order
order = Order.objects.create(customer=user, status='new', notes='Test order for email')

for product in products:
    OrderLine.objects.create(
        order=order,
        product=product,
        quantity=2,
        unit_price_ex_gst=product.price_ex_gst,
        unit_price_inc_gst=product.price_inc_gst
    )

# Send both emails
send_order_notification_email(order)
send_customer_confirmation_email(order)
print(f"Emails sent for order #{order.id}")
```

Run it:
```bash
python manage.py shell < test_order_email.py
```

---

## Troubleshooting

### Email not appearing in console
- Check that your server is running in the terminal
- Verify `EMAIL_BACKEND` is set to `console.EmailBackend`

### Gmail authentication fails
- Ensure 2FA is enabled on your Gmail account
- Use an App Password, not your regular password
- Check that "Less secure app access" is not blocking (should use App Password instead)

### No error but email not received
- Check spam folder
- Verify the recipient email address
- Check Django logs for email errors
- Try the test script above to isolate the issue

### Connection timeout
- Check firewall settings
- Verify `EMAIL_PORT` (usually 587 for TLS, 465 for SSL)
- Ensure `EMAIL_USE_TLS` matches your port

---

## Customizing Email Content

The email templates are located at:
- **Admin notification**: `templates/cart/order_notification_email.txt`
- **Customer confirmation**: `templates/cart/customer_confirmation_email.txt`

You can modify these templates to change the email content.

### Adding HTML Emails

To send HTML emails instead of plain text, modify `cart/views.py`:

```python
from django.core.mail import EmailMultiAlternatives

def send_order_notification_email(order):
    subject = f'New Order #{order.id} from {order.customer.username}'
    
    # ... prepare context ...
    
    text_content = render_to_string('cart/order_notification_email.txt', context)
    html_content = render_to_string('cart/order_notification_email.html', context)
    
    email = EmailMultiAlternatives(
        subject,
        text_content,
        settings.DEFAULT_FROM_EMAIL,
        ['mpbenti@gmail.com', 'mpbenti2@gmail.com']
    )
    email.attach_alternative(html_content, "text/html")
    email.send()

def send_customer_confirmation_email(order):
    subject = f'Order Confirmation - Order #{order.id}'
    
    # ... prepare context ...
    
    text_content = render_to_string('cart/customer_confirmation_email.txt', context)
    html_content = render_to_string('cart/customer_confirmation_email.html', context)
    
    email = EmailMultiAlternatives(
        subject,
        text_content,
        settings.DEFAULT_FROM_EMAIL,
        [order.customer.email]
    )
    email.attach_alternative(html_content, "text/html")
    email.send()
```

Then create the HTML templates with styled content.

---

## Production Recommendations

For production, consider:

1. **Use a transactional email service**:
   - SendGrid
   - Mailgun
   - Amazon SES
   - Postmark

2. **Add error handling and logging**

3. **Queue emails** (using Celery) to avoid blocking the checkout process

4. **Track email delivery** status

5. **Add email analytics** to track open rates and customer engagement

---

## Summary

**Current Setup**: Console backend (emails print to terminal)
**Easiest for testing**: Keep console backend - just watch your terminal
**For real emails**: Use Gmail SMTP with App Password
**For safe testing**: Use Mailtrap or Mailhog

Choose the method that best fits your testing needs!

