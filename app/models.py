import os
import uuid

from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify


# MODEL 1: Universitas (data master kampus tempat pelanggan wisuda)
class Universitas(models.Model):
    nama_universitas = models.CharField(max_length=150)
    singkatan = models.CharField(max_length=20, blank=True, default='')
    aktif = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = 'Universitas'
        ordering = ['nama_universitas']

    def __str__(self):
        return self.nama_universitas


GENDER_CHOICES = [
    ('Laki-laki', 'Laki-laki'),
    ('Perempuan', 'Perempuan'),
]


# MODEL 2: Profil Admin (role last_name = "Super Admin")
class UserAdmin(models.Model):
    username = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='useradmin'
    )
    photo = models.ImageField(upload_to='admin/', blank=True, null=True)
    telp = models.CharField(max_length=20, blank=True)
    gender = models.CharField(max_length=20, choices=GENDER_CHOICES, blank=True)

    def __str__(self):
        return f"Admin {self.username}"


# MODEL 3: Profil Pengguna / customer (role last_name = "Pengguna")
class UserPengguna(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='userpengguna'
    )
    photo = models.ImageField(upload_to='pengguna/', blank=True, null=True)
    telp = models.CharField(max_length=20, blank=True)
    gender = models.CharField(max_length=20, choices=GENDER_CHOICES, blank=True)
    tanggal_lahir = models.DateField(null=True, blank=True)
    universitas = models.ForeignKey(
        Universitas,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    jurusan = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return f"Pengguna {self.user}"


# ===================== KATALOG PAKET (setara "produk" di materi dosen) =====================
def _slug_unik(model, dasar, pk=None, maks=100):
    dasar = (slugify(dasar) or 'paket')[:maks - 8]
    slug, n = dasar, 2
    qs = model.objects.exclude(pk=pk) if pk else model.objects.all()
    while qs.filter(slug=slug).exists():
        slug = f"{dasar}-{n}"
        n += 1
    return slug


# MODEL 4: Kategori Paket (aktif/tidak, supaya bisa disembunyikan tanpa menghapus data)
class KategoriPaket(models.Model):
    slug = models.SlugField(max_length=100, unique=True, blank=True)
    nama_kategori = models.CharField(max_length=100)
    deskripsi_kategori = models.TextField(blank=True)
    aktif = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Kategori Paket'
        verbose_name_plural = 'Kategori Paket'
        ordering = ['nama_kategori']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = _slug_unik(KategoriPaket, self.nama_kategori, self.pk)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.nama_kategori


def rename_featured_image(instance, filename):
    ext = filename.split('.')[-1]
    stamp = timezone.now().strftime('%Y%m%d%H%M%S')
    return os.path.join('paket/featured_image/', f"paket_{stamp}_{uuid.uuid4().hex[:6]}.{ext}")


def rename_media_paket(instance, filename):
    ext = filename.split('.')[-1]
    stamp = timezone.now().strftime('%Y%m%d%H%M%S')
    return os.path.join('paket/media/', f"media_paket_{stamp}_{uuid.uuid4().hex[:6]}.{ext}")


# MODEL 5: Paket Fotografi
class Package(models.Model):
    STATUS_PAKET = [
        ('Tersedia', 'Tersedia'),
        ('Draft', 'Draft (disembunyikan)'),
    ]

    slug = models.SlugField(max_length=120, unique=True, blank=True)
    name = models.CharField(max_length=100)
    kategori = models.ForeignKey(KategoriPaket, on_delete=models.SET_NULL, null=True, blank=True,
                                 related_name='paket')
    badge = models.CharField(max_length=30, blank=True)
    peserta = models.CharField(max_length=30, default='1 Orang')
    price = models.PositiveIntegerField()
    harga_potongan = models.PositiveIntegerField(null=True, blank=True)
    duration_minutes = models.PositiveIntegerField()
    hasil = models.CharField(max_length=100, blank=True)
    edited_photo_count = models.PositiveIntegerField(default=0)
    stok = models.PositiveIntegerField(default=0)  # BARU (slide Products)
    deskripsi = models.TextField(blank=True)
    subtitle = models.CharField(max_length=200, blank=True)
    kicker = models.CharField(max_length=120, blank=True)
    deskripsi_lengkap = models.TextField(blank=True)
    featured_image = models.ImageField(upload_to=rename_featured_image, max_length=255, null=True, blank=True)
    faq_json = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_PAKET, default='Tersedia')
    urutan = models.PositiveSmallIntegerField(default=0)
    created_at = models.DateTimeField(default=timezone.now, editable=False)
    updated_at = models.DateTimeField(default=timezone.now, editable=False)

    class Meta:
        verbose_name = 'Paket'
        verbose_name_plural = 'Paket'
        ordering = ['urutan', 'name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = _slug_unik(Package, self.name, self.pk, 120)
        self.updated_at = timezone.now()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        if self.kategori and self.kategori.slug:
            return reverse('paket_detail', kwargs={'kategori_slug': self.kategori.slug, 'slug': self.slug})
        return f"/detail.html?paket={self.slug}"

    @property
    def harga_akhir(self):
        """Harga yang dipakai transaksi: harga potongan kalau ada, kalau tidak harga awal."""
        if self.harga_potongan and 0 < self.harga_potongan < self.price:
            return self.harga_potongan
        return self.price

    @staticmethod
    def _rp(n):
        return 'Rp ' + f'{n:,}'.replace(',', '.')

    @property
    def price_rp(self):
        return self._rp(self.price)

    @property
    def potongan_rp(self):
        return self._rp(self.harga_potongan) if self.harga_potongan else ''

    @property
    def persentase_diskon(self):
        if self.price and self.price > 0 and self.harga_potongan and self.harga_potongan < self.price:
            return int(round(((self.price - self.harga_potongan) / self.price) * 100))
        return 0


# MODEL 6: Media Paket (satu paket bisa punya banyak foto galeri)
class MediaPaket(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    package = models.ForeignKey(Package, on_delete=models.CASCADE, related_name='media_paket')
    media = models.ImageField(upload_to=rename_media_paket, max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Media Paket'
        verbose_name_plural = 'Media Paket'
        ordering = ['created_at']

    def __str__(self):
        return f"Media: {self.package.name}"


# MODEL 7: Booking Pelanggan
class Booking(models.Model):

    STATUS_CHOICES = [
        ('pending', 'Menunggu Pembayaran'),
        ('confirmed', 'Booking Dikonfirmasi'),
        ('completed', 'Selesai'),
        ('cancelled', 'Dibatalkan'),
    ]

    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )
    package = models.ForeignKey(
        Package,
        on_delete=models.PROTECT
    )
    booking_date = models.DateField()
    booking_time = models.TimeField()
    location = models.CharField(max_length=255)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Booking #{self.pk}"


# MODEL 8: Pembayaran
class Payment(models.Model):

    STATUS_CHOICES = [
        ('pending', 'Menunggu Pembayaran'),
        ('partial', 'DP Dibayar'),
        ('paid', 'Lunas'),
        ('failed', 'Gagal'),
    ]

    booking = models.ForeignKey(
        Booking,
        on_delete=models.PROTECT
    )
    amount = models.PositiveIntegerField()
    payment_method = models.CharField(max_length=50)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    transaction_id = models.CharField(max_length=150, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Payment #{self.pk}"


# KONTEN WEBSITE 
def _rename(folder, prefix):
    def fn(instance, filename):
        ext = filename.split('.')[-1]
        stamp = timezone.now().strftime('%Y%m%d%H%M%S')
        return os.path.join(folder, f"{prefix}_{stamp}_{uuid.uuid4().hex[:6]}.{ext}")
    return fn


def rename_article_image(instance, filename):
    return _rename('artikel/', 'artikel')(instance, filename)


def rename_page_image(instance, filename):
    return _rename('halaman/', 'halaman')(instance, filename)


def rename_hero_banner(instance, filename):
    return _rename('hero_slides/', 'slide')(instance, filename)


def rename_hero_icon(instance, filename):
    return _rename('hero_slides/icon/', 'icon')(instance, filename)


def rename_mitra_logo(instance, filename):
    return _rename('mitra/', 'mitra')(instance, filename)


# MODEL 9: Kategori Artikel
class Category(models.Model):
    STATUS_CHOICES = (
        ('aktif', 'Aktif'),
        ('nonaktif', 'Nonaktif'),
    )
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True, blank=True)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='aktif')  # BARU
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Kategori Artikel'
        verbose_name_plural = 'Kategori Artikel'
        ordering = ['name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = _slug_unik(Category, self.name, self.pk)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


# MODEL 10: Artikel (tips, info, dan pengumuman)
class Article(models.Model):
    STATUS_CHOICES = (
        ('draft', 'Draft'),
        ('published', 'Published'),
        ('archived', 'Archived'),
    )
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
                               blank=True, related_name='articles')
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True,
                                 related_name='articles')
    deskripsi_seo = models.CharField(max_length=300, blank=True,
                                     help_text='Meta description untuk SEO/GEO')  # BARU
    content = models.TextField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='draft')
    featured_image = models.ImageField(upload_to=rename_article_image, max_length=255, blank=True, null=True)
    views_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Artikel'
        verbose_name_plural = 'Artikel'
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = _slug_unik(Article, self.title, self.pk, 200)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title


