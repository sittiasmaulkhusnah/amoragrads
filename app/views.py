import json
import hashlib
import requests
from datetime import date, time, timedelta        # tambah timedelta
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie   # tambah csrf_exempt
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
from .models import (Article, Booking, HeroSlide, KategoriPaket, KerjaSama, Package, Payment, Page,
                     UserAdmin, UserPengguna, WebSetting, nominal_dp_aktif)
from .views_konten import konteks_publik
from .roles import ROLE_ADMIN, ROLE_PENGGUNA

JAM_BOOKING = ['09.00', '10.30', '12.00', '13.30', '15.00', '16.30']   # sama dengan TIME_SLOTS di booking.html
STATUS_BISA_UBAH = ('pending', 'confirmed')



def _auth_midtrans():
    return (settings.MIDTRANS_SERVER_KEY, '')   # Basic Auth: Server Key sebagai username


LABEL_JENIS = {'dp': 'DP', 'full': 'Pembayaran', 'pelunasan': 'Pelunasan'}


def _buat_snap_token(order_id, paket, user, phone, amount, jenis='dp'):
    payload = {
        'transaction_details': {'order_id': order_id, 'gross_amount': amount},
        'item_details': [{'id': f'PKG-{paket.pk}', 'price': amount, 'quantity': 1,
                          'name': f'{LABEL_JENIS.get(jenis, "Pembayaran")} {paket.name}'[:50]}],
        'customer_details': {'first_name': (user.first_name or user.username)[:50],
                             'email': user.email, 'phone': phone},
        'expiry': {'unit': 'minutes', 'duration': 15},
    }
    r = requests.post(settings.MIDTRANS_SNAP_URL, json=payload, auth=_auth_midtrans(), timeout=20)
    r.raise_for_status()
    return r.json()['token']


def _terapkan_status(payment, data):
    """Terjemahkan status Midtrans ke status Payment dan Booking di database kita."""
    ts = data.get('transaction_status')
    fraud = data.get('fraud_status', 'accept')
    b = payment.booking
    if ts in ('settlement', 'capture') and fraud == 'accept':
            payment.status = 'partial' if payment.jenis == 'dp' else 'paid'   # DP Dibayar / Lunas
    if data.get('payment_type'):
            payment.payment_method = str(data['payment_type'])[:50]
    if b.status == 'pending':
            b.status = 'confirmed'
    elif ts in ('deny', 'cancel', 'expire', 'failure'):
        payment.status = 'failed'
        # hanya pembayaran pertama (DP / bayar penuh) yang menentukan nasib booking;
        # pelunasan yang gagal cuma bisa dicoba lagi, booking tetap aman
        if payment.jenis in ('dp', 'full') and b.status == 'pending':
            b.status = 'cancelled'                      # jadwal dilepas lagi
    elif payment.status not in ('partial', 'paid'):
        payment.status = 'pending'
    payment.save()
    b.save()

def _bersihkan_pending():
    """Booking Midtrans yang tidak dibayar > 20 menit dibatalkan supaya jadwalnya bebas lagi."""
    batas = timezone.now() - timedelta(minutes=20)
    lama = Booking.objects.filter(status='pending', created_at__lt=batas,
                                  payment__payment_method='Midtrans',
                                  payment__status='pending').distinct()
    for b in lama:
        b.payment_set.filter(status='pending').update(status='failed')
        b.status = 'cancelled'
        b.save()

BULAN = ['Jan', 'Feb', 'Mar', 'Apr', 'Mei', 'Jun', 'Jul', 'Agu', 'Sep', 'Okt', 'Nov', 'Des']


def rupiah(n):
    return 'Rp ' + f'{n:,}'.replace(',', '.')

    return 'Rp ' + f'{n:,}'.replace(',', '.')


def wa_link(telp, teks):
    from urllib.parse import quote
    digit = ''.join(ch for ch in (telp or '') if ch.isdigit())
    if digit.startswith('0'):
        digit = '62' + digit[1:]
    if not digit:
        return ''
    return f'https://wa.me/{digit}?text={quote(teks)}'


def tgl_pendek(d):
    return f'{d.day} {BULAN[d.month - 1]} {d.year}'


