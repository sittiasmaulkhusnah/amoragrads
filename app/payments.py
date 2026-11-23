"""Pembayaran: tagihan DP / pelunasan / lunas, dan integrasi Midtrans (Snap).

Alur singkat:
  1. Booking dibuat -> buat_tagihan() membuat baris Payment (DP + pelunasan H-1, atau satu tagihan lunas).
  2. Pengguna menekan "Bayar" -> buat_snap() meminta token ke Midtrans -> popup Snap terbuka.
  3. Setelah bayar, status dicek lewat cek_status() (dan/atau notifikasi dari Midtrans) -> terapkan_status().
Tanpa kunci Midtrans, aplikasi memakai mode manual (konfirmasi lewat WhatsApp + admin menandai lunas).
"""
import base64
import hashlib
import json
import urllib.error
import urllib.request
import uuid
from datetime import timedelta

from django.utils import timezone

from .models import Payment, WebSetting

PELUNASAN_H_MINUS = 1          # pelunasan jatuh tempo H-1 sesi foto
SNAP_BERLAKU_JAM = 20          # token Snap dipakai ulang kalau umurnya masih di bawah ini


class PembayaranError(Exception):
    pass


# ---------------------------------------------------------------- konfigurasi
def config():
    ws = WebSetting.objects.first()
    sk = (ws.midtrans_server_key if ws else '').strip()
    ck = (ws.midtrans_client_key if ws else '').strip()
    prod = bool(ws and ws.midtrans_production)
    return {
        'server_key': sk, 'client_key': ck, 'production': prod, 'enabled': bool(sk and ck),
        'snap_js': 'https://app.midtrans.com/snap/snap.js' if prod else 'https://app.sandbox.midtrans.com/snap/snap.js',
        'snap_api': 'https://app.midtrans.com/snap/v1/transactions' if prod
        else 'https://app.sandbox.midtrans.com/snap/v1/transactions',
        'status_api': ('https://api.midtrans.com/v2/%s/status' if prod else 'https://api.sandbox.midtrans.com/v2/%s/status'),
    }


def _request(method, url, server_key, payload=None):
    """Memanggil API Midtrans. Mengembalikan (kode_http, dict)."""
    kunci = base64.b64encode(f'{server_key}:'.encode()).decode()
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(url, data=data, method=method, headers={
        'Accept': 'application/json', 'Content-Type': 'application/json', 'Authorization': f'Basic {kunci}'})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return r.status, json.loads(r.read().decode() or '{}')
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read().decode() or '{}')
        except ValueError:
            return e.code, {}
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        raise PembayaranError('Tidak bisa terhubung ke Midtrans. Periksa koneksi internet.') from e


# ---------------------------------------------------------------- tagihan
def buat_tagihan(booking, metode):
    """Membuat baris Payment untuk booking baru.

    metode 'dp'    -> DP sekarang + pelunasan jatuh tempo H-1 sesi.
    metode 'lunas' -> satu tagihan lunas.
    Kalau sesi tinggal <= 1 hari lagi (atau DP >= total), otomatis jadi lunas.
    """
    total = booking.total_harga
    dp = booking.package.dp_amount
    hari = (booking.booking_date - timezone.localdate()).days
    if hari <= PELUNASAN_H_MINUS or dp <= 0 or dp >= total:
        metode = 'lunas'
    booking.metode_bayar = metode
    booking.save(update_fields=['metode_bayar'])
    if metode == 'lunas':
        Payment.objects.create(booking=booking, jenis='lunas', amount=total, payment_method='midtrans')
        return
    Payment.objects.create(booking=booking, jenis='dp', amount=dp, payment_method='midtrans')
    Payment.objects.create(booking=booking, jenis='pelunasan', amount=total - dp, payment_method='midtrans',
                           due_date=booking.booking_date - timedelta(days=PELUNASAN_H_MINUS))


def sinkron_jatuh_tempo(booking):
    """Dipanggil setelah jadwal diganti: jatuh tempo pelunasan ikut H-1 jadwal baru."""
    booking.payment_set.filter(jenis='pelunasan').exclude(status__in=['paid', 'partial']).update(
        due_date=booking.booking_date - timedelta(days=PELUNASAN_H_MINUS))


def batalkan_tagihan(booking):
    """Booking dibatalkan: tagihan yang belum dibayar ikut dibatalkan."""
    booking.payment_set.filter(status__in=['pending', 'failed', 'expired']).update(status='cancelled')


