#!/usr/bin/env python
"""
Diagnostic script to check staff user permissions
Run with: python manage.py shell < check_staff_users.py
"""

from django.contrib.auth.models import User

print("\n" + "="*60)
print("STAFF USER PERMISSION CHECK")
print("="*60 + "\n")

users = User.objects.all()

if not users.exists():
    print("❌ No users found in database")
else:
    print(f"Total users: {users.count()}\n")

    for user in users:
        print(f"Username: {user.username}")
        print(f"  Email: {user.email}")
        print(f"  is_active: {user.is_active}")
        print(f"  is_staff: {'✅ YES' if user.is_staff else '❌ NO'}")
        print(f"  is_superuser: {'✅ YES' if user.is_superuser else '❌ NO'}")
        print(f"  Dashboard access: {'✅ GRANTED' if user.is_staff else '❌ DENIED'}")
        print()

print("-"*60)
print("SUMMARY:")
print(f"  Staff users: {User.objects.filter(is_staff=True).count()}")
print(f"  Superusers: {User.objects.filter(is_superuser=True).count()}")
print(f"  Regular users: {User.objects.filter(is_staff=False).count()}")
print("="*60 + "\n")

print("To grant dashboard access to a user, run:")
print("  user = User.objects.get(username='USERNAME')")
print("  user.is_staff = True")
print("  user.save()")
print()
