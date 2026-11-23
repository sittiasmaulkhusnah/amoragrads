from pathlib import Path
from urllib.parse import unquote

from django.conf import settings
from django.contrib import admin
from django.http import FileResponse, Http404
from django.urls import include, path, re_path
from django.views.generic import RedirectView

from app import views, views_konten


def serve_static_aset(request, path):
    clean_path = unquote(path).lstrip('/')
    base_dir = Path(settings.BASE_DIR)
    candidates = [
        base_dir / 'static' / clean_path,
        base_dir / clean_path,
    ]
    for file_path in candidates:
        try:
            resolved = file_path.resolve()
            if resolved.is_file() and (
                (base_dir / 'static').resolve() in resolved.parents
                or base_dir.resolve() in resolved.parents
            ):
                return FileResponse(open(resolved, 'rb'))
        except OSError:
            continue
    raise Http404('File not found')


urlpatterns = [
    path('admin/', admin.site.urls),
]

urlpatterns += [
    path('app/', include(('app.urls', 'app'), namespace='app')),
    path('login/', views.loginView, name='login'),
    path('register/', views.registerView, name='register'),
    path('logout/', views.LogoutView, name='logout'),
]

# Halaman frontend Amora Grads
urlpatterns += [
    path('', views.home, name='home'),
    path('index.html', views.home),
    path('paket.js', views.paket_js, name='paket_js'),
    path('artikel/', views_konten.artikel_list, name='artikel_list'),
    path('artikel/<slug:slug>/', views_konten.artikel_detail, name='artikel_detail'),
    path('halaman/<slug:slug>/', views_konten.halaman_detail, name='halaman_detail'),
    path('produk/<slug:kategori_slug>/<slug:slug>/', views.paket_detail, name='paket_detail'),
    path('katalog.html', views.katalog, name='katalog'),
    path('detail.html', views.detail, name='detail'),
    path('booking.html', views.booking_page, name='booking'),
    path('login.html', RedirectView.as_view(pattern_name='login')),
    path('profil.html', RedirectView.as_view(pattern_name='app:dashboard')),
    path('auth.js', serve_static_aset, {'path': 'auth.js'}),
    re_path(r'^static/(?P<path>.+)$', serve_static_aset),
    re_path(r'^(?P<path>aset/.+)$', serve_static_aset),
]