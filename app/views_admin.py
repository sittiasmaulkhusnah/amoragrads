from django.contrib import messages
from django.db.models import ProtectedError
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .decorators_admin import admin_required
from .form_admin import KategoriPaketForm, PaketForm, formProfile
from .models import Booking, KategoriPaket, MediaPaket, Package, Payment, UserAdmin, UserPengguna


@admin_required
def profile_admin(request):
    try:
        useradmin = UserAdmin.objects.get(username=request.user)
    except UserAdmin.DoesNotExist:
        useradmin = UserAdmin(username=request.user)

    if request.method == 'POST':
        form = formProfile(request.POST, request.FILES, instance=useradmin)
        if form.is_valid():
            obj = form.save()
            request.user.first_name = form.cleaned_data['nama_lengkap']
            request.user.save()
            messages.success(request, 'Profil Anda berhasil diperbarui!')
            return redirect('app:profile_admin')
        messages.error(request, 'Gagal memperbarui profil. Periksa isian form.')
    else:
        form = formProfile(instance=useradmin)

    context = {
        'title': 'Profile Admin',
        'heading': 'Edit Profile Admin',
        'useradmin': useradmin,
        'photo': useradmin.photo if getattr(useradmin, 'photo', None) else None,
        'form': form,
    }
    return render(request, 'admin_super/profile_admin.html', context)


@admin_required
def daftar_pengguna(request):
    pengguna = UserPengguna.objects.select_related('user', 'universitas').order_by('-user__date_joined')
    return render(request, 'admin_super/daftar_pengguna.html', {
        'title': 'Daftar Pengguna',
        'photo': None,
        'pengguna': pengguna,
    })


@admin_required
@require_POST
def booking_status(request, pk):
    b = get_object_or_404(Booking, pk=pk)
    st = request.POST.get('status')
    if st in dict(Booking.STATUS_CHOICES):
        b.status = st
        b.save()
    ps = request.POST.get('pay_status')
    pay = b.payment_set.first()
    if pay and ps in dict(Payment.STATUS_CHOICES):
        pay.status = ps
        pay.save()
    messages.success(request, 'Status booking diperbarui.')
    return redirect('app:dashboard')


def _foto_admin(request):
    ua = UserAdmin.objects.filter(username=request.user).first()
    return ua.photo if ua and ua.photo else None



# KATEGORI PAKET
@admin_required
def kategori_paket_list(request):
    return render(request, 'admin_super/kategori_paket_list.html', {
        'title': 'Kategori Paket', 'photo': _foto_admin(request),
        'kategori_list': KategoriPaket.objects.all(),
    })


@admin_required
def kategori_paket_tambah(request):
    form = KategoriPaketForm(request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            form.save()
            messages.success(request, 'Kategori paket berhasil ditambahkan!')
            return redirect('app:kategori_paket_list')
        messages.error(request, 'Gagal menyimpan. Periksa isian form.')
    return render(request, 'admin_super/kategori_paket_form.html', {
        'title': 'Tambah Kategori Paket', 'form': form, 'photo': _foto_admin(request)})


@admin_required
def kategori_paket_edit(request, pk):
    kategori = get_object_or_404(KategoriPaket, pk=pk)
    form = KategoriPaketForm(request.POST or None, instance=kategori)
    if request.method == 'POST':
        if form.is_valid():
            form.save()
            messages.success(request, 'Kategori paket berhasil diperbarui!')
            return redirect('app:kategori_paket_list')
        messages.error(request, 'Gagal menyimpan. Periksa isian form.')
    return render(request, 'admin_super/kategori_paket_form.html', {
        'title': 'Edit Kategori Paket', 'form': form, 'photo': _foto_admin(request)})


@admin_required
@require_POST
def kategori_paket_hapus(request, pk):
    kategori = get_object_or_404(KategoriPaket, pk=pk)
    nama = kategori.nama_kategori
    kategori.delete()
    messages.success(request, f'Kategori "{nama}" dihapus. Paket di dalamnya jadi tanpa kategori. '
                              'Lain kali cukup nonaktifkan saja supaya relasinya tidak hilang.')
    return redirect('app:kategori_paket_list')


# KELOLA PAKET
@admin_required
def paket_list(request):
    return render(request, 'admin_super/paket_list.html', {
        'title': 'Kelola Paket', 'photo': _foto_admin(request),
        'paket_list': Package.objects.select_related('kategori'),
    })


def _simpan_media(request, paket):
    for f in request.FILES.getlist('media_files'):
        MediaPaket.objects.create(package=paket, media=f)


@admin_required
def paket_tambah(request):
    form = PaketForm(request.POST or None, request.FILES or None)
    if request.method == 'POST':
        if form.is_valid():
            paket = form.save()
            _simpan_media(request, paket)
            messages.success(request, f'Paket "{paket.name}" berhasil ditambahkan!')
            return redirect('app:paket_list')
        messages.error(request, 'Gagal menyimpan paket. Periksa isian form.')
    return render(request, 'admin_super/paket_form.html', {
        'title': 'Tambah Paket', 'form': form, 'paket': None, 'photo': _foto_admin(request)})


@admin_required
def paket_edit(request, pk):
    paket = get_object_or_404(Package.objects.prefetch_related('media_paket'), pk=pk)
    form = PaketForm(request.POST or None, request.FILES or None, instance=paket)
    if request.method == 'POST':
        if form.is_valid():
            form.save()
            _simpan_media(request, paket)
            messages.success(request, f'Paket "{paket.name}" berhasil diperbarui!')
            return redirect('app:paket_edit', pk=paket.pk)
        messages.error(request, 'Gagal menyimpan paket. Periksa isian form.')
    return render(request, 'admin_super/paket_form.html', {
        'title': 'Edit Paket', 'form': form, 'paket': paket, 'photo': _foto_admin(request)})


@admin_required
@require_POST
def paket_hapus(request, pk):
    paket = get_object_or_404(Package, pk=pk)
    try:
        nama = paket.name
        paket.delete()
        messages.success(request, f'Paket "{nama}" berhasil dihapus!')
    except ProtectedError:
        messages.error(request, 'Paket ini sudah dipakai di booking, jadi tidak bisa dihapus. '
                                'Ubah statusnya jadi Draft supaya tidak tampil di website.')
    return redirect('app:paket_list')


@admin_required
@require_POST
def paket_media_hapus(request, paket_pk, media_uuid):
    get_object_or_404(MediaPaket, id=media_uuid, package_id=paket_pk).delete()
    messages.success(request, 'Foto galeri berhasil dihapus!')
    return redirect('app:paket_edit', pk=paket_pk)