def tgl_booking(b):
    return f'{b.booking_date.day} {BULAN[b.booking_date.month - 1]} {b.booking_date.year} · {b.booking_time:%H.%M}'


# Halaman frontend
@ensure_csrf_cookie
def home(request):
    ctx = konteks_publik()
    ctx.update({
        'hero_slides': HeroSlide.objects.filter(is_active=True),
        'artikel_terbaru' : Article.objects.filter(status='published').order_by('-created_at')[:3],
        'mitra': KerjaSama.objects.all(),
    })
    return render(request, 'index.html', ctx)


@ensure_csrf_cookie
def katalog(request):
    return render(request, 'katalog.html', konteks_publik())


@ensure_csrf_cookie
def detail(request):
    return render(request, 'detail.html', konteks_publik())


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
        'wa_number': (WebSetting.objects.first().wa_number if WebSetting.objects.exists() else '') or '6281296772025',
    })
    resp = HttpResponse(js, content_type='application/javascript; charset=utf-8')
    resp['Cache-Control'] = 'no-cache'
    return resp


@ensure_csrf_cookie
def paket_detail(request, kategori_slug, slug):
    """URL cantik /produk/<kategori>/<slug>/ -- tampilannya memakai detail.html."""
    ctx = konteks_publik()
    ctx['paket_slug'] = slug
    return render(request, 'detail.html', ctx)


@ensure_csrf_cookie
def booking_page(request):
    ctx = konteks_publik()
    ctx['midtrans_client_key'] = settings.MIDTRANS_CLIENT_KEY
    ctx['midtrans_snap_js'] = settings.MIDTRANS_SNAP_JS
    ctx['dp_amount'] = nominal_dp_aktif()
    return render(request, 'booking.html', ctx)


# Login, Register, Logout
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


