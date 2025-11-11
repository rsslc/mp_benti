# Database Migration Instructions

## Changes Made

The following model changes have been made to support Australian tax invoice generation:

### 1. SiteSettings Model (dashboard/models.py)
**New fields:**
- `business_name` - Business name for invoices (default: "MP Benti")
- `abn` - Australian Business Number (11 digits)
- `business_address` - Full business address
- `business_phone` - Business phone number
- `business_email` - Business email address

### 2. Customer Model (customers/models.py)
**New field:**
- `address` - Customer delivery/billing address

### 3. Order Model (orders/models.py)
**New fields:**
- `invoice_number` - Auto-generated sequential number (e.g., INV-2025-00001)
- `invoice_date` - Date invoice was generated

**New methods:**
- `generate_invoice_number()` - Generates unique invoice number
- `get_subtotal_ex_gst()` - Calculate order subtotal excl GST
- `get_gst_amount()` - Calculate total GST
- `get_total_inc_gst()` - Calculate total incl GST

### 4. OrderLine Model (orders/models.py)
**New fields:**
- `unit_price_ex_gst` - Price per unit excl GST (captured at order time)
- `unit_price_inc_gst` - Price per unit incl GST (captured at order time)

**New methods:**
- `get_line_total_ex_gst()` - Calculate line total excl GST
- `get_line_gst()` - Calculate GST for this line
- `get_line_total_inc_gst()` - Calculate line total incl GST

## Running Migrations

### After Deployment to Railway:

```bash
# The migrations will be created and run automatically by Railway
# using the entrypoint.sh script which runs:
python manage.py makemigrations
python manage.py migrate
```

### Manual Migration (if needed):

If you need to run migrations manually:

```bash
# SSH into Railway container
railway shell

# Create migrations
python manage.py makemigrations

# Apply migrations
python manage.py migrate
```

### Local Development:

If you're testing locally with Docker:

```bash
docker compose -f docker-compose.dev.yml exec web python manage.py makemigrations
docker compose -f docker-compose.dev.yml exec web python manage.py migrate
```

## Post-Migration Steps

### 1. Configure Business Details

After migrations run, configure your business details:

1. Login to dashboard as superuser
2. Go to Dashboard → Settings
3. Fill in:
   - Business Name
   - ABN (11 digits)
   - Business Address
   - Business Phone
   - Business Email

### 2. Update Customer Addresses (Optional)

If you want to add addresses to existing customers:

```bash
railway run python manage.py shell
```

```python
from customers.models import Customer

# Add address to specific customer
customer = Customer.objects.get(business_name="Customer Name")
customer.address = "123 Main St\nSydney NSW 2000"
customer.save()
```

### 3. Test Invoice Generation

1. Create a new test order through the dashboard
2. Prices will automatically be captured
3. Click "Generate Invoice" button
4. Invoice number will be created (INV-2025-00001)
5. Click "Print Invoice" to download PDF

## Important Notes

**Existing Orders:**
- Old orders without captured prices CANNOT be invoiced
- Only new orders (created after this update) can generate invoices
- This is by design to ensure invoice accuracy

**Invoice Numbers:**
- Sequential per year (resets annually)
- Format: INV-YYYY-NNNNN
- First invoice of 2025: INV-2025-00001
- Unique constraint ensures no duplicates

**Price Capture:**
- Prices are now captured at order creation time
- Ensures historical accuracy even if product prices change
- Both ex-GST and inc-GST prices are stored
