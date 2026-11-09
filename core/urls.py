from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path, re_path
from django.views.generic import RedirectView
from django.views.static import serve

from app import views, views_konten

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
    # file statis frontend: folder aset/ dan auth.js (paket.js dibangkitkan dari database)
    re_path(r'^(?P<path>(?:aset/.+|auth\.js))$', serve,
            {'document_root': settings.BASE_DIR / 'static'}),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
