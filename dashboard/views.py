from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.db.models import Q
from django.http import HttpResponse
from django.utils import timezone
from decimal import Decimal

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_RIGHT, TA_CENTER
import os
from django.conf import settings as django_settings

from catalogue.models import Product, Category
from catalogue.utils import validate_image_size, validate_image_format
from customers.models import Customer
from orders.models import Order, OrderLine, ORDER_STATUS
from .models import SiteSettings


def staff_required(view):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(f'/admin/login/?next={request.path}')
        if not request.user.is_staff:
            messages.error(request, 'You do not have permission to access the dashboard. Please contact an administrator.')
            return redirect('/')
        return view(request, *args, **kwargs)
    return wrapper


def superuser_required(view):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(f'/admin/login/?next={request.path}')
        if not request.user.is_superuser:
            messages.error(request, 'You do not have permission to access this page. Superuser privileges required.')
            return redirect('/dashboard/')
        return view(request, *args, **kwargs)
    return wrapper


@staff_required
def dashboard_home(request):
    stats = {
        "new": Order.objects.filter(status="new").count(),
        "processing": Order.objects.filter(status="processing").count(),
        "fulfilled": Order.objects.filter(status="fulfilled").count(),
    }
    return render(request, "dashboard_home.html", {"stats": stats})


@staff_required
def orders_list(request):
    orders = Order.objects.select_related("customer").prefetch_related("lines__product").all()

    # Search functionality
    search = request.GET.get('search', '')
    if search:
        orders = orders.filter(
            Q(customer__username__icontains=search) |
            Q(customer__customer__business_name__icontains=search) |
            Q(id__icontains=search)
        )

    # Status filter
    status_filter = request.GET.get('status', '')
    if status_filter:
        orders = orders.filter(status=status_filter)

    # Date range filter
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    if date_from:
        orders = orders.filter(created_at__date__gte=date_from)
    if date_to:
        orders = orders.filter(created_at__date__lte=date_to)

    # Order by most recent first
    orders = orders.order_by("-created_at")

    context = {
        'orders': orders,
        'search': search,
        'status_filter': status_filter,
        'date_from': date_from,
        'date_to': date_to,
        'order_statuses': ORDER_STATUS,
    }
    return render(request, "dashboard/orders_list.html", context)


@staff_required
def order_detail(request, order_id):
    order = get_object_or_404(Order.objects.select_related("customer").prefetch_related("lines__product"), id=order_id)

    # Calculate order total
    order_total = 0
    for line in order.lines.all():
        if line.product.price_inc_gst:
            order_total += line.product.price_inc_gst * line.quantity

    context = {
        'order': order,
        'order_total': order_total,
    }
    return render(request, "dashboard/order_detail.html", context)


@staff_required
def order_add(request):
    users = User.objects.filter(is_active=True).order_by('username')
    products = Product.objects.filter(available=True).select_related('category').order_by('category__name', 'name')

    if request.method == 'POST':
        customer_id = request.POST.get('customer')
        status = request.POST.get('status', 'new')
        notes = request.POST.get('notes', '')

        # Validation
        if not customer_id:
            messages.error(request, 'Customer is required')
            return render(request, "dashboard/order_form.html", {
                'users': users,
                'products': products,
                'order_statuses': ORDER_STATUS,
                'form_data': request.POST,
                'is_edit': False
            })

        customer = get_object_or_404(User, id=customer_id)

        # Create order
        order = Order.objects.create(
            customer=customer,
            status=status,
            notes=notes
        )

        # Create order lines
        lines_created = 0
        for key, value in request.POST.items():
            if key.startswith('quantity_') and value and int(value) > 0:
                product_id = key.replace('quantity_', '')
                product = get_object_or_404(Product, id=product_id)

                # Check for manually entered prices first, otherwise use product prices
                price_ex_gst = request.POST.get(f'price_ex_gst_{product_id}')
                price_inc_gst = request.POST.get(f'price_inc_gst_{product_id}')

                # Convert to Decimal if provided, otherwise use product prices
                if price_ex_gst:
                    price_ex_gst = Decimal(price_ex_gst)
                else:
                    price_ex_gst = product.price_ex_gst

                if price_inc_gst:
                    price_inc_gst = Decimal(price_inc_gst)
                else:
                    price_inc_gst = product.price_inc_gst

                OrderLine.objects.create(
                    order=order,
                    product=product,
                    quantity=int(value),
                    unit_price_ex_gst=price_ex_gst,
                    unit_price_inc_gst=price_inc_gst
                )
                lines_created += 1

        if lines_created == 0:
            messages.warning(request, f'Order #{order.id} created but no items were added')
        else:
            messages.success(request, f'Order #{order.id} created successfully with {lines_created} items')

        return redirect('order_detail', order_id=order.id)

    return render(request, "dashboard/order_form.html", {
        'users': users,
        'products': products,
        'order_statuses': ORDER_STATUS,
        'is_edit': False
    })


