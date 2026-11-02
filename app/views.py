import json
from datetime import date, time

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Q, Sum
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.utils import timezone
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_POST

from .form_pengguna import LoginForm, RegisterForm
from .models import Booking, KategoriPaket, Package, Payment, UserAdmin, UserPengguna
from .roles import ROLE_ADMIN, ROLE_PENGGUNA

JAM_BOOKING = ['09.00', '10.30', '12.00', '13.30', '15.00', '16.30']   # sama dengan TIME_SLOTS di booking.html
STATUS_BISA_UBAH = ('pending', 'confirmed')

BULAN = ['Jan', 'Feb', 'Mar', 'Apr', 'Mei', 'Jun', 'Jul', 'Agu', 'Sep', 'Okt', 'Nov', 'Des']


def rupiah(n):
    return 'Rp ' + f'{n:,}'.replace(',', '.')


def tgl_booking(b):
    return f'{b.booking_date.day} {BULAN[b.booking_date.month - 1]} {b.booking_date.year} · {b.booking_time:%H.%M}'


# Halaman frontend
@ensure_csrf_cookie
def home(request):
    return render(request, 'index.html')


@ensure_csrf_cookie
def katalog(request):
    return render(request, 'katalog.html')


@ensure_csrf_cookie
def detail(request):
    return render(request, 'detail.html')


def paket_tersedia():
    """Paket yang tampil di website: status Tersedia dan kategorinya aktif (atau tanpa kategori)."""
    return (Package.objects.filter(status='Tersedia')
            .filter(Q(kategori__isnull=True) | Q(kategori__aktif=True))
            .select_related('kategori').prefetch_related('media_paket'))


def paket_untuk_frontend():
    data = []
    for p in paket_tersedia():
        item = {
            'id': p.slug,
            'badge': p.badge or None,
            'name': p.name,
            'people': p.peserta,
            'duration': f'{p.duration_minutes} Menit',
            'photos': p.hasil or ('Unlimited Foto Edit' if not p.edited_photo_count else f'{p.edited_photo_count} Foto Edit'),
            'price': rupiah(p.harga_akhir)[3:],
            'oldPrice': rupiah(p.price)[3:] if p.persentase_diskon else None,
            'diskon': p.persentase_diskon or None,
            'desc': p.deskripsi,
            'img': p.featured_image.url if p.featured_image else 'aset/logo.png',
            'kategori': p.kategori.nama_kategori if p.kategori else '',
        }
        if p.kicker:
            item['kicker'] = p.kicker
        if p.subtitle:
            item['subtitle'] = p.subtitle
        if p.deskripsi_lengkap:
            item['long'] = p.deskripsi_lengkap
        galeri = [m.media.url for m in p.media_paket.all()]
        if galeri:
            item['gallery'] = galeri
        if p.faq_json:
            try:
                item['faq'] = json.loads(p.faq_json)
            except ValueError:
                pass
        data.append(item)
    return data


def paket_js(request):
    """paket.js dibangkitkan dari database, jadi katalog/detail/beranda/booking otomatis ikut data terbaru."""
    js = render_to_string('paket.js', {
        'packages_json': json.dumps(paket_untuk_frontend(), ensure_ascii=False),
    })
    resp = HttpResponse(js, content_type='application/javascript; charset=utf-8')
    resp['Cache-Control'] = 'no-cache'
    return resp


@ensure_csrf_cookie
def paket_detail(request, kategori_slug, slug):
    """URL cantik /produk/<kategori>/<slug>/ -- tampilannya memakai detail.html."""
    return render(request, 'detail.html', {'paket_slug': slug})


@ensure_csrf_cookie
def booking_page(request):
    return render(request, 'booking.html')


#  Login, Register, Logout 
@ensure_csrf_cookie
def loginView(request):
    if request.user.is_authenticated:
        return redirect('app:dashboard')
    error = ''
    email = ''
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email'].strip()
            # boleh login dengan email atau username (mis. superuser "admin")
            u = (User.objects.filter(email__iexact=email).first()
                 or User.objects.filter(username__iexact=email).first())
            user = authenticate(request, username=u.username if u else email,
                                password=form.cleaned_data['password'])
            if user is not None:
                login(request, user)
                return redirect('app:dashboard')
        error = 'Email atau kata sandi salah.'
    return render(request, 'login.html', {
        'start_screen': 'login', 'login_error': error, 'email_value': email,
    })


