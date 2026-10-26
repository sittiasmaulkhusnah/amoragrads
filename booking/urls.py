from django.urls import path
from . import views

urlpatterns = [
    # halaman frontend (nama file .html dipertahankan supaya link lama tetap jalan)
    path('', views.home, name='home'),
    path('index.html', views.home),
    path('katalog.html', views.katalog),
    path('detail.html', views.detail),
    path('booking.html', views.booking_page),
    path('login.html', views.login_page, name='login'),
    path('profil.html', views.profil, name='profil'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('dashboard-admin/', views.dashboard_admin, name='dashboard_admin'),
    path('dashboard-admin/booking/<int:pk>/', views.admin_update_booking, name='admin_update_booking'),
    # API
    path('api/me/', views.api_me),
    path('api/register/', views.api_register),
    path('api/login/', views.api_login),
    path('api/logout/', views.api_logout),
    path('api/profile/', views.api_profile),
    path('api/bookings/', views.api_bookings),
]
