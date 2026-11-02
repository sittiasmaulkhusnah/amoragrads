from django.contrib import admin

from .models import (Booking, KategoriPaket, MediaPaket, Package, Payment, Universitas,
                     UserAdmin, UserPengguna)

admin.site.register(UserPengguna)
admin.site.register(UserAdmin)
admin.site.register(Universitas)
admin.site.register(Package)
admin.site.register(Booking)
admin.site.register(Payment)
admin.site.register(KategoriPaket)
admin.site.register(MediaPaket)
