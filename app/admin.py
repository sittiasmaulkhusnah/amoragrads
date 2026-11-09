from django.contrib import admin

from .models import (Article, Booking, Category, HeroSlide, KategoriPaket, KerjaSama, MediaPaket, Package,
                     Page, Payment, Universitas, UserAdmin, UserPengguna, WebSetting)

admin.site.register(UserPengguna)
admin.site.register(UserAdmin)
admin.site.register(Universitas)
admin.site.register(Package)
admin.site.register(Booking)
admin.site.register(Payment)
admin.site.register(KategoriPaket)
admin.site.register(MediaPaket)
for m in (Category, Article, Page, WebSetting, KerjaSama, HeroSlide):
    admin.site.register(m)
