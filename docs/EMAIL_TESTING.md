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

### Method 3: Gmail API (Real Emails)

**Best for**: Testing actual email delivery with Gmail

**Important**: Gmail no longer supports SMTP with app passwords for new applications. You must use the Gmail API instead.

**Setup**:

1. **Create Google Cloud Project and Enable Gmail API**:
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project (e.g., "MP Benti Email")
   - Go to "APIs & Services" → "Library"
   - Search for "Gmail API" and click "Enable"

2. **Create OAuth 2.0 Credentials**:
   - Go to "APIs & Services" → "Credentials"
   - Click "Create Credentials" → "OAuth client ID"
   - Configure OAuth consent screen first if prompted:
     - User Type: External (for testing) or Internal (if G Suite)
     - Add your email as a test user
   - Application type: "Desktop app"
   - Name it "MP Benti Local Dev"
   - Download the credentials JSON file
   - Save it as `credentials.json` in your project root

3. **Install Gmail API dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **First-time Authentication**:
   
   **Option A: Using the authentication script (recommended)**
   ```bash
   python authenticate_gmail.py
   ```
   
   **Option B: Using Django shell**
   ```bash
   python manage.py shell
   ```
   Then execute:
   ```python
   from cart.gmail_utils import authenticate_gmail
   authenticate_gmail()
   ```
   
   **Two authentication methods are supported:**
   
   **Method A: Automatic (tries first)**
   - A browser window will open automatically
   - Sign in with your Gmail account
   - Grant ALL permissions (click "Continue" on every screen)
   - The system will automatically capture the token and save it
   
   **Method B: Manual (fallback if automatic fails)**
   - If the automatic method fails (e.g., can't start local server), you'll see manual instructions
   - You'll be given a URL to open in your browser
   - After granting permissions, copy the ENTIRE redirect URL from your browser
   - Paste it back in the terminal when prompted
   - The URL will look like: `http://localhost:PORT/?code=XXXXX&scope=...`
   
   - **IMPORTANT**: Make sure to click "Continue" on ALL permission screens to ensure a refresh token is granted
   - A `token.json` file will be **automatically created** in your project root (keep this secure!)
   - You should see: "✓✓✓ SUCCESS! Refresh token received! Authentication will persist - no need to log in again!"

5. **Token Storage and Lifetime**:
   - The `token.json` file contains:
     - **Access token**: Short-lived (1 hour), used to make API calls
     - **Refresh token**: Long-lived (no expiration), used to get new access tokens
   - The system **automatically** handles token refresh:
     - When the access token expires (after ~1 hour), the refresh token is used to get a new access token
     - This happens transparently - you won't need to re-authenticate
     - The refreshed token is automatically saved back to `token.json`
   - **You only need to authenticate once** (when you first run `authenticate_gmail()`)
   - The refresh token **does not expire** unless:
     - You revoke access in your Google account settings
     - You delete the `token.json` file
     - The refresh token hasn't been used for 6 months (Google's inactivity policy)
   - If re-authentication is needed, the system will automatically prompt you with a browser window

6. **Update your `.env` file**:
   ```env
   EMAIL_BACKEND=gmail_api
   DEFAULT_FROM_EMAIL=your-email@gmail.com
   ```

7. **Add `credentials.json` and `token.json` to `.gitignore`**:
   ```bash
   echo "credentials.json" >> .gitignore
   echo "token.json" >> .gitignore
   ```

8. **Restart your server**

**How to test**:
1. Authenticate once (see step 4 above)
2. Place a test order through checkout
3. Check `mpbenti@gmail.com` and `mpbenti2@gmail.com` inboxes for the admin notification
4. Check the customer's email inbox for the confirmation email

**Quick test without placing an order:**
```bash
python test_gmail.py
```
This script will send a test email to verify Gmail API is working.

**Note**: For testing, you might want to temporarily change the recipient email addresses in `cart/views.py` to your own email address.

**Security Notes**:
- Never commit `credentials.json` or `token.json` to git
- The `token.json` contains refresh tokens that allow sending emails
- For production, use a service account or secure credential management
- Gmail API has a sending limit: 2,000 emails per day for free accounts

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

