# Staff Dashboard Access Fix

## Problem
Users marked as staff were unable to access the dashboard, being redirected to the login page even when authenticated.

## Root Cause
The previous `staff_required` and `superuser_required` decorators used Django's `user_passes_test()`, which:
- Redirected failed permission checks back to the login page
- Provided no error message or feedback to users
- Made it unclear why access was denied for authenticated users

## Solution Implemented

### 1. Improved Permission Decorators (dashboard/views.py:15-34)

**New `staff_required` decorator:**
```python
def staff_required(view):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(f'/admin/login/?next={request.path}')
        if not request.user.is_staff:
            messages.error(request, 'You do not have permission to access the dashboard. Please contact an administrator.')
            return redirect('/')
        return view(request, *args, **kwargs)
    return wrapper
```

**Benefits:**
- Clear error messages for insufficient permissions
- Redirects non-staff users to home page (not login)
- Preserves login redirect for unauthenticated users
- Better user experience

### 2. Management Command for Granting Staff Access

**New command:** `python manage.py make_staff <username>`

**Usage:**
```bash
# Grant staff access (dashboard access)
python manage.py make_staff john

# Grant staff + superuser access (full admin)
python manage.py make_staff john --superuser
```

**File:** `dashboard/management/commands/make_staff.py`

### 3. Diagnostic Script

**File:** `check_staff_users.py`

**Usage:**
```bash
python manage.py shell < check_staff_users.py
```

Shows all users and their permission levels for troubleshooting.

## How to Grant Dashboard Access

### Method 1: Using Management Command (Recommended)
```bash
python manage.py make_staff username
```

### Method 2: Django Admin Panel
1. Login to `/admin/` as superuser
2. Go to Users
3. Edit the user
4. Check "Staff status" checkbox
5. Save

### Method 3: Django Shell
```bash
python manage.py shell
```
```python
from django.contrib.auth.models import User
user = User.objects.get(username='username')
user.is_staff = True
user.save()
```

### Method 4: Dashboard Accounts Management (Superuser Only)
1. Login to dashboard as superuser
2. Go to Accounts → List
3. Edit the user
4. Check "Staff" checkbox
5. Save

## Permission Levels

### Regular User (is_staff=False)
- ❌ Cannot access dashboard
- ✓ Can place orders via customer portal

### Staff User (is_staff=True)
- ✓ Can access dashboard
- ✓ View and manage orders
- ✓ View and manage products
- ✓ View and manage categories
- ✓ View customers list
- ❌ Cannot manage user accounts
- ❌ Cannot change site settings

### Superuser (is_superuser=True, implies is_staff=True)
- ✓ All staff permissions
- ✓ Manage user accounts (create, edit, delete)
- ✓ Grant/revoke staff privileges
- ✓ Change site settings (price visibility, etc.)
- ✓ Full Django admin access

## Testing the Fix

### Test 1: Staff user access
1. Create or modify a user to have `is_staff=True`
2. Login as that user
3. Navigate to `/dashboard/`
4. ✓ Should see dashboard home with order stats

### Test 2: Non-staff user blocked
1. Login as a regular user (is_staff=False)
2. Navigate to `/dashboard/`
3. ✓ Should see error message and redirect to home

### Test 3: Superuser access
1. Login as superuser
2. Navigate to `/dashboard/accounts/`
3. ✓ Should see accounts management page

## Verifying User Permissions

### Check via Django Admin
1. Go to `/admin/auth/user/`
2. View user list with "Staff status" column

### Check via Shell
```python
python manage.py shell
from django.contrib.auth.models import User

# Check all staff users
User.objects.filter(is_staff=True).values('username', 'is_staff', 'is_superuser')

# Check specific user
user = User.objects.get(username='username')
print(f"is_staff: {user.is_staff}, is_superuser: {user.is_superuser}")
```

### Check via Diagnostic Script
```bash
python manage.py shell < check_staff_users.py
```

## Migration Notes

No database migrations required - this only changes view logic and adds helper tools.

## Files Changed/Added

### Modified:
- `dashboard/views.py` - Improved permission decorators

### Added:
- `dashboard/management/commands/make_staff.py` - Management command
- `dashboard/management/__init__.py` - Package init
- `dashboard/management/commands/__init__.py` - Package init
- `check_staff_users.py` - Diagnostic script
- `STAFF_ACCESS_FIX.md` - This documentation

## Troubleshooting

### Issue: User still can't access dashboard after setting is_staff=True

**Solution:**
1. Verify the user is truly marked as staff:
   ```bash
   python manage.py shell < check_staff_users.py
   ```
2. Ensure user is logged out and logs back in (session refresh)
3. Check browser console for errors
4. Verify `is_active=True` for the user

### Issue: Error messages not appearing

**Solution:**
- Check that `django.contrib.messages` middleware is enabled in settings
- Ensure your base template includes messages display block
- Verify messages framework is properly configured

### Issue: Redirects to wrong page

**Solution:**
- Non-staff users redirect to `/` (home page)
- Non-superusers accessing superuser pages redirect to `/dashboard/`
- Unauthenticated users redirect to `/admin/login/?next=<path>`

## Best Practices

1. **Grant minimal permissions**: Only give staff access to users who need it
2. **Use superuser sparingly**: Reserve for trusted administrators
3. **Regular audits**: Periodically review staff users list
4. **Onboarding**: Use `make_staff` command for consistency
5. **Documentation**: Keep this guide updated with any permission changes
