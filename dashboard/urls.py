from django.urls import path

from . import views


urlpatterns = [
    path("", views.dashboard_home, name="dashboard_home"),
    path("orders/", views.orders_list, name="dashboard_orders"),
    # Order management
    path("orders/<int:order_id>/", views.order_detail, name="order_detail"),
    path("orders/add/", views.order_add, name="order_add"),
    path("orders/<int:order_id>/edit/", views.order_edit, name="order_edit"),
    path("orders/<int:order_id>/delete/", views.order_delete, name="order_delete"),
    path("products/", views.products_list, name="products_list"),
    path("categories/", views.categories_list, name="categories_list"),
    path("customers/", views.customers_list, name="dashboard_customers"),
    # Product management
    path("products/add/", views.product_add, name="product_add"),
    path("products/<int:product_id>/edit/", views.product_edit, name="product_edit"),
    path("products/<int:product_id>/delete/", views.product_delete, name="product_delete"),
    # Category management
    path("categories/add/", views.category_add, name="category_add"),
    path("categories/<int:category_id>/edit/", views.category_edit, name="category_edit"),
    path("categories/<int:category_id>/delete/", views.category_delete, name="category_delete"),
    # Superadmin only account management
    path("accounts/", views.accounts_list, name="accounts_list"),
    path("accounts/add/", views.account_add, name="account_add"),
    path("accounts/<int:user_id>/edit/", views.account_edit, name="account_edit"),
    path("accounts/<int:user_id>/delete/", views.account_delete, name="account_delete"),
    # Site settings
    path("settings/", views.site_settings, name="site_settings"),
]