**For console/SMTP backends:**
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

**For Gmail API backend:**
```python
from cart.gmail_utils import send_mail_gmail_api
from django.conf import settings

send_mail_gmail_api(
    'Test Email',
    'This is a test email from MP Benti using Gmail API.',
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

### Gmail API authentication fails
- Ensure you've enabled Gmail API in Google Cloud Console
- Check that OAuth consent screen is properly configured
- Verify you've added your email as a test user (if using External user type)
- Delete `token.json` and re-authenticate if you see permission errors
- Check that `credentials.json` is in the correct location

### Gmail API quota exceeded
- Gmail API has a limit of 2,000 emails per day for free accounts
- Check your quota usage in Google Cloud Console → APIs & Services → Dashboard
- For higher limits, consider using a transactional email service (SendGrid, Mailgun, etc.)

### No error but email not received
- Check spam folder
- Verify the recipient email address
- Check Django logs for email errors
- Try the test script above to isolate the issue
- Verify your Gmail account can send emails normally

### Token expired or "Please visit this URL to authorize" appearing repeatedly
- **Problem**: The refresh token was not properly saved during initial authentication, or the authentication flow never completed
- **Cause**: 
  - Not clicking "Continue" on all permission screens
  - OAuth callback not captured (local server failed)
  - Browser/OAuth flow issues
- **Solution**: Delete `token.json` and re-authenticate using manual method:
  ```bash
  rm token.json
  python manage.py shell
  ```
  Then run:
  ```python
  from cart.gmail_utils import authenticate_gmail
  authenticate_gmail()
  ```
  **If automatic authentication fails:**
  - The system will automatically switch to manual mode
  - Copy the authorization URL shown and open it in a browser
  - After granting permissions, copy the ENTIRE redirect URL (starts with `http://localhost`)
  - Paste it when prompted in the terminal
  
  Make sure to:
  1. Complete ALL permission screens
  2. Look for the message: "✓✓✓ SUCCESS! Refresh token received!"
  3. If you see "WARNING: No refresh token received", the authentication didn't complete properly - try again
  4. Verify `token.json` was created: `ls -la token.json`

- **Note**: Access tokens expire after ~1 hour, but the system automatically refreshes them using the refresh token. If you keep getting prompted to authenticate, the refresh token is missing from `token.json`

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

1. **Use a transactional email service** (recommended):
   - SendGrid (99,000 free emails/month with good deliverability)
   - Mailgun (5,000 free emails/month)
   - Amazon SES (62,000 free emails/month on AWS free tier)
   - Postmark (100 free emails/month, excellent deliverability)
   
   These services provide:
   - Higher sending limits than Gmail API
   - Better deliverability and reputation management
   - Email analytics and tracking
   - Dedicated IP addresses
   - Professional support

2. **If using Gmail API in production**:
   - Use a service account instead of OAuth for unattended operation
   - Be aware of the 2,000 emails/day limit
   - Set up proper error handling and retry logic
   - Monitor your API quota in Google Cloud Console
   - Consider upgrading to Google Workspace for higher limits

3. **Add error handling and logging**:
   - Log all email sending attempts
   - Handle API failures gracefully
   - Alert administrators if emails fail to send

4. **Queue emails** (using Celery with Redis/RabbitMQ):
   - Prevents blocking the checkout process
   - Allows for retry on failure
   - Better scalability

5. **Track email delivery**:
   - Monitor bounce rates
   - Track open rates (if using transactional service)
   - Set up webhooks for delivery status

6. **Security considerations**:
   - Store credentials securely (use environment variables or secret managers)
   - Rotate tokens/credentials periodically
   - Monitor for unauthorized access
   - Use least-privilege service accounts

---

## Summary

**Current Setup**: Console backend (emails print to terminal)
**Easiest for testing**: Keep console backend - just watch your terminal
**For real emails (development)**: Use Gmail API with OAuth authentication
**For safe testing**: Use Mailtrap or Mailhog
**For production**: Use a transactional email service (SendGrid, Mailgun, Amazon SES)

Choose the method that best fits your testing needs!

