import json
import os
import re
from pathlib import Path

from django.conf import settings
from django.contrib.auth.models import User
from django.core.files import File
from django.core.management.base import BaseCommand

from app.models import (Article, Category, HeroSlide, KategoriPaket, MediaPaket, Package, Page,
                        Universitas, UserAdmin, WebSetting)
from app.roles import ROLE_ADMIN

UNIVERSITAS = [  # kampus di Makassar dan sekitarnya (bisa diubah lewat /admin/)
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
        self.seed_konten()
        for nama, singkat in UNIVERSITAS:
            Universitas.objects.update_or_create(nama_universitas=nama, defaults=dict(singkatan=singkat, aktif=True))
        for u in User.objects.filter(is_superuser=True):
            u.last_name = ROLE_ADMIN
            if not u.first_name:
                u.first_name = 'Admin Amora'
            u.save()
            UserAdmin.objects.get_or_create(username=u)
        self.stdout.write(self.style.SUCCESS('Seed selesai (paket, universitas, konten website, role Super Admin).'))

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

    def seed_konten(self):
        """Isi awal konten website. Hanya dibuat kalau tabelnya masih kosong,
        jadi perubahan dan penghapusan dari panel admin tidak ditimpa lagi."""
        admin = User.objects.filter(is_superuser=True).first()

        if not WebSetting.objects.exists():
            WebSetting.objects.create(
                nama_web='Amora Grads',
                tagline='Jasa foto wisuda dan momen spesial, berbasis di Makassar.',
                alamat='Makassar, Sulawesi Selatan',
                no_telp='081296772025',
                link_instagram='https://www.instagram.com/amora.grads',
                link_tiktok='https://www.tiktok.com/@amoragrads',
            )

        if not HeroSlide.objects.exists():
            HeroSlide.objects.create(
                judul='Abadikan momen kelulusanmu.', badge_text='Studio foto wisuda & momen kelulusan',
                deskripsi='Amora Grads bantu kamu mengabadikan hari kelulusan dengan hasil yang natural, hangat, dan tetap kamu banget.',
                tombol_teks='Booking sekarang', tombol_url='/katalog.html', urutan=1)
            HeroSlide.objects.create(
                judul='Pilih paket yang pas untuk harimu.', badge_text='Dari sesi solo sampai bersama sahabat',
                deskripsi='Semua paket sudah termasuk hasil edit. Lihat pilihan paketnya dan amankan jadwal sesimu.',
                tombol_teks='Lihat katalog', tombol_url='/katalog.html', urutan=2)

        if not Category.objects.exists():
            tips = Category.objects.create(name='Tips Wisuda', description='Persiapan dan inspirasi untuk hari wisuda.')
            info = Category.objects.create(name='Info Amora', description='Informasi seputar layanan Amora Grads.')
            Article.objects.create(
                title='5 Tips Memilih Outfit untuk Foto Wisuda', category=tips, author=admin, status='published',
                content=(
                    'Outfit sangat memengaruhi hasil foto wisuda. Beberapa hal yang bisa kamu perhatikan:\n\n'
                    '1. Pilih warna yang kontras dengan toga dan latar tempat foto, supaya kamu tidak tenggelam di dalam gambar.\n\n'
                    '2. Utamakan kenyamanan. Pakaian yang nyaman membuat ekspresimu lebih natural saat bergerak dan berpose.\n\n'
                    '3. Coba outfit-mu lebih dulu dan cek tampilannya dari berbagai sudut, terutama saat duduk dan berjalan.\n\n'
                    '4. Gunakan riasan yang tahan lama dan tidak berlebihan, karena sesi foto bisa berlangsung cukup lama.\n\n'
                    '5. Siapkan satu set pakaian cadangan atau perlengkapan kecil seperti sisir, tisu, dan cermin.'))
            Article.objects.create(
                title='Persiapan Sebelum Hari Sesi Foto', category=tips, author=admin, status='published',
                content=(
                    'Supaya sesi fotomu berjalan lancar, coba siapkan hal-hal berikut:\n\n'
                    'Istirahat yang cukup di malam sebelumnya agar wajah tetap segar.\n\n'
                    'Datang sedikit lebih awal dari jadwal, supaya ada waktu merapikan diri tanpa terburu-buru.\n\n'
                    'Bawa perlengkapan pribadi seperti air minum, tisu, dan alat rias untuk touch up.\n\n'
                    'Kumpulkan beberapa referensi pose atau suasana yang kamu suka, lalu bagikan ke fotografer.'))
            Article.objects.create(
                title='Cara Booking Sesi Foto di Amora Grads', category=info, author=admin, status='published',
                content=(
                    'Booking sesi foto bisa dilakukan langsung lewat website:\n\n'
                    '1. Buat akun dan lengkapi profilmu.\n\n'
                    '2. Buka halaman Katalog, lalu pilih paket yang sesuai.\n\n'
                    '3. Pilih tanggal dan jam sesi yang masih tersedia, lalu isi data pemesan.\n\n'
                    '4. Selesaikan pembayaran DP.\n\n'
                    '5. Pantau jadwalmu di dashboard. Dari sana kamu juga bisa memindahkan jadwal atau membatalkan booking.'))

        if not Page.objects.exists():
            Page.objects.create(
                title='Tentang Kami', author=admin,
                content=(
                    'Amora Grads adalah jasa foto wisuda dan momen spesial yang berbasis di Makassar.\n\n'
                    'Kami membantu kamu mengabadikan hari kelulusan dengan hasil yang natural, hangat, dan tetap kamu banget. '
                    'Kamu bisa memilih paket sesuai kebutuhan di halaman Katalog, lalu mengatur jadwal sesimu langsung dari website.'))
            Page.objects.create(
                title='Kebijakan Privasi', author=admin,
                content=(
                    '(Teks contoh awal. Admin dapat mengubahnya kapan saja lewat panel admin, menu Kelola Halaman.)\n\n'
                    'Saat membuat akun dan melakukan booking, website ini menyimpan data yang kamu isi, yaitu nama, email, '
                    'nomor WhatsApp, kampus, serta detail booking dan pembayaran DP.\n\n'
                    'Data tersebut digunakan untuk mengelola akunmu, mengatur jadwal sesi foto, dan menghubungimu terkait booking.'))