@ensure_csrf_cookie
def registerView(request):
    if request.user.is_authenticated:
        return redirect('app:dashboard')
    errors, values = [], {}
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        values = {'nama': request.POST.get('nama', ''), 'email': request.POST.get('email', '')}
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Registrasi berhasil. Lengkapi profil Anda terlebih dahulu.')
            return redirect('app:dashboard')
        for field, errs in form.errors.items():
            for e in errs:
                errors.append(e)
    return render(request, 'login.html', {
        'start_screen': 'register', 'register_errors': errors, 'reg': values,
    })


def LogoutView(request):
    logout(request)
    return redirect('home')


#  Dashboard 
@login_required
def index(request):
    user = request.user
    # superuser dari "createsuperuser" otomatis dijadikan Super Admin
    if user.is_superuser and user.last_name not in (ROLE_ADMIN, ROLE_PENGGUNA):
        user.last_name = ROLE_ADMIN
        user.save()

    if user.last_name == ROLE_ADMIN:
        useradmin = UserAdmin.objects.filter(username=user).first()
        bookings = Booking.objects.select_related('customer', 'package').order_by('-created_at')
        diterima = Payment.objects.filter(status__in=['partial', 'paid']).aggregate(s=Sum('amount'))['s'] or 0
        rows = []
        for b in bookings[:30]:
            p = b.payment_set.first()
            ph = UserPengguna.objects.filter(user=b.customer).first()
            rows.append({'b': b, 'pay': p, 'tgl': tgl_booking(b), 'telp': ph.telp if ph else ''})
        return render(request, 'admin_super/index.html', {
            'title': 'Dashboard Admin',
            'photo': useradmin.photo if useradmin and useradmin.photo else None,
            'userdetail': useradmin,
            'total_pengguna': UserPengguna.objects.count(),
            'dikonfirmasi': bookings.filter(status='confirmed').count(),
            'total_booking': bookings.count(),
            'menunggu': bookings.filter(status='pending').count(),
            'total_paket': Package.objects.count(),
            'total_kategori': KategoriPaket.objects.count(),
            'diterima': rupiah(diterima),
            'rows': rows,
            'status_choices': Booking.STATUS_CHOICES,
            'pay_choices': Payment.STATUS_CHOICES,
        })

    elif user.last_name == ROLE_PENGGUNA:
        userC = UserPengguna.objects.filter(user=user).first()
        if not userC:
            messages.error(request, 'Profil pengguna belum tersedia.')
            return redirect('app:profile_pengguna')
        if not userC.telp or not userC.universitas:
            messages.error(request, 'Harap lengkapi profil Anda terlebih dahulu.')
            return redirect('app:profile_pengguna')
        status_map = {'pending': 'Terjadwal', 'confirmed': 'Terjadwal',
                      'completed': 'Selesai', 'cancelled': 'Dibatalkan'}
        orders = [{
            'pkg': b.package.name,
            'date': tgl_booking(b),
            'location': b.location,
            'price': rupiah(b.package.harga_akhir),
            'status': status_map.get(b.status, 'Terjadwal'),
            'id': b.pk,
            'raw_date': b.booking_date.isoformat(),
            'raw_time': f'{b.booking_time:%H.%M}',
            'bisa_ubah': b.status in STATUS_BISA_UBAH and b.booking_date >= timezone.localdate(),
        } for b in Booking.objects.filter(customer=user).select_related('package').order_by('-created_at')]
        return render(request, 'pengguna/index.html', {
            'title': 'Dashboard',
            'nama': user.first_name or user.username,
            'amora_orders': orders,
            'total': len(orders),
            'terjadwal': sum(1 for o in orders if o['status'] == 'Terjadwal'),
            'selesai': sum(1 for o in orders if o['status'] == 'Selesai'),
        })

    logout(request)
    messages.error(request, 'Role akun belum diatur.')
    return redirect('login')


# ======================= API kecil untuk frontend =======================
@ensure_csrf_cookie
def api_me(request):
    u = request.user
    if not u.is_authenticated:
        return JsonResponse({'loggedIn': False})
    return JsonResponse({
        'loggedIn': True, 'name': u.first_name, 'email': u.email,
        'role': 'admin' if u.last_name == ROLE_ADMIN or u.is_superuser else 'pengguna',
    })


