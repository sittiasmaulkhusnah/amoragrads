import json

from django.contrib import messages
from django.db.models import Q, Sum
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie
from django.views.decorators.http import require_POST

from . import payments
from .decorators_admin import admin_required
from .decorators_pengguna import pengguna_required
from .models import Booking, Payment, UserAdmin, UserPengguna, WebSetting, rp
from .roles import ROLE_ADMIN
from .views import tanggal_pendek


def _urut(payment):
    return (0 if payment.jenis in ('dp', 'lunas') else 1, payment.pk)


def _json_login(request):
    if not request.user.is_authenticated:
        return JsonResponse({'ok': False, 'error': 'Silakan login dulu.'}, status=401)
    return None


def _payment_milik(request, pk):
    return Payment.objects.select_related('booking__package', 'booking__customer').filter(
        pk=pk, booking__customer=request.user).first()


def _wa_url(teks):
    ws = WebSetting.objects.first()
    nomor = (ws.wa_number if ws else '') or '6281296772025'
    from urllib.parse import quote
    return f'https://wa.me/{nomor}?text={quote(teks)}'


# checkout

@pengguna_required
@ensure_csrf_cookie
def checkout(request, pk):
    b = get_object_or_404(Booking.objects.select_related('package').prefetch_related('payment_set'),
                          pk=pk, customer=request.user)
    if b.status == 'cancelled':
        messages.error(request, 'Pesanan ini sudah dibatalkan.')
        return redirect('app:dashboard')
    cfg = payments.config()
    berikut = b.tagihan_berikut
    pel = [p for p in b.payment_set.all() if p.jenis == 'pelunasan' and p.status not in ('cancelled',)]
    pel = pel[0] if pel else None
    teks_wa = (f'Halo Amora Grads, saya ingin konfirmasi pembayaran {berikut.jenis_label} untuk pesanan '
               f'{b.package.name} ({tanggal_pendek(b.booking_date)} {b.booking_time:%H.%M}) '
               f'sebesar {rp(berikut.amount)}.') if berikut else ''
    return render(request, 'pengguna/checkout.html', {
        'title': 'Ringkasan Pesanan', 'b': b,
        'payments': sorted([p for p in b.payment_set.all() if p.status != 'cancelled'], key=_urut),
        'berikut': berikut, 'pelunasan': pel,
        'mid': {'enabled': cfg['enabled'], 'client_key': cfg['client_key'], 'snap_js': cfg['snap_js'],
                'production': cfg['production']},
        'bisa_lunas': b.dibayar == 0 and b.metode_bayar == 'dp',
        'wa_url': _wa_url(teks_wa) if berikut else '',
        'hari_ke_sesi': (b.booking_date - timezone.localdate()).days,
    })


@require_POST
def api_bayar_snap(request, pk):
    """Meminta token Snap (popup pembayaran Midtrans) untuk satu tagihan."""
    if (r := _json_login(request)):
        return r
    p = _payment_milik(request, pk)
    if not p:
        return JsonResponse({'ok': False, 'error': 'Tagihan tidak ditemukan.'}, status=404)
    b = p.booking
    if b.status == 'cancelled':
        return JsonResponse({'ok': False, 'error': 'Pesanan sudah dibatalkan.'}, status=400)
    if p.sudah_bayar:
        return JsonResponse({'ok': False, 'error': 'Tagihan ini sudah dibayar.'}, status=400)
    if p.status == 'cancelled':
        return JsonResponse({'ok': False, 'error': 'Tagihan ini sudah dibatalkan.'}, status=400)
    if p.jenis == 'pelunasan' and not any(x.sudah_bayar and x.jenis == 'dp' for x in b.payment_set.all()):
        return JsonResponse({'ok': False, 'error': 'Bayar DP terlebih dahulu.'}, status=400)
    cfg = payments.config()
    if not cfg['enabled']:
        return JsonResponse({'ok': True, 'manual': True})
    telp = getattr(getattr(request.user, 'userpengguna', None), 'telp', '') or ''
    try:
        token = payments.buat_snap(p, request.user, telp)
    except payments.PembayaranError as e:
        return JsonResponse({'ok': False, 'error': str(e)}, status=502)
    return JsonResponse({'ok': True, 'token': token, 'client_key': cfg['client_key'],
                         'snap_js': cfg['snap_js'], 'order_id': p.order_id})


@require_POST
def api_bayar_cek(request, pk):
    """Memeriksa status tagihan ke Midtrans lalu memperbarui data (dipanggil setelah popup selesai)."""
    if (r := _json_login(request)):
        return r
    p = _payment_milik(request, pk)
    if not p:
        return JsonResponse({'ok': False, 'error': 'Tagihan tidak ditemukan.'}, status=404)
    try:
        data = payments.cek_status(p)
        if data:
            payments.terapkan_status(p, data)
    except payments.PembayaranError as e:
        return JsonResponse({'ok': False, 'error': str(e)}, status=502)
    p.refresh_from_db()
    return JsonResponse({'ok': True, 'status': p.status, 'midtrans': p.midtrans_status,
                         'lunas': p.booking.status_bayar == 'lunas'})


