from django.urls import path

from . import views


urlpatterns = [
    path("", views.home, name="home"),
    path("about/", views.about, name="about"),
    path("products/", views.category_list, name="category_list"),
    path("products/<slug:category_slug>/", views.category_detail, name="parent_category_detail"),
    path("products/<slug:parent_slug>/<slug:child_slug>/", views.category_detail, name="category_detail"),
    path("contact/", views.contact, name="contact"),
    path("order/", views.order_form, name="order_form"),
    path("order/review/", views.order_review, name="order_review"),
    path("order/confirmation/", views.order_confirmation, name="order_confirmation"),
    path("my-orders/", views.my_orders, name="my_orders"),
    path("my-orders/<int:order_id>/", views.order_detail_view, name="order_detail"),
]