@staff_required
def order_edit(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    users = User.objects.filter(is_active=True).order_by('username')
    products = Product.objects.filter(available=True).select_related('category').order_by('category__name', 'name')

    if request.method == 'POST':
        customer_id = request.POST.get('customer')
        status = request.POST.get('status', 'new')
        notes = request.POST.get('notes', '')

        # Validation
        if not customer_id:
            messages.error(request, 'Customer is required')
            return render(request, "dashboard/order_form.html", {
                'order': order,
                'users': users,
                'products': products,
                'order_statuses': ORDER_STATUS,
                'form_data': request.POST,
                'is_edit': True
            })

        customer = get_object_or_404(User, id=customer_id)

        # Update order
        order.customer = customer
        order.status = status
        order.notes = notes
        order.save()

        # Clear existing order lines
        order.lines.all().delete()

        # Create new order lines
        lines_created = 0
        for key, value in request.POST.items():
            if key.startswith('quantity_') and value and int(value) > 0:
                product_id = key.replace('quantity_', '')
                product = get_object_or_404(Product, id=product_id)

                # Check for manually entered prices first, otherwise use product prices
                price_ex_gst = request.POST.get(f'price_ex_gst_{product_id}')
                price_inc_gst = request.POST.get(f'price_inc_gst_{product_id}')

                # Convert to Decimal if provided, otherwise use product prices
                if price_ex_gst:
                    price_ex_gst = Decimal(price_ex_gst)
                else:
                    price_ex_gst = product.price_ex_gst

                if price_inc_gst:
                    price_inc_gst = Decimal(price_inc_gst)
                else:
                    price_inc_gst = product.price_inc_gst

                OrderLine.objects.create(
                    order=order,
                    product=product,
                    quantity=int(value),
                    unit_price_ex_gst=price_ex_gst,
                    unit_price_inc_gst=price_inc_gst
                )
                lines_created += 1

        if lines_created == 0:
            messages.warning(request, f'Order #{order.id} updated but no items were added')
        else:
            messages.success(request, f'Order #{order.id} updated successfully with {lines_created} items')

        return redirect('order_detail', order_id=order.id)

    # Prepare form data for editing
    form_data = {
        'customer': order.customer.id,
        'status': order.status,
        'notes': order.notes,
    }

    # Add existing quantities and prices
    for line in order.lines.all():
        form_data[f'quantity_{line.product.id}'] = line.quantity
        if line.unit_price_ex_gst:
            form_data[f'price_ex_gst_{line.product.id}'] = line.unit_price_ex_gst
        if line.unit_price_inc_gst:
            form_data[f'price_inc_gst_{line.product.id}'] = line.unit_price_inc_gst

    return render(request, "dashboard/order_form.html", {
        'order': order,
        'users': users,
        'products': products,
        'order_statuses': ORDER_STATUS,
        'form_data': form_data,
        'is_edit': True
    })


@staff_required
def order_delete(request, order_id):
    order = get_object_or_404(Order, id=order_id)

    if request.method == 'POST':
        order_id_display = order.id
        order.delete()
        messages.success(request, f'Order #{order_id_display} deleted successfully')
        return redirect('dashboard_orders')

    # Calculate order total for display
    order_total = 0
    for line in order.lines.all():
        if line.product.price_inc_gst:
            order_total += line.product.price_inc_gst * line.quantity

    return render(request, "dashboard/order_confirm_delete.html", {
        'order': order,
        'order_total': order_total
    })


@staff_required
def products_list(request):
    products = Product.objects.select_related("category").all()
    categories = Category.objects.all()

    # Search functionality
    search = request.GET.get('search', '')
    if search:
        products = products.filter(
            Q(name__icontains=search) | Q(description__icontains=search)
        )

    # Category filter
    category_filter = request.GET.get('category', '')
    if category_filter:
        products = products.filter(category_id=category_filter)

    # Availability filter
    available_filter = request.GET.get('available', '')
    if available_filter == 'true':
        products = products.filter(available=True)
    elif available_filter == 'false':
        products = products.filter(available=False)

    # Order by category then name
    products = products.order_by('category__name', 'name')

    context = {
        'products': products,
        'categories': categories,
        'search': search,
        'category_filter': category_filter,
        'available_filter': available_filter,
    }
    return render(request, "dashboard/products_list.html", context)


@staff_required
def customers_list(request):
    # For superadmins, redirect to the full user accounts management
    if request.user.is_superuser:
        return redirect('accounts_list')

    # For regular staff, show read-only customer list
    customers = Customer.objects.select_related("user").all()
    return render(request, "dashboard/customers_list.html", {"customers": customers})


@superuser_required
def accounts_list(request):
    users = User.objects.all().order_by('-date_joined')
    return render(request, "dashboard/accounts_list.html", {"users": users})


@superuser_required
def account_add(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        first_name = request.POST.get('first_name', '')
        last_name = request.POST.get('last_name', '')
        password = request.POST.get('password')
        is_staff = request.POST.get('is_staff') == 'on'
        is_superuser = request.POST.get('is_superuser') == 'on'

        # Customer fields
        business_name = request.POST.get('business_name', '')
        phone = request.POST.get('phone', '')
        address = request.POST.get('address', '')

        # Check if username already exists
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists')
            return render(request, "dashboard/account_form.html", {
                'form_data': request.POST,
                'is_edit': False
            })

        # Create user
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name
        )
        user.is_staff = is_staff
        user.is_superuser = is_superuser
        user.save()

        # Create customer profile if business_name provided
        if business_name:
            Customer.objects.create(
                user=user,
                business_name=business_name,
                phone=phone,
                address=address
            )

        messages.success(request, f'Account for {username} created successfully')
        return redirect('accounts_list')

    return render(request, "dashboard/account_form.html", {'is_edit': False})


@superuser_required
def account_edit(request, user_id):
    user = get_object_or_404(User, id=user_id)
    customer = None
    try:
        customer = user.customer
    except Customer.DoesNotExist:
        pass

    if request.method == 'POST':
        user.username = request.POST.get('username')
        user.email = request.POST.get('email')
        user.first_name = request.POST.get('first_name', '')
        user.last_name = request.POST.get('last_name', '')
        user.is_staff = request.POST.get('is_staff') == 'on'
        user.is_superuser = request.POST.get('is_superuser') == 'on'

        # Update password if provided
        new_password = request.POST.get('password')
        if new_password:
            user.set_password(new_password)

        user.save()

        # Handle customer profile
        business_name = request.POST.get('business_name', '')
        phone = request.POST.get('phone', '')
        address = request.POST.get('address', '')

        if business_name:
            if customer:
                customer.business_name = business_name
                customer.phone = phone
                customer.address = address
                customer.save()
            else:
                Customer.objects.create(
                    user=user,
                    business_name=business_name,
                    phone=phone,
                    address=address
                )
        elif customer:
            # Remove customer profile if business_name is empty
            customer.delete()

        messages.success(request, f'Account for {user.username} updated successfully')
        return redirect('accounts_list')

    form_data = {
        'username': user.username,
        'email': user.email,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'is_staff': user.is_staff,
        'is_superuser': user.is_superuser,
        'business_name': customer.business_name if customer else '',
        'phone': customer.phone if customer else '',
        'address': customer.address if customer else ''
    }

    return render(request, "dashboard/account_form.html", {
        'is_edit': True,
        'user': user,
        'form_data': form_data
    })


@superuser_required
def account_delete(request, user_id):
    user = get_object_or_404(User, id=user_id)

    # Prevent deleting own account
    if user == request.user:
        messages.error(request, "You cannot delete your own account")
        return redirect('accounts_list')

    if request.method == 'POST':
        username = user.username
        user.delete()
        messages.success(request, f'Account for {username} deleted successfully')
        return redirect('accounts_list')

    return render(request, "dashboard/account_confirm_delete.html", {'user': user})


@staff_required
def product_add(request):
    categories = Category.objects.all()

    if request.method == 'POST':
        # Get form data
        name = request.POST.get('name')
        description = request.POST.get('description', '')
        category_id = request.POST.get('category')
        unit = request.POST.get('unit', '')
        unit_weight = request.POST.get('unit_weight')
        pack_size = request.POST.get('pack_size', '')
        price_ex_gst = request.POST.get('price_ex_gst')
        price_inc_gst = request.POST.get('price_inc_gst')
        available = request.POST.get('available') == 'on'
        stock_quantity = request.POST.get('stock_quantity')

        # Validation
        if not name or not category_id:
            messages.error(request, 'Name and category are required')
            return render(request, "dashboard/product_form.html", {
                'categories': categories,
                'form_data': request.POST,
                'is_edit': False
            })

        # Create product
        category = get_object_or_404(Category, id=category_id)
        product = Product.objects.create(
            name=name,
            description=description,
            category=category,
            unit=unit,
            unit_weight=float(unit_weight) if unit_weight else None,
            pack_size=pack_size,
            price_ex_gst=float(price_ex_gst) if price_ex_gst else None,
            price_inc_gst=float(price_inc_gst) if price_inc_gst else None,
            available=available,
            stock_quantity=int(stock_quantity) if stock_quantity else None
        )

        # Handle image uploads
        if request.FILES.get('image_main'):
            image_main = request.FILES['image_main']

            # Validate image size and format
            is_valid, error_msg = validate_image_size(image_main, max_size_mb=5)
            if not is_valid:
                messages.error(request, f"Main image: {error_msg}")
                return render(request, "dashboard/product_form.html", {
                    'categories': categories,
                    'form_data': request.POST,
                    'is_edit': False
                })

            is_valid, error_msg = validate_image_format(image_main)
            if not is_valid:
                messages.error(request, f"Main image: {error_msg}")
                return render(request, "dashboard/product_form.html", {
                    'categories': categories,
                    'form_data': request.POST,
                    'is_edit': False
                })

            product.image_main = image_main

        if request.FILES.get('image_alt'):
            image_alt = request.FILES['image_alt']

            # Validate image size and format
            is_valid, error_msg = validate_image_size(image_alt, max_size_mb=5)
            if not is_valid:
                messages.error(request, f"Alt image: {error_msg}")
                return render(request, "dashboard/product_form.html", {
                    'categories': categories,
                    'form_data': request.POST,
                    'is_edit': False
                })

            is_valid, error_msg = validate_image_format(image_alt)
            if not is_valid:
                messages.error(request, f"Alt image: {error_msg}")
                return render(request, "dashboard/product_form.html", {
                    'categories': categories,
                    'form_data': request.POST,
                    'is_edit': False
                })

            product.image_alt = image_alt

        product.save()

        messages.success(request, f'Product "{name}" created successfully')
        return redirect('products_list')

    return render(request, "dashboard/product_form.html", {
        'categories': categories,
        'is_edit': False
    })


@staff_required
def product_edit(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    categories = Category.objects.all()

    if request.method == 'POST':
        # Update product fields
        product.name = request.POST.get('name')
        product.description = request.POST.get('description', '')
        category_id = request.POST.get('category')
        product.category = get_object_or_404(Category, id=category_id)
        product.unit = request.POST.get('unit', '')

        unit_weight = request.POST.get('unit_weight')
        product.unit_weight = float(unit_weight) if unit_weight else None

        product.pack_size = request.POST.get('pack_size', '')

        price_ex_gst = request.POST.get('price_ex_gst')
        product.price_ex_gst = float(price_ex_gst) if price_ex_gst else None

        price_inc_gst = request.POST.get('price_inc_gst')
        product.price_inc_gst = float(price_inc_gst) if price_inc_gst else None

        product.available = request.POST.get('available') == 'on'

        stock_quantity = request.POST.get('stock_quantity')
        product.stock_quantity = int(stock_quantity) if stock_quantity else None

        # Handle image uploads
        if request.FILES.get('image_main'):
            image_main = request.FILES['image_main']

            # Validate image size and format
            is_valid, error_msg = validate_image_size(image_main, max_size_mb=5)
            if not is_valid:
                messages.error(request, f"Main image: {error_msg}")
                return redirect('product_edit', product_id=product_id)

            is_valid, error_msg = validate_image_format(image_main)
            if not is_valid:
                messages.error(request, f"Main image: {error_msg}")
                return redirect('product_edit', product_id=product_id)

            product.image_main = image_main

        if request.FILES.get('image_alt'):
            image_alt = request.FILES['image_alt']

            # Validate image size and format
            is_valid, error_msg = validate_image_size(image_alt, max_size_mb=5)
            if not is_valid:
                messages.error(request, f"Alt image: {error_msg}")
                return redirect('product_edit', product_id=product_id)

            is_valid, error_msg = validate_image_format(image_alt)
            if not is_valid:
                messages.error(request, f"Alt image: {error_msg}")
                return redirect('product_edit', product_id=product_id)

            product.image_alt = image_alt

        product.save()
        messages.success(request, f'Product "{product.name}" updated successfully')
        return redirect('products_list')

    form_data = {
        'name': product.name,
        'description': product.description,
        'category': product.category.id,
        'unit': product.unit,
        'unit_weight': product.unit_weight,
        'pack_size': product.pack_size,
        'price_ex_gst': product.price_ex_gst,
        'price_inc_gst': product.price_inc_gst,
        'available': product.available,
        'stock_quantity': product.stock_quantity,
    }

    return render(request, "dashboard/product_form.html", {
        'categories': categories,
        'product': product,
        'form_data': form_data,
        'is_edit': True
    })


@staff_required
def product_delete(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    if request.method == 'POST':
        product_name = product.name
        product.delete()
        messages.success(request, f'Product "{product_name}" deleted successfully')
        return redirect('products_list')

    return render(request, "dashboard/product_confirm_delete.html", {'product': product})


@superuser_required
def site_settings(request):
    settings = SiteSettings.get_settings()

    if request.method == 'POST':
        # Price display settings
        settings.show_prices = request.POST.get('show_prices') == 'on'
        settings.price_hidden_message = request.POST.get('price_hidden_message', 'Contact us for pricing')

        # Business details for invoices
        settings.business_name = request.POST.get('business_name', 'MP Benti')
        settings.abn = request.POST.get('abn', '')
        settings.business_address = request.POST.get('business_address', '')
        settings.business_phone = request.POST.get('business_phone', '')
        settings.business_email = request.POST.get('business_email', '')

        settings.save()
        messages.success(request, 'Site settings updated successfully')
        return redirect('site_settings')

    return render(request, "dashboard/site_settings.html", {'settings': settings})


@staff_required
def categories_list(request):
    parent_categories = Category.objects.filter(parent=None).prefetch_related('children').order_by('name')
    child_categories = Category.objects.exclude(parent=None).select_related('parent').order_by('parent__name', 'name')

    context = {
        'parent_categories': parent_categories,
        'child_categories': child_categories,
    }
    return render(request, "dashboard/categories_list.html", context)


@staff_required
def category_add(request):
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        slug = request.POST.get('slug', '').strip()
        description = request.POST.get('description', '').strip()
        parent_id = request.POST.get('parent')

        if not name:
            messages.error(request, 'Category name is required')
            return render(request, "dashboard/category_form.html", {
                'parent_categories': Category.objects.filter(parent=None),
                'form_data': request.POST
            })

        # Create category
        category = Category()
        category.name = name
        category.description = description

        if parent_id:
            try:
                category.parent = Category.objects.get(id=parent_id, parent=None)
            except Category.DoesNotExist:
                messages.error(request, 'Invalid parent category')
                return render(request, "dashboard/category_form.html", {
                    'parent_categories': Category.objects.filter(parent=None),
                    'form_data': request.POST
                })

        # Handle slug
        if slug:
            # Check if slug is unique
            if Category.objects.filter(slug=slug).exists():
                messages.error(request, 'A category with this slug already exists')
                return render(request, "dashboard/category_form.html", {
                    'parent_categories': Category.objects.filter(parent=None),
                    'form_data': request.POST
                })
            category.slug = slug

        # Handle image upload
        if request.FILES.get('image'):
            image = request.FILES['image']

            # Validate image size
            is_valid, error_msg = validate_image_size(image, max_size_mb=5)
            if not is_valid:
                messages.error(request, error_msg)
                return render(request, "dashboard/category_form.html", {
                    'parent_categories': Category.objects.filter(parent=None),
                    'form_data': request.POST
                })

            # Validate image format
            is_valid, error_msg = validate_image_format(image)
            if not is_valid:
                messages.error(request, error_msg)
                return render(request, "dashboard/category_form.html", {
                    'parent_categories': Category.objects.filter(parent=None),
                    'form_data': request.POST
                })

            category.image = image

        category.save()
        messages.success(request, f'Category "{category.name}" created successfully')
        return redirect('categories_list')

    context = {
        'parent_categories': Category.objects.filter(parent=None),
        'is_edit': False
    }
    return render(request, "dashboard/category_form.html", context)


@staff_required
def category_edit(request, category_id):
    category = get_object_or_404(Category, id=category_id)

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        slug = request.POST.get('slug', '').strip()
        description = request.POST.get('description', '').strip()
        parent_id = request.POST.get('parent')

        if not name:
            messages.error(request, 'Category name is required')
            return render(request, "dashboard/category_form.html", {
                'category': category,
                'parent_categories': Category.objects.filter(parent=None).exclude(id=category.id),
                'is_edit': True
            })

        # Update category
        category.name = name
        category.description = description

        # Handle parent
        if parent_id:
            try:
                parent = Category.objects.get(id=parent_id, parent=None)
                # Prevent circular relationships
                if parent.id == category.id:
                    messages.error(request, 'A category cannot be its own parent')
                    return render(request, "dashboard/category_form.html", {
                        'category': category,
                        'parent_categories': Category.objects.filter(parent=None).exclude(id=category.id),
                        'is_edit': True
                    })
                category.parent = parent
            except Category.DoesNotExist:
                messages.error(request, 'Invalid parent category')
                return render(request, "dashboard/category_form.html", {
                    'category': category,
                    'parent_categories': Category.objects.filter(parent=None).exclude(id=category.id),
                    'is_edit': True
                })
        else:
            category.parent = None

        # Handle slug
        if slug:
            # Check if slug is unique (excluding current category)
            if Category.objects.filter(slug=slug).exclude(id=category.id).exists():
                messages.error(request, 'A category with this slug already exists')
                return render(request, "dashboard/category_form.html", {
                    'category': category,
                    'parent_categories': Category.objects.filter(parent=None).exclude(id=category.id),
                    'is_edit': True
                })
            category.slug = slug

        # Handle image upload
        if request.FILES.get('image'):
            image = request.FILES['image']

            # Validate image size
            is_valid, error_msg = validate_image_size(image, max_size_mb=5)
            if not is_valid:
                messages.error(request, error_msg)
                return render(request, "dashboard/category_form.html", {
                    'category': category,
                    'parent_categories': Category.objects.filter(parent=None).exclude(id=category.id),
                    'is_edit': True
                })

            # Validate image format
            is_valid, error_msg = validate_image_format(image)
            if not is_valid:
                messages.error(request, error_msg)
                return render(request, "dashboard/category_form.html", {
                    'category': category,
                    'parent_categories': Category.objects.filter(parent=None).exclude(id=category.id),
                    'is_edit': True
                })

            category.image = image
        elif request.POST.get('remove_image') == 'on':
            category.image = None

        category.save()
        messages.success(request, f'Category "{category.name}" updated successfully')
        return redirect('categories_list')

    context = {
        'category': category,
        'parent_categories': Category.objects.filter(parent=None).exclude(id=category.id),
        'is_edit': True
    }
    return render(request, "dashboard/category_form.html", context)


@staff_required
def category_delete(request, category_id):
    category = get_object_or_404(Category, id=category_id)

    if request.method == 'POST':
        category_name = category.name

        # Check if category has children
        if category.children.exists():
            messages.error(request, f'Cannot delete "{category_name}" because it has subcategories. Delete the subcategories first.')
            return redirect('categories_list')

        # Check if category has products
        if category.products.exists():
            messages.error(request, f'Cannot delete "{category_name}" because it contains products. Move or delete the products first.')
            return redirect('categories_list')

        category.delete()
        messages.success(request, f'Category "{category_name}" deleted successfully')
        return redirect('categories_list')

    return render(request, "dashboard/category_confirm_delete.html", {'category': category})


# Invoice Generation Views

@staff_required
def generate_invoice(request, order_id):
    """Generate invoice number for an order"""
    order = get_object_or_404(Order, id=order_id)

    if order.invoice_number:
        messages.info(request, f'Order #{order.id} already has invoice number: {order.invoice_number}')
    else:
        # Auto-populate prices from product if missing (for old orders)
        for line in order.lines.all():
            if line.unit_price_ex_gst is None or line.unit_price_inc_gst is None:
                # Use current product prices as fallback
                line.unit_price_ex_gst = line.product.price_ex_gst
                line.unit_price_inc_gst = line.product.price_inc_gst
                line.save()

        invoice_number = order.generate_invoice_number()
        messages.success(request, f'Invoice {invoice_number} generated successfully for Order #{order.id}')

    return redirect('order_detail', order_id=order.id)


@staff_required
def order_invoice_pdf(request, order_id):
    """Generate and download PDF invoice"""
    order = get_object_or_404(Order, id=order_id)
    settings = SiteSettings.get_settings()

    # Check if invoice number exists
    if not order.invoice_number:
        messages.error(request, 'Cannot generate PDF: Invoice number has not been generated yet')
        return redirect('order_detail', order_id=order.id)

    # Auto-populate prices from product if missing (for old orders or edited orders)
    for line in order.lines.all():
        if line.unit_price_ex_gst is None or line.unit_price_inc_gst is None:
            # Use current product prices as fallback
            line.unit_price_ex_gst = line.product.price_ex_gst
            line.unit_price_inc_gst = line.product.price_inc_gst
            line.save()

    # Create response
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="invoice_{order.invoice_number}.pdf"'

    # Create PDF document
    doc = SimpleDocTemplate(response, pagesize=A4,
                            leftMargin=20*mm, rightMargin=20*mm,
                            topMargin=20*mm, bottomMargin=20*mm)

    # Container for PDF elements
    elements = []
    styles = getSampleStyleSheet()

    # Custom styles - Modern & Minimal
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=28,
        textColor=colors.HexColor('#1f2937'),
        spaceAfter=4,
        fontName='Helvetica-Bold',
    )

    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Normal'],
        fontSize=11,
        textColor=colors.HexColor('#6b7280'),
        spaceAfter=12,
    )

    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=11,
        textColor=colors.HexColor('#374151'),
        spaceAfter=4,
        fontName='Helvetica-Bold',
        textTransform='uppercase',
    )

    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontSize=9,
        textColor=colors.HexColor('#4b5563'),
        leading=12,
    )

    small_style = ParagraphStyle(
        'CustomSmall',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.HexColor('#6b7280'),
    )

    # Header with Logo and Title
    logo_path = os.path.join(django_settings.BASE_DIR, 'static', 'images', 'logo.png')

    if os.path.exists(logo_path):
        try:
            # Add logo (scaled to appropriate size)
            logo = Image(logo_path, width=40*mm, height=40*mm, kind='proportional')

            # Create header table with logo and title
            header_data = [
                [logo, Paragraph("TAX INVOICE", title_style)],
                ['', Paragraph(f"Invoice #{order.invoice_number}", subtitle_style)]
            ]

            header_table = Table(header_data, colWidths=[45*mm, 125*mm])
            header_table.setStyle(TableStyle([
                ('VALIGN', (0, 0), (0, -1), 'TOP'),
                ('VALIGN', (1, 0), (1, -1), 'MIDDLE'),
                ('LEFTPADDING', (0, 0), (-1, -1), 0),
                ('RIGHTPADDING', (0, 0), (-1, -1), 0),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
            ]))
            elements.append(header_table)
        except:
            # Fallback if logo fails to load
            elements.append(Paragraph("TAX INVOICE", title_style))
            elements.append(Paragraph(f"Invoice #{order.invoice_number}", subtitle_style))
    else:
        # No logo available
        elements.append(Paragraph("TAX INVOICE", title_style))
        elements.append(Paragraph(f"Invoice #{order.invoice_number}", subtitle_style))

    elements.append(Spacer(1, 8*mm))

    # Business Details Section
    elements.append(Paragraph("<font size=8 color='#9ca3af'>FROM</font>", small_style))
    elements.append(Paragraph(f"<b>{settings.business_name}</b>", normal_style))
    elements.append(Paragraph(f"ABN: {settings.abn}", normal_style))
    elements.append(Paragraph(settings.business_address.replace('\n', '<br/>'), normal_style))
    if settings.business_phone:
        elements.append(Paragraph(f"Phone: {settings.business_phone}", normal_style))
    if settings.business_email:
        elements.append(Paragraph(f"Email: {settings.business_email}", normal_style))

    elements.append(Spacer(1, 6*mm))

    # Invoice details in a light gray box
    invoice_details_data = [
        [Paragraph(f"<b>Invoice Date:</b>", normal_style), Paragraph(order.invoice_date.strftime('%d %B %Y'), normal_style)],
        [Paragraph(f"<b>Order Date:</b>", normal_style), Paragraph(order.created_at.strftime('%d %B %Y'), normal_style)],
    ]

    invoice_details_table = Table(invoice_details_data, colWidths=[40*mm, 50*mm])
    invoice_details_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f9fafb')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(invoice_details_table)
    elements.append(Spacer(1, 8*mm))

    # Bill To Section
    elements.append(Paragraph("<font size=8 color='#9ca3af'>BILL TO</font>", small_style))

    customer = order.customer
    try:
        customer_profile = customer.customer
        customer_info = f"<b>{customer_profile.business_name}</b><br/>"
        if customer.get_full_name():
            customer_info += f"{customer.get_full_name()}<br/>"
        if customer_profile.address:
            customer_info += customer_profile.address.replace('\n', '<br/>') + '<br/>'
        if customer_profile.phone:
            customer_info += f"Phone: {customer_profile.phone}<br/>"
        if customer.email:
            customer_info += f"Email: {customer.email}"
    except:
        customer_info = f"<b>{customer.username}</b><br/>"
        if customer.email:
            customer_info += f"Email: {customer.email}"

    elements.append(Paragraph(customer_info, normal_style))
    elements.append(Spacer(1, 10*mm))

    # Order Items Table
    item_data = [
        ['Description', 'Quantity', 'Unit Price (ex GST)', 'GST', 'Total (inc GST)']
    ]

    for line in order.lines.all():
        item_data.append([
            line.product.name,
            str(line.quantity),
            f"${line.unit_price_ex_gst:.2f}" if line.unit_price_ex_gst else '-',
            f"${line.get_line_gst():.2f}",
            f"${line.get_line_total_inc_gst():.2f}"
        ])

    # Add totals
    item_data.append(['', '', '', '', ''])
    item_data.append(['', '', '', 'Subtotal (ex GST):', f"${order.get_subtotal_ex_gst():.2f}"])
    item_data.append(['', '', '', 'GST (10%):', f"${order.get_gst_amount():.2f}"])
    item_data.append(['', '', '', 'TOTAL (inc GST):', f"${order.get_total_inc_gst():.2f}"])

    item_table = Table(item_data, colWidths=[80*mm, 25*mm, 35*mm, 30*mm, 30*mm])
    item_table.setStyle(TableStyle([
        # Header row
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f3f4f6')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#1f2937')),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('TOPPADDING', (0, 0), (-1, 0), 8),

        # Data rows
        ('FONTNAME', (0, 1), (-1, -5), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -5), 9),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 1), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 6),

        # Align numbers to the right
        ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),
        ('ALIGN', (0, 1), (0, -1), 'LEFT'),

        # Grid
        ('GRID', (0, 0), (-1, -5), 0.5, colors.HexColor('#e5e7eb')),
        ('LINEBELOW', (0, 0), (-1, 0), 1, colors.HexColor('#d1d5db')),

        # Totals section
        ('FONTNAME', (3, -3), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (3, -3), (-1, -1), 10),
        ('LINEABOVE', (3, -3), (-1, -3), 1, colors.HexColor('#d1d5db')),
        ('LINEABOVE', (3, -1), (-1, -1), 1.5, colors.HexColor('#1f2937')),
    ]))

    elements.append(item_table)
    elements.append(Spacer(1, 15*mm))

    # Footer notes
    if order.notes:
        elements.append(Paragraph("<b>Notes:</b>", heading_style))
        elements.append(Paragraph(order.notes.replace('\n', '<br/>'), normal_style))
        elements.append(Spacer(1, 5*mm))

    elements.append(Paragraph("This is a tax invoice for GST purposes.", normal_style))

    # Build PDF
    doc.build(elements)

    return response
