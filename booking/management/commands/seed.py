from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from booking.models import Package, Profile

# (nama, harga, durasi menit, jumlah foto edit; 0 = unlimited / video) -- sama dengan paket.js
PAKET = [
    ('Grads 1', 400000, 60, 25),
    ('Grads 2', 450000, 60, 35),
    ('Couple & Bestie', 700000, 60, 60),
    ('Group', 150000, 90, 0),
    ('Photo & Video', 999000, 120, 0),
    ('Video Cinematic Only', 650000, 120, 0),
    ('Eksklusif', 600000, 90, 40),
]


class Command(BaseCommand):
    help = 'Isi data paket + akun super admin (admin@amora.com / admin123)'

    def handle(self, *args, **opts):
        for nama, harga, durasi, foto in PAKET:
            Package.objects.update_or_create(name=nama, defaults=dict(
                price=harga, duration_minutes=durasi, edited_photo_count=foto))
        if not User.objects.filter(username='admin@amora.com').exists():
            u = User.objects.create_superuser('admin@amora.com', 'admin@amora.com', 'admin123',
                                              first_name='Admin Amora', last_name='super admin')
            Profile.objects.get_or_create(user=u)
        self.stdout.write(self.style.SUCCESS('Seed selesai. Admin: admin@amora.com / admin123'))
