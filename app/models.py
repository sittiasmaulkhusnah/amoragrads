import os
import uuid

from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify


# MODEL 1: Universitas 
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


# MODEL 2: Profil Admin 
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


# MODEL 3: Profil Pengguna / customer 
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


# KATALOG PAKET 
def _slug_unik(model, dasar, pk=None, maks=100):
    dasar = (slugify(dasar) or 'paket')[:maks - 8]
    slug, n = dasar, 2
    qs = model.objects.exclude(pk=pk) if pk else model.objects.all()
    while qs.filter(slug=slug).exists():
        slug = f"{dasar}-{n}"
        n += 1
    return slug


# MODEL 4: Kategori Paket (aktif/tidak)
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


# MODEL 6: Media Paket 
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


# MODEL 8: Payment
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
