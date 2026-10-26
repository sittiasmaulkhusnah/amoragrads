from django.db import models
from django.conf import settings


# MODEL 1: Paket Fotografi
class Package(models.Model):
    name = models.CharField(max_length=100)
    price = models.PositiveIntegerField()
    duration_minutes = models.PositiveIntegerField()
    edited_photo_count = models.PositiveIntegerField()

    def __str__(self):
        return self.name


# MODEL 2: Booking Pelanggan
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


# MODEL 3: Pembayaran
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

    payment_method = models.CharField(
        max_length=50
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )

    transaction_id = models.CharField(
        max_length=150,
        blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Payment #{self.pk}"

# MODEL 4: Profil tambahan pengguna (no HP, tanggal lahir, gender)
class Profile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='profile'
    )
    phone = models.CharField(max_length=20, blank=True)
    dob = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=20, blank=True)

    def __str__(self):
        return f"Profil {self.user.username}"