# MODEL 11: Halaman statis 
class Page(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
                               blank=True, related_name='pages')
    deskripsi = models.CharField(max_length=300, blank=True,
                                 help_text='Meta description untuk SEO')  # BARU
    content = models.TextField()
    featured_image = models.ImageField(upload_to=rename_page_image, max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Halaman'
        verbose_name_plural = 'Halaman'
        ordering = ['title']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = _slug_unik(Page, self.title, self.pk, 200)
        else:
            self.slug = slugify(self.slug) or _slug_unik(Page, self.title, self.pk, 200)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title


# MODEL 12: Pengaturan Website (satu baris data untuk seluruh website)
class WebSetting(models.Model):
    nama_web = models.CharField(max_length=200, default='Amora Grads')
    tagline = models.CharField(max_length=200, blank=True)
    alamat = models.TextField(blank=True)
    no_telp = models.CharField(max_length=20, blank=True, help_text='Nomor WhatsApp, contoh: 081234567890')
    email = models.EmailField(blank=True)
    jam_operasional = models.CharField(max_length=200, blank=True)
    logo = models.ImageField(upload_to='web_setting/logo/', max_length=255, blank=True, null=True)
    favicon = models.ImageField(upload_to='web_setting/favicon/', max_length=255, blank=True, null=True)  # BARU
    link_instagram = models.URLField(blank=True)
    link_tiktok = models.URLField(blank=True)
    link_twitter = models.URLField(blank=True)  # BARU
    link_facebook = models.URLField(blank=True)
    link_youtube = models.URLField(blank=True)
    link_maps = models.URLField(blank=True)

    class Meta:
        verbose_name = 'Pengaturan Website'
        verbose_name_plural = 'Pengaturan Website'

    @property
    def wa_number(self):
        """Nomor WhatsApp format internasional tanpa tanda + (dipakai wa.me)."""
        digits = ''.join(ch for ch in (self.no_telp or '') if ch.isdigit())
        if digits.startswith('0'):
            digits = '62' + digits[1:]
        return digits

    def __str__(self):
        return self.nama_web


# MODEL 13: Kerja Sama / Mitra (networking)
class KerjaSama(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nama_kerjasama = models.CharField(max_length=200)
    logo = models.ImageField(upload_to=rename_mitra_logo, max_length=255, blank=True, null=True)
    link_website = models.URLField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Kerja Sama'
        verbose_name_plural = 'Kerja Sama'
        ordering = ['-created_at']

    def __str__(self):
        return self.nama_kerjasama


# MODEL 14: Hero Slide 
class HeroSlide(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    judul = models.CharField(max_length=200, verbose_name='Judul slide')
    judul_highlight = models.CharField(max_length=200, blank=True, verbose_name='Judul (bagian berwarna)')
    badge_text = models.CharField(max_length=100, blank=True, verbose_name='Teks kecil di atas judul')
    badge_icon = models.ImageField(upload_to=rename_hero_icon, max_length=255, blank=True, null=True,
                                   verbose_name='Ikon badge (opsional)')  # BARU
    deskripsi = models.TextField(verbose_name='Deskripsi')
    tombol_teks = models.CharField(max_length=100, default='Booking sekarang', verbose_name='Teks tombol')
    tombol_url = models.CharField(max_length=200, default='/katalog.html', verbose_name='Tujuan tombol',
                                  help_text='Contoh: /katalog.html atau #galeri')
    banner = models.ImageField(upload_to=rename_hero_banner, max_length=255, blank=True, null=True,
                               verbose_name='Foto slide (opsional)')
    urutan = models.PositiveIntegerField(default=0, verbose_name='Urutan tampil')
    is_active = models.BooleanField(default=True, verbose_name='Aktif')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Hero Slide'
        verbose_name_plural = 'Hero Slide'
        ordering = ['urutan', 'created_at']

    def __str__(self):
        return self.judul