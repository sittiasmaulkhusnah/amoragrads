# Progres model user registes, login dan dashboard user
Pada tahap ini ditambahkan **backend Django + database MySQL** sehingga tersedia:

- Login dan register 
- **Dashboard pengguna** (profil dan riwayat booking)
- **Dashboard admin** (statistik, daftar booking, ubah status booking dan pembayaran)
- Pembatasan akses berdasarkan **role** (admin dan pengguna)
- Data booking tersimpan di database

---

## Teknologi

| Bagian | Teknologi |
|---|---|
| Frontend | HTML, CSS, JavaScript |
| Backend | Python, Django |
| Database | MySQL (XAMPP, dikelola lewat phpMyAdmin) |
| Driver database | PyMySQL |

---

## Struktur Project

```
AmoraGrads/
├── manage.py                  # pintu masuk perintah Django
├── config/                    # project Django (pengaturan utama)
│   ├── settings.py            # database, daftar app, bahasa, zona waktu
│   └── urls.py                # rute utama (/admin/, file statis, app booking)
├── booking/                   # app Django (logika website)
│   ├── models.py              # struktur tabel database
│   ├── views.py               # logika: login, register, profil, booking, dashboard
│   ├── urls.py                # daftar alamat halaman dan API
│   ├── decorators.py          # pembatas akses (admin_required)
│   ├── admin.py               # pendaftaran model ke panel /admin/
│   ├── migrations/            # riwayat pembuatan tabel
│   └── management/commands/
│       └── seed.py            # mengisi data paket + akun admin awal
├── index.html                 # beranda
├── katalog.html, detail.html  # katalog dan detail paket
├── booking.html               # form pemesanan (wajib login)
├── login.html                 # login dan register
├── profil.html                # dashboard pengguna
├── dashboard_admin.html       # dashboard admin
├── auth.js                    # status login di navbar (membaca /api/me/)
├── paket.js                   # data paket di sisi frontend
└── aset/                      # gambar dan logo
```

---

## Database

Database: `amoragrads`. Tabel utama yang dibuat dari `models.py`:

| Tabel | Isi | Kolom penting |
|---|---|---|
| `auth_user` | Akun (bawaan Django) | `username` (email), `first_name` (nama), `last_name` (**role**), `password` (ter-hash) |
| `booking_package` | Paket foto | `name`, `price`, `duration_minutes`, `edited_photo_count` |
| `booking_booking` | Pesanan | `customer`, `package`, `booking_date`, `booking_time`, `location`, `status` |
| `booking_payment` | Pembayaran | `booking`, `amount`, `payment_method`, `status`, `transaction_id` |
| `booking_profile` | Profil tambahan | `user`, `phone`, `dob`, `gender` |

Relasi singkat: satu pengguna dapat memiliki banyak booking, satu booking terkait satu paket, dan satu booking dapat memiliki data pembayaran.

**Status booking:** `pending` (menunggu pembayaran), `confirmed` (dikonfirmasi), `completed` (selesai), `cancelled` (dibatalkan).

**Status pembayaran:** `pending`, `partial` (DP dibayar), `paid` (lunas), `failed` (gagal).

---

## Sistem Role (Admin dan Pengguna)

Role disimpan di kolom `last_name` bawaan Django (sesuai arahan dosen):

| Nilai `last_name` | Role | Diarahkan ke |
|---|---|---|
| `super admin` | Admin | `/dashboard-admin/` |
| `pengguna` | Pengguna | `/profil.html` |

Cara kerjanya:

1. Pengguna login lewat `login.html`, lalu data dikirim ke `/api/login/`.
2. Django memeriksa email dan password ke tabel `auth_user`.
3. Jika benar, fungsi `_after_login()` di `views.py` memeriksa role dan mengarahkan ke dashboard yang sesuai.
4. Halaman admin dilindungi decorator `@admin_required` (`decorators.py`). Pengguna biasa yang mencoba membuka `/dashboard-admin/` dikembalikan ke profilnya.

Akun yang mendaftar lewat website otomatis diberi role `pengguna`.

---

## Fitur

### Dashboard Pengguna (`/profil.html`)
- Menampilkan dan mengubah data profil (nama, email, no HP, tanggal lahir, gender)
- Riwayat booking dari database (paket, jadwal, lokasi, harga, status)
- Logout

### Dashboard Admin (`/dashboard-admin/`)
- Statistik: jumlah pelanggan, total booking, booking menunggu pembayaran, total DP/pembayaran diterima
- Tabel booking terbaru (nama pelanggan, kontak, paket, jadwal, status)
- Mengubah **status booking** dan **status pembayaran** langsung dari tabel
- Daftar pelanggan terdaftar
- Tautan ke panel bawaan Django (`/admin/`) untuk mengelola paket

### Booking (`/booking.html`)
- Wajib login (jika belum, otomatis diarahkan ke halaman login)
- Data booking dan pembayaran DP tersimpan ke database
- Pengecekan jadwal bentrok: tanggal dan jam yang sama tidak dapat dipesan dua kali
- Tanggal yang sudah lewat ditolak

---

## Endpoint

| Alamat | Metode | Fungsi |
|---|---|---|
| `/api/register/` | POST | Daftar akun baru |
| `/api/login/` | POST | Login |
| `/api/logout/` | POST | Logout |
| `/api/me/` | GET | Status login dan role pengguna saat ini |
| `/api/profile/` | POST | Simpan perubahan profil |
| `/api/bookings/` | POST | Simpan booking baru |
| `/dashboard/` | GET | Redirect otomatis sesuai role |
| `/dashboard-admin/` | GET | Dashboard admin (khusus admin) |
| `/dashboard-admin/booking/<id>/` | POST | Ubah status booking dan pembayaran (khusus admin) |
| `/admin/` | GET | Panel admin bawaan Django |

---

## Perubahan pada Frontend Lama

| File | Sebelum | Sesudah |
|---|---|---|
| `auth.js` | Status login dari `localStorage` | Status login dari server (`/api/me/`); tombol menjadi Login, Profil, atau Dashboard sesuai role |
| `login.html` | Tombol submit hanya menyimpan tanda login palsu | Form mengirim data ke `/api/login/` dan `/api/register/`, menampilkan pesan error |
| `profil.html` | Data contoh (dummy) | Data profil dan riwayat booking dari database |
| `booking.html` | Hanya tampilan | Menyimpan booking ke database dan wajib login |
| `index.html` | Kode login lama di dalam halaman | Memakai `auth.js` |

---

## Cara Menjalankan

**Prasyarat:** Python, XAMPP (MySQL aktif), dan database kosong bernama `amoragrads` di phpMyAdmin.

```bash
# 1. Aktifkan virtual environment
venv\Scripts\activate

# 2. Install dependensi (jika belum)
pip install django pymysql

# 3. Buat tabel di database
python manage.py migrate

# 4. Isi data paket dan akun admin awal
python manage.py seed

# 5. Jalankan server
python manage.py runserver
```
