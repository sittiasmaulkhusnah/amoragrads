import json
import os
import re
from pathlib import Path

from django.conf import settings
from django.contrib.auth.models import User
from django.core.files import File
from django.core.management.base import BaseCommand

from app.models import KategoriPaket, MediaPaket, Package, Universitas, UserAdmin
from app.roles import ROLE_ADMIN

UNIVERSITAS = [  # kampus di Makassar dan sekitarnya 
    ('Universitas Hasanuddin', 'UNHAS'),
    ('Universitas Negeri Makassar', 'UNM'),
    ('UIN Alauddin Makassar', 'UINAM'),
    ('Universitas Muhammadiyah Makassar', 'UNISMUH'),
    ('Universitas Muslim Indonesia', 'UMI'),
    ('Universitas Bosowa', 'UNIBOS'),
    ('Universitas Fajar', 'UNIFA'),
    ('Politeknik Negeri Ujung Pandang', 'PNUP'),
    ('Universitas Islam Makassar', 'UIM'),
    ('Universitas Cokroaminoto Makassar', 'UCM'),
    ('Universitas Kristen Indonesia Paulus', 'UKI Paulus'),
    ('Universitas Handayani Makassar', 'UNHAN'),
    ('Universitas Patria Artha', 'UPA'),
    ('Universitas Dipa Makassar', 'UNDIPA'),
    ('Kampus lainnya', ''),
]


class Command(BaseCommand):
    help = 'Isi data paket + universitas, dan jadikan superuser sebagai "Super Admin".'

    def handle(self, *args, **opts):
        self.seed_paket()
        for nama, singkat in UNIVERSITAS:
            Universitas.objects.update_or_create(nama_universitas=nama, defaults=dict(singkatan=singkat, aktif=True))
        for u in User.objects.filter(is_superuser=True):
            u.last_name = ROLE_ADMIN
            if not u.first_name:
                u.first_name = 'Admin Amora'
            u.save()
            UserAdmin.objects.get_or_create(username=u)
        self.stdout.write(self.style.SUCCESS('Seed selesai (kategori, paket + galeri, universitas, role Super Admin).'))

    def _salin_gambar(self, field, path_statis):
        """Salin gambar dari static/aset ke media supaya bisa dikelola lewat dashboard admin."""
        sumber = Path(settings.BASE_DIR) / 'static' / path_statis
        if not sumber.exists():
            self.stdout.write(self.style.WARNING(f'  gambar tidak ditemukan: {path_statis}'))
            return False
        with open(sumber, 'rb') as f:
            field.save(sumber.name, File(f), save=False)
        return True

    def seed_paket(self):
        data = json.loads((Path(__file__).resolve().parents[2] / 'data' / 'paket_awal.json').read_text(encoding='utf-8'))
        kategori = {}
        for urut, item in enumerate(data):
            nama_kat = item['kategori']
            if nama_kat not in kategori:
                kategori[nama_kat], _ = KategoriPaket.objects.get_or_create(
                    nama_kategori=nama_kat, defaults={'aktif': True})
            durasi = int(re.findall(r'\d+', item['duration'])[0])
            m = re.match(r'(\d+) Foto Edit', item['photos'])
            paket, _ = Package.objects.update_or_create(name=item['name'], defaults=dict(
                slug=item['id'], kategori=kategori[nama_kat], badge=item['badge'] or '',
                peserta=item['people'], price=int(item['price'].replace('.', '')),
                duration_minutes=durasi, edited_photo_count=int(m.group(1)) if m else 0,
                hasil=item['photos'], deskripsi=item['desc'], subtitle=item.get('subtitle', ''),
                kicker=item.get('kicker', ''), deskripsi_lengkap=item.get('long', ''),
                faq_json=json.dumps(item.get('faq', []), ensure_ascii=False),
                status='Tersedia', urutan=urut))
            if not paket.featured_image and item.get('img'):
                if self._salin_gambar(paket.featured_image, item['img']):
                    paket.save()
            if not paket.media_paket.exists():
                for g in item.get('gallery', []):
                    media = MediaPaket(package=paket)
                    if self._salin_gambar(media.media, g):
                        media.save()