def ubah_ke_lunas(booking):
    """Mengganti DP+pelunasan menjadi satu tagihan lunas (hanya bila belum ada yang dibayar)."""
    if booking.dibayar > 0 or booking.metode_bayar == 'lunas':
        raise PembayaranError('Pilihan bayar lunas hanya bisa dipakai sebelum ada pembayaran masuk.')
    batalkan_tagihan(booking)
    booking.metode_bayar = 'lunas'
    booking.save(update_fields=['metode_bayar'])
    return Payment.objects.create(booking=booking, jenis='lunas', amount=booking.total_harga, payment_method='midtrans')


# ---------------------------------------------------------------- Midtrans
def _order_id(payment):
    return f'AG{payment.booking_id}-{payment.jenis[:3].upper()}-{uuid.uuid4().hex[:8].upper()}'


def buat_snap(payment, user, telepon=''):
    """Mengembalikan token Snap untuk satu tagihan (memakai ulang token yang masih berlaku)."""
    cfg = config()
    if not cfg['enabled']:
        raise PembayaranError('Midtrans belum dikonfigurasi.')
    if payment.sudah_bayar:
        raise PembayaranError('Tagihan ini sudah dibayar.')
    if (payment.snap_token and payment.order_id and payment.snap_at
            and payment.midtrans_status in ('', 'pending')
            and timezone.now() - payment.snap_at < timedelta(hours=SNAP_BERLAKU_JAM)):
        return payment.snap_token
    oid = _order_id(payment)
    nama_item = f'{payment.jenis_label} {payment.booking.package.name}'[:50]
    payload = {
        'transaction_details': {'order_id': oid, 'gross_amount': int(payment.amount)},
        'item_details': [{'id': f'{payment.jenis}-{payment.booking_id}', 'price': int(payment.amount),
                          'quantity': 1, 'name': nama_item}],
        'customer_details': {'first_name': (user.first_name or user.username)[:50], 'email': user.email,
                             'phone': telepon or ''},
    }
    kode, data = _request('POST', cfg['snap_api'], cfg['server_key'], payload)
    token = data.get('token')
    if kode not in (200, 201) or not token:
        pesan = '; '.join(data.get('error_messages', [])) or 'Midtrans menolak permintaan.'
        raise PembayaranError(pesan)
    payment.order_id, payment.snap_token, payment.snap_at = oid, token, timezone.now()
    payment.midtrans_status, payment.status = 'pending', 'pending'
    payment.save()
    return token


def cek_status(payment):
    """Menanyakan status transaksi ke Midtrans. None kalau transaksinya belum dibuat."""
    cfg = config()
    if not cfg['enabled']:
        raise PembayaranError('Midtrans belum dikonfigurasi.')
    if not payment.order_id:
        return None
    kode, data = _request('GET', cfg['status_api'] % payment.order_id, cfg['server_key'])
    if kode == 404 or str(data.get('status_code')) == '404':
        return None
    if kode != 200:
        raise PembayaranError(data.get('status_message') or 'Gagal memeriksa status pembayaran.')
    return data


def terapkan_status(payment, data):
    """Menerapkan hasil dari Midtrans (cek status atau notifikasi) ke Payment dan Booking. Aman dipanggil berulang."""
    status = data.get('transaction_status', '')
    fraud = data.get('fraud_status')
    payment.midtrans_status = status
    payment.transaction_id = data.get('transaction_id', payment.transaction_id) or ''
    if data.get('payment_type'):
        payment.payment_method = data['payment_type']
    if payment.sudah_bayar:
        payment.save()
        return payment
    if status == 'settlement' or (status == 'capture' and fraud in (None, 'accept')):
        tandai_bayar(payment, simpan=False)
    elif status in ('deny', 'cancel', 'failure'):
        payment.status = 'failed'
    elif status == 'expire':
        payment.status = 'expired'
    elif status == 'pending':
        payment.status = 'pending'
    payment.save()
    return payment


def tandai_bayar(payment, metode=None, simpan=True):
    payment.status = 'paid'
    payment.paid_at = timezone.now()
    if metode:
        payment.payment_method = metode
    if simpan:
        payment.save()
    b = payment.booking
    if b.status == 'pending' and payment.jenis in ('dp', 'lunas'):
        b.status = 'confirmed'
        b.save(update_fields=['status'])


def signature_valid(data, server_key):
    """Memeriksa signature_key pada notifikasi Midtrans."""
    mentah = f"{data.get('order_id', '')}{data.get('status_code', '')}{data.get('gross_amount', '')}{server_key}"
    return hashlib.sha512(mentah.encode()).hexdigest() == (data.get('signature_key') or '')
