# Amora Grads

Website jasa foto wisuda yang saya buat dengan Django dan MySQL (XAMPP). Tampilan frontend memakai HTML, CSS, dan JavaScript yang saya buat sendiri.

## Progres 3

Di progres ini, isi website tidak lagi ditulis langsung di file HTML. Semuanya disimpan di database dan bisa diubah lewat dashboard admin.

Yang sudah dikerjakan:

- **Artikel**: admin bisa menambah, mengubah, dan menghapus artikel lengkap dengan kategori, status (draft/published), foto, dan deskripsi SEO. Artikel yang berstatus published tampil di halaman `/artikel/` dan di beranda.
- **Kategori artikel**: dipakai sebagai filter di halaman artikel, dan bisa dinonaktifkan.
- **Halaman statis**: Tentang Kami, Kebijakan Privasi, dan Syarat & Ketentuan, diakses lewat `/halaman/<slug>/` dan muncul di footer.
- **Hero slide**: slider di beranda, isinya (judul, deskripsi, tombol, foto) diatur dari dashboard.
- **Mitra / kerja sama**: nama, logo, dan link mitra yang tampil di bagian "Mitra kami" di beranda.
- **Pengaturan website**: nama, alamat, nomor WhatsApp, link media sosial, logo, dan favicon. Datanya dipakai di footer dan tombol WhatsApp.
- **Stok pada paket**: kolom stok ditambahkan di data paket.

## Model

Universitas, UserAdmin, UserPengguna, KategoriPaket, Package, MediaPaket, Booking, Payment, Category, Article, Page, WebSetting, KerjaSama, dan HeroSlide.

## Struktur folder

- `core/` berisi pengaturan dan URL utama project
- `app/` berisi model, form, view, URL, dan migrasi
- `templates/` berisi halaman publik, `publik/`, `admin_super/`, dan `pengguna/`
- `static/` berisi gambar (`aset/`) dan `auth.js`
- `compose.yml` contoh MariaDB dan phpMyAdmin untuk Docker, tapi project ini saya jalankan dengan XAMPP

## Cara menjalankan

Pertama kali:

```
# nyalakan Apache dan MySQL di XAMPP, lalu buat database amoragrads di phpMyAdmin
python -m venv venv
venv\Scripts\activate
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py seed
python manage.py runserver
```

Selanjutnya cukup:

```
venv\Scripts\activate
python manage.py runserver
```

`python manage.py migrate` dijalankan lagi kalau ada migrasi baru.

Role akun disimpan di kolom `last_name`, yaitu Super Admin atau Pengguna. Dashboard admin ada di `http://127.0.0.1:8000/app/dashboard`.