@require_POST
def api_bookings(request):
    if not request.user.is_authenticated:
        return JsonResponse({'ok': False, 'error': 'Silakan login dulu.'}, status=401)
    try:
        d = json.loads(request.body or '{}')
    except ValueError:
        d = {}
    paket = paket_tersedia().filter(name=d.get('package')).first()
    if not paket:
        return JsonResponse({'ok': False, 'error': 'Paket tidak ditemukan.'}, status=400)
    try:
        tgl = date(int(d['y']), int(d['m']) + 1, int(d['d']))  # bulan dari JavaScript mulai 0
        jam, menit = str(d['time']).replace(':', '.').split('.')
        waktu = time(int(jam), int(menit))
    except (KeyError, ValueError, TypeError):
        return JsonResponse({'ok': False, 'error': 'Tanggal atau jam tidak valid.'}, status=400)
    if tgl < timezone.localdate():
        return JsonResponse({'ok': False, 'error': 'Tanggal sudah lewat.'}, status=400)
    if Booking.objects.filter(booking_date=tgl, booking_time=waktu).exclude(status='cancelled').exists():
        return JsonResponse({'ok': False, 'error': 'Jadwal itu sudah terisi.'}, status=409)
    b = Booking.objects.create(customer=request.user, package=paket, booking_date=tgl,
                               booking_time=waktu, location='Ditentukan via WhatsApp')
    Payment.objects.create(booking=b, amount=int(d.get('dp') or 50000), payment_method='QRIS',
                           transaction_id=str(d.get('order_id') or '')[:150])
    if d.get('phone'):
        up, _ = UserPengguna.objects.get_or_create(user=request.user)
        if not up.telp:
            up.telp = str(d['phone'])[:20]
            up.save()
    return JsonResponse({'ok': True, 'id': b.pk})


def _booking_milik(request, pk):
    return Booking.objects.filter(pk=pk, customer=request.user).first()


@require_POST
def api_booking_batal(request, pk):
    """Pengguna membatalkan bookingnya sendiri (hanya yang masih menunggu / sudah dikonfirmasi)."""
    if not request.user.is_authenticated:
        return JsonResponse({'ok': False, 'error': 'Silakan login dulu.'}, status=401)
    b = _booking_milik(request, pk)
    if not b:
        return JsonResponse({'ok': False, 'error': 'Booking tidak ditemukan.'}, status=404)
    if b.status not in STATUS_BISA_UBAH:
        return JsonResponse({'ok': False, 'error': 'Booking ini tidak bisa dibatalkan.'}, status=400)
    b.status = 'cancelled'
    b.save()
    return JsonResponse({'ok': True})


@require_POST
def api_booking_reschedule(request, pk):
    """Pengguna memindahkan jadwal bookingnya ke tanggal/jam lain yang masih kosong."""
    if not request.user.is_authenticated:
        return JsonResponse({'ok': False, 'error': 'Silakan login dulu.'}, status=401)
    b = _booking_milik(request, pk)
    if not b:
        return JsonResponse({'ok': False, 'error': 'Booking tidak ditemukan.'}, status=404)
    if b.status not in STATUS_BISA_UBAH:
        return JsonResponse({'ok': False, 'error': 'Booking ini tidak bisa dijadwalkan ulang.'}, status=400)
    try:
        d = json.loads(request.body or '{}')
        tgl = date.fromisoformat(str(d.get('date')))
        jam_str = str(d.get('time')).replace(':', '.')
        if jam_str not in JAM_BOOKING:
            raise ValueError
        jam, menit = jam_str.split('.')
        waktu = time(int(jam), int(menit))
    except (ValueError, TypeError):
        return JsonResponse({'ok': False, 'error': 'Tanggal atau jam tidak valid.'}, status=400)
    if tgl < timezone.localdate():
        return JsonResponse({'ok': False, 'error': 'Tanggal sudah lewat.'}, status=400)
    bentrok = (Booking.objects.filter(booking_date=tgl, booking_time=waktu)
               .exclude(status='cancelled').exclude(pk=b.pk).exists())
    if bentrok:
        return JsonResponse({'ok': False, 'error': 'Jadwal itu sudah terisi. Pilih tanggal atau jam lain.'}, status=409)
    b.booking_date, b.booking_time = tgl, waktu
    b.save()
    return JsonResponse({'ok': True})
