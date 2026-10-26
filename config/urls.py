from django.conf import settings
from django.contrib import admin
from django.urls import path, include, re_path
from django.views.static import serve

urlpatterns = [
    path('admin/', admin.site.urls),
    # file statis frontend: folder aset/, paket.js, auth.js
    re_path(r'^(?P<path>(?:aset/.+|paket\.js|auth\.js))$', serve, {'document_root': settings.BASE_DIR}),
    path('', include('booking.urls')),
]
