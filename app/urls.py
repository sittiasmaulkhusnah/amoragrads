from django.urls import path

from . import views, views_admin, views_konten, views_pengguna

urlpatterns = [
    path('profile/admin', views_admin.profile_admin, name='profile_admin'),
    path('profile/pengguna', views_pengguna.profile_pengguna, name='profile_pengguna'),
    path('pengguna/daftar', views_admin.daftar_pengguna, name='daftar_pengguna'),
    path('booking/<int:pk>/status', views_admin.booking_status, name='booking_status'),
    path('paket/kategori/', views_admin.kategori_paket_list, name='kategori_paket_list'),
    path('paket/kategori/tambah/', views_admin.kategori_paket_tambah, name='kategori_paket_tambah'),
    path('paket/kategori/edit/<int:pk>/', views_admin.kategori_paket_edit, name='kategori_paket_edit'),
    path('paket/kategori/hapus/<int:pk>/', views_admin.kategori_paket_hapus, name='kategori_paket_hapus'),
    path('paket/', views_admin.paket_list, name='paket_list'),
    path('paket/tambah/', views_admin.paket_tambah, name='paket_tambah'),
    path('paket/edit/<int:pk>/', views_admin.paket_edit, name='paket_edit'),
    path('paket/hapus/<int:pk>/', views_admin.paket_hapus, name='paket_hapus'),
    path('paket/<int:paket_pk>/media/hapus/<uuid:media_uuid>/', views_admin.paket_media_hapus, name='paket_media_hapus'),
    path('konten/<str:jenis>/', views_konten.konten_list, name='konten_list'),
    path('konten/<str:jenis>/tambah/', views_konten.konten_form, name='konten_tambah'),
    path('konten/<str:jenis>/<uuid:pk>/edit/', views_konten.konten_form, name='konten_edit'),
    path('konten/<str:jenis>/<uuid:pk>/hapus/', views_konten.konten_hapus, name='konten_hapus'),
    path('pengaturan/', views_konten.pengaturan_web, name='pengaturan_web'),
    path('api/me/', views.api_me, name='api_me'),
    path('api/bookings/', views.api_bookings, name='api_bookings'),
    path('api/bookings/<int:pk>/batal/', views.api_booking_batal, name='api_booking_batal'),
    path('api/bookings/<int:pk>/reschedule/', views.api_booking_reschedule, name='api_booking_reschedule'),
    path('dashboard', views.index, name='dashboard'),
    path('', views.index, name='index'),
]