# ======================= Dashboard (role di kolom last_name) =======================
@login_required
def index(request):
    user = request.user
    # superuser dari "createsuperuser" otomatis dijadikan Super Admin
    if user.is_superuser and user.last_name not in (ROLE_ADMIN, ROLE_PENGGUNA):
        user.last_name = ROLE_ADMIN
        user.save()

    if user.last_name == ROLE_ADMIN:
        useradmin = UserAdmin.objects.filter(username=user).first()
        bookings = (Booking.objects.select_related('customer', 'package')
                    .prefetch_related('payment_set').order_by('-created_at'))
        diterima = Payment.objects.filter(status__in=['partial', 'paid']).aggregate(s=Sum('amount'))['s'] or 0
        rows = []
        for b in bookings[:30]:
            ph = UserPengguna.objects.filter(user=b.customer).first()
            rows.append({'b': b, 'tgl': tgl_booking(b), 'telp': ph.telp if ph else '',
                         'dibayar': rupiah(b.total_dibayar), 'total': rupiah(b.harga_total),
                         'sisa': rupiah(b.sisa_tagihan),
                         'bisa_tandai_lunas': b.status != 'cancelled' and b.sisa_tagihan > 0})

        hari_ini = timezone.localdate()
        pengingat = []
        for b in (bookings.filter(status='confirmed', booking_date__gte=hari_ini,
                                  booking_date__lte=hari_ini + timedelta(days=3))
                  .order_by('booking_date', 'booking_time')):
            if b.sisa_tagihan <= 0:
                continue
            ph = UserPengguna.objects.filter(user=b.customer).first()
            nama = b.customer.first_name or b.customer.username
            teks = (f'Halo kak {nama}, pengingat dari Amora Grads: sesi foto {b.package.name} kakak '
                    f'tanggal {tgl_pendek(b.booking_date)} jam {b.booking_time:%H.%M}. Sisa pembayaran '
                    f'{rupiah(b.sisa_tagihan)} mohon dilunasi paling lambat {tgl_pendek(b.batas_pelunasan)} '
                    f'lewat Dashboard > Riwayat booking > Lunasi. Terima kasih!')
            pengingat.append({'b': b, 'nama': nama, 'tgl': tgl_booking(b), 'sisa': rupiah(b.sisa_tagihan),
                              'batas': tgl_pendek(b.batas_pelunasan),
                              'hari_lagi': (b.booking_date - hari_ini).days,
                              'wa': wa_link(ph.telp if ph else '', teks)})
        return render(request, 'admin_super/index.html', {
            'title': 'Dashboard Admin',
            'pengingat': pengingat,
            'photo': useradmin.photo if useradmin and useradmin.photo else None,
            'userdetail': useradmin,
            'total_pengguna': UserPengguna.objects.count(),
            'dikonfirmasi': bookings.filter(status='confirmed').count(),
            'total_booking': bookings.count(),
            'menunggu': bookings.filter(status='pending').count(),
            'total_paket': Package.objects.count(),
            'total_kategori': KategoriPaket.objects.count(),
            'total_artikel': Article.objects.count(),
            'total_halaman': Page.objects.count(),
            'diterima': rupiah(diterima),
            'rows': rows,
            'status_choices': Booking.STATUS_CHOICES,
            'dp_amount': nominal_dp_aktif(),
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
            'price': rupiah(b.harga_total),
            'dibayar': rupiah(b.total_dibayar),
            'sisa': rupiah(b.sisa_tagihan),
            'status_bayar': b.status_bayar_label,
            'batas_lunas': tgl_pendek(b.batas_pelunasan),
            'bisa_lunas': (b.status == 'confirmed' and b.sisa_tagihan > 0
                           and b.booking_date >= timezone.localdate()),
            'status': status_map.get(b.status, 'Terjadwal'),
            'id': b.pk,
            'raw_date': b.booking_date.isoformat(),
            'raw_time': f'{b.booking_time:%H.%M}',
            'bisa_ubah': b.status in STATUS_BISA_UBAH and b.booking_date >= timezone.localdate(),
        } for b in (Booking.objects.filter(customer=user).select_related('package')
                    .prefetch_related('payment_set').order_by('-created_at'))]
        hari_ini = timezone.localdate()
        pengingat = [{'pkg': o['pkg'], 'sisa': o['sisa'], 'batas': o['batas_lunas']}
                     for o in orders if o['bisa_lunas'] and
                     (date.fromisoformat(o['raw_date']) - hari_ini).days <= 3]
        return render(request, 'pengguna/index.html', {
            'title': 'Dashboard',
            'pengingat': pengingat,
            'midtrans_client_key': settings.MIDTRANS_CLIENT_KEY,
            'midtrans_snap_js': settings.MIDTRANS_SNAP_JS,
            'nama': user.first_name or user.username,
            'amora_orders': orders,
            'total': len(orders),
            'terjadwal': sum(1 for o in orders if o['status'] == 'Terjadwal'),
            'selesai': sum(1 for o in orders if o['status'] == 'Selesai'),
        })

    logout(request)
    messages.error(request, 'Role akun belum diatur.')
    return redirect('login')


# API kecil untuk frontend
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
    _bersihkan_pending() 
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
    harga = paket.harga_akhir
    dp = nominal_dp_aktif()
    opsi = 'full' if d.get('opsi') == 'full' else 'dp'
    if opsi == 'dp' and dp >= harga:
        opsi = 'full'
    jumlah = harga if opsi == 'full' else dp
    b = Booking.objects.create(customer=request.user, package=paket, booking_date=tgl,
                               booking_time=waktu, location='Ditentukan via WhatsApp', total_harga=harga)
    phone = str(d.get('phone') or '')[:20]
    order_id = f'AG-{"DP" if opsi == "dp" else "FULL"}-{b.pk}-{timezone.now():%d%H%M%S}'
    pay = Payment.objects.create(booking=b, jenis=opsi, amount=jumlah, payment_method='Midtrans',
                                 transaction_id=order_id)
    if phone:
        up, _ = UserPengguna.objects.get_or_create(user=request.user)
        if not up.telp:
            up.telp = phone
            up.save()
    try:
        token = _buat_snap_token(order_id, paket, request.user, phone, jumlah, opsi)
    except Exception:
        b.status = 'cancelled'
        b.save()
        pay.status = 'failed'
        pay.save()
        return JsonResponse({'ok': False, 'error': 'Gagal menghubungi Midtrans. Coba lagi.'}, status=502)
    pay.snap_token = token
    pay.save()
    return JsonResponse({'ok': True, 'id': b.pk, 'token': token, 'opsi': opsi, 'amount': jumlah,
                         'sisa': harga - jumlah})


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

