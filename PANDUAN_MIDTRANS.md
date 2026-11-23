# Panduan Midtrans (Sandbox) untuk Amora Grads

Sandbox = mode uji coba Midtrans. Tidak butuh persetujuan akun dan tidak memakai uang sungguhan,
jadi cocok untuk tugas dan demo.

## 1. Ambil kunci Sandbox
1. Buka https://dashboard.sandbox.midtrans.com dan login dengan akun Midtrans-mu.
2. Pastikan environment yang aktif **Sandbox** (bukan Production).
3. Menu **Settings > Access Keys**, salin:
   - **Client Key** (diawali `SB-Mid-client-`)
   - **Server Key** (diawali `SB-Mid-server-`), rahasia, jangan di-commit ke GitHub.

## 2. Pasang di website
Login admin > **Pengaturan Website** > bagian paling bawah:
- Midtrans Client Key: tempel
- Midtrans Server Key: tempel
- Mode Production: **jangan dicentang**
Klik Simpan. Kunci disimpan di database (bukan di file kode), jadi aman dari GitHub.

## 3. Coba bayar
1. Login sebagai pengguna > Katalog > pilih paket > Booking (DP atau lunas).
2. Di halaman Ringkasan Pesanan klik **Bayar**. Popup Midtrans terbuka.
3. Pilih metode (QRIS / Virtual Account / kartu), lalu selesaikan di simulator:
   - QRIS dan Virtual Account: https://simulator.sandbox.midtrans.com
   - Kartu uji: lihat https://docs.midtrans.com (bagian Testing / Test Card)
4. Setelah bayar, status otomatis diperbarui. Kalau belum berubah, klik
   **Saya sudah bayar, cek status**.

## 4. Notifikasi otomatis (opsional)
Di komputer lokal, Midtrans tidak bisa menghubungi `127.0.0.1`. Itu tidak masalah, karena website
memeriksa status sendiri setelah popup selesai. Kalau website sudah online (atau memakai ngrok),
isi di dashboard Midtrans: **Settings > Configuration > Payment Notification URL**:

    https://DOMAIN-KAMU/app/api/midtrans/notifikasi/

## 5. Tanpa Midtrans (mode manual)
Kosongkan kedua kunci. Tombol Bayar akan menampilkan tombol WhatsApp ke admin, lalu admin menandai
pembayaran **Lunas** di menu **Kelola Pembayaran**.

## 6. Production (uang sungguhan)
Butuh akun Midtrans yang sudah disetujui. Setelah disetujui, tempel kunci Production dan centang
**Mode Production**. Selama belum disetujui, tetap pakai Sandbox.

## Masalah umum
- Pesan "Midtrans menolak permintaan" atau 401: kunci salah, atau kunci Sandbox dipakai dengan
  Mode Production dicentang (atau sebaliknya).
- Popup tidak muncul: cek koneksi internet (script Snap dimuat dari Midtrans).