@require_POST
def api_ubah_lunas(request, pk):
    """Pengguna memilih langsung melunasi (mengganti tagihan DP + pelunasan)."""
    if (r := _json_login(request)):
        return r
    b = Booking.objects.filter(pk=pk, customer=request.user).first()
    if not b or b.status == 'cancelled':
        return JsonResponse({'ok': False, 'error': 'Pesanan tidak ditemukan.'}, status=404)
    try:
        payments.ubah_ke_lunas(b)
    except payments.PembayaranError as e:
        return JsonResponse({'ok': False, 'error': str(e)}, status=400)
    return JsonResponse({'ok': True, 'checkout_url': f'/app/checkout/{b.pk}/'})


@csrf_exempt
@require_POST
def api_midtrans_notifikasi(request):
    """Webhook dari Midtrans (isi alamat ini di dashboard Midtrans: Settings > Payment > Notification URL)."""
    try:
        data = json.loads(request.body or '{}')
    except ValueError:
        return JsonResponse({'ok': False}, status=400)
    cfg = payments.config()
    if not cfg['enabled'] or not payments.signature_valid(data, cfg['server_key']):
        return JsonResponse({'ok': False, 'error': 'signature tidak valid'}, status=403)
    p = Payment.objects.filter(order_id=data.get('order_id', '')).first()
    if not p:
        return JsonResponse({'ok': False, 'error': 'order tidak dikenal'}, status=404)
    try:
        if int(float(data.get('gross_amount', 0))) != int(p.amount):
            return JsonResponse({'ok': False, 'error': 'nominal tidak cocok'}, status=400)
    except (TypeError, ValueError):
        return JsonResponse({'ok': False}, status=400)
    payments.terapkan_status(p, data)
    return JsonResponse({'ok': True})


# ====================================================== RIWAYAT & INVOICE
@pengguna_required
def riwayat_pembayaran(request):
    daftar = (Payment.objects.filter(booking__customer=request.user)
              .select_related('booking__package').order_by('-created_at'))
    dibayar = sum(p.amount for p in daftar if p.sudah_bayar)
    return render(request, 'pengguna/riwayat_pembayaran.html', {
        'title': 'Riwayat Pembayaran', 'daftar': daftar, 'total_dibayar': rp(dibayar),
    })


def invoice(request, pk):
    if not request.user.is_authenticated:
        return redirect('login')
    p = get_object_or_404(Payment.objects.select_related('booking__package', 'booking__customer'), pk=pk)
    if p.booking.customer != request.user and request.user.last_name != ROLE_ADMIN:
        raise Http404()
    return render(request, 'pengguna/invoice.html', {
        'p': p, 'b': p.booking, 'ws': WebSetting.objects.first(),
        'profil': UserPengguna.objects.filter(user=p.booking.customer).first(),
    })


# ====================================================== ADMIN: kelola pembayaran
@admin_required
def pembayaran_admin(request):
    status, jenis, q = request.GET.get('status', ''), request.GET.get('jenis', ''), (request.GET.get('q') or '').strip()
    daftar = Payment.objects.select_related('booking__package', 'booking__customer').order_by('-created_at')
    if status:
        daftar = daftar.filter(status=status)
    if jenis:
        daftar = daftar.filter(jenis=jenis)
    if q:
        daftar = daftar.filter(Q(order_id__icontains=q) | Q(booking__customer__first_name__icontains=q)
                               | Q(booking__customer__email__icontains=q) | Q(booking__package__name__icontains=q))
    semua = Payment.objects.exclude(booking__status='cancelled')
    belum = semua.filter(status__in=['pending', 'failed', 'expired'])
    ua = UserAdmin.objects.filter(username=request.user).first()
    return render(request, 'admin_super/pembayaran_list.html', {
        'title': 'Kelola Pembayaran', 'photo': ua.photo if ua and ua.photo else None,
        'daftar': daftar[:200], 'f_status': status, 'f_jenis': jenis, 'q': q,
        'status_choices': Payment.STATUS_CHOICES, 'jenis_choices': Payment.JENIS_CHOICES,
        'diterima': rp(semua.filter(status__in=['paid', 'partial']).aggregate(s=Sum('amount'))['s'] or 0),
        'belum_bayar': rp(belum.aggregate(s=Sum('amount'))['s'] or 0),
        'lewat_tempo': belum.filter(due_date__lt=timezone.localdate()).count(),
        'hari_ini': timezone.localdate(),
    })


@admin_required
@require_POST
def pembayaran_admin_status(request, pk):
    p = get_object_or_404(Payment, pk=pk)
    baru = request.POST.get('status')
    if baru not in ('paid', 'pending', 'failed', 'cancelled'):
        return redirect('app:pembayaran_list')
    if baru == 'paid':
        payments.tandai_bayar(p, metode=p.payment_method if p.payment_method not in ('', 'midtrans') else 'manual')
    else:
        p.status = baru
        p.save(update_fields=['status'])
    messages.success(request, f'Status {p.no_invoice} diubah.')
    return redirect(request.POST.get('next') or 'app:pembayaran_list')
