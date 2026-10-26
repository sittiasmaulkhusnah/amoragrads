import json
from datetime import date, time

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.db.models import Sum
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_POST

from .decorators import ROLE_USER, admin_required, is_admin
from .models import Booking, Package, Payment, Profile


# ======================= Halaman frontend =======================
@ensure_csrf_cookie
def home(request):
    return render(request, 'index.html')


@ensure_csrf_cookie
def katalog(request):
    return render(request, 'katalog.html')


@ensure_csrf_cookie
def detail(request):
    return render(request, 'detail.html')


@ensure_csrf_cookie
def booking_page(request):
    return render(request, 'booking.html')


@ensure_csrf_cookie
def login_page(request):
    if request.user.is_authenticated:
        return redirect(_after_login(request.user))
    return render(request, 'login.html')


# ======================= Helper =======================
def _after_login(user):
    return '/dashboard-admin/' if is_admin(user) else '/profil.html'


def _json(request):
    try:
        return json.loads(request.body or '{}')
    except ValueError:
        return {}


def _profile(user):
    p, _ = Profile.objects.get_or_create(user=user)
    return p


def _rupiah(n):
    return 'Rp ' + f'{n:,}'.replace(',', '.')


BULAN = ['Jan', 'Feb', 'Mar', 'Apr', 'Mei', 'Jun', 'Jul', 'Agu', 'Sep', 'Okt', 'Nov', 'Des']


def _tgl(b):
    return f'{b.booking_date.day} {BULAN[b.booking_date.month - 1]} {b.booking_date.year} · {b.booking_time:%H.%M}'


def _user_data(user):
    p = _profile(user)
    return {
        'loggedIn': True,
        'name': user.first_name,
        'email': user.email,
        'role': 'admin' if is_admin(user) else 'pengguna',
        'phone': p.phone,
        'dob': p.dob.isoformat() if p.dob else '',
        'gender': p.gender or 'Perempuan',
        'avatar': None,
    }


# ======================= Dashboard pengguna (profil + riwayat booking) =======================
@ensure_csrf_cookie
def profil(request):
    if not request.user.is_authenticated:
        return redirect('/login.html')
    if is_admin(request.user):
        return redirect('/dashboard-admin/')
    status_map = {'pending': 'Terjadwal', 'confirmed': 'Terjadwal',
                  'completed': 'Selesai', 'cancelled': 'Dibatalkan'}
    orders = [{
        'pkg': b.package.name,
        'date': _tgl(b),
        'location': b.location,
        'price': _rupiah(b.package.price),
        'status': status_map.get(b.status, 'Terjadwal'),
    } for b in Booking.objects.filter(customer=request.user).select_related('package').order_by('-created_at')]
    return render(request, 'profil.html', {
        'amora_user': _user_data(request.user),
        'amora_orders': orders,
    })


def dashboard(request):
    """Redirect sesuai role: super admin -> dashboard admin, pengguna -> profil/dashboard pengguna."""
    if not request.user.is_authenticated:
        return redirect('/login.html')
    return redirect(_after_login(request.user))


# ======================= API: auth =======================
@ensure_csrf_cookie
def api_me(request):
    if not request.user.is_authenticated:
        return JsonResponse({'loggedIn': False})
    return JsonResponse(_user_data(request.user))


@require_POST
def api_register(request):
    d = _json(request)
    nama = (d.get('nama') or '').strip()
    email = (d.get('email') or '').strip().lower()
    password = d.get('password') or ''
    if not nama or not email:
        return JsonResponse({'ok': False, 'error': 'Nama dan email wajib diisi.'}, status=400)
    if '@' not in email or '.' not in email.split('@')[-1]:
        return JsonResponse({'ok': False, 'error': 'Format email tidak valid.'}, status=400)
    if len(password) < 6:
        return JsonResponse({'ok': False, 'error': 'Kata sandi minimal 6 karakter.'}, status=400)
    if User.objects.filter(username=email).exists():
        return JsonResponse({'ok': False, 'error': 'Email sudah terdaftar. Silakan masuk.'}, status=400)
    user = User.objects.create_user(username=email, email=email, password=password,
                                    first_name=nama, last_name=ROLE_USER)
    Profile.objects.create(user=user, phone=(d.get('phone') or '').strip())
    login(request, user)
    return JsonResponse({'ok': True, 'redirect': _after_login(user)})


