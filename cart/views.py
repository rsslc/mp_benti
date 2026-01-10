from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.shortcuts import redirect, render, get_object_or_404
from django.template.loader import render_to_string
from django.conf import settings

from catalogue.models import Product
from orders.models import Order, OrderLine
from .cart import Cart


def cart_detail(request):
    """Display the cart"""
    cart = Cart(request)

    # Update quantities if POST request
    if request.method == 'POST':
        for key, value in request.POST.items():
            if key.startswith('quantity_'):
                product_id = key.replace('quantity_', '')
                try:
                    quantity = int(value)
                    cart.update_quantity(product_id, quantity)
                except (ValueError, TypeError):
                    pass
        messages.success(request, 'Cart updated successfully.')
        return redirect('cart_detail')

    return render(request, 'cart/cart_detail.html', {'cart': cart})


def cart_add(request, product_id):
    """Add a product to the cart or update quantity"""
    product = get_object_or_404(Product, id=product_id)
    cart = Cart(request)

    quantity = int(request.POST.get('quantity', 1))
    update_mode = request.POST.get('update_mode', 'false') == 'true'

    if update_mode:
        # Update mode: set to exact quantity
        cart.add(product=product, quantity=quantity, override_quantity=True)
        messages.success(request, f'{product.name} quantity updated to {quantity}.')
    else:
        # Add mode: add to existing quantity
        cart.add(product=product, quantity=quantity, override_quantity=False)
        messages.success(request, f'{product.name} added to cart.')

    # Redirect back to the referring page or to cart
    next_url = request.POST.get('next', request.META.get('HTTP_REFERER', 'cart_detail'))
    return redirect(next_url)


def cart_remove(request, product_id):
    """Remove a product from the cart"""
    product = get_object_or_404(Product, id=product_id)
    cart = Cart(request)
    cart.remove(product)

    messages.success(request, f'{product.name} removed from cart.')
    return redirect('cart_detail')


@login_required
def checkout(request):
    """Process checkout and create order"""
    cart = Cart(request)

    if len(cart) == 0:
        messages.warning(request, 'Your cart is empty.')
        return redirect('cart_detail')

    if request.method == 'POST':
        # Create the order
        notes = request.POST.get('notes', '')
        order = Order.objects.create(customer=request.user, status='new', notes=notes)

        # Create order lines
        for item in cart:
            product = item['product']
            OrderLine.objects.create(
                order=order,
                product=product,
                quantity=item['quantity'],
                unit_price_ex_gst=product.price_ex_gst,
                unit_price_inc_gst=product.price_inc_gst
            )

        # Send email notifications
        try:
            # Send notification to admin/owner
            send_order_notification_email(order)
        except Exception as e:
            # Log the error but don't fail the order
            print(f"Failed to send admin notification email: {e}")

        try:
            # Send confirmation to customer
            send_customer_confirmation_email(order)
        except Exception as e:
            # Log the error but don't fail the order
            print(f"Failed to send customer confirmation email: {e}")

        # Clear the cart
        cart.clear()

        messages.success(request, f'Order #{order.id} placed successfully!')
        return redirect('order_detail', order_id=order.id)

    # Calculate totals for display
    items = list(cart)
    total = cart.get_total_price()

    return render(request, 'cart/checkout.html', {
        'cart': cart,
        'items': items,
        'total': total
    })


def send_order_notification_email(order):
    """Send order notification email to admin/owner"""
    subject = f'New Order #{order.id} from {order.customer.username}'

    # Prepare order items
    items = []
    for line in order.lines.all():
        items.append({
            'product': line.product.name,
            'quantity': line.quantity,
            'price': line.unit_price_inc_gst or 0,
            'total': (line.unit_price_inc_gst or 0) * line.quantity
        })

    context = {
        'order': order,
        'items': items,
        'total': order.get_total_inc_gst()
    }

    # Render email template
    message = render_to_string('cart/order_notification_email.txt', context)

    # Send to both admin email addresses
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        ['mpbenti@gmail.com', 'mpbenti2@gmail.com'],
        fail_silently=False,
    )


def send_customer_confirmation_email(order):
    """Send order confirmation email to customer"""
    subject = f'Order Confirmation - Order #{order.id}'

    # Prepare order items
    items = []
    for line in order.lines.all():
        items.append({
            'product': line.product.name,
            'pack_size': line.product.pack_size,
            'quantity': line.quantity,
            'price': line.unit_price_inc_gst or 0,
            'total': (line.unit_price_inc_gst or 0) * line.quantity
        })

    context = {
        'order': order,
        'customer': order.customer,
        'items': items,
        'total': order.get_total_inc_gst()
    }

    # Render email template
    message = render_to_string('cart/customer_confirmation_email.txt', context)

    # Send to customer
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [order.customer.email],
        fail_silently=False,
    )

