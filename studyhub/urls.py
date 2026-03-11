from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),

    # Django built-in auth routes:
    # /accounts/login/, /accounts/logout/, password reset ...
    path("accounts/", include("django.contrib.auth.urls")),

    # Your app routes
    path("", include("core.urls")),
]