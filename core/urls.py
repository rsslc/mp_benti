from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path


urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("catalogue.urls")),
    path("cart/", include("cart.urls")),
    path("dashboard/", include("dashboard.urls")),
    path("__reload__/", include("django_browser_reload.urls")),
    path(
        "accounts/login/",
        auth_views.LoginView.as_view(template_name="login.html"),
        name="login",
    ),
    path(
        "accounts/logout/", auth_views.LogoutView.as_view(next_page="/"), name="logout"
    ),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
