# Amora Grads — Jasa Fotografi Wisuda

Website jasa foto wisuda (Django 5.2 + MariaDB/MySQL). Desain frontend HTML/CSS/JS milik sendiri.

## Struktur (mengikuti materi dosen)
- `core/` — project Django (`django-admin startproject core .`), `core/__init__.py` memuat PyMySQL
- `app/` — app Django (`python manage.py startapp app`): model, form, view, decorator, url
- `templates/` — `index`, `katalog`, `detail`, `booking`, `login`, `pengguna/`, `admin_super/`
- `static/` — `aset/` (gambar), `paket.js`, `auth.js`
- `compose.yml` — contoh MariaDB 10.11 + phpMyAdmin (Docker) dari materi dosen; project ini default memakai XAMPP

## Menjalankan (XAMPP + phpMyAdmin)
```
# Start Apache & MySQL di XAMPP, lalu buat database amoragrads di http://localhost/phpmyadmin
python -m venv venv
venv\Scripts\activate
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py seed      # isi paket, universitas, dan jadikan superuser Super Admin
python manage.py runserver
```
Role disimpan di kolom last_name: Super Admin atau Pengguna.