@require_POST
def api_login(request):
    d = _json(request)
    user = authenticate(request, username=(d.get('email') or '').strip().lower(),
                        password=d.get('password') or '')
    if user is None:
        return JsonResponse({'ok': False, 'error': 'Email atau kata sandi salah.'}, status=401)
    login(request, user)
    return JsonResponse({'ok': True, 'redirect': _after_login(user)})


@require_POST
def api_logout(request):
    logout(request)
    return JsonResponse({'ok': True})


@require_POST
def api_profile(request):
    if not request.user.is_authenticated:
        return JsonResponse({'ok': False}, status=401)
    d = _json(request)
    u, p = request.user, _profile(request.user)
    if d.get('name'):
        u.first_name = d['name'].strip()[:150]
    email = (d.get('email') or '').strip().lower()
    if email and email != u.username:
        if User.objects.filter(username=email).exists():
            return JsonResponse({'ok': False, 'error': 'Email sudah dipakai.'}, status=400)
        u.username = u.email = email
    u.save()
    p.phone = (d.get('phone') or p.phone)[:20]
    p.gender = (d.get('gender') or p.gender)[:20]
    try:
        p.dob = date.fromisoformat(d['dob']) if d.get('dob') else p.dob
    except ValueError:
        pass
    p.save()
    return JsonResponse({'ok': True})


# ======================= API: booking =======================
@require_POST
def api_bookings(request):
    if not request.user.is_authenticated:
        return JsonResponse({'ok': False, 'error': 'Silakan login dulu.'}, status=401)
    d = _json(request)
    paket = Package.objects.filter(name=d.get('package')).first()
    if not paket:
        return JsonResponse({'ok': False, 'error': 'Paket tidak ditemukan.'}, status=400)
    try:
        tgl = date(int(d['y']), int(d['m']) + 1, int(d['d']))   # bulan dari JS mulai 0
        jam, menit = str(d['time']).replace(':', '.').split('.')
        waktu = time(int(jam), int(menit))
    except (KeyError, ValueError, TypeError):
        return JsonResponse({'ok': False, 'error': 'Tanggal atau jam tidak valid.'}, status=400)
    if tgl < date.today():
        return JsonResponse({'ok': False, 'error': 'Tanggal sudah lewat.'}, status=400)
    if Booking.objects.filter(booking_date=tgl, booking_time=waktu).exclude(status='cancelled').exists():
        return JsonResponse({'ok': False, 'error': 'Jadwal itu sudah terisi.'}, status=409)

    b = Booking.objects.create(customer=request.user, package=paket, booking_date=tgl,
                               booking_time=waktu, location='Ditentukan via WhatsApp')
    Payment.objects.create(booking=b, amount=int(d.get('dp') or 50000), payment_method='QRIS',
                           transaction_id=str(d.get('order_id') or '')[:150])
    p = _profile(request.user)
    if d.get('phone'):
        p.phone = str(d['phone'])[:20]
        p.save()
    return JsonResponse({'ok': True, 'id': b.pk})


# ======================= Dashboard admin =======================
@admin_required
def dashboard_admin(request):
    bookings = Booking.objects.select_related('customer', 'package').prefetch_related('payment_set').order_by('-created_at')
    diterima = Payment.objects.filter(status__in=['partial', 'paid']).aggregate(s=Sum('amount'))['s'] or 0
    customers = User.objects.filter(last_name=ROLE_USER).order_by('-date_joined')
    rows = []
    for b in bookings[:50]:
        pay = b.payment_set.first()
        rows.append({'b': b, 'pay': pay, 'tgl': _tgl(b), 'phone': _profile(b.customer).phone})
    return render(request, 'dashboard_admin.html', {
        'admin_name': request.user.first_name or request.user.username,
        'total_customer': customers.count(),
        'total_booking': bookings.count(),
        'menunggu': bookings.filter(status='pending').count(),
        'diterima': _rupiah(diterima),
        'rows': rows,
        'customers': customers[:15],
        'status_choices': Booking.STATUS_CHOICES,
        'pay_choices': Payment.STATUS_CHOICES,
    })


@admin_required
@require_POST
def admin_update_booking(request, pk):
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
    return redirect('/dashboard-admin/')
