from pathlib import Path
from urllib.parse import unquote

from django.conf import settings
from django.contrib import admin
from django.http import FileResponse, Http404
from django.urls import include, path, re_path
from django.views.generic import RedirectView

from app import views, views_konten


def _find_file(candidates):
    for file_path in candidates:
        try:
            resolved = file_path.resolve()
            if resolved.is_file():
                return resolved
        except OSError:
            continue
    return None


def serve_static_aset(request, path):
    clean_path = unquote(path).lstrip('/')
    base_dir = Path(settings.BASE_DIR)
    resolved = _find_file([
        base_dir / 'static' / clean_path,
        base_dir / clean_path,
    ])
    if resolved:
        return FileResponse(open(resolved, 'rb'))
    raise Http404('File not found')


def serve_media_fallback(request, path):
    clean_path = unquote(path).lstrip('/')
    base_dir = Path(settings.BASE_DIR)
    aset_dir = base_dir / 'static' / 'aset'
    filename = Path(clean_path).name

    fallback_candidates = [
        base_dir / 'static' / 'media' / clean_path,
        base_dir / 'media' / clean_path,
        aset_dir / filename,
        aset_dir / 'foto 1.png',
        aset_dir / 'foto 2.png',
        aset_dir / 'foto 3.jpeg',
    ]

    if aset_dir.is_dir():
        for ext in ('.png', '.jpg', '.jpeg', '.webp'):
            matches = sorted(aset_dir.glob(f'*{ext}'))
            if matches:
                fallback_candidates.append(matches[0])

    resolved = _find_file(fallback_candidates)
    if resolved:
        return FileResponse(open(resolved, 'rb'))
    raise Http404('Media not found')


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
    re_path(r'^media/(?P<path>.+)$', serve_media_fallback),
    re_path(r'^(?P<path>aset/.+)$', serve_static_aset),
]