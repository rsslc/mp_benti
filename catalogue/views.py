from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import redirect, render, get_object_or_404

from catalogue.models import Product
from orders.models import Order, OrderLine

from .models import Category


def home(request):
    categories = Category.objects.filter(parent=None)
    return render(request, "home.html", {"categories": categories})


def about(request):
    return render(request, "about.html")


def category_list(request):
    parent_categories = Category.objects.filter(parent=None).prefetch_related("children")
    return render(request, "catalogue/category_list.html", {"parent_categories": parent_categories})


def category_detail(request, category_slug=None, parent_slug=None, child_slug=None):
    breadcrumbs = [{'name': 'Products', 'url': '/products/'}]

    # Get search query
    search_query = request.GET.get('q', '').strip()

    if child_slug:
        # Viewing a child category
        parent_category = get_object_or_404(Category, slug=parent_slug, parent=None)
        category = get_object_or_404(Category, slug=child_slug, parent=parent_category)
        products = category.products.all()

        breadcrumbs.append({'name': parent_category.name, 'url': parent_category.get_absolute_url()})
        breadcrumbs.append({'name': category.name, 'url': None})

        # Apply search filter for child categories
        if search_query:
            products = products.filter(
                Q(name__icontains=search_query) |
                Q(description__icontains=search_query) |
                Q(pack_description__icontains=search_query)
            )
    else:
        # Viewing a category (could be parent or child)
        category = get_object_or_404(Category, slug=category_slug)

        if category.parent:
            # This is a child category, redirect to proper URL
            return redirect('category_detail', parent_slug=category.parent.slug, child_slug=category.slug)

        # This is a parent category
        child_categories = category.children.prefetch_related('products').all()
        products = category.get_all_products()

        breadcrumbs.append({'name': category.name, 'url': None})

        # Apply search filter if query exists
        # When searching, hide child categories and show all matching products in flat list
        if search_query:
            products = products.filter(
                Q(name__icontains=search_query) |
                Q(description__icontains=search_query) |
                Q(pack_description__icontains=search_query)
            )
            # Hide child categories when searching to show flat product list
            child_categories = None

        context = {
            'category': category,
            'child_categories': child_categories,
            'products': products,
            'breadcrumbs': breadcrumbs,
            'search_query': search_query,
        }
        return render(request, "catalogue/category_detail.html", context)


    context = {
        'category': category,
        'products': products,
        'breadcrumbs': breadcrumbs,
        'search_query': search_query,
    }
    return render(request, "catalogue/category_detail.html", context)


def product_search(request):
    query = request.GET.get('q', '').strip()
    products = Product.objects.none()

    if query:
        products = Product.objects.select_related('category').filter(
            Q(name__icontains=query) |
            Q(description__icontains=query) |
            Q(pack_description__icontains=query) |
            Q(category__name__icontains=query)
        ).distinct().order_by('name')

    context = {
        'products': products,
        'search_query': query,
    }
    return render(request, "catalogue/product_search.html", context)


def contact(request):
    return render(request, "contact.html")


@login_required
def order_form(request):
    parent_categories = Category.objects.filter(parent=None).prefetch_related("children__products", "products")

    if request.method == "POST":
        # Store order data in session for review
        order_data = {}
        order_items = []
        total = 0

        for parent_cat in parent_categories:
            # Check products in child categories
            for child_cat in parent_cat.children.all():
                for p in child_cat.products.all():
                    qty_str = request.POST.get(f"qty_{p.id}", "")
                    if qty_str and qty_str.isdigit():
                        qty = int(qty_str)
                        if qty > 0:
                            item_total = (p.price_inc_gst or 0) * qty
                            order_items.append({
                                'product_id': p.id,
                                'product_name': p.name,
                                'pack_description': p.pack_description,
                                'price': p.price_inc_gst or 0,
                                'quantity': qty,
                                'total': item_total
                            })
                            total += item_total

            # Also check products directly in parent category (backward compatibility)
            for p in parent_cat.products.all():
                qty_str = request.POST.get(f"qty_{p.id}", "")
                if qty_str and qty_str.isdigit():
                    qty = int(qty_str)
                    if qty > 0:
                        item_total = (p.price_inc_gst or 0) * qty
                        order_items.append({
                            'product_id': p.id,
                            'product_name': p.name,
                            'pack_description': p.pack_description,
                            'price': p.price_inc_gst or 0,
                            'quantity': qty,
                            'total': item_total
                        })
                        total += item_total

        if not order_items:
            return render(
                request,
                "order_form.html",
                {"parent_categories": parent_categories, "error": "Please select at least one item."},
            )

        # Store in session
        request.session['order_data'] = {
            'items': order_items,
            'total': total,
            'item_count': sum(item['quantity'] for item in order_items)
        }

        return redirect("order_review")

    return render(request, "order_form.html", {"parent_categories": parent_categories})


@login_required
def order_review(request):
    order_data = request.session.get('order_data')
    if not order_data:
        return redirect('order_form')

    if request.method == "POST":
        # Create the actual order
        notes = request.POST.get('notes', '')
        order = Order.objects.create(customer=request.user, status="new", notes=notes)

        # Create order lines
        for item in order_data['items']:
            product = Product.objects.get(id=item['product_id'])
            OrderLine.objects.create(
                order=order,
                product=product,
                quantity=item['quantity']
            )

        # Store order ID in session for confirmation page
        request.session['last_order_id'] = order.id

        # Clear order data from session
        del request.session['order_data']

        return redirect("order_confirmation")

    context = {
        'order_data': order_data,
        'user': request.user
    }
    return render(request, "order_review.html", context)


@login_required
def order_confirmation(request):
    last_order_id = request.session.get('last_order_id')
    order = None

    if last_order_id:
        try:
            order = Order.objects.select_related('customer').prefetch_related('lines__product').get(
                id=last_order_id,
                customer=request.user
            )
            # Calculate total
            order_total = sum(
                line.product.price_inc_gst * line.quantity
                for line in order.lines.all()
                if line.product.price_inc_gst
            )
            order.calculated_total = order_total
        except Order.DoesNotExist:
            pass

    return render(request, "order_confirmation.html", {"order": order})


@login_required
def my_orders(request):
    """Display customer's order history"""
    orders = Order.objects.filter(customer=request.user).order_by('-created_at')

    # Calculate totals for each order
    for order in orders:
        order.calculated_total = order.get_total_inc_gst()

    return render(request, "my_orders.html", {"orders": orders})


@login_required
def order_detail_view(request, order_id):
    """Display a specific order's details"""
    order = get_object_or_404(Order, id=order_id, customer=request.user)
    order.calculated_total = order.get_total_inc_gst()

    return render(request, "order.html", {"order": order})