@require_POST
def api_booking_pelunasan(request, pk):
    if not request.user.is_authenticated:
        return JsonResponse({'ok': False, 'error': 'Silakan login dulu.'}, status=401)
    b = _booking_milik(request, pk)
    if not b:
        return JsonResponse({'ok': False, 'error': 'Booking tidak ditemukan.'}, status=404)
    if b.status != 'confirmed':
        return JsonResponse({'ok': False, 'error': 'Booking ini belum dikonfirmasi atau sudah tidak aktif.'}, status=400)
    sisa = b.sisa_tagihan
    if sisa <= 0:
        return JsonResponse({'ok': False, 'error': 'Booking ini sudah lunas.'}, status=400)
    if b.booking_date < timezone.localdate():
        return JsonResponse({'ok': False, 'error': 'Tanggal pemotretan sudah lewat. Hubungi admin.'}, status=400)

    sekarang = timezone.now()
    aktif = (b.payment_set.filter(jenis='pelunasan', status='pending', payment_method='Midtrans',
                                  created_at__gte=sekarang - timedelta(minutes=14))
             .exclude(snap_token='').order_by('-pk').first())
    if aktif and aktif.amount == sisa:
        return JsonResponse({'ok': True, 'id': b.pk, 'token': aktif.snap_token, 'amount': sisa})
    b.payment_set.filter(jenis='pelunasan', status='pending',
                         created_at__lt=sekarang - timedelta(minutes=20)).update(status='failed')

    order_id = f'AG-LUNAS-{b.pk}-{sekarang:%d%H%M%S}'
    pay = Payment.objects.create(booking=b, jenis='pelunasan', amount=sisa, payment_method='Midtrans',
                                 transaction_id=order_id)
    ph = UserPengguna.objects.filter(user=request.user).first()
    try:
        token = _buat_snap_token(order_id, b.package, request.user, ph.telp if ph else '', sisa, 'pelunasan')
    except Exception:
        pay.status = 'failed'
        pay.save()
        return JsonResponse({'ok': False, 'error': 'Gagal menghubungi Midtrans. Coba lagi.'}, status=502)
    pay.snap_token = token
    pay.save()
    return JsonResponse({'ok': True, 'id': b.pk, 'token': token, 'amount': sisa})

@require_POST
def api_cek_bayar(request, pk):
    """Tanya langsung ke Midtrans: order ini sudah dibayar belum?"""
    if not request.user.is_authenticated:
        return JsonResponse({'ok': False, 'error': 'Silakan login dulu.'}, status=401)
    pay = (Payment.objects.filter(booking__pk=pk, booking__customer=request.user)
           .order_by('-pk').first())
    if not pay:
        return JsonResponse({'ok': False, 'error': 'Pembayaran tidak ditemukan.'}, status=404)
    try:
        r = requests.get(settings.MIDTRANS_STATUS_URL.format(order_id=pay.transaction_id),
                         auth=_auth_midtrans(), timeout=20)
        data = r.json()
    except Exception:
        return JsonResponse({'ok': False, 'error': 'Gagal memeriksa ke Midtrans.'}, status=502)
    if 'transaction_status' in data:
        _terapkan_status(pay, data)
    return JsonResponse({'ok': True, 'status': pay.status})

@csrf_exempt
@require_POST
def midtrans_notifikasi(request):
    """Webhook: Midtrans yang menghubungi server kita (butuh URL publik, lihat catatan)."""
    try:
        d = json.loads(request.body or '{}')
    except ValueError:
        return HttpResponse(status=400)
    teks = f"{d.get('order_id')}{d.get('status_code')}{d.get('gross_amount')}{settings.MIDTRANS_SERVER_KEY}"
    if hashlib.sha512(teks.encode()).hexdigest() != d.get('signature_key'):
        return HttpResponse(status=403)          # bukan dari Midtrans
    pay = Payment.objects.filter(transaction_id=d.get('order_id')).first()
    if not pay:
        return HttpResponse(status=404)
    _terapkan_status(pay, d)
    return HttpResponse('OK')